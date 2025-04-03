import tkinter as tk
import os
import cv2
from PIL import Image, ImageTk
import components

class App:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x520+350+100")
        self.main_window.configure(bg='gray20')  # Fixed: Removed '#' prefix
        
        # Webcam setup
        self.webcam_label = components.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=10, width=600, height=500)
        
        # Button configuration
        self.setup_buttons()
        
        # Directory setup
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
        self.log_path = './log.txt'
        
        # Initialize webcam
        self.cap = None
        self.add_webcam(self.webcam_label)

    def setup_buttons(self):
        """Centralized button configuration"""
        button_configs = [
            ('Login', 'dodgerblue', self.login, 200, 'white'),
            ('Logout', 'firebrick', self.logout, 300, 'white'),
            ('Register New User', 'slategray', self.register_new_user, 400, 'black')
        ]
        
        for text, color, command, y_pos, fg in button_configs:
            btn = components.get_button(
                self.main_window, 
                text, 
                color, 
                command,
                fg=fg
            )
            btn.place(x=750, y=y_pos)

    def login(self):
        pass
    
    def logout(self):
        pass
    
    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")
        self.register_new_user_window.configure(bg='gray20')
        
        # Capture area
        self.capture_label = components.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)
        self.add_img_to_label(self.capture_label)
        
        # Buttons for registration
        buttons = [
            ('Accept', 'dodgerblue', self.accept_register_new_user, 300),
            ('Try Again', 'firebrick', self.try_again_register_new_user, 400)
        ]
        
        for text, color, command, y_pos in buttons:
            btn = components.get_button(
                self.register_new_user_window,
                text,
                color,
                command
            )
            btn.place(x=750, y=y_pos)

    def add_img_to_label(self, label):
        """Display the most recent capture on a label"""
        if hasattr(self, 'most_recent_capture_pil'):
            imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
            label.imgtk = imgtk
            label.configure(image=imgtk)

    def accept_register_new_user(self):
        pass
    
    def try_again_register_new_user(self):
        pass
    
    def start(self):
        self.main_window.title('KFCS Attendance System')
        self.main_window.mainloop()
        
    def add_webcam(self, label):
        """Initialize webcam with error handling"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open webcam")
                
            self._label = label
            self.process_webcam()
            return True
        except Exception as e:
            print(f"Webcam Error: {e}")
            # Fallback: Display placeholder image
            placeholder = Image.new('RGB', (600, 500), 'gray30')
            imgtk = ImageTk.PhotoImage(image=placeholder)
            label.imgtk = imgtk
            label.configure(image=imgtk)
            return False
        
    def process_webcam(self):
        """Webcam processing loop with error handling"""
        try:
            ret, frame = self.cap.read()
            if ret:
                self.most_recent_capture_arr = frame
                img_ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.most_recent_capture_pil = Image.fromarray(img_)
                imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
                self._label.imgtk = imgtk
                self._label.configure(image=imgtk)
        except Exception as e:
            print(f"Frame processing error: {e}")
            
        self._label.after(20, self.process_webcam)
        
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    app = App()
    app.start()