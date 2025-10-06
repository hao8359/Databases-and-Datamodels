#!/usr/bin/env python3
"""
Clinic Database Management System - Core Database Operations
===========================================================

This module provides the core database functionality for the clinic management system.
It implements all database operations without GUI components, making it suitable for:
- Command-line usage
- API backend services
- GUI application integration
- Automated testing

The module is based on Jupyter Notebook implementation and provides:
- Database connection management
- Table creation and management
- Sample data insertion
- Query execution and data retrieval
- Comprehensive error handling

Author: Clinic Management System Team
Version: 2.0
"""

# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
import mysql.connector          # MySQL database connector
from mysql.connector import Error  # MySQL error handling
import sys                      # System-specific parameters and functions
from typing import Optional, List, Tuple  # Type hints for better code documentation


# =============================================================================
# MAIN DATABASE CLASS
# =============================================================================
class ClinicDatabaseNotebook:
    """
    Core database management class for the clinic management system.
    
    This class provides all database operations including:
    - Connection management (connect, disconnect)
    - Database creation and management
    - Table creation with proper foreign key relationships
    - Sample data insertion for testing
    - Query execution and data retrieval
    - Error handling and logging
    
    The class is designed to be used both standalone and as a backend
    for GUI applications.
    """
    
    def __init__(self, host: str = "localhost", user: str = "root", 
                 password: str = "root", database: str = "clinic_db"):
        """
        Initialize database connection parameters.
        
        Args:
            host (str): MySQL server hostname (default: "localhost")
            user (str): MySQL username (default: "root")
            password (str): MySQL password (default: "root")
            database (str): Database name (default: "clinic_db")
        """
        self.host = host              # MySQL server address
        self.user = user              # Database username
        self.password = password      # Database password
        self.database = database      # Target database name
        self.connection = None        # MySQL connection object
        self.cursor = None           # Database cursor for queries
    
    # =============================================================================
    # CONNECTION MANAGEMENT METHODS
    # =============================================================================
    def connect(self) -> bool:
        """
        Establish connection to the specified MySQL database.
        
        This method creates a connection to the MySQL server using the configured
        parameters and initializes a cursor for executing queries.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create MySQL connection with specified parameters
            self.connection = mysql.connector.connect(
                host=self.host,           # Server address
                user=self.user,           # Username
                password=self.password,   # Password
                database=self.database    # Target database
            )
            # Create cursor for executing queries
            self.cursor = self.connection.cursor()
            print(f"Successfully connected to MySQL database: {self.database}")
            return True
        except Error as e:
            # Handle connection errors gracefully
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def connect_without_database(self) -> bool:
        """
        Connect to MySQL server without specifying a database.
        
        This method is used when we need to create a new database or
        perform operations that don't require a specific database context.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Connect to MySQL server without specifying database
            self.connection = mysql.connector.connect(
                host=self.host,           # Server address
                user=self.user,           # Username
                password=self.password    # Password (no database specified)
            )
            # Create cursor for executing queries
            self.cursor = self.connection.cursor()
            print(f"Successfully connected to MySQL server")
            return True
        except Error as e:
            # Handle connection errors
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self):
        """
        Close database connection and clean up resources.
        
        This method properly closes the cursor and connection objects
        to free up database resources and prevent connection leaks.
        """
        # Close cursor if it exists
        if self.cursor:
            self.cursor.close()
        
        # Close connection if it exists and is still active
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")
    
    # =============================================================================
    # DATABASE MANAGEMENT METHODS
    # =============================================================================
    def create_database(self) -> bool:
        """
        Create the clinic database if it doesn't exist.
        
        This method connects to the MySQL server without specifying a database,
        then creates the target database using CREATE DATABASE IF NOT EXISTS.
        
        Returns:
            bool: True if database created successfully, False otherwise
        """
        try:
            # Connect to MySQL server without specifying database
            if not self.connect_without_database():
                return False
            
            # Create database using IF NOT EXISTS to avoid errors
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"Database '{self.database}' created successfully or already exists.")
            
            # Disconnect after creating database
            self.disconnect()
            return True
        except Error as e:
            # Handle database creation errors
            print(f"Error creating database: {e}")
            return False
    
    def show_databases(self):
        """Show all databases."""
        try:
            if not self.connect_without_database():
                return
            
            self.cursor.execute("SHOW DATABASES")
            databases = self.cursor.fetchall()
            
            print("Available databases:")
            for db in databases:
                print(db[0])
            
            self.disconnect()
        except Error as e:
            print(f"Error showing databases: {e}")
    
    def drop_tables_in_order(self):
        """Drop all tables in the correct order to handle foreign key constraints."""
        tables_to_drop = [
            'medical_files', 'diagnosis', 'observation', 'appointment', 
            'patient', 'doctor', 'department', 'clinic'
        ]
        
        for table in tables_to_drop:
            try:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"Dropped table {table} if it existed.")
            except Error as e:
                print(f"Error dropping table {table}: {e}")
    
    # =============================================================================
    # TABLE CREATION METHODS
    # =============================================================================
    def create_clinic_table(self):
        """
        Create the clinic table with basic clinic information.
        
        This table stores information about different clinics in the system.
        It serves as the parent table for departments.
        
        Table structure:
        - clinic_id: Primary key (auto-increment)
        - name: Clinic name (required)
        - address: Clinic address (required)
        - phone: Contact phone number (required)
        - email: Contact email (optional)
        """
        try:
            # Drop existing table to ensure clean creation
            self.cursor.execute("DROP TABLE IF EXISTS clinic")
            
            # Create clinic table with proper structure
            self.cursor.execute("""
                CREATE TABLE clinic (
                    clinic_id INT AUTO_INCREMENT PRIMARY KEY,    -- Primary key
                    name VARCHAR(255) NOT NULL,                  -- Clinic name
                    address VARCHAR(255) NOT NULL,               -- Physical address
                    phone VARCHAR(30) NOT NULL,                  -- Contact phone
                    email VARCHAR(100)                           -- Contact email (optional)
                )
            """)
            print("Created 'clinic' table.")
        except Error as e:
            print(f"Error creating clinic table: {e}")
    
    def create_department_table(self):
        """
        Create the department table with foreign key relationship to clinic.
        
        This table stores information about different medical departments
        within each clinic (e.g., Cardiology, Pediatrics, etc.).
        
        Table structure:
        - department_id: Primary key (auto-increment)
        - name: Department name (required)
        - clinic_id: Foreign key to clinic table (required)
        
        Foreign key constraints:
        - References clinic(clinic_id)
        - CASCADE DELETE: If clinic is deleted, departments are deleted
        - CASCADE UPDATE: If clinic_id changes, department references update
        """
        try:
            # Drop existing table to ensure clean creation
            self.cursor.execute("DROP TABLE IF EXISTS department")
            
            # Create department table with foreign key constraint
            self.cursor.execute("""
                CREATE TABLE department (
                    department_id INT AUTO_INCREMENT PRIMARY KEY,    -- Primary key
                    name VARCHAR(255) NOT NULL,                      -- Department name
                    clinic_id INT,                                   -- Foreign key to clinic
                    CONSTRAINT fk_clinic
                        FOREIGN KEY (clinic_id) 
                        REFERENCES clinic(clinic_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE          -- Cascade operations
                )
            """)
            print("Created 'department' table.")
        except Error as e:
            print(f"Error creating department table: {e}")
    
    def create_doctor_table(self):
        """Create the doctor table."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS doctor")
            self.cursor.execute("""
                CREATE TABLE doctor (
                    doctor_id INT AUTO_INCREMENT PRIMARY KEY, 
                    first_name VARCHAR(255) NOT NULL, 
                    last_name VARCHAR(255) NOT NULL, 
                    department_id INT, 
                    CONSTRAINT fk_department
                        FOREIGN KEY (department_id) 
                        REFERENCES department(department_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'doctor' table.")
        except Error as e:
            print(f"Error creating doctor table: {e}")
    
    def create_patient_table(self):
        """Create the patient table."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS patient")
            self.cursor.execute("""
                CREATE TABLE patient (
                    patient_id INT AUTO_INCREMENT PRIMARY KEY, 
                    first_name VARCHAR(255) NOT NULL, 
                    last_name VARCHAR(255) NOT NULL, 
                    doctor_id INT, 
                    CONSTRAINT fk_doctor_patient
                        FOREIGN KEY (doctor_id) 
                        REFERENCES doctor(doctor_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'patient' table.")
        except Error as e:
            print(f"Error creating patient table: {e}")
    
    def create_appointment_table(self):
        """Create the appointment table."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS appointment")
            self.cursor.execute("""
                CREATE TABLE appointment (
                    appointment_id INT AUTO_INCREMENT PRIMARY KEY, 
                    doctor_id INT, 
                    date DATE, 
                    patient_id INT, 
                    CONSTRAINT fk_patient
                        FOREIGN KEY (patient_id) 
                        REFERENCES patient(patient_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE, 
                    CONSTRAINT fk_doctor
                        FOREIGN KEY (doctor_id) 
                        REFERENCES doctor(doctor_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'appointment' table.")
        except Error as e:
            print(f"Error creating appointment table: {e}")
    
    def create_observation_table(self):
        """Create the observation table."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS observation")
            self.cursor.execute("""
                CREATE TABLE observation (
                    observation_id INT AUTO_INCREMENT PRIMARY KEY, 
                    type VARCHAR(255), 
                    description TEXT, 
                    appointment_id INT, 
                    CONSTRAINT fk_appointment
                        FOREIGN KEY (appointment_id) 
                        REFERENCES appointment(appointment_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'observation' table.")
        except Error as e:
            print(f"Error creating observation table: {e}")
    
    def create_diagnosis_table(self):
        """Create the diagnosis table."""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS diagnosis")
            self.cursor.execute("""
                CREATE TABLE diagnosis (
                    diagnosis_id INT AUTO_INCREMENT PRIMARY KEY, 
                    description TEXT, 
                    observation_id INT, 
                    CONSTRAINT fk_observation
                        FOREIGN KEY (observation_id) 
                        REFERENCES observation(observation_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'diagnosis' table.")
        except Error as e:
            print(f"Error creating diagnosis table: {e}")
    
    def create_medical_files_table(self):
        """
        Create the medical_files table for storing uploaded files and images.
        
        This table stores binary file data directly in the database along with
        metadata about the files. This approach provides better data integrity
        and eliminates the need for separate file system storage.
        
        Table structure:
        - file_id: Primary key (auto-increment)
        - filename: Original filename (required)
        - file_type: MIME type or file extension (required)
        - file_size: File size in bytes (required)
        - file_data: Binary file content (LONGBLOB)
        - upload_date: When the file was uploaded (required)
        - observation_id: Foreign key to observation table (optional)
        - description: Optional description of the file
        """
        try:
            self.cursor.execute("DROP TABLE IF EXISTS medical_files")
            self.cursor.execute("""
                CREATE TABLE medical_files (
                    file_id INT AUTO_INCREMENT PRIMARY KEY,           -- Primary key
                    filename VARCHAR(255) NOT NULL,                   -- Original filename
                    file_type VARCHAR(100) NOT NULL,                  -- MIME type or extension
                    file_size BIGINT NOT NULL,                        -- File size in bytes
                    file_data LONGBLOB NOT NULL,                      -- Binary file content
                    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Upload timestamp
                    observation_id INT,                               -- Foreign key to observation
                    description TEXT,                                 -- Optional description
                    CONSTRAINT fk_observation_file
                        FOREIGN KEY (observation_id) 
                        REFERENCES observation(observation_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            print("Created 'medical_files' table.")
        except Error as e:
            print(f"Error creating medical_files table: {e}")
    
    def create_all_tables(self):
        """Create all tables in the correct order."""
        print("Creating all tables...")
        self.create_clinic_table()
        self.create_department_table()
        self.create_doctor_table()
        self.create_patient_table()
        self.create_appointment_table()
        self.create_observation_table()
        self.create_diagnosis_table()
        self.create_medical_files_table()
    
    def show_tables(self):
        """Show all tables in the database."""
        try:
            self.cursor.execute("SHOW TABLES")
            tables = self.cursor.fetchall()
            
            print("Tables in database:")
            for table in tables:
                print(table[0])
        except Error as e:
            print(f"Error showing tables: {e}")
    
    def describe_table(self, table_name: str):
        """Describe the structure of a table."""
        try:
            self.cursor.execute(f"DESCRIBE {table_name}")
            columns = self.cursor.fetchall()
            
            print(f"Structure of {table_name} table:")
            for col in columns:
                print(col)
        except Error as e:
            print(f"Error describing table {table_name}: {e}")
    
    def show_create_table(self, table_name: str):
        """Show the CREATE TABLE statement for a table."""
        try:
            self.cursor.execute(f"SHOW CREATE TABLE {table_name}")
            result = self.cursor.fetchone()
            
            if result:
                print(f"CREATE TABLE statement for {table_name}:")
                print(result[1])
        except Error as e:
            print(f"Error showing CREATE TABLE for {table_name}: {e}")
    
    # =============================================================================
    # SAMPLE DATA INSERTION METHODS
    # =============================================================================
    def insert_clinic_data(self):
        """
        Insert sample clinic data for testing and demonstration.
        
        This method inserts two sample clinics with complete information
        including contact details. The data is used for testing the
        application functionality.
        
        Sample data includes:
        - Sunshine Health Center: Main clinic with contact information
        - Green Valley Clinic: Secondary clinic with different contact details
        """
        try:
            # Insert sample clinic records
            self.cursor.execute("""
                INSERT INTO clinic (name, address, phone, email) VALUES
                ('Sunshine Health Center', '123 Wellness Ave', '+46701234567', 'contact@sunshine.com'),
                ('Green Valley Clinic', '456 Nature Rd', '+46707654321', 'info@greenvalley.com')
            """)
            # Commit the transaction to save changes
            self.connection.commit()
            print("Inserted clinic data.")
        except Error as e:
            print(f"Error inserting clinic data: {e}")
    
    def insert_department_data(self):
        """Insert sample department data."""
        try:
            self.cursor.execute("""
                INSERT INTO department (name, clinic_id) VALUES
                ('Cardiology', 1),
                ('Pediatrics', 1), ('Emergency',1), 
                ('Internal medicine',1),('Surgery',1),('Obstetrics & Gynecology',1), 
                ('Orthopedics',1), ('Neurology',1),('Oncology',1), 
                ('ENT', 1),('Psychiatry',1), ('Radiology',1), 
                ('Ophtalmology',1), ('Laboratory',1),('Dermatology',1), 
                ('Dermatology',1),('Rehabilitation',1), ('Nutrition',1), 
                ('Medical records',1),('Biomedical Engineering',1), 
                ('Nephrology',1), ('Gastroenterology',1), ('Pulmonology',1), 
                ('Urology',1), ('Plastic Surgery',1)

            """)
            self.connection.commit()
            print("Inserted department data.")
        except Error as e:
            print(f"Error inserting department data: {e}")
    
    def insert_doctor_data(self):
        try:
            self.cursor.execute("""
                INSERT INTO doctor (first_name, last_name, department_id) VALUES
                ('Anna', 'Johnson', 1),
                ('Michael', 'Chen', 1),
                ('Reine', 'Bergström', 1),
                ('Erik', 'Andersson', 2),
                ('Sarah', 'Williams', 2),
                ('James', 'Brown', 3),
                ('Lisa', 'Garcia', 3),
                ('Robert', 'Davis', 4),
                ('Maria', 'Rodriguez', 4),
                ('David', 'Miller', 5),
                ('Jennifer', 'Wilson', 5),
                ('Christopher', 'Moore', 6),
                ('Amanda', 'Taylor', 6),
                ('Daniel', 'Anderson', 7),
                ('Jessica', 'Thomas', 7),
                ('Datthew', 'Jackson', 8),
                ('Ashley', 'White', 8),
                ('Andrew', 'Harris', 9),
                ('Samantha', 'Martin', 9),
                ('Joshua', 'Thompson', 10),
                ('Nicole', 'Garcia', 10),
                ('Kevin', 'Martinez', 11),
                ('Rachel', 'Robinson', 11),
                ('Brian', 'Clark', 12),
                ('Lauren', 'Rodriguez', 12),
                ('Ryan', 'Lewis', 13),
                ('Megan', 'Lee', 13),
                ('Tyler', 'Walker', 14),
                ('Stephanie', 'Hall', 14),
                ('Nathan', 'Allen', 15),
                ('Danielle', 'Young', 15),
                ('Justin', 'King', 16),
                ('Michelle', 'Wright', 16),
                ('Brandon', 'Scott', 17),
                ('Kimberly', 'Torres', 17),
                ('Jacob', 'Nguyen', 18),
                ('Angela', 'Hill', 18),
                ('Zachary', 'Flores', 19),
                ('Heather', 'Green', 19),
                ('Aaron', 'Adams', 20),
                ('Rebecca', 'Nelson', 20),
                ('Kyle', 'Baker', 21),
                ('Victoria', 'Carter', 21),
                ('Ethan', 'Mitchell', 22),
                ('Christina', 'Perez', 22),
                ('Noah', 'Roberts', 23),
                ('Kelly', 'Turner', 23),
                ('Logan', 'Phillips', 24),
                ('Amy', 'Campbell', 24)
            """)
            self.connection.commit()
            print("Inserted doctor data for all departments (2 doctors per department).")
        except Error as e:
            print(f"Error inserting doctor data: {e}")
    
    def insert_patient_data(self):
        """Insert sample patient data."""
        try:
            # Clear existing data first
            self.cursor.execute("DELETE FROM patient")
            
            self.cursor.execute("""
                INSERT INTO patient (first_name, last_name, doctor_id) VALUES
                ('Lars', 'Nilsson', 1),
                ('Maria', 'Garcia', 1)
            """)
            self.connection.commit()
            print("Inserted patient data.")
        except Error as e:
            print(f"Error inserting patient data: {e}")
    
    def insert_appointment_data(self):
        """Insert sample appointment data."""
        try:
            self.cursor.execute("""
                INSERT INTO appointment (doctor_id, date, patient_id) VALUES
                (1, '2024-01-15', 1),
                (2, '2024-01-16', 2),
                (1, '2024-01-17', 1),
                (2, '2024-01-18', 2)
            """)
            self.connection.commit()
            print("Inserted appointment data.")
        except Error as e:
            print(f"Error inserting appointment data: {e}")
    
    def insert_observation_data(self):
        """Insert sample observation data."""
        try:
            self.cursor.execute("""
                INSERT INTO observation (type, description, appointment_id) VALUES
                ('Physical Examination', 'Patient shows signs of elevated blood pressure and irregular heartbeat', 1),
                ('Blood Test', 'Complete blood count shows elevated white blood cell count', 1),
                ('Physical Examination', 'Child shows normal growth patterns and healthy vital signs', 2),
                ('X-Ray', 'Chest X-ray reveals clear lungs with no abnormalities', 2),
                ('Physical Examination', 'Follow-up examination shows improved blood pressure readings', 3),
                ('Blood Test', 'Follow-up blood work shows normal white blood cell count', 3),
                ('Physical Examination', 'Routine check-up shows excellent health status', 4)
            """)
            self.connection.commit()
            print("Inserted observation data.")
        except Error as e:
            print(f"Error inserting observation data: {e}")
    
    def insert_diagnosis_data(self):
        """Insert sample diagnosis data."""
        try:
            self.cursor.execute("""
                INSERT INTO diagnosis (description, observation_id) VALUES
                ('Hypertension - Stage 1', 1),
                ('Possible infection - requires further monitoring', 2),
                ('Healthy child - no medical concerns', 3),
                ('Normal chest examination', 4),
                ('Blood pressure under control with medication', 5),
                ('Infection resolved - normal blood work', 6),
                ('Excellent health - no medical issues', 7)
            """)
            self.connection.commit()
            print("Inserted diagnosis data.")
        except Error as e:
            print(f"Error inserting diagnosis data: {e}")
    
    def insert_all_sample_data(self):
        """Insert all sample data."""
        print("Inserting all sample data...")
        self.insert_clinic_data()
        self.insert_department_data()
        self.insert_doctor_data()
        self.insert_patient_data()
        self.insert_appointment_data()
        self.insert_observation_data()
        self.insert_diagnosis_data()
        print("All sample data inserted successfully!")
    
    def display_table_data(self, table_name: str):
        """Display all data from a specific table."""
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            results = self.cursor.fetchall()
            
            print(f"\nData from {table_name} table:")
            for row in results:
                print(row)
        except Error as e:
            print(f"Error displaying data from {table_name}: {e}")
    
    # =============================================================================
    # FILE STORAGE METHODS
    # =============================================================================
    def store_file(self, file_path: str, observation_id: int = None, description: str = None) -> int:
        """
        Store a file directly in the database as binary data.
        
        This method reads a file from the local filesystem and stores its binary content
        directly in the MySQL database using LONGBLOB data type. This approach provides
        better data integrity and eliminates the need for separate file system storage.
        
        The file is stored in the 'medical_files' table with the following information:
        - Original filename and file extension
        - MIME type (automatically detected)
        - File size in bytes
        - Binary file content (LONGBLOB)
        - Optional association with a medical observation
        - Optional description text
        
        Args:
            file_path (str): Full path to the file to store (e.g., "C:/images/xray.jpg")
            observation_id (int, optional): ID of the observation to attach the file to.
                                          If provided, the file will be linked to this
                                          medical observation record.
            description (str, optional): Human-readable description of the file content.
                                       Useful for medical staff to understand what the
                                       file contains (e.g., "Chest X-ray - Front view")
            
        Returns:
            int: The file_id of the newly created file record in the database.
                 Returns None if the operation failed.
                 
        Raises:
            Error: MySQL database errors (connection issues, SQL errors, etc.)
            Exception: File system errors (file not found, permission denied, etc.)
            
        Example:
            # Store a medical image file
            file_id = db.store_file(
                file_path="/path/to/xray.jpg",
                observation_id=123,
                description="Chest X-ray showing pneumonia"
            )
            if file_id:
                print(f"File stored with ID: {file_id}")
        """
        try:
            # Import required modules for file operations
            import os          # For file path operations
            import mimetypes   # For automatic MIME type detection
            
            # ===== STEP 1: READ FILE BINARY DATA =====
            # Open file in binary read mode ('rb') to handle all file types
            # including images, documents, videos, etc.
            with open(file_path, 'rb') as file:
                file_data = file.read()  # Read entire file content as bytes
            
            # ===== STEP 2: EXTRACT FILE METADATA =====
            # Get the original filename without the full path
            # e.g., "/home/user/images/xray.jpg" -> "xray.jpg"
            filename = os.path.basename(file_path)
            
            # Calculate file size in bytes
            # This is used for storage planning and user information
            file_size = len(file_data)
            
            # Detect MIME type automatically (e.g., "image/jpeg", "application/pdf")
            # This helps identify file type for proper handling and display
            file_type, _ = mimetypes.guess_type(file_path)
            
            # If MIME type detection fails, use file extension as fallback
            # e.g., "xray.jpg" -> ".jpg"
            if not file_type:
                file_type = os.path.splitext(filename)[1].lower()
            
            # ===== STEP 3: STORE IN DATABASE =====
            # Insert file information and binary data into medical_files table
            # The LONGBLOB column can store up to 4GB of binary data
            self.cursor.execute("""
                INSERT INTO medical_files (filename, file_type, file_size, file_data, observation_id, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (filename, file_type, file_size, file_data, observation_id, description))
            
            # Commit the transaction to make changes permanent
            # This ensures data integrity - either all data is saved or none
            self.connection.commit()
            
            # Get the auto-generated file_id from the database
            # This ID is used for future file operations (retrieve, delete, etc.)
            file_id = self.cursor.lastrowid
            
            # Provide user feedback about successful storage
            print(f"File '{filename}' stored successfully with ID: {file_id}")
            return file_id
            
        except Error as e:
            # Handle MySQL database errors
            # This includes connection issues, SQL syntax errors, constraint violations, etc.
            print(f"Error storing file: {e}")
            return None
        except Exception as e:
            # Handle file system errors
            # This includes file not found, permission denied, disk full, etc.
            print(f"Error reading file: {e}")
            return None
    
    def retrieve_file(self, file_id: int) -> dict:
        """
        Retrieve a file from the database.
        
        Args:
            file_id (int): ID of the file to retrieve
            
        Returns:
            dict: File information including data, or None if failed
        """
        try:
            self.cursor.execute("""
                SELECT file_id, filename, file_type, file_size, file_data, upload_date, observation_id, description
                FROM medical_files WHERE file_id = %s
            """, (file_id,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'file_id': result[0],
                    'filename': result[1],
                    'file_type': result[2],
                    'file_size': result[3],
                    'file_data': result[4],
                    'upload_date': result[5],
                    'observation_id': result[6],
                    'description': result[7]
                }
            return None
            
        except Error as e:
            print(f"Error retrieving file: {e}")
            return None
    
    def save_file_to_disk(self, file_id: int, output_path: str = None) -> bool:
        """
        Save a file from database to disk.
        
        Args:
            file_id (int): ID of the file to save
            output_path (str, optional): Path to save the file. If None, uses original filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_info = self.retrieve_file(file_id)
            if not file_info:
                return False
            
            if not output_path:
                output_path = file_info['filename']
            
            with open(output_path, 'wb') as file:
                file.write(file_info['file_data'])
            
            print(f"File saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving file to disk: {e}")
            return False
    
    def get_files_by_observation(self, observation_id: int) -> list:
        """
        Get all files associated with a specific observation.
        
        Args:
            observation_id (int): ID of the observation
            
        Returns:
            list: List of file information dictionaries
        """
        try:
            self.cursor.execute("""
                SELECT file_id, filename, file_type, file_size, upload_date, description
                FROM medical_files WHERE observation_id = %s
                ORDER BY upload_date DESC
            """, (observation_id,))
            
            results = self.cursor.fetchall()
            files = []
            for row in results:
                files.append({
                    'file_id': row[0],
                    'filename': row[1],
                    'file_type': row[2],
                    'file_size': row[3],
                    'upload_date': row[4],
                    'description': row[5]
                })
            return files
            
        except Error as e:
            print(f"Error retrieving files for observation: {e}")
            return []
    
    def delete_file(self, file_id: int) -> bool:
        """
        Delete a file from the database.
        
        Args:
            file_id (int): ID of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute("DELETE FROM medical_files WHERE file_id = %s", (file_id,))
            self.connection.commit()
            
            if self.cursor.rowcount > 0:
                print(f"File with ID {file_id} deleted successfully")
                return True
            else:
                print(f"No file found with ID {file_id}")
                return False
                
        except Error as e:
            print(f"Error deleting file: {e}")
            return False
    
    # =============================================================================
    # QUERY AND DISPLAY METHODS
    # =============================================================================
    def run_sample_queries(self):
        """
        Execute sample queries to demonstrate database functionality.
        
        This method runs a series of queries to showcase the database structure
        and relationships. It includes both simple table displays and complex
        JOIN queries to demonstrate the relational nature of the database.
        
        Queries include:
        1. Display all tables individually
        2. Complex JOIN query showing patient appointments with doctor information
        """
        print("\n" + "="*50)
        print("SAMPLE QUERIES")
        print("="*50)
        
        # Query 1: Display all clinics
        print("\n1. All Clinics:")
        self.display_table_data("clinic")
        
        # Query 2: Display all departments
        print("\n2. All Departments:")
        self.display_table_data("department")
        
        # Query 3: Display all doctors
        print("\n3. All Doctors:")
        self.display_table_data("doctor")
        
        # Query 4: Display all patients
        print("\n4. All Patients:")
        self.display_table_data("patient")
        
        # Query 5: Display all appointments
        print("\n5. All Appointments:")
        self.display_table_data("appointment")
        
        # Query 6: Display all observations
        print("\n6. All Observations:")
        self.display_table_data("observation")
        
        # Query 7: Display all diagnoses
        print("\n7. All Diagnoses:")
        self.display_table_data("diagnosis")
        
        # Query 8: Complex JOIN query - Patient appointments with doctor names
        print("\n8. Patient Appointments with Doctor Names:")
        try:
            # Complex query joining patient, appointment, and doctor tables
            self.cursor.execute("""
                SELECT 
                    p.first_name, p.last_name,        -- Patient information
                    d.first_name, d.last_name,        -- Doctor information
                    a.date                           -- Appointment date
                FROM patient p
                JOIN appointment a ON p.patient_id = a.patient_id    -- Join patient to appointment
                JOIN doctor d ON a.doctor_id = d.doctor_id           -- Join appointment to doctor
                ORDER BY a.date                      -- Sort by appointment date
            """)
            results = self.cursor.fetchall()
            
            # Display results in formatted manner
            for row in results:
                print(f"  Patient: {row[0]} {row[1]} | Doctor: {row[2]} {row[3]} | Date: {row[4]}")
        except Error as e:
            print(f"Error in complex query: {e}")


# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================
def main():
    """
    Main function to run the clinic database notebook implementation.
    
    This function demonstrates the complete database setup process including:
    1. Database creation
    2. Table creation with proper relationships
    3. Sample data insertion
    4. Query execution and data display
    
    The function follows a step-by-step approach to ensure proper database
    initialization and provides comprehensive logging of each operation.
    """
    print("Clinic Database Management System - Notebook Implementation")
    print("=" * 60)
    
    # Create database instance with default parameters
    db = ClinicDatabaseNotebook()
    
    try:
        # ===== STEP 1: DATABASE CREATION =====
        print("\n1. Creating database...")
        if not db.create_database():
            print("Failed to create database. Exiting.")
            return
        
        # ===== STEP 2: DATABASE LISTING =====
        print("\n2. Available databases:")
        db.show_databases()
        
        # ===== STEP 3: DATABASE CONNECTION =====
        print("\n3. Connecting to clinic_db...")
        if not db.connect():
            print("Failed to connect to database. Exiting.")
            return
        
        # ===== STEP 4: TABLE CLEANUP =====
        print("\n4. Dropping existing tables...")
        db.drop_tables_in_order()
        
        # ===== STEP 5: TABLE CREATION =====
        print("\n5. Creating all tables...")
        db.create_all_tables()
        
        # ===== STEP 6: TABLE VERIFICATION =====
        print("\n6. Database structure:")
        db.show_tables()
        
        # ===== STEP 7: TABLE STRUCTURE DISPLAY =====
        print("\n7. Table structures:")
        db.describe_table("department")      # Show department table structure
        db.describe_table("doctor")          # Show doctor table structure
        db.show_create_table("doctor")       # Show CREATE statement for doctor table
        
        # ===== STEP 8: SAMPLE DATA INSERTION =====
        print("\n8. Inserting sample data...")
        db.insert_all_sample_data()
        
        # ===== STEP 9: FINAL VERIFICATION =====
        print("\n9. Final table data:")
        db.show_tables()
        
        # ===== STEP 10: DEMONSTRATION QUERIES =====
        db.run_sample_queries()
        
        # ===== COMPLETION MESSAGE =====
        print("\n" + "="*60)
        print("Database setup completed successfully!")
        print("="*60)
        
    except Exception as e:
        # Handle any unexpected errors
        print(f"An error occurred: {e}")
    finally:
        # Always ensure database connection is closed
        db.disconnect()


# =============================================================================
# APPLICATION STARTUP
# =============================================================================
if __name__ == "__main__":
    # Only run main() if this script is executed directly (not imported)
    main()
