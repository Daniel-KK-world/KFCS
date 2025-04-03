import os
import pickle

import tkinter as tk
from tkinter import messagebox
import face_recognition


def get_button(window, text, color, command, fg='white'):
    # Modern flat button with hover effects
    button = tk.Button(
        window,
        text=text,
        bg=color,
        fg=fg,
        activebackground=color,  # Slightly darker version of 'color' would be better
        activeforeground=fg,
        command=command,
        height=2,
        width=20,
        font=('Helvetica', 20, 'bold'),  # More standard than 'Helvetica bold'
        borderwidth=0,                   # Remove default 3D border
        highlightthickness=0,            # Remove focus ring
        relief='flat'                    # Flat modern style
    )

    # Add hover effects (dynamic color change)
    def on_enter(e):
        e.widget.config(bg=darken_color(color))  # Darken color by 20% on hover

    def on_leave(e):
        e.widget.config(bg=color)  # Restore original color

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    return button

def darken_color(self, color, amount=20):
    """
    Darkens a color by specified percentage (0-100)
    Works with:
    - Hex strings ('#RRGGBB')
    - Named colors ('dodgerblue')
    - RGB tuples ((255, 0, 0))
    """
    try:
        # Convert named colors to hex
        if isinstance(color, str) and not color.startswith('#') and hasattr(tk, 'color_map'):
            if color.lower() in tk.color_map:
                color = tk.color_map[color.lower()]
            else:
                return color  # Return original if not a known color name
        
        # Handle hex colors
        if isinstance(color, str) and color.startswith('#'):
            if len(color) == 7:  # #RRGGBB format
                r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
            elif len(color) == 4:  # #RGB format
                r, g, b = (int(color[i]*2, 16) for i in (1, 2, 3))
            else:
                return color
            
            # Darken each channel
            r = max(0, int(r * (100 - amount) / 100))
            g = max(0, int(g * (100 - amount) / 100))
            b = max(0, int(b * (100 - amount) / 100))
            
            return f'#{int(r):02x}{int(g):02x}{int(b):02x}'
        
        # Handle RGB tuples
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            return tuple(max(0, int(channel * (100 - amount) / 100)) for channel in color)
        
        return color  # Fallback for invalid formats
    
    except Exception:
        return color  # Return original color if any error occurs


def get_img_label(window):
    label = tk.Label(window)
    label.grid(row=0, column=0)
    return label


def get_text_label(window, text):
    label = tk.Label(window, text=text)
    label.config(font=("sans-serif", 21), justify="left")
    return label


def get_entry_text(window):
    inputtxt = tk.Text(window,
                       height=2,
                       width=15, font=("Arial", 32))
    return inputtxt


def msg_box(title, description):
    messagebox.showinfo(title, description)


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

