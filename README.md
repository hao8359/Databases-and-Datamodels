# Clinic Database Management System

A comprehensive database management system for clinic operations with both command-line and GUI interfaces.

## Features

### Database Structure
- **Clinics**: Medical clinic information
- **Departments**: Medical departments within clinics
- **Doctors**: Medical staff assigned to departments
- **Patients**: Patient records assigned to doctors
- **Appointments**: Patient appointments with doctors
- **Observations**: Medical observations during appointments
- **Diagnoses**: Medical diagnoses based on observations

### GUI Interface

#### Main Interface
- Two main buttons: **DOCTOR** and **PATIENT**
- Clean, modern interface design

#### Patient Interface (2 tabs)
1. **Book Appointment**
   - Enter patient name
   - Select department from dropdown
   - Choose appointment date (YYYY-MM-DD format)
   - Book appointment with available doctor

2. **View Appointments**
   - Display all appointments with patient, doctor, department, and date information
   - Refresh button to update the view

#### Doctor Interface (3 tabs)
1. **Doctor Login**
   - Enter Doctor ID to login
   - View appointments for the logged-in doctor only
   - Display patient information and appointment dates

2. **Image Upload**
   - Select and upload medical images
   - Support for JPG, PNG, GIF, BMP formats
   - Image preview and file information display

3. **Query Research**
   - Execute custom SQL queries
   - Results displayed in formatted text area
   - Support for SELECT, SHOW, DESCRIBE, and other SQL commands
   - Error handling for invalid queries

## Installation

1. **Prerequisites**
   - Python 3.7+
   - MySQL Server
   - Virtual environment (recommended)

2. **Setup**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Database Configuration**
   - Update database credentials in `main.py` if needed:
     - Host: localhost
     - User: root
     - Password: 28092675
     - Database: clinic_db

## Usage

### Command Line Interface
```bash
python main.py
```
This will create the database, tables, and insert sample data.

### GUI Interface
```bash
python gui_interface.py
```
This will launch the graphical user interface.

## Database Schema

The system uses MySQL with the following relationships:
- Clinic → Department (1:many)
- Department → Doctor (1:many)
- Doctor → Patient (1:many)
- Doctor → Appointment (1:many)
- Patient → Appointment (1:many)
- Appointment → Observation (1:many)
- Observation → Diagnosis (1:many)

## Sample Data

The system includes sample data:
- 2 clinics (Sunshine Health Center, Green Valley Clinic)
- 2 departments (Cardiology, Pediatrics)
- 2 doctors (Dr. Anna Johnson, Dr. Erik Andersson)
- 2 patients (Lars Nilsson, Maria Garcia)
- 4 appointments with various dates
- 7 medical observations and diagnoses

## File Structure

```
lab1/
├── main.py                 # Command-line database interface
├── gui_interface.py        # GUI application
├── setup_database.sql      # SQL setup script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

- **Backend**: Python with MySQL Connector
- **Frontend**: Tkinter for GUI
- **Image Processing**: Pillow (PIL)
- **Database**: MySQL with foreign key constraints
- **Error Handling**: Comprehensive error handling throughout

## Troubleshooting

1. **MySQL Connection Issues**
   - Ensure MySQL server is running
   - Check database credentials in `main.py`
   - Verify MySQL user has proper permissions

2. **GUI Issues**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Image Upload Issues**
   - Supported formats: JPG, PNG, GIF, BMP
   - Check file permissions and path validity
