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