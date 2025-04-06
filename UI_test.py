import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import tkinter.font as tkFont
from PIL import Image, ImageTk

class AttendanceUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1280x720+100+50")
        self.root.title("KFCS Attendance Pro")
        self.root.configure(bg='#f5f5f5')
        
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
        
        # logo call 
        self.create_logo()
        
        self.root.mainloop()
    
    def create_main_container(self):
        # Shadow effect
        self.shadow = tk.Frame(self.root, bg='#e0e0e0')
        self.shadow.place(x=52, y=52, width=1180, height=620)
        
        # Main white container
        self.main_frame = tk.Frame(self.root, bg='white', bd=0, 
                                 highlightthickness=0, relief='ridge')
        self.main_frame.place(x=50, y=50, width=1180, height=620)
    
    def create_webcam_section(self):
        # Container for webcam with dark border
        self.webcam_container = tk.Frame(self.main_frame, bg='#333', bd=0)
        self.webcam_container.place(x=30, y=30, width=640, height=480)
        
        # Placeholder for webcam feed
        self.webcam_label = tk.Label(self.webcam_container, bg='#333')
        self.webcam_label.place(x=2, y=2, width=636, height=476)
        
        #  "webcam not active" message
        self.webcam_label.config(text="WEBCAM FEED\n[Preview Area]", 
                               fg="white", font=self.button_font,
                               justify='center')
    
    def create_control_panel(self):
        """Create the right-side control panel"""
        self.control_panel = tk.Frame(self.main_frame, bg='white', bd=0)
        self.control_panel.place(x=700, y=30, width=450, height=560)
        
        # Welcome message
        tk.Label(self.control_panel, text="Welcome to KFCS", 
                font=self.title_font, bg='white', fg='#333').pack(pady=10)
        
        # Modern buttons
        self.login_btn = self.create_modern_button(
            self.control_panel, "CHECK IN", "#4CAF50", self.mock_command)
        self.login_btn.pack(pady=15, ipady=10)
        
        self.logout_btn = self.create_modern_button(
            self.control_panel, "CHECK OUT", "#F44336", self.mock_command)
        self.logout_btn.pack(pady=15, ipady=10)
        
        self.register_btn = self.create_modern_button(
            self.control_panel, "REGISTER NEW USER", "#2196F3", self.mock_command)
        self.register_btn.pack(pady=15, ipady=10)
        
        # Add some decorative elements
        ttk.Separator(self.control_panel, orient='horizontal').pack(fill='x', pady=20)
        
        # Quick stats placeholder
        stats_frame = tk.Frame(self.control_panel, bg='white')
        stats_frame.pack()
        
        tk.Label(stats_frame, text="Today's Stats", font=self.button_font,
                bg='white').grid(row=0, columnspan=2, pady=5)
                
        tk.Label(stats_frame, text="Checked in:", bg='white').grid(row=1, column=0, sticky='e')
        tk.Label(stats_frame, text="24", bg='white', fg='#4CAF50').grid(row=1, column=1, sticky='w')
        
        tk.Label(stats_frame, text="Pending:", bg='white').grid(row=2, column=0, sticky='e')
        tk.Label(stats_frame, text="5", bg='white', fg='#FF9800').grid(row=2, column=1, sticky='w')
    
    def create_status_bar(self):
        self.status = tk.Label(self.main_frame, text="System Ready | Connected | Last sync: Today 10:00 AM", 
                             font=self.small_font, bg='white', fg='#666',
                             anchor='w')
        self.status.place(x=30, y=530, width=1120)
    
    def create_admin_button(self):
        self.admin_btn = tk.Label(self.main_frame, text="⚙", font=("Arial", 14), 
                                 bg='white', fg='#999', cursor="hand2")
        self.admin_btn.place(x=1130, y=580)
        self.admin_btn.bind("<Button-1>", lambda e: self.show_admin_panel())
    
    def create_logo(self):
        try:
            # Try to load actual logo
            self.logo_img = Image.open("logo.png").resize((200,80))
            self.logo_tk = ImageTk.PhotoImage(self.logo_img)
        except:
            # Create a placeholder if logo not found
            self.logo_img = Image.new('RGB', (200, 80), color='#2196F3')
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
    
    def show_admin_panel(self):
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
        columns = ("Date", "User", "Action", "Status")
        self.tree = ttk.Treeview(reports_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Insert sample data
        sample_data = [
            ("2023-05-01 08:45", "John Doe", "Check-in", "On time"),
            ("2023-05-01 17:30", "John Doe", "Check-out", "Complete"),
            ("2023-05-01 09:15", "Jane Smith", "Check-in", "Late"),
            ("2023-05-01 16:45", "Jane Smith", "Check-out", "Early")
        ]
        
        for item in sample_data:
            self.tree.insert("", "end", values=item)
        
        # Export button
        ttk.Button(reports_frame, text="Export to Excel", 
                  command=self.mock_command).pack(pady=10)
        
        # Tab 2: Working Hours
        hours_frame = ttk.Frame(notebook)
        notebook.add(hours_frame, text="Working Hours")
        
        #Sample working hours chart
        tk.Label(hours_frame, text="Weekly Hours Report", 
                font=self.title_font).pack(pady=10)
        
        #Placeholder for chart
        chart_placeholder = tk.Canvas(hours_frame, bg='white', height=300)
        chart_placeholder.pack(fill='x', padx=20, pady=20)
        
        #simple bar chart
        chart_placeholder.create_rectangle(50, 50, 100, 250, fill='#4CAF50')
        chart_placeholder.create_rectangle(120, 100, 170, 250, fill='#4CAF50')
        chart_placeholder.create_rectangle(190, 150, 240, 250, fill='#4CAF50')
        chart_placeholder.create_text(75, 270, text="Mon")
        chart_placeholder.create_text(145, 270, text="Tue")
        chart_placeholder.create_text(215, 270, text="Wed")
        
        # Tab 3: User Management
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="User Management")
        
        # User list
        user_list = ttk.Treeview(user_frame, columns=("ID", "Name", "Department"), 
                               show="headings")
        user_list.heading("ID", text="ID")
        user_list.heading("Name", text="Name")
        user_list.heading("Department", text="Department")
        user_list.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sample users
        users = [
            ("101", "John Doe", "Accounting"),
            ("102", "Jane Smith", "HR"),
            ("103", "Bob Johnson", "IT")
        ]
        
        for user in users:
            user_list.insert("", "end", values=user)
        
        # Action buttons
        btn_frame = tk.Frame(user_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Add User", command=self.mock_command).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Edit User", command=self.mock_command).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove User", command=self.mock_command).pack(side='left', padx=5)
    #manipulate message box to get shots for the UI in the meantime. 
    def mock_command(self):
        """Placeholder for button commands"""
        messagebox.showinfo("Notice", "This is a UI mockup\nFunctionality not implemented")


if __name__ == "__main__":
    app = AttendanceUI()