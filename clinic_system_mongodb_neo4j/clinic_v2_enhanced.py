# -*- coding: utf-8 -*-
"""
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
import re                   # Regular expressions for validation
import datetime             # Date and time handling
import tkinter as tk        # Main GUI framework
from tkinter import ttk, filedialog, messagebox, Text  # GUI components
from clinic_v2_withoutgui import ClinicDatabaseNotebook  # Database operations
from mongodb_messaging import MongoMessagingSystem
messaging = MongoMessagingSystem()
messaging.connect()

# =============================================================================
# CONFIGURATION SETTINGS
# =============================================================================
# Database connection parameters for Neo4j
DB_CONFIG = {
    "host": "bolt://localhost:7687",   # Neo4j Bolt URI
    "user": "neo4j",                   # Neo4j username
    "password": "clinicdatabase",            # Neo4j password
    "database": "neo4j"                # Neo4j database name
}

# File upload configuration - files will be stored directly in database
# No need for local file system storage

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
        # Connect to Neo4j
        if not db.connect():
            created = db.create_database()
            if not created:
                raise RuntimeError("Could not setup Neo4j database/credentials.")
            if not db.connect():
                raise RuntimeError("Failed to connect to Neo4j after setup.")

        # If no departments exist, bootstrap sample data
        departments = db.get_departments()
        if not departments:
            print("No data found – creating constraints and inserting sample graph data...")
            db.create_all_tables()
            db.insert_all_sample_data()
        else:
            print(f"Found departments: {[name for (_id, name) in departments]}")

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
    
    This function executes read-only Cypher queries for Neo4j. For safety, only
    queries starting with MATCH or RETURN (case-insensitive) are allowed.
    
    Args:
        query (str): Cypher query string (read-only)
        params (tuple): Not used (kept for signature compatibility)
        
    Returns:
        tuple: (column_names, rows) - Query results
        
    Raises:
        ValueError: If query is not a read-only Cypher (MATCH/RETURN)
    """
    q = query.strip()
    if not (q.lower().startswith("match") or q.lower().startswith("return")):
        raise ValueError("Only read-only Cypher starting with MATCH/RETURN is allowed.")
    
    # Run Cypher and format results
    records = []
    with db.driver.session(database=db.database) as session:
        for rec in session.run(q):
            records.append(rec)
    colnames = list(records[0].keys()) if records else []
    rows = [tuple(rec.get(k) for k in colnames) for rec in records]
    return colnames, rows

