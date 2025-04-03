import tkinter as tk
import os
import cv2
from PIL import Image, ImageTk

import components 


class App: 
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.geometry("1200x520+350+100")
        
        self.login_button_main_window = components.get_button(self.main_window, 'Login', 'dodgerblue', self.login)
        self.login_button_main_window.place(x=750, y=200)
        
        self.register_new_user_button_main_window = components.get_button(self.main_window, 'Register new user', 'slategray',
                                                                    self.register_new_user, fg='black')
        self.register_new_user_button_main_window.place(x=750, y=400)
        
        self.logout_button_main_window = components.get_button(self.main_window,'Logout' , 'firebrick',self.logout )
        self.logout_button_main_window.place(x=750, y=300)
        
        self.webcam_label = components.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=10, width=600, height=500)
        
        self.add_webcam(self.webcam_label)
        
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
        self.log_path = './log.txt'
    def login(self):
        pass
    
    def logout(self):
        pass 
    
    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x520+370+120")
        #self.main_window.configure(background='#151515')
        
        self.accept_button_register_new_user_window = components.get_button(self.register_new_user_window,
                                                                            'Accept',
                                                                            'blue',
                                                                            self.accept_register_new_user)
        self.accept_button_register_new_user_window.place(x=750, y=300)
        
        self.try_again_button_register_new_user_window = components.get_button(self.register_new_user_window,
                                                                               'Try Again',
                                                                               'red',
                                                                               self.try_again_register_new_user)
        self.try_again_button_register_new_user_window.place(x=750, y=400)
        
        self.capture_label = components.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)
        
        self.add_img_to_label(self.capture_label)
        
        self.entry_text_register_new_user = components.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user.place(x=750, y=150)
        
        self.text_label_register_new_user = components.get_text_label(self.register_new_user_window,'Please, \ninput username: ')
        self.text_label_register_new_user.place(x=750, y=70)
        
        #does not work for now.  
    def add_img_to_label(self, label):
            imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
            label.imgtk = imgtk
            label.configure(image=imgtk)

            self.register_new_user_capture = self.most_recent_capture_arr.copy()
        
    def accept_register_new_user(self):
        name = self.entry_text_register_new_user.get(1.0, "end-1c")
        
    
    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()
    
    def start(self):
        self.main_window.title('Kantanka Financial Co-operative Society (KFCS) Attendance System')
        self.main_window.mainloop()
        
        
    def add_webcam(self, label):
    #Initialize and start webcam feed in a Tkinter label
    # Initialize VideoCapture if not already done
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)  # 0 = default camera
        if not self.cap.isOpened():
            print("Error: Could not open webcam!")
            return False
    
        self._label = label  # Tkinter label where the webcam feed will be displayed
        self.process_webcam()  # Start the webcam processing loop  
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
