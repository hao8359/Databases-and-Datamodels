# -*- coding: utf-8 -*-
"""
Enhanced Clinic Management System - GUI Application
==================================================

Created on Wed Sep 10 15:04:12 2025
@author: marin

This is a comprehensive clinic management system with a modern GUI interface.
It provides separate interfaces for patients and doctors with the following features:

PATIENT FEATURES:
- Book appointments with specific doctors and departments
- View personal appointment history
- Search appointments by name

DOCTOR FEATURES:
- Login with doctor credentials
- View assigned appointments
- Upload and manage medical files (images, documents, etc.)
- Record medical observations
- Execute database queries for research

TECHNICAL FEATURES:
- Modern Tkinter GUI with custom styling
- MySQL database integration
- File upload and management system
- Comprehensive error handling
- Responsive design with modern color scheme
"""

# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
import os                    # File system operations
import shutil               # File copying and moving
import re                   # Regular expressions for validation
import datetime             # Date and time handling
import tkinter as tk        # Main GUI framework
from tkinter import ttk, filedialog, messagebox, Text  # GUI components
from clinic_v2_withoutGUI import ClinicDatabaseNotebook  # Database operations

# =============================================================================
# CONFIGURATION SETTINGS
# =============================================================================
# Database connection parameters
DB_CONFIG = {
    "host": "localhost",        # MySQL server address
    "user": "root",            # Database username
    "password": "root",    # Database password
    "database": "clinic_db"    # Database name
}

# File upload directory - creates 'uploads' folder in the same directory as this script
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create directory if it doesn't exist

# =============================================================================
# UI COLOR SCHEME
# =============================================================================
# Modern color palette for consistent theming throughout the application
COLORS = {
    'primary': '#2E86AB',        # Medical blue - main brand color
    'secondary': '#A23B72',      # Accent pink - highlights and accents
    'success': '#06A77D',        # Success green - positive actions
    'warning': '#F18F01',        # Warning orange - caution messages
    'danger': '#C73E1D',         # Error red - error states
    'light': '#F5F5F5',          # Light gray - subtle backgrounds
    'dark': '#2C3E50',           # Dark blue-gray - text and headers
    'white': '#FFFFFF',          # Pure white
    'text': '#2C3E50',           # Primary text color
    'bg_main': '#F8F9FA',        # Main background color
    'bg_card': '#FFFFFF',        # Card/panel background
    'border': '#DEE2E6'          # Border color for separation
}

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
# Create database connection object with configuration parameters
db = ClinicDatabaseNotebook(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"]
)

