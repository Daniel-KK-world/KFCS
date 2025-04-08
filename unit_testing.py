import tkinter as tk
from tkinter import simpledialog

class CustomDialog(simpledialog.Dialog):
    def body(self, master):
        self.geometry("400x300")  # Attempt to resize
        tk.Label(master, text="Enter user's name:").pack()
        self.entry = tk.Entry(master, width=50)  # Make input field bigger
        self.entry.pack()
        return self.entry

    def apply(self):
        self.result = self.entry.get()

root = tk.Tk()
root.withdraw()

dialog = CustomDialog(root, "Register New User")
print("User entered:", dialog.result)
