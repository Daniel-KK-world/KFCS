import tkinter as tk
import os.path

import pickle
import datetime 

import cv2
from PIL import Image, ImageTk
import subprocess
import face_recognition

import components 
import threading


class App: 
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x520+350+100")
        self.main_window.configure(background='#1a001a')
        
        
        self.login_button_main_window = components.get_button(self.main_window, 'Login', '#a300a3', self.login)
        self.login_button_main_window.place(x=750, y=300)
        
        self.register_new_user_button_main_window = components.get_button(self.main_window, 'Register new user', 'slategray',
                                                                    self.register_new_user, fg='white')
        self.register_new_user_button_main_window.place(x=750, y=400)
        
        #self.logout_button_main_window = components.get_button(self.main_window,'Logout' , 'firebrick',self.logout )
        #self.logout_button_main_window.place(x=750, y=300)
        
        self.text_label_register_new_user = components.get_text_label(self.main_window,'KFCS, \nLogin or Register: ')
        self.text_label_register_new_user.place(x=750, y=150)
        
        self.webcam_label = components.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=10, width=600, height=500)
        
        self.add_webcam(self.webcam_label)
        
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
        self.log_path = './log.txt'
    def login(self):
        unknown_image_path = './.tmp.jpg'
        
        cv2.imwrite(unknown_image_path, self.most_recent_capture_arr) 

        # Corrected subprocess call
        output = subprocess.check_output(['face_recognition', self.db_dir, unknown_image_path])
        name = output.decode('utf-8').split(',')[1].strip()  # Decode bytes to string and clean up
        
        if name in ['unknown_person', 'no_persons_found']:
            components.msg_box('Ooops...', 'Unknown user. Please register new user or try again.')
        else:
            components.msg_box('Welcome back !', 'Welcome, {}.'.format(name))
            
            # Get current timestamp in a nice format
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Create a more organized log entry
            log_entry = f"""
            {'-' * 40}
            User: {name}
            Time: {timestamp}
            Action: Check-in
            {'-' * 40}
            """
            
            with open(self.log_path, 'a') as f:
                f.write(log_entry + '\n')

        os.remove(unknown_image_path)
        
        login_thread = threading.Thread(target="login", args=("self"))
        login_thread.run()
        
    def logout(self):
        pass 
    
    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")
        self.register_new_user_window.configure(background='#1a001a')
        
        self.accept_button_register_new_user_window = components.get_button(self.register_new_user_window,
                                                                            'Accept',
                                                                            '#a300a3',
                                                                            self.accept_register_new_user)
        self.accept_button_register_new_user_window.place(x=750, y=300)
        
        self.try_again_button_register_new_user_window = components.get_button(self.register_new_user_window,
                                                                               'Try Again',
                                                                               '#393900',
                                                                               self.try_again_register_new_user)
        self.try_again_button_register_new_user_window.place(x=750, y=400)
        
        self.capture_label = components.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=10, width=700, height=500)
        
        self.add_img_to_label(self.capture_label)
        
        self.entry_text_register_new_user = components.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)
        
        self.text_label_register_new_user = components.get_text_label(self.register_new_user_window,'Please, \ninput username: ')
        self.text_label_register_new_user.place(x=750, y=45)
        
          
    def add_img_to_label(self, label):
            imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
            label.imgtk = imgtk
            label.configure(image=imgtk)

            self.register_new_user_capture = self.most_recent_capture_arr.copy()
        
    def accept_register_new_user(self):
        name = self.entry_text_register_new_user.get(1.0, "end-1c")
        
        cv2.imwrite(os.path.join(self.db_dir, '{}.jpg'.format(name)), self.register_new_user_capture) 
        
        components.msg_box(name, "You have been successfully registered")
        
        self.register_new_user_window.destroy()
    
    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()
    
    def start(self):
        self.main_window.title('Kantanka Financial Co-operative Society (KFCS) Attendance System')
        
        try:
            # For Windows (.ico)
            self.main_window.iconbitmap("company_logo\KFCS.ico")  
            
            # For Linux/macOS (or if above fails)
            icon = tk.PhotoImage(file="company_logo/KFCS.ico")
            self.main_window.tk.call('wm', 'iconphoto', self.main_window._w, icon)
        except:
            print("Icon not found - using default")
        
        self.main_window.mainloop()
        
        
    def add_webcam(self, label):
    #Initialize and start webcam feed in a Tkinter label
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)  # 0 = default camera
        if not self.cap.isOpened():
            print("Error: Could not open webcam!")
            return False
    
        self._label = label  # Tkinter label where the webcam feed will be displayed
        self.process_webcam()  
        return True
        
    def process_webcam(self):
        ret, frame = self.cap.read()

        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)

        self._label.after(20, self.process_webcam)

        
if __name__ == "__main__":
    app = App()
    app.start()
