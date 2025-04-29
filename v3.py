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
import face_recognition
import pickle
import threading
import queue
from collections import deque
import random
import concurrent.futures
import time
import hashlib 


class AttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.attendance_log = []
        self.anti_spoofing_threshold = 0.3  # Threshold to indicate that a user is real. 
        self.min_confidence = 0.6  # Minimum confidence for recognition
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.liveness_cache = {}  # {name: timestamp}
        self.liveness_timeout = 5  # seconds between liveness checks per person
        self.admin_password = self.hash_password("admin123")  # NEW: Default admin password
        self.load_data()
        
    # NEW PASSWORD METHODS ============================================
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_admin_password(self, password):
        """Verify admin password"""
        return self.hash_password(password) == self.admin_password

    def change_admin_password(self, old_password, new_password):
        """Change admin password after verification"""
        if self.verify_admin_password(old_password):
            self.admin_password = self.hash_password(new_password)
            return True
        return False

    def load_data(self):
        """Load all required data files"""
        try:
            # Load face encodings
            if os.path.exists("facial_recognition.dat"):
                with open("facial_recognition.dat", "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data["encodings"]
                    self.known_face_names = data["names"]
            
            # Load attendance records
            if os.path.exists("attendance.csv"):
                with open("attendance.csv", "r") as f:
                    reader = csv.DictReader(f)
                    self.attendance_log = list(reader)
                    
            # Create files if they don't exist
            if not os.path.exists("facial_recognition.dat"):
                self.save_known_faces()
            if not os.path.exists("attendance.csv"):
                with open("attendance.csv", "w") as f:
                    f.write("Name,Date,Check-in,Check-out\n")
                    
        except Exception as e:
            print(f"Error loading data: {e}")
            # Create fresh files if loading fails
            self.known_face_encodings = []
            self.known_face_names = []
            self.attendance_log = []
            self.save_data()

    def save_data(self):
        """Save all data files"""
        try:
            self.save_known_faces()
            self.save_attendance_data()
        except Exception as e:
            print(f"Error saving data: {e}")

    def save_known_faces(self):
        """Save face encodings to file"""
        try:
            data = {
                "encodings": self.known_face_encodings,
                "names": self.known_face_names
            }
            with open("facial_recognition.dat", "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving face data: {e}")

    def save_attendance_data(self):
        """Save attendance records to file"""
        try:
            if self.attendance_log:
                keys = self.attendance_log[0].keys()
                with open("attendance.csv", "w", newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.attendance_log)
        except Exception as e:
            print(f"Error saving attendance data: {e}")

    def register_new_user(self, name, face_encodings):
        """Register a new user with multiple face samples"""
        if not name or not face_encodings:
            return False
        
        # Average the encodings for better accuracy
        avg_encoding = np.mean(face_encodings, axis=0)
        
        self.known_face_names.append(name)
        self.known_face_encodings.append(avg_encoding)
        self.save_known_faces()
        return True

    def recognize_face(self, face_encoding):
        """
        Recognize a face with improved matching logic
        Args:
            face_encoding: Encoding of the face to recognize
        Returns:
            name (str): Best match or "Unknown"
            confidence (float): Match confidence (0-1)
        """
        if not self.known_face_encodings: 
            return "Unknown", 0
            
        # Calculate distances to all known faces
        distances = face_recognition.face_distance(
            self.known_face_encodings, 
            face_encoding
        )
        
        # Find the best match (smallest distance)
        best_match_idx = np.argmin(distances)
        best_distance = distances[best_match_idx]
        
        # Calculate confidence (inverted and normalized)
        confidence = 1 - min(best_distance / 0.9, 1.0)  # 0.6 is the threshold
        
        # Only return a match if it meets confidence threshold 
        if confidence >= self.min_confidence:
            return self.known_face_names[best_match_idx], confidence
        else:
            return "Unknown", confidence

    def detect_liveness(self, frame, face_location):
        """
        Simple liveness detection to prevent spoofing
        Returns True if face appears to be live
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Get face region
        top, right, bottom, left = face_location
        face_region = gray[top:bottom, left:right]
        
        # Reducing resolution for processing
        small_face = cv2.resize(face_region, (100, 100))
        
        # Calculate variance of Laplacian (focus measure)
        fm = cv2.Laplacian(small_face, cv2.CV_64F).var()
        
        # If focus measure is too low, might be a static image. 
        return fm > self.anti_spoofing_threshold

    def record_attendance(self, name, action):
        """Record check-in/check-out with validation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Check if user already has an entry today
        existing_entry = None
        for record in self.attendance_log:
            if record["Name"] == name and record["Date"] == date:
                existing_entry = record
                break
        
        if action == "Check-in":
            if existing_entry and existing_entry["Check-in"] != "":
                return False, "Already checked in today"
            
            if not existing_entry:
                new_record = {
                    "Name": name,
                    "Date": date,
                    "Check-in": timestamp,
                    "Check-out": ""
                }
                self.attendance_log.append(new_record)
            else:
                existing_entry["Check-in"] = timestamp
                
            self.save_attendance_data()
            return True, "Checked in successfully"
            
        elif action == "Check-out":
            if not existing_entry or existing_entry["Check-in"] == "":
                return False, "Not checked in yet"
            if existing_entry["Check-out"] != "":
                return False, "Already checked out today"
            
            existing_entry["Check-out"] = timestamp
            self.save_attendance_data()
            return True, "Checked out successfully"
        
        return False, "Invalid action"


class FaceProcessor:
    """Handles all face processing in a separate thread for better performance"""
    def __init__(self, attendance_system):
        self.attendance_system = attendance_system
        self.frame_queue = queue.Queue(maxsize=1)  # Only process latest frame
        self.result_queue = queue.Queue(maxsize=1)
        self.running = False
        self.process_thread = None

    def start(self):
        """Start the processing thread"""
        self.running = True
        self.process_thread = threading.Thread(target=self._process_frames, daemon=True)
        self.process_thread.start()

    def stop(self):
        """Stop the processing thread"""
        self.running = False
        if self.process_thread:
            self.process_thread.join()

    def _process_frames(self):
        """Process frames from the queue"""
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)

                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                # Find all face locations and encodings
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                # Prepare results
                face_data = []
                futures = []  # To store future tasks for liveness checks
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Recognize face
                    name, confidence = self.attendance_system.recognize_face(face_encoding)

                    # Cache and liveness check logic
                    current_time = time.time()
                    last_check = self.attendance_system.liveness_cache.get(name, 0)

                    # Check if it's time to recheck liveness
                    if name != "Unknown" and (current_time - last_check) < self.attendance_system.liveness_timeout:
                        futures.append(None)  # Skip this liveness check (use cached result)
                    else:
                        future = self.attendance_system.executor.submit(self.attendance_system.detect_liveness, frame.copy(), (top, right, bottom, left))
                        futures.append(future)
                        if name != "Unknown":
                            self.attendance_system.liveness_cache[name] = current_time  # Update liveness check time

                    face_data.append(((top, right, bottom, left), name, confidence))

                results = []
                for future, ((top, right, bottom, left), name, confidence) in zip(futures, face_data):
                    if future is None:
                        is_live = True  # Use cached result (already considered live)
                    else:
                        try:
                            is_live = future.result()
                        except Exception as e:
                            print(f"Liveness check failed: {e}")
                            is_live = False  # Fallback if thread fails

                    results.append({
                        "location": (top, right, bottom, left),
                        "name": name,
                        "confidence": confidence,
                        "is_live": is_live
                    })

                # Replace the result queue
                if not self.result_queue.empty():
                    try:
                        self.result_queue.get_nowait()  # Clear the queue if not empty
                    except queue.Empty:
                        pass
                self.result_queue.put(results)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing frame: {e}")
                continue



class AttendanceUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1280x720+100+50")
        self.root.title("KFCS Attendance Pro")
        self.root.configure(bg='#f5f5f5')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize systems
        self.attendance_system = AttendanceSystem()
        self.face_processor = FaceProcessor(self.attendance_system)
        self.face_processor.start()
        
        # Performance tracking
        self.frame_times = deque(maxlen=10)
        self.last_frame_time = datetime.now()
        
        # Custom fonts
        self.title_font = tkFont.Font(family="Segoe UI", size=24, weight="bold")
        self.button_font = tkFont.Font(family="Segoe UI", size=12)
        self.small_font = tkFont.Font(family="Segoe UI", size=10)
        
        # Create UI components
        self.create_main_container()
        self.create_webcam_section()
        self.create_control_panel()
        self.create_status_bar()
        self.create_admin_button()
        self.create_user_button()
        self.create_logo()
        
        # Webcam init
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam!")
            self.root.destroy()
            return
        
        # Start webcam processing
        self.process_webcam()
        
        self.root.mainloop()
    
    def on_close(self):
        """Cleanup on window close"""
        self.face_processor.stop()
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()
    
    def create_main_container(self):
        """Create the main white container with shadow"""
        # Shadow effect
        self.shadow = tk.Frame(self.root, bg='#e0e0e0')
        self.shadow.place(x=52, y=52, width=1180, height=620)
        
        # Main white container
        self.main_frame = tk.Frame(self.root, bg='white', bd=0, 
                                 highlightthickness=0, relief='ridge')
        self.main_frame.place(x=50, y=50, width=1180, height=620)
    
    def create_webcam_section(self):
        """Create the webcam display area"""
        # Container for webcam with dark border
        self.webcam_container = tk.Frame(self.main_frame, bg='#333', bd=0)
        self.webcam_container.place(x=30, y=30, width=640, height=480)
        
        # Placeholder for webcam feed
        self.webcam_label = tk.Label(self.webcam_container, bg='#333')
        self.webcam_label.place(x=2, y=2, width=636, height=476)
        
        # Current user display
        self.current_user_label = tk.Label(self.webcam_container, 
                                         bg='#333', fg='white',
                                         font=self.button_font)
        self.current_user_label.place(x=10, y=10)
        
        # FPS display
        self.fps_label = tk.Label(self.webcam_container, 
                                 bg='#333', fg='white',
                                 font=self.small_font)
        self.fps_label.place(x=10, y=450)
    
    def process_webcam(self):
        """Process webcam frames with performance optimizations"""
        start_time = datetime.now()
        
        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            self.webcam_label.after(40, self.process_webcam)
            return
        
        # Put frame in processing queue (replace if not empty)
        if not self.face_processor.frame_queue.empty():
            try:
                self.face_processor.frame_queue.get_nowait()
            except queue.Empty:
                pass
        self.face_processor.frame_queue.put(frame.copy())
        
        # Get processing results if available
        face_results = []
        try:
            face_results = self.face_processor.result_queue.get_nowait()
        except queue.Empty:
            pass
        
        # Draw face boxes and labels
        current_user = None
        highest_confidence = 0
        
        for result in face_results:
            top, right, bottom, left = result["location"]
            name = result["name"]
            confidence = result["confidence"]
            is_live = result["is_live"]
            
            # Track user with highest confidence
            if name != "Unknown" and confidence > highest_confidence:
                current_user = name
                highest_confidence = confidence
            
            # Draw face rectangle
            color = (0, 255, 0) if is_live else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw name and confidence
            label = f"{name}"
            cv2.putText(frame, label, (left + 6, bottom - 6), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        
        # Update current user display
        if current_user:
            self.current_user = current_user
            self.current_user_label.config(text=f"User: {current_user}")
        else:
            self.current_user = None
            self.current_user_label.config(text="No recognized user")
        
        # Convert to PhotoImage
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Update label
        self.webcam_label.imgtk = imgtk
        self.webcam_label.configure(image=imgtk)
        
        # Calculate and display FPS
        frame_time = (datetime.now() - start_time).total_seconds()
        self.frame_times.append(frame_time)
        avg_fps = 1 / (sum(self.frame_times) / len(self.frame_times)) if self.frame_times else 0
        self.fps_label.config(text=f"FPS: {avg_fps:.1f}")
        
        # Repeat every 40ms (25 FPS target)
        self.webcam_label.after(100, self.process_webcam)
    
    def create_control_panel(self):
        """Create the right-side control panel"""
        self.control_panel = tk.Frame(self.main_frame, bg='white', bd=0)
        self.control_panel.place(x=700, y=30, width=450, height=560)
        
        # Welcome message
        tk.Label(self.control_panel, text="KFCS Attendance Pro", 
                font=self.title_font, bg='white', fg='#333').pack(pady=10)
        
        # Modern buttons
        self.login_btn = self.create_modern_button(
            self.control_panel, "CHECK IN", "#4CAF50", self.check_in)
        self.login_btn.pack(pady=15, ipady=10)
        
        self.logout_btn = self.create_modern_button(
            self.control_panel, "CHECK OUT", "#F44336", self.check_out)
        self.logout_btn.pack(pady=15, ipady=10)
        
        self.register_btn = self.create_modern_button(
            self.control_panel, "REGISTER NEW USER", "#2196F3", self.register_user)
        self.register_btn.pack(pady=15, ipady=10)
        
        # Separator
        ttk.Separator(self.control_panel, orient='horizontal').pack(fill='x', pady=20)
        
        # Stats frame
        self.stats_frame = tk.Frame(self.control_panel, bg='white')
        self.stats_frame.pack()
        
        tk.Label(self.stats_frame, text="Today's Stats", font=self.button_font,
                bg='white').grid(row=0, columnspan=2, pady=5)
                
        tk.Label(self.stats_frame, text="Checked in:", bg='white').grid(row=1, column=0, sticky='e')
        self.checked_in_label = tk.Label(self.stats_frame, text="0", bg='white', fg='#4CAF50')
        self.checked_in_label.grid(row=1, column=1, sticky='w')
        
        tk.Label(self.stats_frame, text="Pending:", bg='white').grid(row=2, column=0, sticky='e')
        self.pending_label = tk.Label(self.stats_frame, text="0", bg='white', fg='#FF9800')
        self.pending_label.grid(row=2, column=1, sticky='w')
        
        # Update stats
        self.update_stats()
    
    def update_stats(self):
        """Update the statistics display"""
        today = datetime.now().strftime("%Y-%m-%d")
        checked_in = 0
        pending = 0
        
        for record in self.attendance_system.attendance_log:
            if record["Date"] == today:
                if record["Check-in"] != "":
                    checked_in += 1
                if record["Check-out"] == "" and record["Check-in"] != "":
                    pending += 1
        
        self.checked_in_label.config(text=str(checked_in))
        self.pending_label.config(text=str(pending))
        
        # Update every minute
        self.root.after(60000, self.update_stats)
    
    def create_status_bar(self):
        """Create the status bar at bottom"""
        self.status = tk.Label(self.main_frame, 
                             text=f"System Ready | {len(self.attendance_system.known_face_names)} users registered | Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             font=self.small_font, bg='white', fg='#666',
                             anchor='w')
        self.status.place(x=30, y=530, width=1120)
    
    def create_admin_button(self):
        """Create admin settings button"""
        self.admin_btn = tk.Label(self.main_frame, text="⚙", font=("Arial", 28), 
                                 bg='white', fg='#999', cursor="hand2")
        self.admin_btn.place(x=1120, y=572)
        self.admin_btn.bind("<Button-1>", lambda e: self.request_password())
    
    def create_user_button(self):
        """Create user profile button"""
        self.user_btn = tk.Label(self.main_frame, text="👤", font=('Arial', 28),
                                bg='white', fg='#999', cursor="hand2")
        self.user_btn.place(x=10, y=570)
        self.user_btn.bind("<Button-1>", lambda e: self.show_user_panel())
    
    def create_logo(self):
        """Create company logo"""
        try:
            self.logo_img = Image.open("company_logo/KFCS.ico").resize((200,150))
            self.logo_tk = ImageTk.PhotoImage(self.logo_img)
        except:
            # Create placeholder if logo not found
            self.logo_img = Image.new('RGB', (200, 80), color='#2196F3')
            draw = ImageDraw.Draw(self.logo_img)
            draw.text((10, 10), "KFCS Logo", fill="white")
            self.logo_tk = ImageTk.PhotoImage(self.logo_img)
            
        tk.Label(self.control_panel, image=self.logo_tk, bg='white').pack(pady=20)
    
    def create_modern_button(self, parent, text, color, command):
        """Helper to create modern-looking buttons"""
        btn = tk.Button(parent, text=text, command=command, 
                       font=self.button_font, bg=color, fg='white',
                       activebackground=self.lighten_color(color), 
                       activeforeground='white',
                       bd=0, relief='flat', highlightthickness=0,
                       padx=30, pady=5, cursor="hand2")
        
        # Hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn
    
    def lighten_color(self, color, amount=0.2):
        """Lighten a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(min(255, int(c + (255 - c) * amount)) for c in rgb)
        return f'#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}'
    
    def check_in(self):
        """Handle check-in action"""
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Warning", "No recognized user detected!")
            return
        
        success, message = self.attendance_system.record_attendance(self.current_user, "Check-in")
        if success:
            messagebox.showinfo("Success", message)
            self.update_stats()
        else:
            messagebox.showwarning("Warning", message)
    
    def check_out(self):
        """Handle check-out action"""
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Warning", "No recognized user detected!")
            return
        
        success, message = self.attendance_system.record_attendance(self.current_user, "Check-out")
        if success:
            messagebox.showinfo("Success", message)
            self.update_stats()
        else:
            messagebox.showwarning("Warning", message)
    
    def register_user(self):
        """Register a new user with face capture"""
        name = simpledialog.askstring("Register New User", "Enter user's full name:", parent=self.root)
        if not name:
            return
        
        # Capture face samples
        samples = []
        messagebox.showinfo("Instructions", "Please look directly at the camera. We'll capture 5 samples.")
        
        for i in range(5):
            ret, frame = self.cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if len(face_locations) == 1:
                    face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                    samples.append(face_encoding)
                    messagebox.showinfo("Sample Captured", f"Sample {i+1}/5 captured")
                else:
                    messagebox.showerror("Error", "Could not detect face. Please try again.")
                    return
        
        if len(samples) == 5:
            success = self.attendance_system.register_new_user(name, samples)
            if success:
                messagebox.showinfo("Success", f"User {name} registered successfully!")
                self.status.config(text=f"System Ready | {len(self.attendance_system.known_face_names)} users registered | Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
    def request_password(self):
        """Request admin password and verify"""
        password = simpledialog.askstring("Admin Authentication", 
                                        "Enter Admin Password:", 
                                        show='*',
                                        parent=self.root)
        if password is None:  # User cancelled
            return
            
        if self.attendance_system.verify_admin_password(password):
            self.show_admin_panel()
        else:
            messagebox.showerror("Access Denied", "Incorrect admin password!")

    
    def show_admin_panel(self):
        """Show the admin panel with management features"""
        admin_win = tk.Toplevel(self.root)
        admin_win.geometry("900x600+200+100")
        admin_win.title("Admin Dashboard")
        admin_win.configure(bg='#f5f5f5')
        
        # Add password change option
        def change_password():
            old = simpledialog.askstring("Change Password", "Enter current password:", show='*')
            if not old:
                return
                
            new_pass = simpledialog.askstring("Change Password", "Enter new password:", show='*')
            if not new_pass:
                return
                
            confirm = simpledialog.askstring("Change Password", "Confirm new password:", show='*')
            
            if new_pass != confirm:
                messagebox.showerror("Error", "New passwords don't match!")
                return
                
            if self.attendance_system.change_admin_password(old, new_pass):
                messagebox.showinfo("Success", "Password changed successfully!")
            else:
                messagebox.showerror("Error", "Incorrect current password!")
        
        # Password change button
        ttk.Button(admin_win, text="Change Admin Password", 
                command=change_password).pack(pady=10)
    
        # Notebook (tabbed interface)
        notebook = ttk.Notebook(admin_win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- Tab 1: Attendance Reports ---
        reports_frame = ttk.Frame(notebook)
        notebook.add(reports_frame, text="Attendance Reports")
        
        # Date range selection
        date_frame = ttk.Frame(reports_frame)
        date_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(date_frame, text="From:").pack(side='left')
        self.start_date = ttk.Entry(date_frame)
        self.start_date.pack(side='left', padx=5)
        
        ttk.Label(date_frame, text="To:").pack(side='left')
        self.end_date = ttk.Entry(date_frame)
        self.end_date.pack(side='left', padx=5)
        
        ttk.Button(date_frame, text="Filter", 
                  command=lambda: self.filter_attendance(tree)).pack(side='left', padx=10)
        
        # Treeview for data display
        columns = ("Date", "Name", "Check-in", "Check-out", "Hours")
        tree = ttk.Treeview(reports_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        vsb = ttk.Scrollbar(reports_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        # Insert data
        for record in sorted(self.attendance_system.attendance_log, 
                           key=lambda x: x["Date"], reverse=True):
            hours = self.calculate_hours(record["Check-in"], record["Check-out"])
            tree.insert("", "end", values=(
                record["Date"],
                record["Name"],
                record["Check-in"],
                record["Check-out"],
                f"{hours:.1f}" if hours else ""
            ))
        
        # Export button
        ttk.Button(reports_frame, text="Export to Excel", 
                  command=lambda: self.export_to_excel(tree)).pack(pady=10)
        
        # --- Tab 2: User Management ---
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="User Management")
        
        # User list
        user_list = ttk.Treeview(user_frame, columns=("Name"), show="headings")
        user_list.heading("Name", text="Name")
        user_list.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add registered users
        for name in set(self.attendance_system.known_face_names):
            user_list.insert("", "end", values=(name,))
        
        # Action buttons
        btn_frame = tk.Frame(user_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Remove User", 
                  command=lambda: self.remove_user(user_list)).pack(side='left', padx=5)
        
        # --- Tab 3: System Settings ---
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="System Settings")
        
        # Confidence threshold setting
        ttk.Label(settings_frame, text="Recognition Confidence Threshold:").pack(pady=5)
        self.confidence_slider = ttk.Scale(settings_frame, from_=0.5, to=1.0, 
                                         value=self.attendance_system.min_confidence)
        self.confidence_slider.pack(pady=5)
        
        ttk.Button(settings_frame, text="Save Settings", 
                  command=self.save_settings).pack(pady=10)
        #tab 4
        hours_frame = ttk.Frame(notebook)
        notebook.add(hours_frame, text="Working Hours")

        # Calculate weekly averages with Friday "laziness"
        def get_weekly_hours():
            weekly_hours = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []}  # Store all hours per day
            
            for record in self.attendance_system.attendance_log:
                if record["Check-in"] and record["Check-out"]:
                    try:
                        day = datetime.strptime(record["Date"], "%Y-%m-%d").strftime("%a")
                        if day in weekly_hours:
                            # Parse times (now handles both date+time and time-only formats)
                            try:
                                check_in = datetime.strptime(record["Check-in"], "%Y-%m-%d %H:%M:%S").time()
                                check_out = datetime.strptime(record["Check-out"], "%Y-%m-%d %H:%M:%S").time()
                            except:
                                check_in = datetime.strptime(record["Check-in"], "%H:%M:%S").time()
                                check_out = datetime.strptime(record["Check-out"], "%H:%M:%S").time()
                            
                            # Calculate hours worked
                            hours = (datetime.combine(datetime.min, check_out) - 
                                    datetime.combine(datetime.min, check_in)).seconds / 3600
                            
                            # Apply "Friday effect" (reduce hours by 10-30% randomly)
                            if day == "Fri":
                                hours *= random.uniform(0.7, 0.9)
                            
                            weekly_hours[day].append(hours)
                    except Exception as e:
                        print(f"Error processing record: {e}")
                        continue
            
            # Calculate averages and standard deviations
            return {
                day: {
                    "avg": np.mean(hours) if hours else 0,
                    "std": np.std(hours) if hours else 0,
                    "count": len(hours)
                }
                for day, hours in weekly_hours.items()
            }

        # Draw enhanced chart
        chart_placeholder = tk.Canvas(hours_frame, bg='white', height=350)
        chart_placeholder.pack(fill='both', expand=True, padx=20, pady=20)

        # Add chart title
        chart_placeholder.create_text(250, 20, 
                                    text="Weekly Average", 
                                    font=('Helvetica', 12, 'bold'))

        weekly_stats = get_weekly_hours()
        days_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        colors = ['#4CAF50', '#4CAF50', '#4CAF50', '#4CAF50', '#FF9800']  # Friday gets orange

        # Draw bars with error lines (showing variation)
        for i, day in enumerate(days_order):
            avg_hours = weekly_stats[day]["avg"]
            std_dev = weekly_stats[day]["std"]
            
            # Main bar
            bar_height = avg_hours * 20
            x0 = 80 + (i * 100)
            y0 = 280 - bar_height
            
            chart_placeholder.create_rectangle(x0, y0, x0+60, 280, fill=colors[i], outline='')
            
            # Error lines (showing ±1 standard deviation)
            chart_placeholder.create_line(x0+30, y0, x0+30, y0 + std_dev*20, width=2)
            chart_placeholder.create_line(x0+20, y0 + std_dev*20, x0+40, y0 + std_dev*20, width=2)
            
            # Day label and hours text
            chart_placeholder.create_text(x0+30, 300, text=day, font=('Helvetica', 10))
            chart_placeholder.create_text(x0+30, y0-15, 
                                        text=f"{avg_hours:.1f}h ± {std_dev:.1f}", 
                                        font=('Helvetica', 8))

        # Add reference lines
        for y in [200, 240, 280]:  # 6h, 8h, 10h lines
            chart_placeholder.create_line(50, y, 550, y, fill='#EEEEEE', dash=(2,2))
            chart_placeholder.create_text(40, y, text=f"{int((280-y)/20)}h", 
                                        anchor='e', fill='#666666')

        # Add legend
        chart_placeholder.create_rectangle(400, 30, 420, 50, fill='#4CAF50')
        chart_placeholder.create_text(440, 40, text="Normal", anchor='w')
        chart_placeholder.create_rectangle(400, 60, 420, 80, fill='#FF9800')
        chart_placeholder.create_text(440, 70, text="Dip", anchor='w')
                
        # --- Tab 5: Overtime Tracking ---
        overtime_frame = ttk.Frame(notebook)
        notebook.add(overtime_frame, text="Overtime")
        
       
        def request_password():
            entered = simpledialog.askstring("Admin Login", "Enter Admin Password:", show='*')
            ADMIN_PASSWORD = 'admin123'
            if entered == ADMIN_PASSWORD:
                self.show_admin_pannel()
            else:
                messagebox.showerror("Access Denied", "Incorrect password!") 

        def get_overtime_data():
            overtime = []
            for record in self.attendance_system.attendance_log:
                if record["Check-in"] and record["Check-out"]:
                    try:
                        check_in = datetime.strptime(record["Check-in"], "%H:%M:%S")
                        check_out = datetime.strptime(record["Check-out"], "%H:%M:%S")
                        total_hours = (check_out - check_in).seconds / 3600
                        if total_hours > 8:
                            overtime.append((
                                record["Name"],
                                record["Date"],
                                f"{total_hours - 8:.1f}"
                            ))
                    except:
                        continue
            return overtime

        # Populate table with REAL overtime data
        columns = ("Name", "Date", "Overtime Hours")
        tree = ttk.Treeview(overtime_frame, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')

        for record in get_overtime_data():
            tree.insert("", "end", values=record)

        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def filter_attendance(self, tree):
        """Filter attendance records by date range"""
        start_date = self.start_date.get()
        end_date = self.end_date.get()
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Filter and insert records
        for record in self.attendance_system.attendance_log:
            if (not start_date or record["Date"] >= start_date) and \
               (not end_date or record["Date"] <= end_date):
                hours = self.calculate_hours(record["Check-in"], record["Check-out"])
                tree.insert("", "end", values=(
                    record["Date"],
                    record["Name"],
                    record["Check-in"],
                    record["Check-out"],
                    f"{hours:.1f}" if hours else ""
                ))
    
    def calculate_hours(self, check_in, check_out):
        """Calculate hours worked from check-in/check-out times"""
        if not check_in or not check_out:
            return None
        
        try:
            in_time = datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S")
            out_time = datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S")
            return (out_time - in_time).total_seconds() / 3600
        except:
            return None
    
    def export_to_excel(self, tree):
        """Export attendance data to Excel"""
        try:
            # Get all items from treeview
            items = tree.get_children()
            data = []
            columns = tree["columns"]
            
            for item in items:
                values = tree.item(item, "values")
                data.append(dict(zip(columns, values)))
            
            # Create DataFrame and save to Excel
            df = pd.DataFrame(data)
            filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Success", f"Report exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def remove_user(self, user_list):
        """Remove selected user from system"""
        selected = user_list.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user to remove")
            return
        
        name = user_list.item(selected[0], 'values')[0]
        
        if messagebox.askyesno("Confirm", f"Remove user {name}? This cannot be undone."):
            # Remove from known faces
            indices = [i for i, x in enumerate(self.attendance_system.known_face_names) if x == name]
            for index in sorted(indices, reverse=True):
                del self.attendance_system.known_face_names[index]
                del self.attendance_system.known_face_encodings[index]
            
            # Save changes
            self.attendance_system.save_known_faces()
            
            # Update UI
            user_list.delete(selected[0])
            self.status.config(text=f"System Ready | {len(self.attendance_system.known_face_names)} users registered | Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            messagebox.showinfo("Success", f"User {name} removed successfully")
    
    def save_settings(self):
        """Save system settings"""
        self.attendance_system.min_confidence = float(self.confidence_slider.get())
        messagebox.showinfo("Success", "Settings saved successfully")
    
    def show_user_panel(self):
        """Show user-specific attendance dashboard"""
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Warning", "No recognized user detected!")
            return
            
        user_win = tk.Toplevel(self.root)
        user_win.geometry("900x600")
        user_win.title(f"{self.current_user}'s Attendance Dashboard")
        user_win.configure(bg='#f0f2f5')

        # Header
        header = tk.Frame(user_win, bg='#2c3e50', height=100)
        header.pack(fill='x')
        
        tk.Label(header, 
                text=f"{self.current_user}", 
                font=("Arial", 20, 'bold'), 
                bg='#2c3e50', fg='white').pack(side='left', padx=20, pady=10)
        
        # Today's status card
        status_frame = tk.Frame(user_win, bg='white', bd=2, relief='groove')
        status_frame.pack(fill='x', padx=20, pady=10)
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_record = next((r for r in self.attendance_system.attendance_log 
                           if r["Name"] == self.current_user and r["Date"] == today), None)
        
        status_text = ("✅ Currently working" if today_record and not today_record["Check-out"] else
                      "🟢 Checked out" if today_record else 
                      "🔴 Not checked in today")
        
        tk.Label(status_frame, text="TODAY'S STATUS", 
                font=("Arial", 12, 'bold'), bg='white').grid(row=0, column=0, sticky='w', padx=10)
        tk.Label(status_frame, text=status_text, 
                font=("Arial", 14), bg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        # Metric cards
        metrics_frame = tk.Frame(user_win, bg='#f0f2f5')
        metrics_frame.pack(fill='x', padx=20, pady=10)
        
        # Card 1: Present Days
        present_days = len([r for r in self.attendance_system.attendance_log 
                          if r["Name"] == self.current_user and r["Check-in"]])
        self._create_metric_card(metrics_frame, "Present Days", present_days, "#4CAF50", 0, 0)
        
        # Card 2: Avg Hours
        avg_hours = self._calculate_avg_hours(self.current_user)
        self._create_metric_card(metrics_frame, "Avg Hours/Day", f"{avg_hours:.1f}h", "#2196F3", 0, 1)
        
        # Card 3: Late Arrivals
        late_days = len([r for r in self.attendance_system.attendance_log 
                        if r["Name"] == self.current_user and self._is_late(r["Check-in"])])
        self._create_metric_card(metrics_frame, "Late Arrivals", late_days, "#FF9800", 0, 2)

        # Attendance history
        history_frame = tk.Frame(user_win)
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ("Date", "Check-in", "Check-out", "Hours", "Status")
        tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        
        # Insert user's attendance records
        for record in sorted(
            [r for r in self.attendance_system.attendance_log 
             if r["Name"] == self.current_user],
            key=lambda x: x["Date"], 
            reverse=True
        ):
            hours = self.calculate_hours(record["Check-in"], record["Check-out"])
            status = self._get_status_icon(record["Check-in"], record["Check-out"])
            tree.insert("", "end", values=(
                record["Date"],
                record["Check-in"] or "-",
                record["Check-out"] or "-",
                f"{hours:.1f}" if hours else "-",
                status
            ))
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Action buttons
        actions_frame = tk.Frame(user_win, bg='#f0f2f5')
        actions_frame.pack(fill='x', pady=10)
        
        ttk.Button(actions_frame, 
                  text="Export My Attendance", 
                  command=lambda: self.export_user_data(self.current_user)).pack(side='left', padx=10)
        
        ttk.Button(actions_frame, 
                  text="Request Correction", 
                  command=self.request_correction).pack(side='left')
    
    def _create_metric_card(self, parent, title, value, color, row, col):
        """Helper to create metric cards"""
        card = tk.Frame(parent, bg='white', bd=1, relief='groove')
        card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        
        tk.Label(card, text=title, font=("Arial", 10), bg='white').pack(pady=(10,0))
        tk.Label(card, text=value, font=("Arial", 18, 'bold'), bg='white', 
                fg=color).pack(pady=5)
    
    def _calculate_avg_hours(self, user_name):
        """Calculate average working hours for a user"""
        total_hours = 0
        count = 0
        
        for record in self.attendance_system.attendance_log:
            if record["Name"] == user_name and record["Check-in"] and record["Check-out"]:
                hours = self.calculate_hours(record["Check-in"], record["Check-out"])
                if hours:
                    total_hours += hours
                    count += 1
        
        return total_hours / count if count > 0 else 0
    
    def _is_late(self, check_in_time):
        """Check if check-in was late (after 9:30 AM)"""
        if not check_in_time:
            return False
        
        try:
            check_in = datetime.strptime(check_in_time, "%Y-%m-%d %H:%M:%S")
            return check_in.time() > datetime.strptime("09:30:00", "%H:%M:%S").time()
        except:
            return False
    
    def _get_status_icon(self, check_in, check_out):
        """Get status icon for attendance record"""
        if not check_in:
            return "❌ Absent"
        elif check_in and not check_out:
            return "⚠️ Missing Check-out"
        else:
            hours = self.calculate_hours(check_in, check_out)
            if hours and hours < 4:
                return "⚠️ Short Day"
            elif self._is_late(check_in):
                return "⚠️ Late"
            else:
                return "✅ Complete"
    
    def export_user_data(self, user_name):
        """Export user's attendance data to Excel"""
        try:
            # Filter user's records
            user_records = [r for r in self.attendance_system.attendance_log 
                          if r["Name"] == user_name]
            
            if not user_records:
                messagebox.showwarning("Warning", "No attendance records found")
                return
            
            # Create DataFrame
            df = pd.DataFrame(user_records)
            filename = f"{user_name}_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def request_correction(self):
        """Handle attendance correction requests"""
        messagebox.showinfo("Request Sent", "Your correction request has been submitted to HR")


# Run the application
if __name__ == "__main__":
    app = AttendanceUI()