import os
import pickle
import ctypes

import tkinter as tk
from tkinter import messagebox
import face_recognition


def get_button(window, text, color, command, fg='white'):
    # Modern flat button base with hover effects
    button = tk.Button(
        window,
        text=text,
        bg=color,
        fg=fg,
        activebackground='black',
        activeforeground=fg,
        command=command,
        height=2,
        width=20,
        font=('Helvetica', 20, 'bold'), 
        borderwidth=0,                  
        highlightthickness=0,     
        relief='flat'                   
    )

    return button



def get_img_label(window):
    label = tk.Label(window)
    label.grid(row=0, column=0)
    return label


def get_text_label(window, text, bg_color="#390039", text_color="white"):
    label = tk.Label(
        window,
        text=text,
        font=("Helvetica", 21, "bold"),  
        fg=text_color,     
        bg=bg_color,       
        justify="left",
        padx=20,                      
        pady=10,                        
        relief="flat",                   
        bd=0                            
    )
    return label

'''def get_entry_text(window):
    inputtxt = tk.Text(window,
                       height=2,
                       width=15, font=("Arial", 32)
                       bg='#868600')
    return inputtxt '''

def get_entry_text(window):
    inputtxt = tk.Text(
        window,
        height=2,
        width=15,
        font=("Arial", 32),
        background= 'slategray',  # Background color (your dark yellow)
        fg='white',   # Text color
        insertbackground='white',  # Cursor color
        selectbackground='#555555',  # Selection highlight bg
        selectforeground='white',    # Selection text color
        relief='flat',  # Remove border relief
        highlightthickness=1,  # Border thickness
        highlightcolor='#868600',  # Border color (matches bg)
        highlightbackground='#868600',  # Border color when not focused
        padx=10,  # Inner padding
        pady=5
    )
    return inputtxt

ctypes.windll.user32.MessageBoxW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
ctypes.windll.user32.MessageBoxW.restype = ctypes.c_int

def msg_box(title, description):
    ctypes.windll.user32.MessageBoxW(0, description, title, 0x40)


def recognize(img, db_path):
    # it is assumed there will be at most 1 match in the db

    embeddings_unknown = face_recognition.face_encodings(img)
    if len(embeddings_unknown) == 0:
        return 'no_persons_found'
    else:
        embeddings_unknown = embeddings_unknown[0]

    db_dir = sorted(os.listdir(db_path))

    match = False
    j = 0
    while not match and j < len(db_dir):
        path_ = os.path.join(db_path, db_dir[j])

        file = open(path_, 'rb')
        embeddings = pickle.load(file)

        match = face_recognition.compare_faces([embeddings], embeddings_unknown)[0]
        j += 1

    if match:
        return db_dir[j - 1][:-7]
    else:
        return 'unknown_person'