# =============================================================================
# DATABASE SETUP FUNCTIONS
# =============================================================================
def setup_database_if_needed():
    """
    Initialize database connection and setup tables if needed.
    
    This function:
    1. Attempts to connect to the database
    2. Creates the database if it doesn't exist
    3. Creates all necessary tables if they don't exist
    4. Inserts sample data for testing purposes
    
    Raises:
        RuntimeError: If database connection or creation fails
    """
    try:
        # Try to connect to existing database
        if not db.connect():
            # If connection fails, try to create the database
            created = db.create_database()
            if not created:
                raise RuntimeError("Could not create database. Check MySQL access/credentials.")
            # Try connecting again after creating database
            if not db.connect():
                raise RuntimeError("Failed to connect after creating database.")

        # Check if tables exist
        db.cursor.execute("SHOW TABLES")
        tables = db.cursor.fetchall()
        
        if not tables:
            # No tables found - create them and insert sample data
            print("No tables found – creating tables and inserting sample data...")
            db.create_all_tables()
            db.insert_all_sample_data()
        else:
            # Tables exist - just show what we found
            print(f"Found tables: {[t[0] for t in tables]}")

    except Exception as e:
        # Re-raise any exceptions for proper error handling
        raise

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def validate_date_yyyy_mm_dd(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid date format, False otherwise
    """
    # Check if string matches YYYY-MM-DD pattern using regex
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        # Try to parse the date to ensure it's a valid date
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        # Invalid date (e.g., 2024-02-30)
        return False

def safe_select(query, params=()):
    """
    Execute a SELECT query safely and return results.
    
    This function provides a safety mechanism to prevent dangerous SQL operations
    by only allowing SELECT queries. This prevents accidental data modification
    or deletion through the query interface.
    
    Args:
        query (str): SQL query string
        params (tuple): Query parameters for prepared statements
        
    Returns:
        tuple: (column_names, rows) - Query results
        
    Raises:
        ValueError: If query is not a SELECT statement
    """
    q = query.strip()
    # Security check: only allow SELECT queries
    if not q.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed in Query tab for safety.")
    
    # Execute the query
    db.cursor.execute(query, params)
    rows = db.cursor.fetchall()
    
    # Extract column names from cursor description
    colnames = [desc[0] for desc in db.cursor.description] if db.cursor.description else []
    return colnames, rows

# =============================================================================
# UI STYLING FUNCTIONS
# =============================================================================
def configure_modern_style():
    """
    Configure modern Tkinter TTK styles for a professional appearance.
    
    This function sets up custom styles for all GUI components including:
    - Buttons with different states (normal, active, pressed)
    - Frames with card-like appearance
    - Labels with consistent typography
    - Entry fields and comboboxes with modern styling
    
    The styles use the predefined color scheme for consistency.
    """
    style = ttk.Style()
    
    # ===== BUTTON STYLES =====
    # Primary button style - main action buttons
    style.configure('Modern.TButton',
                   background=COLORS['primary'],
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none',
                   relief='flat',
                   padding=(20, 10))
    
    # Button state mappings - different colors for hover/press states
    style.map('Modern.TButton',
              background=[('active', COLORS['secondary']),
                         ('pressed', COLORS['dark'])])
    
    # Success button style - for positive actions (save, confirm)
    style.configure('Success.TButton',
                   background=COLORS['success'],
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none',
                   relief='flat',
                   padding=(15, 8))
    
    # Warning button style - for caution actions (upload, delete)
    style.configure('Warning.TButton',
                   background=COLORS['warning'],
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none',
                   relief='flat',
                   padding=(15, 8))
    
    # ===== FRAME STYLES =====
    # Card frame style - for content panels
    style.configure('Card.TFrame',
                   background=COLORS['bg_card'],
                   relief='flat',
                   borderwidth=1)
    
    # ===== LABEL STYLES =====
    # Heading label style - for section titles
    style.configure('Heading.TLabel',
                   background=COLORS['bg_card'],
                   foreground=COLORS['text'],
                   font=('Segoe UI', 12, 'bold'))
    
    # Modern label style - for regular text
    style.configure('Modern.TLabel',
                   background=COLORS['bg_card'],
                   foreground=COLORS['text'],
                   font=('Segoe UI', 10))
    
    # ===== INPUT STYLES =====
    # Modern entry field style
    style.configure('Modern.TEntry',
                   relief='flat',
                   borderwidth=1,
                   padding=8)
    
    # Modern combobox style
    style.configure('Modern.TCombobox',
                   relief='flat',
                   borderwidth=1,
                   padding=8)

# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================
class ClinicApp(tk.Tk):
    """
    Main application class for the Clinic Management System.
    
    This is the root window that provides the main interface with two primary options:
    1. Patient Portal - for booking appointments and viewing medical history
    2. Doctor Dashboard - for managing patients, appointments, and medical records
    
    The interface uses a modern card-based design with clear visual hierarchy.
    """
    
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        self.title("Advanced Clinic Management System")
        self.geometry("800x600")
        self.configure(bg=COLORS['bg_main'])
        
        # Apply modern styling to all components
        configure_modern_style()
        
        # Create main container with padding for better visual spacing
        main_container = tk.Frame(self, bg=COLORS['bg_main'])
        main_container.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Header section
        header_frame = tk.Frame(main_container, bg=COLORS['bg_main'])
        header_frame.pack(fill='x', pady=(0, 30))
        
        # Title with medical symbol
        title_label = tk.Label(header_frame, 
                              text="🏥 Advanced Clinic Management System",
                              font=('Segoe UI', 24, 'bold'),
                              fg=COLORS['primary'],
                              bg=COLORS['bg_main'])
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame,
                                 text="Modern Healthcare Management Solution",
                                 font=('Segoe UI', 12),
                                 fg=COLORS['text'],
                                 bg=COLORS['bg_main'])
        subtitle_label.pack(pady=(5, 0))
        
        # Main buttons container
        buttons_frame = tk.Frame(main_container, bg=COLORS['bg_main'])
        buttons_frame.pack(expand=True)
        
        # Patient interface button
        patient_frame = tk.Frame(buttons_frame, bg=COLORS['bg_card'], relief='solid', bd=1)
        patient_frame.pack(pady=15, padx=20, fill='x')
        
        patient_icon = tk.Label(patient_frame, text="👤", font=('Segoe UI', 32), 
                               bg=COLORS['bg_card'])
        patient_icon.pack(pady=(20, 10))
        
        patient_title = tk.Label(patient_frame, text="Patient Portal",
                                font=('Segoe UI', 16, 'bold'),
                                fg=COLORS['text'], bg=COLORS['bg_card'])
        patient_title.pack()
        
        patient_desc = tk.Label(patient_frame, 
                               text="Book appointments and view your medical history",
                               font=('Segoe UI', 10),
                               fg=COLORS['text'], bg=COLORS['bg_card'])
        patient_desc.pack(pady=(5, 15))
        
        patient_btn = ttk.Button(patient_frame, text="Enter Patient Portal", 
                                style='Modern.TButton',
                                command=self.open_patient)
        patient_btn.pack(pady=(0, 20))
        
        # Doctor interface button
        doctor_frame = tk.Frame(buttons_frame, bg=COLORS['bg_card'], relief='solid', bd=1)
        doctor_frame.pack(pady=15, padx=20, fill='x')
        
        doctor_icon = tk.Label(doctor_frame, text="👩‍⚕️", font=('Segoe UI', 32), 
                              bg=COLORS['bg_card'])
        doctor_icon.pack(pady=(20, 10))
        
        doctor_title = tk.Label(doctor_frame, text="Doctor Dashboard",
                               font=('Segoe UI', 16, 'bold'),
                               fg=COLORS['text'], bg=COLORS['bg_card'])
        doctor_title.pack()
        
        doctor_desc = tk.Label(doctor_frame, 
                              text="Manage appointments, patients and medical observations",
                              font=('Segoe UI', 10),
                              fg=COLORS['text'], bg=COLORS['bg_card'])
        doctor_desc.pack(pady=(5, 15))
        
        doctor_btn = ttk.Button(doctor_frame, text="Enter Doctor Dashboard", 
                               style='Modern.TButton',
                               command=self.open_doctor)
        doctor_btn.pack(pady=(0, 20))
        
        # Footer
        footer_frame = tk.Frame(main_container, bg=COLORS['bg_main'])
        footer_frame.pack(side='bottom', fill='x', pady=(30, 0))
        
        status_label = tk.Label(footer_frame,
                               text="💡 Ensure MySQL server is running with correct credentials",
                               font=('Segoe UI', 9),
                               fg=COLORS['warning'],
                               bg=COLORS['bg_main'])
        status_label.pack()

    def open_patient(self):
        PatientWindow(self)

    def open_doctor(self):
        DoctorWindow(self)

class PatientWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Patient Portal")
        self.geometry("900x700")
        self.configure(bg=COLORS['bg_main'])
        
        # Header
        header = tk.Frame(self, bg=COLORS['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(header, text="👤 Patient Portal", 
                        font=('Segoe UI', 18, 'bold'),
                        fg='white', bg=COLORS['primary'])
        title.pack(expand=True)
        
        # Main content with notebook
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Tab 1: Book Appointment
        tab1 = self.create_booking_tab(notebook)
        notebook.add(tab1, text="📅 Book Appointment")
        
        # Tab 2: View Appointments
        tab2 = self.create_appointments_tab(notebook)
        notebook.add(tab2, text="📋 My Appointments")
        
        # Load initial data
        self._dept_map = {}
        self._doctor_map = {}
        self.load_departments()
    
    def create_booking_tab(self, parent):
        tab = ttk.Frame(parent)
        
        # Main container
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Patient Information Card
        info_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        info_card.pack(fill='x', pady=(0, 20))
        
        info_title = tk.Label(info_card, text="📝 Patient Information",
                             font=('Segoe UI', 14, 'bold'),
                             fg=COLORS['text'], bg=COLORS['bg_card'])
        info_title.pack(pady=(15, 10))
        
        # Form grid
        form_frame = tk.Frame(info_card, bg=COLORS['bg_card'])
        form_frame.pack(padx=30, pady=(0, 20))
        
        # First Name
        tk.Label(form_frame, text="First Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=8)
        self.fname_entry = ttk.Entry(form_frame, style='Modern.TEntry', font=('Segoe UI', 11), width=25)
        self.fname_entry.grid(row=0, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        # Last Name
        tk.Label(form_frame, text="Last Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=1, column=0, sticky='w', pady=8)
        self.lname_entry = ttk.Entry(form_frame, style='Modern.TEntry', font=('Segoe UI', 11), width=25)
        self.lname_entry.grid(row=1, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Appointment Details Card
        appt_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        appt_card.pack(fill='x', pady=(0, 20))
        
        appt_title = tk.Label(appt_card, text="🏥 Appointment Details",
                             font=('Segoe UI', 14, 'bold'),
                             fg=COLORS['text'], bg=COLORS['bg_card'])
        appt_title.pack(pady=(15, 10))
        
        # Appointment form
        appt_form = tk.Frame(appt_card, bg=COLORS['bg_card'])
        appt_form.pack(padx=30, pady=(0, 20))
        
        # Department
        tk.Label(appt_form, text="Department:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=8)
        self.dept_combo = ttk.Combobox(appt_form, state="readonly", style='Modern.TCombobox',
                                      font=('Segoe UI', 11), width=23)
        self.dept_combo.grid(row=0, column=1, sticky='ew', pady=8, padx=(10, 0))
        self.dept_combo.bind("<<ComboboxSelected>>", self.on_dept_selected)
        
        # Doctor
        tk.Label(appt_form, text="Doctor:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=1, column=0, sticky='w', pady=8)
        self.doctor_combo = ttk.Combobox(appt_form, state="readonly", style='Modern.TCombobox',
                                        font=('Segoe UI', 11), width=23)
        self.doctor_combo.grid(row=1, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        # Date
        tk.Label(appt_form, text="Preferred Date:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=2, column=0, sticky='w', pady=8)
        self.date_entry = ttk.Entry(appt_form, style='Modern.TEntry', font=('Segoe UI', 11), width=25)
        self.date_entry.grid(row=2, column=1, sticky='ew', pady=8, padx=(10, 0))
        self.date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        appt_form.grid_columnconfigure(1, weight=1)
        
        # Book button
        book_btn = ttk.Button(container, text="📅 Book Appointment", 
                             style='Success.TButton',
                             command=self.book_appointment)
        book_btn.pack(pady=10)
        
        return tab
    
    def create_appointments_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Search card
        search_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        search_card.pack(fill='x', pady=(0, 20))
        
        search_title = tk.Label(search_card, text="🔍 Find My Appointments",
                               font=('Segoe UI', 14, 'bold'),
                               fg=COLORS['text'], bg=COLORS['bg_card'])
        search_title.pack(pady=(15, 10))
        
        search_form = tk.Frame(search_card, bg=COLORS['bg_card'])
        search_form.pack(padx=30, pady=(0, 20))
        
        tk.Label(search_form, text="First Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=5)
        self.view_fname = ttk.Entry(search_form, style='Modern.TEntry', font=('Segoe UI', 11), width=20)
        self.view_fname.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 20))
        
        tk.Label(search_form, text="Last Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=2, sticky='w', pady=5)
        self.view_lname = ttk.Entry(search_form, style='Modern.TEntry', font=('Segoe UI', 11), width=20)
        self.view_lname.grid(row=0, column=3, sticky='ew', pady=5, padx=(10, 0))
        
        search_btn = ttk.Button(search_form, text="🔍 Search", 
                               style='Modern.TButton',
                               command=self.load_appointments_for_patient)
        search_btn.grid(row=0, column=4, padx=(20, 0))
        
        search_form.grid_columnconfigure(1, weight=1)
        search_form.grid_columnconfigure(3, weight=1)
        
        # Results card
        results_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        results_card.pack(fill='both', expand=True)
        
        results_title = tk.Label(results_card, text="📋 Your Appointments",
                                font=('Segoe UI', 14, 'bold'),
                                fg=COLORS['text'], bg=COLORS['bg_card'])
        results_title.pack(pady=(15, 10))
        
        # Text area with scrollbar
        text_frame = tk.Frame(results_card, bg=COLORS['bg_card'])
        text_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.appt_text = Text(text_frame, height=15, width=80, font=('Segoe UI', 10),
                             relief='flat', bg=COLORS['light'], fg=COLORS['text'])
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.appt_text.yview)
        self.appt_text.configure(yscrollcommand=scrollbar.set)
        
        self.appt_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        return tab
    
    def load_departments(self):
        try:
            db.cursor.execute("SELECT department_id, name FROM department ORDER BY name")
            rows = db.cursor.fetchall()
            names = []
            for r in rows:
                self._dept_map[r[1]] = r[0]
                names.append(r[1])
            self.dept_combo["values"] = names
            if names:
                self.dept_combo.current(0)
                self.on_dept_selected()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load departments:\n{e}")
    
    def on_dept_selected(self, event=None):
        dept_name = self.dept_combo.get()
        dept_id = self._dept_map.get(dept_name)
        if not dept_id:
            self.doctor_combo["values"] = []
            return
        try:
            db.cursor.execute("SELECT doctor_id, first_name, last_name FROM doctor WHERE department_id=%s", (dept_id,))
            rows = db.cursor.fetchall()
            names = []
            self._doctor_map = {}
            for r in rows:
                label = f"Dr. {r[1]} {r[2]}"
                self._doctor_map[label] = r[0]
                names.append(label)
            self.doctor_combo["values"] = names
            if names:
                self.doctor_combo.current(0)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load doctors for department:\n{e}")
    
    def book_appointment(self):
        fname = self.fname_entry.get().strip()
        lname = self.lname_entry.get().strip()
        doctor_label = self.doctor_combo.get()
        date = self.date_entry.get().strip()
        
        if not (fname and lname and doctor_label and date):
            messagebox.showerror("Input Error", "Please fill in all required fields.")
            return
        if not validate_date_yyyy_mm_dd(date):
            messagebox.showerror("Input Error", "Date must be in YYYY-MM-DD format")
            return
        
        try:
            doctor_id = self._doctor_map.get(doctor_label)
            if not doctor_id:
                messagebox.showerror("Input Error", "Please select a valid doctor.")
                return
            
            # Check if patient exists
            db.cursor.execute("SELECT patient_id FROM patient WHERE first_name=%s AND last_name=%s", (fname, lname))
            row = db.cursor.fetchone()
            if row:
                patient_id = row[0]
            else:
                # Create new patient
                db.cursor.execute("INSERT INTO patient (first_name, last_name, doctor_id) VALUES (%s,%s,%s)",
                                 (fname, lname, doctor_id))
                db.connection.commit()
                patient_id = db.cursor.lastrowid
            
            # Create appointment
            db.cursor.execute("INSERT INTO appointment (doctor_id, date, patient_id) VALUES (%s,%s,%s)",
                             (doctor_id, date, patient_id))
            db.connection.commit()
            
            messagebox.showinfo("Success", "✅ Appointment booked successfully!\n\nYou will receive a confirmation shortly.")
            
            # Clear form
            self.fname_entry.delete(0, tk.END)
            self.lname_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not book appointment:\n{e}")
    
    def load_appointments_for_patient(self):
        fname = self.view_fname.get().strip()
        lname = self.view_lname.get().strip()
        if not (fname and lname):
            messagebox.showerror("Input Error", "Please enter both first and last name.")
            return
        try:
            db.cursor.execute("""
                SELECT a.appointment_id, a.date, d.first_name, d.last_name, dept.name
                FROM appointment a
                JOIN doctor d ON a.doctor_id=d.doctor_id
                JOIN patient p ON a.patient_id=p.patient_id
                JOIN department dept ON d.department_id=dept.department_id
                WHERE p.first_name=%s AND p.last_name=%s
                ORDER BY a.date
            """, (fname, lname))
            rows = db.cursor.fetchall()
            
            self.appt_text.delete("1.0", tk.END)
            if not rows:
                self.appt_text.insert(tk.END, "No appointments found for this patient.\n\n")
                self.appt_text.insert(tk.END, "Please check the name spelling or book a new appointment.")
                return
            
            self.appt_text.insert(tk.END, f"📋 Appointments for {fname} {lname}\n")
            self.appt_text.insert(tk.END, "="*50 + "\n\n")
            
            for r in rows:
                self.appt_text.insert(tk.END, f"🏥 Appointment #{r[0]}\n")
                self.appt_text.insert(tk.END, f"📅 Date: {r[1]}\n")
                self.appt_text.insert(tk.END, f"👩‍⚕️ Doctor: Dr. {r[2]} {r[3]}\n")
                self.appt_text.insert(tk.END, f"🏢 Department: {r[4]}\n")
                self.appt_text.insert(tk.END, "-"*30 + "\n\n")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not retrieve appointments:\n{e}")

class DoctorWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Doctor Dashboard")
        self.geometry("1100x800")
        self.configure(bg=COLORS['bg_main'])
        self.doctor_id = None
        self.appointment_map = {}
        
        # Header
        header = tk.Frame(self, bg=COLORS['secondary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(header, text="👩‍⚕️ Doctor Dashboard", 
                        font=('Segoe UI', 18, 'bold'),
                        fg='white', bg=COLORS['secondary'])
        title.pack(expand=True)
        
        # Main content with notebook
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Tab 1: Login & Appointments
        tab1 = self.create_login_tab(notebook)
        notebook.add(tab1, text="🔐 Login & Appointments")
        
        # Tab 2: Medical Observations
        tab2 = self.create_observation_tab(notebook)
        notebook.add(tab2, text="📋 Medical Records & Files")
        
        # Tab 3: Database Queries
        tab3 = self.create_query_tab(notebook)
        notebook.add(tab3, text="🔍 Research Queries")
        
        # Load doctors
        self.doctor_map = {}
        self.load_doctors()
    
    def create_login_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Login Card
        login_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        login_card.pack(fill='x', pady=(0, 20))
        
        login_title = tk.Label(login_card, text="🔐 Doctor Authentication",
                              font=('Segoe UI', 14, 'bold'),
                              fg=COLORS['text'], bg=COLORS['bg_card'])
        login_title.pack(pady=(15, 10))
        
        login_form = tk.Frame(login_card, bg=COLORS['bg_card'])
        login_form.pack(padx=30, pady=(0, 20))
        
        tk.Label(login_form, text="Select Your Profile:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=8)
        self.doctor_combo = ttk.Combobox(login_form, state="readonly", style='Modern.TCombobox',
                                        font=('Segoe UI', 11), width=30)
        self.doctor_combo.grid(row=0, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        login_btn = ttk.Button(login_form, text="🔓 Login", 
                              style='Success.TButton',
                              command=self.login_doctor)
        login_btn.grid(row=0, column=2, padx=(15, 0))
        
        login_form.grid_columnconfigure(1, weight=1)
        
        # Appointments Card
        appt_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        appt_card.pack(fill='both', expand=True)
        
        appt_title = tk.Label(appt_card, text="📅 Today's Appointments",
                             font=('Segoe UI', 14, 'bold'),
                             fg=COLORS['text'], bg=COLORS['bg_card'])
        appt_title.pack(pady=(15, 10))
        
        # Listbox with scrollbar
        list_frame = tk.Frame(appt_card, bg=COLORS['bg_card'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.appt_listbox = tk.Listbox(list_frame, height=12, font=('Segoe UI', 10),
                                      bg=COLORS['light'], fg=COLORS['text'],
                                      selectbackground=COLORS['primary'])
        scrollbar_appt = ttk.Scrollbar(list_frame, orient='vertical', command=self.appt_listbox.yview)
        self.appt_listbox.configure(yscrollcommand=scrollbar_appt.set)
        
        self.appt_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_appt.pack(side='right', fill='y')
        
        refresh_btn = ttk.Button(appt_card, text="🔄 Refresh Appointments", 
                                style='Modern.TButton',
                                command=self.load_doctor_appointments)
        refresh_btn.pack(pady=(0, 15))
        
        return tab
    
    def create_observation_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Appointment Selection Card
        select_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        select_card.pack(fill='x', pady=(0, 20))
        
        select_title = tk.Label(select_card, text="📋 Select Patient Appointment",
                               font=('Segoe UI', 14, 'bold'),
                               fg=COLORS['text'], bg=COLORS['bg_card'])
        select_title.pack(pady=(15, 10))
        
        select_form = tk.Frame(select_card, bg=COLORS['bg_card'])
        select_form.pack(padx=30, pady=(0, 20))
        
        tk.Label(select_form, text="Appointment:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=5)
        self.appt_combo = ttk.Combobox(select_form, state="readonly", style='Modern.TCombobox',
                                      font=('Segoe UI', 11), width=50)
        self.appt_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        select_form.grid_columnconfigure(1, weight=1)
        
        # Medical Observation Card
        obs_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        obs_card.pack(fill='both', expand=True)
        
        obs_title = tk.Label(obs_card, text="🩺 Medical Observation & File Upload",
                            font=('Segoe UI', 14, 'bold'),
                            fg=COLORS['text'], bg=COLORS['bg_card'])
        obs_title.pack(pady=(15, 10))
        
        obs_form = tk.Frame(obs_card, bg=COLORS['bg_card'])
        obs_form.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        # Observation Type
        tk.Label(obs_form, text="Observation Type:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=8)
        self.obs_type_entry = ttk.Entry(obs_form, style='Modern.TEntry', font=('Segoe UI', 11), width=30)
        self.obs_type_entry.grid(row=0, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        # Description
        tk.Label(obs_form, text="Description:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=1, column=0, sticky='nw', pady=8)
        
        text_frame = tk.Frame(obs_form, bg=COLORS['bg_card'])
        text_frame.grid(row=1, column=1, sticky='ew', pady=8, padx=(10, 0))
        
        self.obs_text = Text(text_frame, height=8, width=60, font=('Segoe UI', 10),
                            relief='flat', bg=COLORS['light'], fg=COLORS['text'])
        scrollbar_obs = ttk.Scrollbar(text_frame, orient='vertical', command=self.obs_text.yview)
        self.obs_text.configure(yscrollcommand=scrollbar_obs.set)
        
        self.obs_text.pack(side='left', fill='both', expand=True)
        scrollbar_obs.pack(side='right', fill='y')
        
        # Buttons
        btn_frame = tk.Frame(obs_form, bg=COLORS['bg_card'])
        btn_frame.grid(row=2, column=1, sticky='ew', pady=15, padx=(10, 0))
        
        upload_btn = ttk.Button(btn_frame, text="📁 Upload File", 
                               style='Warning.TButton',
                               command=self.upload_file)
        upload_btn.pack(side='left', padx=(0, 10))
        
        save_btn = ttk.Button(btn_frame, text="💾 Save Observation", 
                             style='Success.TButton',
                             command=self.save_observation)
        save_btn.pack(side='right')
        
        obs_form.grid_columnconfigure(1, weight=1)
        
        return tab
    
    def create_query_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Query Input Card
        query_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        query_card.pack(fill='x', pady=(0, 20))
        
        query_title = tk.Label(query_card, text="🔍 Database Research Query (SELECT only)",
                              font=('Segoe UI', 14, 'bold'),
                              fg=COLORS['text'], bg=COLORS['bg_card'])
        query_title.pack(pady=(15, 10))
        
        # Query text area
        query_text_frame = tk.Frame(query_card, bg=COLORS['bg_card'])
        query_text_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        self.query_text = Text(query_text_frame, height=6, width=100, font=('Consolas', 10),
                              relief='flat', bg=COLORS['light'], fg=COLORS['text'])
        scrollbar_query = ttk.Scrollbar(query_text_frame, orient='vertical', command=self.query_text.yview)
        self.query_text.configure(yscrollcommand=scrollbar_query.set)
        
        self.query_text.pack(side='left', fill='both', expand=True)
        scrollbar_query.pack(side='right', fill='y')
        
        # Sample query
        sample_query = "SELECT p.first_name, p.last_name, a.date, d.first_name as doctor_name\nFROM patient p\nJOIN appointment a ON p.patient_id = a.patient_id\nJOIN doctor d ON a.doctor_id = d.doctor_id\nORDER BY a.date;"
        self.query_text.insert("1.0", sample_query)
        
        run_btn = ttk.Button(query_card, text="▶️ Execute Query", 
                            style='Modern.TButton',
                            command=self.run_query)
        run_btn.pack(pady=(0, 15))
        
        # Results Card
        results_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        results_card.pack(fill='both', expand=True)
        
        results_title = tk.Label(results_card, text="📊 Query Results",
                                font=('Segoe UI', 14, 'bold'),
                                fg=COLORS['text'], bg=COLORS['bg_card'])
        results_title.pack(pady=(15, 10))
        
        self.query_result_frame = tk.Frame(results_card, bg=COLORS['bg_card'])
        self.query_result_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        return tab
    
    def load_doctors(self):
        try:
            db.cursor.execute("SELECT doctor_id, first_name, last_name FROM doctor ORDER BY first_name, last_name")
            rows = db.cursor.fetchall()
            labels = []
            for r in rows:
                label = f"Dr. {r[1]} {r[2]} (ID: {r[0]})"
                labels.append(label)
                self.doctor_map[label] = r[0]
            self.doctor_combo["values"] = labels
            if labels:
                self.doctor_combo.current(0)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load doctors:\n{e}")
    
    def login_doctor(self):
        label = self.doctor_combo.get()
        if not label:
            messagebox.showerror("Input Error", "Please choose a doctor from the dropdown.")
            return
        self.doctor_id = self.doctor_map.get(label)
        self.load_doctor_appointments()
        messagebox.showinfo("Login Successful", f"✅ Successfully logged in as {label}")
    
    def load_doctor_appointments(self):
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Please select and login as a doctor first.")
            return
        try:
            db.cursor.execute("""
                SELECT a.appointment_id, a.date, p.first_name, p.last_name
                FROM appointment a
                JOIN patient p ON a.patient_id=p.patient_id
                WHERE a.doctor_id=%s
                ORDER BY a.date
            """, (self.doctor_id,))
            rows = db.cursor.fetchall()
            
            self.appt_listbox.delete(0, tk.END)
            appt_labels = []
            self.appointment_map = {}
            
            for r in rows:
                label = f"📅 {r[1]} - {r[2]} {r[3]} (ID: {r[0]})"
                appt_labels.append(label)
                self.appointment_map[label] = r[0]
                self.appt_listbox.insert(tk.END, label)
            
            # Update appointment combobox for observation tab
            self.appt_combo["values"] = appt_labels
            if appt_labels:
                self.appt_combo.current(0)
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load appointments:\n{e}")
    
    def upload_file(self):
        """
        Handle file upload functionality for medical records.
        
        This method allows doctors to upload various types of files including:
        - Medical images (X-rays, scans, photos)
        - Documents (PDFs, Word docs, text files)
        - Data files (CSV, Excel, JSON)
        - Archives and other file types
        
        The uploaded file is copied to a timestamped location and file information
        is automatically populated in the observation form.
        """
        # Check if doctor is logged in
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Please login as a doctor first.")
            return
        
        # Define file type categories for the file dialog
        file_types = [
            ("All Files", "*.*"),                                    # Allow any file type
            ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),  # Common image formats
            ("Documents", "*.pdf *.doc *.docx *.txt *.rtf *.odt"),  # Document formats
            ("Medical Files", "*.dcm *.dicom *.nii *.nii.gz"),      # Medical imaging formats
            ("Data Files", "*.csv *.xlsx *.xls *.json *.xml"),      # Data and spreadsheet formats
            ("Archives", "*.zip *.rar *.7z *.tar *.gz"),            # Compressed files
            ("Videos", "*.mp4 *.avi *.mov *.mkv *.wmv"),            # Video formats
            ("Audio", "*.mp3 *.wav *.flac *.aac *.ogg")             # Audio formats
        ]
        
        # Open file selection dialog
        file_path = filedialog.askopenfilename(
            title="Select File to Upload",
            filetypes=file_types
        )
        
        # If user cancels file selection, return without action
        if not file_path:
            return
        
        try:
            # Extract file information
            basename = os.path.basename(file_path)                    # Get filename only
            file_extension = os.path.splitext(basename)[1].lower()    # Get file extension
            timestamp = int(datetime.datetime.now().timestamp())      # Generate unique timestamp
            
            # Create destination path with timestamp to avoid filename conflicts
            dst = os.path.join(UPLOAD_DIR, f"{timestamp}_{basename}")
            
            # Copy file to upload directory
            shutil.copyfile(file_path, dst)
            
            # Determine file type for display purposes
            file_type = self._get_file_type(file_extension)
            
            # Populate observation form with file information
            self.obs_type_entry.delete(0, tk.END)
            self.obs_type_entry.insert(0, f"File Upload - {file_type}")
            
            # Clear and populate observation text area with file details
            self.obs_text.delete("1.0", tk.END)
            file_info = f"File uploaded: {basename}\n"
            file_info += f"File type: {file_type}\n"
            file_info += f"File size: {self._get_file_size(file_path)}\n"
            file_info += f"File path: {dst}\n"
            file_info += f"Upload time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            file_info += f"Original path: {file_path}"
            
            self.obs_text.insert("1.0", file_info)
            
            # Show success message with file details
            messagebox.showinfo("File Upload Successful", 
                               f"✅ File uploaded successfully!\n\nFile: {basename}\nType: {file_type}\nSize: {self._get_file_size(file_path)}\nSaved to: {dst}")
        except Exception as e:
            # Handle any errors during file upload
            messagebox.showerror("File Error", f"Could not upload file:\n{e}")
    
    def _get_file_type(self, extension):
        """
        Determine human-readable file type based on file extension.
        
        Args:
            extension (str): File extension (e.g., '.pdf', '.jpg')
            
        Returns:
            str: Human-readable file type description
        """
        file_types = {
            # Image file types
            '.png': 'Image (PNG)',
            '.jpg': 'Image (JPEG)',
            '.jpeg': 'Image (JPEG)',
            '.bmp': 'Image (BMP)',
            '.gif': 'Image (GIF)',
            '.tiff': 'Image (TIFF)',
            '.webp': 'Image (WebP)',
            
            # Document file types
            '.pdf': 'Document (PDF)',
            '.doc': 'Document (Word)',
            '.docx': 'Document (Word)',
            '.txt': 'Text File',
            '.rtf': 'Rich Text',
            '.odt': 'OpenDocument Text',
        }
        # Return specific type if found, otherwise generic file type
        return file_types.get(extension, f'File ({extension.upper()})')
    
    def _get_file_size(self, file_path):
        """
        Convert file size to human-readable format.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: Human-readable file size (e.g., "1.5 MB", "256 KB")
        """
        try:
            # Get file size in bytes
            size = os.path.getsize(file_path)
            
            # Convert to appropriate unit
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            
            # For very large files (TB)
            return f"{size:.1f} TB"
        except:
            # Return unknown size if file access fails
            return "Unknown size"
    
    def save_observation(self):
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Please login as a doctor first.")
            return
        appt_label = self.appt_combo.get()
        if not appt_label:
            messagebox.showerror("Input Error", "Please select an appointment to attach this observation to.")
            return
        appt_id = self.appointment_map.get(appt_label)
        obs_type = self.obs_type_entry.get().strip()
        desc = self.obs_text.get("1.0", tk.END).strip()
        
        if not (obs_type and desc):
            messagebox.showerror("Input Error", "Both observation type and description are required.")
            return
        try:
            db.cursor.execute("INSERT INTO observation (type, description, appointment_id) VALUES (%s,%s,%s)",
                             (obs_type, desc, appt_id))
            db.connection.commit()
            messagebox.showinfo("Success", "✅ Medical observation saved successfully!")
            
            # Clear form
            self.obs_type_entry.delete(0, tk.END)
            self.obs_text.delete("1.0", tk.END)
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save observation:\n{e}")
    
    def run_query(self):
        q = self.query_text.get("1.0", tk.END).strip()
        if not q:
            messagebox.showerror("Input Error", "Please enter a SELECT query to execute.")
            return
        try:
            colnames, rows = safe_select(q)
            
            # Clear previous results
            for child in self.query_result_frame.winfo_children():
                child.destroy()
            
            if not colnames:
                tk.Label(self.query_result_frame, text="Query executed but returned no columns.",
                        font=('Segoe UI', 11), fg=COLORS['text'], bg=COLORS['bg_card']).pack(pady=20)
                return
            
            # Create treeview for results
            tree_frame = tk.Frame(self.query_result_frame, bg=COLORS['bg_card'])
            tree_frame.pack(fill='both', expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=colnames, show="headings", height=15)
            
            # Configure column headings and widths
            for c in colnames:
                tree.heading(c, text=c)
                tree.column(c, width=150, anchor="w")
            
            # Insert data
            for r in rows:
                tree.insert("", tk.END, values=r)
            
            # Add scrollbars
            v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            tree.grid(row=0, column=0, sticky='nsew')
            v_scrollbar.grid(row=0, column=1, sticky='ns')
            h_scrollbar.grid(row=1, column=0, sticky='ew')
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Results summary
            summary = tk.Label(self.query_result_frame, 
                              text=f"📊 Query returned {len(rows)} rows with {len(colnames)} columns",
                              font=('Segoe UI', 10), fg=COLORS['success'], bg=COLORS['bg_card'])
            summary.pack(pady=(10, 0))
            
        except Exception as e:
            messagebox.showerror("Query Error", f"Error executing query:\n{e}")

# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================
def main():
    """
    Main entry point for the Clinic Management System application.
    
    This function:
    1. Initializes the database connection and creates tables if needed
    2. Creates and displays the main application window
    3. Sets up proper cleanup when the application is closed
    4. Starts the GUI event loop
    
    The application will show an error dialog if database setup fails,
    allowing users to check their MySQL configuration.
    """
    try:
        # Initialize database - create tables and sample data if needed
        setup_database_if_needed()
    except Exception as e:
        # Show error dialog if database setup fails
        messagebox.showerror("Database Setup Error", 
                           f"Could not prepare database:\n{e}\n\nPlease check:\n• MySQL server is running\n• Credentials are correct in the configuration")
        return
    
    # Create the main application window
    app = ClinicApp()
    
    def on_closing():
        """
        Handle application closing event.
        
        This function is called when the user closes the main window.
        It ensures the database connection is properly closed before
        destroying the application.
        """
        try:
            # Close database connection
            db.disconnect()
        except Exception:
            # Ignore errors during cleanup
            pass
        # Destroy the application window
        app.destroy()
    
    # Set up the close event handler
    app.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI event loop - this blocks until the application is closed
    app.mainloop()

# =============================================================================
# APPLICATION STARTUP
# =============================================================================
if __name__ == "__main__":
    # Only run main() if this script is executed directly (not imported)
    main()