# =============================================================================
# MONGODB USER SYNC HELPERS
# =============================================================================
def ensure_mongo_user_for_doctor(doctor_id: int, first_name: str, last_name: str) -> str:
    """
    Ensure a MongoDB user exists for a given MySQL doctor and return the user ObjectId (string).
    """
    try:
        username = f"doctor.{doctor_id}"
        # Prefer lookup by username to avoid mismatched user_id cases
        existing_by_username = messaging.users.find_one({"username": username})
        if existing_by_username:
            return str(existing_by_username["_id"])
        existing = messaging.users.find_one({"user_id": doctor_id, "user_type": "doctor"})
        if existing:
            return str(existing["_id"])
        # Direct upsert without relying on password hashing (auth not used here)
        result = messaging.users.update_one(
            {"username": username},
            {
                "$setOnInsert": {
                    "password_hash": b"",
                    "user_type": "doctor",
                    "first_name": first_name,
                    "last_name": last_name,
                    "user_id": doctor_id,
                    "created_at": datetime.datetime.now(datetime.timezone.utc),
                    "is_active": True,
                    "profile_image": None
                }
            },
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        # Fallback fetch
        fallback = messaging.users.find_one({"username": username})
        return str(fallback["_id"]) if fallback else None
    except Exception:
        return None

def ensure_mongo_user_for_patient(patient_id: int, first_name: str, last_name: str) -> str:
    """
    Ensure a MongoDB user exists for a given MySQL patient and return the user ObjectId (string).
    """
    try:
        username = f"patient.{patient_id}"
        existing_by_username = messaging.users.find_one({"username": username})
        if existing_by_username:
            return str(existing_by_username["_id"])
        existing = messaging.users.find_one({"user_id": patient_id, "user_type": "patient"})
        if existing:
            return str(existing["_id"])
        result = messaging.users.update_one(
            {"username": username},
            {
                "$setOnInsert": {
                    "password_hash": b"",
                    "user_type": "patient",
                    "first_name": first_name,
                    "last_name": last_name,
                    "user_id": patient_id,
                    "created_at": datetime.datetime.now(datetime.timezone.utc),
                    "is_active": True,
                    "profile_image": None
                }
            },
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        fallback = messaging.users.find_one({"username": username})
        return str(fallback["_id"]) if fallback else None
    except Exception:
        return None

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
                               text="💡 Ensure Neo4j server is running with correct credentials",
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

        # Tab 3: Chat
        tab3 = self.create_chat_tab_patient(notebook)
        notebook.add(tab3, text="💬 Chat")
        
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

    def create_chat_tab_patient(self, parent):
        tab = ttk.Frame(parent)
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)

        card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        card.pack(fill='both', expand=True)

        title = tk.Label(card, text="💬 Patient-Doctor Chat", font=('Segoe UI', 14, 'bold'),
                         fg=COLORS['text'], bg=COLORS['bg_card'])
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg=COLORS['bg_card'])
        form.pack(fill='x', padx=20, pady=(0, 10))

        tk.Label(form, text="First Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=5)
        self.chat_p_fname = ttk.Entry(form, style='Modern.TEntry', font=('Segoe UI', 11), width=18)
        self.chat_p_fname.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 20))

        tk.Label(form, text="Last Name:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=2, sticky='w', pady=5)
        self.chat_p_lname = ttk.Entry(form, style='Modern.TEntry', font=('Segoe UI', 11), width=18)
        self.chat_p_lname.grid(row=0, column=3, sticky='ew', pady=5, padx=(10, 20))

        load_btn = ttk.Button(form, text="👨‍⚕️ Load My Doctors", style='Modern.TButton',
                              command=self.patient_chat_load_doctors)
        load_btn.grid(row=0, column=4, padx=(0, 0))

        tk.Label(form, text="Doctor:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=1, column=0, sticky='w', pady=5)
        self.chat_p_doctor_combo = ttk.Combobox(form, state='readonly', style='Modern.TCombobox',
                                                font=('Segoe UI', 11), width=40)
        self.chat_p_doctor_combo.grid(row=1, column=1, columnspan=3, sticky='ew', pady=5, padx=(10, 20))

        open_btn = ttk.Button(form, text="📂 Open Chat", style='Success.TButton',
                              command=self.patient_chat_open_chat)
        open_btn.grid(row=1, column=4)

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # Messages area
        msg_frame = tk.Frame(card, bg=COLORS['bg_card'])
        msg_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        self.chat_p_text = Text(msg_frame, height=16, width=80, font=('Segoe UI', 10),
                                relief='flat', bg=COLORS['light'], fg=COLORS['text'])
        msg_scroll = ttk.Scrollbar(msg_frame, orient='vertical', command=self.chat_p_text.yview)
        self.chat_p_text.configure(yscrollcommand=msg_scroll.set)
        self.chat_p_text.pack(side='left', fill='both', expand=True)
        msg_scroll.pack(side='right', fill='y')

        # Composer
        composer = tk.Frame(card, bg=COLORS['bg_card'])
        composer.pack(fill='x', padx=20, pady=(0, 15))

        self.chat_p_entry = ttk.Entry(composer, style='Modern.TEntry', font=('Segoe UI', 11))
        self.chat_p_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        img_btn = ttk.Button(composer, text="🖼️ Image", style='Warning.TButton',
                             command=self.patient_chat_send_image)
        img_btn.pack(side='left', padx=(0, 10))

        send_btn = ttk.Button(composer, text="➡️ Send", style='Success.TButton',
                              command=self.patient_chat_send_text)
        send_btn.pack(side='left')

        refresh_btn = ttk.Button(card, text="🔄 Refresh", style='Modern.TButton',
                                 command=self.patient_chat_refresh_messages)
        refresh_btn.pack(pady=(0, 12))

        # State
        self._chat_p_doctor_map = {}
        self._chat_p_patient_mysql_id = None
        self._chat_p_patient_mongo_id = None
        self._chat_p_doctor_mongo_id = None
        self._chat_p_conversation_id = None

        return tab

    def _find_patient_by_name(self, first_name: str, last_name: str):
        return db.get_patient_by_name(first_name, last_name)

    def patient_chat_load_doctors(self):
        fname = self.chat_p_fname.get().strip()
        lname = self.chat_p_lname.get().strip()
        if not (fname and lname):
            messagebox.showerror("Input Error", "Enter your first and last name.")
            return
        try:
            row = self._find_patient_by_name(fname, lname)
            if not row:
                messagebox.showerror("Not Found", "Patient not found.")
                return
            self._chat_p_patient_mysql_id = row[0]
            # ensure mongo patient user
            self._chat_p_patient_mongo_id = ensure_mongo_user_for_patient(row[0], row[1], row[2])
            # load distinct doctors for this patient (via appointments)
            doctors = db.get_doctors_for_patient(row[0])
            labels = []
            self._chat_p_doctor_map = {}
            for d in doctors:
                label = f"Dr. {d[1]} {d[2]} (ID: {d[0]})"
                labels.append(label)
                self._chat_p_doctor_map[label] = d
            self.chat_p_doctor_combo['values'] = labels
            if labels:
                self.chat_p_doctor_combo.current(0)
                messagebox.showinfo("Loaded", f"Loaded {len(labels)} doctor(s) for chat.")
            else:
                messagebox.showinfo("No Doctors", "No assigned doctors via appointments.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load doctors: {e}")

    def patient_chat_open_chat(self):
        selection = self.chat_p_doctor_combo.get()
        if not selection:
            messagebox.showerror("Input Error", "Select a doctor.")
            return
        try:
            d = self._chat_p_doctor_map.get(selection)
            if not d:
                return
            doctor_id, dfn, dln = d[0], d[1], d[2]
            self._chat_p_doctor_mongo_id = ensure_mongo_user_for_doctor(doctor_id, dfn, dln)
            if not (self._chat_p_patient_mongo_id and self._chat_p_doctor_mongo_id):
                messagebox.showerror("Error", "Could not initialize chat users.")
                return
            conv_id = messaging.get_or_create_conversation(self._chat_p_patient_mongo_id, self._chat_p_doctor_mongo_id)
            self._chat_p_conversation_id = conv_id
            self.patient_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open chat: {e}")

    def _render_messages_to_text(self, text_widget: Text, messages: list, self_user_id: str):
        text_widget.config(state='normal')
        text_widget.delete('1.0', tk.END)
        for m in messages:
            ts = m.get('timestamp', '')
            sender = 'You' if m.get('sender_id') == self_user_id else 'Them'
            if m.get('message_type') == 'image':
                filename = m.get('image_filename', 'image')
                size = m.get('image_size', 0)
                text_widget.insert(tk.END, f"[{ts}] {sender}: [Image] {filename} ({size} bytes)\n")
            else:
                text_widget.insert(tk.END, f"[{ts}] {sender}: {m.get('message_text','')}\n")
        text_widget.see(tk.END)
        text_widget.config(state='disabled')

    def patient_chat_refresh_messages(self):
        try:
            if not self._chat_p_conversation_id:
                return
            msgs = messaging.get_conversation_messages(self._chat_p_conversation_id, limit=200)
            self._render_messages_to_text(self.chat_p_text, msgs, self._chat_p_patient_mongo_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load messages: {e}")

    def patient_chat_send_text(self):
        msg = self.chat_p_entry.get().strip()
        if not msg:
            return
        try:
            if not self._chat_p_conversation_id:
                messagebox.showerror("Error", "Open a chat first.")
                return
            messaging.send_message(self._chat_p_patient_mongo_id, self._chat_p_conversation_id, message_text=msg)
            self.chat_p_entry.delete(0, tk.END)
            self.patient_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not send message: {e}")

    def patient_chat_send_image(self):
        try:
            if not self._chat_p_conversation_id:
                messagebox.showerror("Error", "Open a chat first.")
                return
            filetypes = [("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp")]
            file_path = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
            if not file_path:
                return
            with open(file_path, 'rb') as f:
                data = f.read()
            basename = os.path.basename(file_path)
            messaging.send_message(self._chat_p_patient_mongo_id, self._chat_p_conversation_id,
                                   message_text="", image_data=data, image_filename=basename)
            self.patient_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not send image: {e}")
    
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
            rows = db.get_departments()
            names = []
            for dept_id, name in rows:
                self._dept_map[name] = dept_id
                names.append(name)
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
            rows = db.get_doctors_by_department(dept_id)
            names = []
            self._doctor_map = {}
            for doc_id, first_name, last_name in rows:
                label = f"Dr. {first_name} {last_name}"
                self._doctor_map[label] = doc_id
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
            
            # Ensure patient exists
            found = db.get_patient_by_name(fname, lname)
            if found:
                patient_id = found[0]
            else:
                patient_id = db.create_patient(fname, lname, doctor_id)
            # Create appointment
            db.create_appointment(doctor_id, date, patient_id)
            
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
            rows = db.get_appointments_for_patient(fname, lname)
            
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
        
        # Tab 3: File Management
        tab3 = self.create_file_management_tab(notebook)
        notebook.add(tab3, text="📁 File Management")
        
        # Tab 4: Database Queries
        tab4 = self.create_query_tab(notebook)
        notebook.add(tab4, text="🔍 Research Queries")

        # Tab 5: Chat
        tab5 = self.create_chat_tab_doctor(notebook)
        notebook.add(tab5, text="💬 Chat")
        
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

    def create_chat_tab_doctor(self, parent):
        tab = ttk.Frame(parent)
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)

        card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        card.pack(fill='both', expand=True)

        title = tk.Label(card, text="💬 Doctor-Patient Chat", font=('Segoe UI', 14, 'bold'),
                         fg=COLORS['text'], bg=COLORS['bg_card'])
        title.pack(pady=(15, 10))

        form = tk.Frame(card, bg=COLORS['bg_card'])
        form.pack(fill='x', padx=20, pady=(0, 10))

        tk.Label(form, text="Patient:", font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text'], bg=COLORS['bg_card']).grid(row=0, column=0, sticky='w', pady=5)
        self.chat_d_patient_combo = ttk.Combobox(form, state='readonly', style='Modern.TCombobox',
                                                 font=('Segoe UI', 11), width=40)
        self.chat_d_patient_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 20))

        load_pat_btn = ttk.Button(form, text="👥 Load Patients", style='Modern.TButton',
                                  command=self.doctor_chat_load_patients)
        load_pat_btn.grid(row=0, column=2, padx=(0, 0))

        open_btn = ttk.Button(form, text="📂 Open Chat", style='Success.TButton',
                              command=self.doctor_chat_open_chat)
        open_btn.grid(row=0, column=3)

        form.grid_columnconfigure(1, weight=1)

        msg_frame = tk.Frame(card, bg=COLORS['bg_card'])
        msg_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        self.chat_d_text = Text(msg_frame, height=16, width=80, font=('Segoe UI', 10),
                                relief='flat', bg=COLORS['light'], fg=COLORS['text'])
        msg_scroll = ttk.Scrollbar(msg_frame, orient='vertical', command=self.chat_d_text.yview)
        self.chat_d_text.configure(yscrollcommand=msg_scroll.set)
        self.chat_d_text.pack(side='left', fill='both', expand=True)
        msg_scroll.pack(side='right', fill='y')

        composer = tk.Frame(card, bg=COLORS['bg_card'])
        composer.pack(fill='x', padx=20, pady=(0, 15))

        self.chat_d_entry = ttk.Entry(composer, style='Modern.TEntry', font=('Segoe UI', 11))
        self.chat_d_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        img_btn = ttk.Button(composer, text="🖼️ Image", style='Warning.TButton',
                             command=self.doctor_chat_send_image)
        img_btn.pack(side='left', padx=(0, 10))

        send_btn = ttk.Button(composer, text="➡️ Send", style='Success.TButton',
                              command=self.doctor_chat_send_text)
        send_btn.pack(side='left')

        refresh_btn = ttk.Button(card, text="🔄 Refresh", style='Modern.TButton',
                                 command=self.doctor_chat_refresh_messages)
        refresh_btn.pack(pady=(0, 12))

        # State
        self._chat_d_patient_map = {}
        self._chat_d_doctor_mongo_id = None
        self._chat_d_patient_mongo_id = None
        self._chat_d_conversation_id = None

        return tab

    def doctor_chat_load_patients(self):
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Login as a doctor first.")
            return
        try:
            # ensure doctor mongo user
            docs = [d for d in db.get_doctors() if d[0] == self.doctor_id]
            if docs:
                _, dfn, dln = docs[0]
                self._chat_d_doctor_mongo_id = ensure_mongo_user_for_doctor(self.doctor_id, dfn, dln)
            # load distinct patients for this doctor
            pts = db.get_patients_for_doctor(self.doctor_id)
            labels = []
            self._chat_d_patient_map = {}
            for p in pts:
                label = f"{p[1]} {p[2]} (ID: {p[0]})"
                labels.append(label)
                self._chat_d_patient_map[label] = p
            self.chat_d_patient_combo['values'] = labels
            if labels:
                self.chat_d_patient_combo.current(0)
                messagebox.showinfo("Loaded", f"Loaded {len(labels)} patient(s) for chat.")
            else:
                messagebox.showinfo("No Patients", "No patients with appointments.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load patients: {e}")

    def doctor_chat_open_chat(self):
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Login as a doctor first.")
            return
        selection = self.chat_d_patient_combo.get()
        if not selection:
            messagebox.showerror("Input Error", "Select a patient.")
            return
        try:
            p = self._chat_d_patient_map.get(selection)
            if not p:
                return
            patient_id, pfn, pln = p[0], p[1], p[2]
            self._chat_d_patient_mongo_id = ensure_mongo_user_for_patient(patient_id, pfn, pln)
            # ensure doctor mongo user (if not already)
            if not self._chat_d_doctor_mongo_id:
                docs = [d for d in db.get_doctors() if d[0] == self.doctor_id]
                if docs:
                    _, dfn, dln = docs[0]
                    self._chat_d_doctor_mongo_id = ensure_mongo_user_for_doctor(self.doctor_id, dfn, dln)
            if not (self._chat_d_doctor_mongo_id and self._chat_d_patient_mongo_id):
                messagebox.showerror("Error", "Could not initialize chat users.")
                return
            conv_id = messaging.get_or_create_conversation(self._chat_d_doctor_mongo_id, self._chat_d_patient_mongo_id)
            self._chat_d_conversation_id = conv_id
            self.doctor_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open chat: {e}")

    def doctor_chat_refresh_messages(self):
        try:
            if not self._chat_d_conversation_id:
                return
            msgs = messaging.get_conversation_messages(self._chat_d_conversation_id, limit=200)
            self._render_messages_to_text(self.chat_d_text, msgs, self._chat_d_doctor_mongo_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load messages: {e}")

    def _render_messages_to_text(self, text_widget: Text, messages: list, self_user_id: str):
        text_widget.config(state='normal')
        text_widget.delete('1.0', tk.END)
        for m in messages:
            ts = m.get('timestamp', '')
            sender = 'You' if m.get('sender_id') == self_user_id else 'Them'
            if m.get('message_type') == 'image':
                filename = m.get('image_filename', 'image')
                size = m.get('image_size', 0)
                text_widget.insert(tk.END, f"[{ts}] {sender}: [Image] {filename} ({size} bytes)\n")
            else:
                text_widget.insert(tk.END, f"[{ts}] {sender}: {m.get('message_text','')}\n")
        text_widget.see(tk.END)
        text_widget.config(state='disabled')

    def doctor_chat_send_text(self):
        msg = self.chat_d_entry.get().strip()
        if not msg:
            return
        try:
            if not self._chat_d_conversation_id:
                messagebox.showerror("Error", "Open a chat first.")
                return
            messaging.send_message(self._chat_d_doctor_mongo_id, self._chat_d_conversation_id, message_text=msg)
            self.chat_d_entry.delete(0, tk.END)
            self.doctor_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not send message: {e}")

    def doctor_chat_send_image(self):
        try:
            if not self._chat_d_conversation_id:
                messagebox.showerror("Error", "Open a chat first.")
                return
            filetypes = [("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp")]
            file_path = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
            if not file_path:
                return
            with open(file_path, 'rb') as f:
                data = f.read()
            basename = os.path.basename(file_path)
            messaging.send_message(self._chat_d_doctor_mongo_id, self._chat_d_conversation_id,
                                   message_text="", image_data=data, image_filename=basename)
            self.doctor_chat_refresh_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Could not send image: {e}")
    
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
    
    def create_file_management_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # File List Card
        file_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        file_card.pack(fill='both', expand=True)
        
        file_title = tk.Label(file_card, text="📁 Uploaded Files Management",
                             font=('Segoe UI', 14, 'bold'),
                             fg=COLORS['text'], bg=COLORS['bg_card'])
        file_title.pack(pady=(15, 10))
        
        # File list with scrollbar
        list_frame = tk.Frame(file_card, bg=COLORS['bg_card'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Create treeview for file list
        columns = ('ID', 'Filename', 'Type', 'Size', 'Upload Date', 'Observation ID')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Configure column headings and widths
        for col in columns:
            self.file_tree.heading(col, text=col)
            if col == 'ID':
                self.file_tree.column(col, width=50, anchor='center')
            elif col == 'Filename':
                self.file_tree.column(col, width=200, anchor='w')
            elif col == 'Type':
                self.file_tree.column(col, width=100, anchor='w')
            elif col == 'Size':
                self.file_tree.column(col, width=80, anchor='e')
            elif col == 'Upload Date':
                self.file_tree.column(col, width=120, anchor='w')
            elif col == 'Observation ID':
                self.file_tree.column(col, width=100, anchor='center')
        
        # Add scrollbars
        v_scrollbar_files = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        h_scrollbar_files = ttk.Scrollbar(list_frame, orient='horizontal', command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar_files.set, xscrollcommand=h_scrollbar_files.set)
        
        self.file_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar_files.grid(row=0, column=1, sticky='ns')
        h_scrollbar_files.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Button frame
        btn_frame = tk.Frame(file_card, bg=COLORS['bg_card'])
        btn_frame.pack(pady=(0, 15))
        
        refresh_files_btn = ttk.Button(btn_frame, text="🔄 Refresh Files", 
                                     style='Modern.TButton',
                                     command=self.load_uploaded_files)
        refresh_files_btn.pack(side='left', padx=(0, 10))
        
        download_btn = ttk.Button(btn_frame, text="⬇️ Download Selected", 
                                style='Success.TButton',
                                command=self.download_selected_file)
        download_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = ttk.Button(btn_frame, text="🗑️ Delete Selected", 
                              style='Warning.TButton',
                              command=self.delete_selected_file)
        delete_btn.pack(side='left')
        
        return tab
    
    def create_query_tab(self, parent):
        tab = ttk.Frame(parent)
        
        container = tk.Frame(tab, bg=COLORS['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Query Input Card
        query_card = tk.Frame(container, bg=COLORS['bg_card'], relief='solid', bd=1)
        query_card.pack(fill='x', pady=(0, 20))
        
        query_title = tk.Label(query_card, text="🔍 Database Research Query (Cypher MATCH/RETURN only)",
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
        sample_query = (
            "MATCH (p:Patient)-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(d:Doctor)\n"
            "RETURN p.first_name AS patient_first_name, p.last_name AS patient_last_name, a.date AS date, d.first_name AS doctor_first_name\n"
            "ORDER BY date"
        )
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
            rows = db.get_doctors()
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
        # Ensure Mongo user for this doctor
        try:
            docs = [d for d in db.get_doctors() if d[0] == self.doctor_id]
            if docs:
                _, dfn, dln = docs[0]
                self._chat_d_doctor_mongo_id = ensure_mongo_user_for_doctor(self.doctor_id, dfn, dln)
        except Exception:
            pass
        self.load_doctor_appointments()
        # Auto-load patients for chat after login
        try:
            self.doctor_chat_load_patients()
        except Exception:
            pass
        messagebox.showinfo("Login Successful", f"✅ Successfully logged in as {label}")
    
    def load_doctor_appointments(self):
        if not self.doctor_id:
            messagebox.showerror("Authentication Required", "Please select and login as a doctor first.")
            return
        try:
            rows = db.get_appointments_for_doctor(self.doctor_id)
            
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
        
        The uploaded file is stored directly in the database and file information
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
            
            # Store file directly in database
            file_id = db.store_file(file_path)
            
            if file_id:
                # Store file_id for later use when saving observation
                self.uploaded_file_id = file_id
                
                # Determine file type for display purposes
                file_type = self._get_file_type(file_extension)
                
                # Populate observation form with file information
                self.obs_type_entry.delete(0, tk.END)
                self.obs_type_entry.insert(0, f"File Upload - {file_type}")
                
                # Clear and populate observation text area with file details
                self.obs_text.delete("1.0", tk.END)
                file_info = f"File uploaded to database: {basename}\n"
                file_info += f"File ID: {file_id}\n"
                file_info += f"File type: {file_type}\n"
                file_info += f"File size: {self._get_file_size(file_path)}\n"
                file_info += f"Upload time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                file_info += f"Original path: {file_path}\n"
                file_info += f"Status: Stored in database (no local copy)"
                
                self.obs_text.insert("1.0", file_info)
                
                # Show success message with file details
                messagebox.showinfo("File Upload Successful", 
                                   f"✅ File uploaded to database successfully!\n\nFile: {basename}\nFile ID: {file_id}\nType: {file_type}\nSize: {self._get_file_size(file_path)}\nStatus: Stored in database")
            else:
                messagebox.showerror("Upload Error", "Failed to store file in database.")
                
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
            # Insert observation record
            observation_id = db.create_observation(appt_id, obs_type, desc)
            # If there's an uploaded file, associate it with this observation
            if hasattr(self, 'uploaded_file_id') and self.uploaded_file_id:
                db.link_file_to_observation(self.uploaded_file_id, observation_id)
                messagebox.showinfo("Success", f"✅ Medical observation and file saved successfully!\n\nObservation ID: {observation_id}\nFile ID: {self.uploaded_file_id}")
            else:
                messagebox.showinfo("Success", f"✅ Medical observation saved successfully!\n\nObservation ID: {observation_id}")
            
            # Clear form
            self.obs_type_entry.delete(0, tk.END)
            self.obs_text.delete("1.0", tk.END)
            if hasattr(self, 'uploaded_file_id'):
                delattr(self, 'uploaded_file_id')
            
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
    
    def load_uploaded_files(self):
        """Load and display all uploaded files in the file management tab."""
        try:
            # Clear existing items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            files = db.list_files()
            
            for file_data in files:
                file_id, filename, file_type, file_size, upload_date, observation_id = file_data
                size_str = self._format_file_size(file_size)
                date_str = upload_date if upload_date else 'Unknown'
                self.file_tree.insert('', 'end', values=(
                    file_id,
                    filename,
                    file_type,
                    size_str,
                    date_str,
                    observation_id if observation_id else 'Not linked'
                ))
            
            messagebox.showinfo("Files Loaded", f"Loaded {len(files)} files from database.")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load files:\n{e}")
    
    def download_selected_file(self):
        """Download the selected file from database to local disk."""
        try:
            # Get selected item
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showerror("Selection Error", "Please select a file to download.")
                return
            
            # Get file ID from selected item
            item_values = self.file_tree.item(selected_item[0])['values']
            file_id = item_values[0]
            filename = item_values[1]
            
            # Ask user where to save the file
            file_path = filedialog.asksaveasfilename(
                title="Save File As",
                initialvalue=filename,
                defaultextension=os.path.splitext(filename)[1]
            )
            
            if not file_path:
                return
            
            # Download file from database
            if db.save_file_to_disk(file_id, file_path):
                messagebox.showinfo("Download Successful", f"File saved to:\n{file_path}")
            else:
                messagebox.showerror("Download Error", "Failed to download file from database.")
                
        except Exception as e:
            messagebox.showerror("Download Error", f"Error downloading file:\n{e}")
    
    def delete_selected_file(self):
        """Delete the selected file from database."""
        try:
            # Get selected item
            selected_item = self.file_tree.selection()
            if not selected_item:
                messagebox.showerror("Selection Error", "Please select a file to delete.")
                return
            
            # Get file information
            item_values = self.file_tree.item(selected_item[0])['values']
            file_id = item_values[0]
            filename = item_values[1]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete this file?\n\nFile: {filename}\nID: {file_id}\n\nThis action cannot be undone."):
                
                # Delete file from database
                if db.delete_file(file_id):
                    messagebox.showinfo("Delete Successful", f"File '{filename}' deleted successfully.")
                    # Refresh the file list
                    self.load_uploaded_files()
                else:
                    messagebox.showerror("Delete Error", "Failed to delete file from database.")
                    
        except Exception as e:
            messagebox.showerror("Delete Error", f"Error deleting file:\n{e}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format."""
        try:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except:
            return "Unknown"

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