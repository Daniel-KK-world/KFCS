import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import tkinter.font as tkFont
from PIL import Image, ImageTk, ImageDraw
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import csv
import pickle
import threading
import queue
from collections import deque, defaultdict
import random
import time
from deepface import DeepFace

# ================== CORE ATTENDANCE SYSTEM ==================
class AttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.attendance_log = []
        self.anti_spoofing_threshold = 0.3
        self.min_confidence = 0.6
        self.model_name = "Facenet"  # Can switch to "OpenFace" for faster but less accurate
        self.load_data()

    def load_data(self):
        """Load or initialize data files"""
        try:
            # Load face encodings
            if os.path.exists("facial_recognition.dat"):
                with open("facial_recognition.dat", "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get("encodings", [])
                    self.known_face_names = data.get("names", [])

            # Load attendance log
            if os.path.exists("attendance.csv"):
                with open("attendance.csv", "r") as f:
                    self.attendance_log = list(csv.DictReader(f))

        except Exception as e:
            print(f"Error loading data: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.attendance_log = []

        # Initialize files if they don't exist
        if not os.path.exists("facial_recognition.dat"):
            self.save_known_faces()
        if not os.path.exists("attendance.csv"):
            with open("attendance.csv", "w") as f:
                f.write("Name,Date,Check-in,Check-out\n")

    def save_known_faces(self):
        """Save current face encodings"""
        with open("facial_recognition.dat", "wb") as f:
            pickle.dump({
                "encodings": self.known_face_encodings,
                "names": self.known_face_names
            }, f)

    def save_attendance_data(self):
        """Save attendance records"""
        if self.attendance_log:
            with open("attendance.csv", "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.attendance_log[0].keys())
                writer.writeheader()
                writer.writerows(self.attendance_log)

    def register_new_user(self, name, face_images):
        """Register user with multiple face samples"""
        if not name or not face_images:
            return False

        encodings = []
        for img in face_images:
            try:
                embedding = DeepFace.represent(
                    img_path=img,
                    model_name=self.model_name,
                    enforce_detection=False,
                    detector_backend='skip'
                )
                if embedding:
                    encodings.append(np.array(embedding[0]['embedding']))
            except Exception as e:
                print(f"Error processing face sample: {e}")
                continue

        if encodings:
            avg_encoding = np.mean(encodings, axis=0)
            self.known_face_names.append(name)
            self.known_face_encodings.append(avg_encoding)
            self.save_known_faces()
            return True
        return False

    def recognize_face(self, face_image):
        """Recognize face from image"""
        if not self.known_face_encodings:
            return "Unknown", 0.0

        try:
            # Get embedding for the new face
            embedding_obj = DeepFace.represent(
                img_path=face_image,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend='skip'
            )
            
            if not embedding_obj:
                return "Unknown", 0.0
                
            face_encoding = np.array(embedding_obj[0]['embedding'])
            
            # Compare with known faces
            distances = []
            for known_encoding in self.known_face_encodings:
                dist = np.linalg.norm(face_encoding - known_encoding)
                distances.append(dist)
            
            if distances:
                min_distance = min(distances)
                confidence = 1 - min(min_distance / 0.6, 1.0)
                if confidence >= self.min_confidence:
                    best_match = np.argmin(distances)
                    return self.known_face_names[best_match], confidence
                    
        except Exception as e:
            print(f"Recognition error: {e}")
            
        return "Unknown", 0.0

    def detect_liveness(self, frame, face_location):
        """Basic liveness detection"""
        top, right, bottom, left = face_location
        face_region = frame[top:bottom, left:right]
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm > self.anti_spoofing_threshold

    def record_attendance(self, name, action):
        """Record check-in/check-out"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Find existing record
        record = next((r for r in self.attendance_log 
                      if r["Name"] == name and r["Date"] == date), None)
        
        if action == "Check-in":
            if record and record["Check-in"]:
                return False, "Already checked in today"
                
            if not record:
                self.attendance_log.append({
                    "Name": name,
                    "Date": date,
                    "Check-in": timestamp,
                    "Check-out": ""
                })
            else:
                record["Check-in"] = timestamp
                
            self.save_attendance_data()
            return True, "Checked in successfully"
            
        elif action == "Check-out":
            if not record or not record["Check-in"]:
                return False, "Not checked in yet"
            if record["Check-out"]:
                return False, "Already checked out today"
                
            record["Check-out"] = timestamp
            self.save_attendance_data()
            return True, "Checked out successfully"
            
        return False, "Invalid action"

# ================== FACE PROCESSING THREAD ==================
class FaceProcessor:
    def __init__(self, attendance_system):
        self.system = attendance_system
        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.running = False
        self.thread = None
        self.tracked_faces = {}
        self.detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.last_process_time = 0
        self.process_interval = 0.2  # Process every 200ms (5 FPS max)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_processing, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _run_processing(self):
        while self.running:
            try:
                current_time = time.time()
                if current_time - self.last_process_time < self.process_interval:
                    time.sleep(0.01)
                    continue
                    
                frame = self.frame_queue.get(timeout=0.1)
                self.last_process_time = current_time
                
                # Detect faces with OpenCV (fast)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(60, 60),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                results = []
                for (x, y, w, h) in faces:
                    face_id = f"{x//20}-{y//20}-{w//20}-{h//20}"
                    
                    # Use cached result if available
                    if face_id in self.tracked_faces:
                        cached = self.tracked_faces[face_id]
                        if current_time - cached['time'] < 2.0:  # Cache for 2 seconds
                            results.append(cached['result'])
                            continue
                    
                    # Process new face
                    top, right, bottom, left = y, x+w, y+h, x
                    face_img = frame[top:bottom, left:right]
                    face_img = cv2.resize(face_img, (160, 160))
                    
                    name, confidence = self.system.recognize_face(face_img)
                    is_live = self.system.detect_liveness(frame, (top, right, bottom, left))
                    
                    result = {
                        "location": (top, right, bottom, left),
                        "name": name,
                        "confidence": confidence,
                        "is_live": is_live,
                        "face_image": face_img
                    }
                    
                    self.tracked_faces[face_id] = {
                        'result': result,
                        'time': current_time
                    }
                    results.append(result)
                
                # Clean old cache
                self._clean_cache(current_time)
                
                # Update results
                if results:
                    if not self.result_queue.empty():
                        self.result_queue.get_nowait()
                    self.result_queue.put(results)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")

    def _clean_cache(self, current_time):
        """Remove old face cache entries"""
        to_delete = [fid for fid, data in self.tracked_faces.items()
                    if current_time - data['time'] > 5.0]  # 5 second cache
        for fid in to_delete:
            del self.tracked_faces[fid]

# ================== MAIN APPLICATION UI ==================
class AttendanceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KFCS Attendance Pro")
        self.root.geometry("1280x720")
        self.root.configure(bg='#f0f2f5')
        
        # Initialize systems
        self.system = AttendanceSystem()
        self.processor = FaceProcessor(self.system)
        self.processor.start()
        
        # UI state
        self.current_user = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Create UI
        self._setup_ui()
        
        # Start webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam!")
            self.root.destroy()
            return
            
        self.update_webcam()
        
    def _setup_ui(self):
        """Initialize all UI components"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg='white')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Webcam display
        self.webcam_frame = tk.Frame(self.main_frame, bg='black')
        self.webcam_frame.place(x=20, y=20, width=800, height=600)
        
        self.webcam_label = tk.Label(self.webcam_frame)
        self.webcam_label.pack(fill='both', expand=True)
        
        # Control panel
        self.control_frame = tk.Frame(self.main_frame, bg='white')
        self.control_frame.place(x=840, y=20, width=400, height=600)
        
        # Title
        tk.Label(self.control_frame, text="Attendance System", 
                font=('Helvetica', 20, 'bold'), bg='white').pack(pady=20)
        
        # Buttons
        btn_style = {'font': ('Helvetica', 14), 'height': 2, 'width': 20}
        self.checkin_btn = tk.Button(self.control_frame, text="CHECK IN", 
                                    command=self.check_in, bg='#4CAF50', fg='white', **btn_style)
        self.checkin_btn.pack(pady=10)
        
        self.checkout_btn = tk.Button(self.control_frame, text="CHECK OUT", 
                                     command=self.check_out, bg='#F44336', fg='white', **btn_style)
        self.checkout_btn.pack(pady=10)
        
        self.register_btn = tk.Button(self.control_frame, text="REGISTER USER", 
                                     command=self.register_user, bg='#2196F3', fg='white', **btn_style)
        self.register_btn.pack(pady=10)
        
        # Status info
        self.status_frame = tk.Frame(self.control_frame, bg='white')
        self.status_frame.pack(pady=20)
        
        tk.Label(self.status_frame, text="Current User:", font=('Helvetica', 12), 
                bg='white').grid(row=0, column=0, sticky='w')
        self.user_label = tk.Label(self.status_frame, text="None", font=('Helvetica', 12, 'bold'),
                                 bg='white')
        self.user_label.grid(row=0, column=1, sticky='w')
        
        tk.Label(self.status_frame, text="FPS:", font=('Helvetica', 12), 
                bg='white').grid(row=1, column=0, sticky='w')
        self.fps_label = tk.Label(self.status_frame, text="0", font=('Helvetica', 12),
                                bg='white')
        self.fps_label.grid(row=1, column=1, sticky='w')
        
        # Admin button
        self.admin_btn = tk.Button(self.control_frame, text="Admin Panel",
                                  command=self.show_admin_panel)
        self.admin_btn.pack(side='bottom', pady=20)

    def update_webcam(self):
        """Update webcam feed with face detection"""
        start_time = time.time()
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self.update_webcam)
            return
            
        # Send frame for processing
        if self.processor.frame_queue.empty():
            self.processor.frame_queue.put(frame.copy())
        
        # Get processed results
        face_results = []
        try:
            face_results = self.processor.result_queue.get_nowait()
        except queue.Empty:
            pass
            
        # Draw face boxes and info
        self.current_user = None
        highest_confidence = 0
        
        for result in face_results:
            top, right, bottom, left = result["location"]
            name = result["name"]
            confidence = result["confidence"]
            is_live = result["is_live"]
            
            # Track highest confidence user
            if name != "Unknown" and confidence > highest_confidence:
                self.current_user = name
                highest_confidence = confidence
                
            # Draw face rectangle
            color = (0, 255, 0) if is_live else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label
            label = f"{name} ({confidence:.0%})"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        
        # Update current user display
        self.user_label.config(text=self.current_user or "None")
        
        # Convert to PhotoImage
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update label
        self.webcam_label.imgtk = imgtk
        self.webcam_label.configure(image=imgtk)
        
        # Calculate FPS
        self.frame_count += 1
        if time.time() - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = time.time()
            self.fps_label.config(text=str(self.fps))
        
        # Repeat every 30ms (~33 FPS)
        self.root.after(30, self.update_webcam)

    def check_in(self):
        if not self.current_user:
            messagebox.showwarning("Warning", "No recognized user!")
            return
            
        success, msg = self.system.record_attendance(self.current_user, "Check-in")
        messagebox.showinfo("Success" if success else "Warning", msg)

    def check_out(self):
        if not self.current_user:
            messagebox.showwarning("Warning", "No recognized user!")
            return
            
        success, msg = self.system.record_attendance(self.current_user, "Check-out")
        messagebox.showinfo("Success" if success else "Warning", msg)

    def register_user(self):
        name = simpledialog.askstring("Register", "Enter user's full name:")
        if not name:
            return
            
        # Capture face samples
        samples = []
        messagebox.showinfo("Instructions", "We'll capture 5 face samples. Please look at the camera.")
        
        for i in range(5):
            ret, frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                faces = self.processor.detector.detectMultiScale(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                    minSize=(60, 60)
                )
                
                if len(faces) == 1:
                    x, y, w, h = faces[0]
                    face_img = frame[y:y+h, x:x+w]
                    face_img = cv2.resize(face_img, (160, 160))
                    samples.append(face_img)
                    messagebox.showinfo("Captured", f"Sample {i+1}/5 captured")
                else:
                    messagebox.showerror("Error", "Face not detected properly")
                    return
                    
        if samples and self.system.register_new_user(name, samples):
            messagebox.showinfo("Success", f"User {name} registered successfully!")
        else:
            messagebox.showerror("Error", "Registration failed")

    def show_admin_panel(self):
        """Admin panel with attendance reports and management"""
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Admin Dashboard")
        admin_win.geometry("1000x700")
        
        # Notebook (tabs)
        notebook = ttk.Notebook(admin_win)
        notebook.pack(fill='both', expand=True)
        
        # Attendance tab
        attendance_frame = ttk.Frame(notebook)
        notebook.add(attendance_frame, text="Attendance")
        
        # [Rest of admin panel implementation...]
        # Similar to previous version with treeview, filters, etc.

    def on_close(self):
        """Cleanup on exit"""
        self.processor.stop()
        self.cap.release()
        self.root.destroy()

# Run application
if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()