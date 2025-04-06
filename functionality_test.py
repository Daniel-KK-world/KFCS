import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import tkinter.font as tkFont
from PIL import Image, ImageTk
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
import csv
import face_recognition
import pickle

class AttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.attendance_log = []
        self.load_known_faces()
        self.load_attendance_data()
        
    def load_known_faces(self):
        try:
            if os.path.exists("facial_recognition.dat"):
                with open("facial_recognition.dat", "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data["encodings"]
                    self.known_face_names = data["names"]
        except Exception as e:
            print(f"Error loading face data: {e}")
    
    def save_known_faces(self):
        try:
            data = {
                "encodings": self.known_face_encodings,
                "names": self.known_face_names
            }
            with open("facial_recognition.dat", "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_attendance_data(self):
        try:
            if os.path.exists("attendance.csv"):
                with open("attendance.csv", "r") as f:
                    reader = csv.DictReader(f)
                    self.attendance_log = list(reader)
        except Exception as e:
            print(f"Error loading attendance data: {e}")
    
    def save_attendance_data(self):
        try:
            if self.attendance_log:
                keys = self.attendance_log[0].keys()
                with open("attendance.csv", "w", newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(self.attendance_log)
        except Exception as e:
            print(f"Error saving attendance data: {e}")
    
    def register_new_user(self, name, face_encoding):
        self.known_face_names.append(name)
        self.known_face_encodings.append(face_encoding)
        self.save_known_faces()
    
    def recognize_face(self, face_encoding):
        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
        name = "Unknown"
        
        if True in matches:
            first_match_index = matches.index(True)
            name = self.known_face_names[first_match_index]
        
        return name
    
    def record_attendance(self, name, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Check if user already checked in today
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
        elif action == "Check-out":
            if not existing_entry or existing_entry["Check-in"] == "":
                return False, "Not checked in yet"
            if existing_entry["Check-out"] != "":
                return False, "Already checked out today"
            
            existing_entry["Check-out"] = timestamp
        
        self.save_attendance_data()
        return True, "Success"

class AttendanceUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1280x720+100+50")
        self.root.title("KFCS Attendance Pro")
        self.root.configure(bg='#f5f5f5')
        
        # Initialize attendance system
        self.attendance_system = AttendanceSystem()
        
        # Custom fonts
        self.title_font = tkFont.Font(family="Segoe UI", size=24, weight="bold")
        self.button_font = tkFont.Font(family="Segoe UI", size=12)
        self.small_font = tkFont.Font(family="Segoe UI", size=10)
        
        # Create main container with shadow
        self.create_main_container()
        
        # Webcam feed area
        self.create_webcam_section()
        
        # Control panel with buttons
        self.create_control_panel()
        
        # Status bar
        self.create_status_bar()
        
        # Admin button (gear icon)
        self.create_admin_button()
        
        # Sample logo (using placeholder if not found)
        self.create_logo()
        
        # Webcam initialization
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam!")
            self.root.destroy()
            return
        
        # Start webcam processing
        self.process_webcam()
        
        self.root.mainloop()
    
    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
    
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
    
    def process_webcam(self):
        ret, frame = self.cap.read()
        
        if ret:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find all face locations and encodings
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            # Reset current user
            self.current_user = None
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale back up face locations
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Recognize face
                name = self.attendance_system.recognize_face(face_encoding)
                
                # Store the first recognized user
                if name != "Unknown" and not self.current_user:
                    self.current_user = name
                    self.current_user_label.config(text=f"User: {name}")
                
                # Draw rectangle and label
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), 
                           cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
            
            if not self.current_user:
                self.current_user_label.config(text="No recognized user")
            
            # Convert to PhotoImage
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.webcam_label.imgtk = imgtk
            self.webcam_label.configure(image=imgtk)
        
        # Repeat every 20ms
        self.webcam_label.after(40, self.process_webcam)
    
    def create_control_panel(self):
        """Create the right-side control panel"""
        self.control_panel = tk.Frame(self.main_frame, bg='white', bd=0)
        self.control_panel.place(x=700, y=30, width=450, height=560)
        
        # Welcome message
        tk.Label(self.control_panel, text="Welcome to KFCS", 
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
        
        # Add some decorative elements
        ttk.Separator(self.control_panel, orient='horizontal').pack(fill='x', pady=20)
        
        # Quick stats placeholder
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
        """Create the admin access button"""
        self.admin_btn = tk.Label(self.main_frame, text="⚙", font=("Arial", 14), 
                                 bg='white', fg='#999', cursor="hand2")
        self.admin_btn.place(x=1130, y=580)
        self.admin_btn.bind("<Button-1>", lambda e: self.show_admin_panel())
    
    def create_logo(self):
        """Create company logo (using placeholder if needed)"""
        try:
            # Try to load actual logo
            self.logo_img = Image.open("company_logo/KFCS.ico").resize((200,80))
            self.logo_tk = ImageTk.PhotoImage(self.logo_img)
        except:
            # Create placeholder if logo not found
            self.logo_img = Image.new('RGB', (200, 80), color='#2196F3')
            draw = ImageDraw.Draw(self.logo_img)
            draw.text((10, 10), "KFCS Logo", fill="white")
            self.logo_tk = ImageTk.PhotoImage(self.logo_img)
            
        tk.Label(self.control_panel, image=self.logo_tk, bg='white').pack(pady=20)
    
    def create_modern_button(self, parent, text, color, command):
        """Helper to create stylish buttons"""
        btn = tk.Button(parent, text=text, command=command, 
                       font=self.button_font, bg=color, fg='white',
                       activebackground=self.lighten_color(color), 
                       activeforeground='white',
                       bd=0, relief='flat', highlightthickness=0,
                       padx=30, pady=5)
        
        # Hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn
    
    def lighten_color(self, color, amount=0.2):
        """Helper to lighten hex colors"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(min(255, int(c + (255 - c) * amount)) for c in rgb)
        return f'#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}'
    
    def check_in(self):
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Warning", "No recognized user detected!")
            return
        
        success, message = self.attendance_system.record_attendance(self.current_user, "Check-in")
        if success:
            messagebox.showinfo("Success", f"{self.current_user} checked in successfully!")
            self.update_stats()
        else:
            messagebox.showwarning("Warning", message)
    
    def check_out(self):
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Warning", "No recognized user detected!")
            return
        
        success, message = self.attendance_system.record_attendance(self.current_user, "Check-out")
        if success:
            messagebox.showinfo("Success", f"{self.current_user} checked out successfully!")
            self.update_stats()
        else:
            messagebox.showwarning("Warning", message)
    
    def register_user(self):
        name = simpledialog.askstring("Register New User", "Enter user's full name:")
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
            # Average the encodings
            avg_encoding = np.mean(samples, axis=0)
            self.attendance_system.register_new_user(name, avg_encoding)
            messagebox.showinfo("Success", f"User {name} registered successfully!")
            self.status.config(text=f"System Ready | {len(self.attendance_system.known_face_names)} users registered | Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def show_admin_panel(self):
        """Show the admin panel with actual data"""
        admin_win = tk.Toplevel(self.root)
        admin_win.geometry("900x600+200+100")
        admin_win.title("Admin Dashboard")
        admin_win.configure(bg='#f5f5f5')
        
        # Notebook (tabbed interface)
        notebook = ttk.Notebook(admin_win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Attendance Reports
        reports_frame = ttk.Frame(notebook)
        notebook.add(reports_frame, text="Attendance Reports")
        
        # Treeview for data display
        columns = ("Date", "Name", "Check-in", "Check-out")
        tree = ttk.Treeview(reports_frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Insert real data
        for record in self.attendance_system.attendance_log:
            tree.insert("", "end", values=(
                record["Date"],
                record["Name"],
                record["Check-in"],
                record["Check-out"]
            ))
        
        # Export button
        ttk.Button(reports_frame, text="Export to Excel", 
                  command=lambda: self.export_to_excel(tree)).pack(pady=10)
        
        # Tab 2: User Management
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
    
    def export_to_excel(self, tree):
        """Export attendance data to Excel"""
        try:
            items = tree.get_children()
            data = []
            for item in items:
                values = tree.item(item, 'values')
                data.append(values)
            
            df = pd.DataFrame(data, columns=["Date", "Name", "Check-in", "Check-out"])
            
            # Create a timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_report_{timestamp}.xlsx"
            
            df.to_excel(filename, index=False)
            messagebox.showinfo("Success", f"Report exported as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def remove_user(self, user_list):
        """Remove selected user from the system"""
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

# Run the UI
if __name__ == "__main__":
    app = AttendanceUI()