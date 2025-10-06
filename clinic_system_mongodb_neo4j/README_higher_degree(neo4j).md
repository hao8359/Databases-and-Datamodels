# Clinic Management System (Neo4j + MongoDB)

## Project Overview

This desktop application (built with Tkinter) manages a clinic using both a graph database (Neo4j) for core clinical/business data and MongoDB for real-time messaging features. The app features:
- **Neo4j:** Stores clinics, departments, doctors, patients, appointments, observations, diagnoses, and uploaded medical files as interconnected graph nodes/relationships.
- **MongoDB:** Handles real-time chat, user sessions, and image messages between healthcare staff and patients.

It boasts a modern, user-friendly GUI for patients and doctors (book/view appointments, chat, upload files, view history, research queries).

---
## Repository Layout

- `clinic_v2_enhanced.py`: Main application with GUI (Tkinter)
  - Patient portal (booking, history, chat)
  - Doctor dashboard (login, manage appointments, observations, upload/manage files, custom queries, chat)
  - Integrates 
     - Neo4j: `ClinicDatabaseNotebook`
     - MongoDB: `MongoMessagingSystem`
- `clinic_v2_withoutgui.py`: Core Neo4j database backend
  - Connection setup, schema/counter constraints
  - Node/relationship creation and retrieval (clinic, department, doctor, patient, appointment, observation, diagnosis, medical files)
  - File binary storage (in MedicalFile nodes)
  - Batch/sample data insertion helpers
- `mongodb_messaging.py`: Messaging backend
  - User/session management, password hashing
  - Conversations & real-time messages (text/image, base64-encoded)
  - Utility functions/sample data for chat
- `main.py`: Optional entry point (normally run GUI directly)
- `.env` (optional): Env credentials; you can configure connection in the GUI code

---
## How Components Work Together

### Startup and Data Model Initialization
When the GUI is launched (`clinic_v2_enhanced.py`), the following happens:
- **Neo4j:** `ClinicDatabaseNotebook` connects to Neo4j. If constraints/nodes are missing, it creates them and inserts sample data.
- **MongoDB:** `MongoMessagingSystem` connects, creating indices, users, and collections for chat if needed.

### Database Roles
**Neo4j**: All clinical, business, and record-oriented data goes here, as a property graph:
- Nodes: Clinic, Department, Doctor, Patient, Appointment, Observation, Diagnosis, MedicalFile
- Relationships: e.g., `Clinic-HASDEPARTMENT->Department`, `Doctor-TREATS->Patient`, `Doctor-HASAPPOINTMENT->Appointment`, `Appointment-HASOBSERVATION->Observation`, etc.
- Uniqueness constraints for each node type using Cypher.
- ID generation tracked via a global Counter node (sequential IDs for data compatibility)
- Attachments/files are binary data in MedicalFile nodes, linked from Observations.

**MongoDB:** Handles all chat, session, and profile data.
- Collections: `users`, `user_sessions`, `conversations`, `messages`
- Users matched to Neo4j Patient/Doctor nodes via external ID mapping.
- Session and password management (bcrypt)
- Messages can be text or image (image stored as base64)
- Conversations automatically tracked; unread/read message counts

### GUI Logic
The `clinic_v2_enhanced.py` GUI allows:
- **Patients:** Book/view appointments, open chat, send text/images, view medical history
- **Doctors:** Login, see roster, manage appointments, upload/download/delete files, enter findings, open chat, run Cypher queries on Neo4j
- Both roles interact with both databases without manual DB knowledge

---
## Detailed Function Overview

### Neo4j Backend (clinic_v2_withoutgui.py)
- **Connection/Setup:**
  - Bolt driver and authentication
  - Cypher constraints for unique node IDs
  - Initializes node counters for auto-increment IDs
  - Sample graph data if starting from scratch
- **CRUD Operations:**
  - `createpatient`, `createappointment`, `createobservation` etc. create and link nodes/relationships
  - `storefile`/`retrievefile`/`linkfiletoobservation` handle MedicalFile storage and links
  - `getappointmentsforpatient`, `getappointmentsfordoctor`, etc. return joined data for GUI lists
  - Comprehensive Cypher read-only queries for dashboard views
  - `savefiletodisk`, `deletefile` for file management
- **Graph Structure:**
  - Highly normalized schema, representing real-world connections visually and efficiently
  - Flexible for advanced querying via Cypher (e.g. find all patients with a diagnosis, all appointments by date, etc.)

### MongoDB Messaging (mongodb_messaging.py)
- **Connection/Initialization:**
  - Setup of collections and text/uniqueness indexes
- **User System:**
  - Create users/doctors/nurses/patients via upsert
  - Secure password hashing
  - Sessions stored with expiry and re-auth
- **Conversations/Messaging:**
  - Store conversation metadata (participants, unread, timestamps)
  - Each message can be text or image data (supports image previews via base64)
  - Efficient retrieval of messages for a conversation, chronological sorting
  - Marking messages as read/unread, notification support
- **Utilities:**
  - Search users, upload profile images, create demo data (sample users and chats)

---
## Data Flow & Database Interaction

- **Mapping:** Users in MongoDB link by stable external ID to Neo4j Doctor/Patient nodes for seamless integration (e.g., chat only listed for patients with real appointments, thanks to Cypher joins and ID consistency)
- **No duplicated data:** Clinical records strictly in Neo4j, chat data strictly in MongoDB, joined at the app logic layer.
- **Authentication:** Patients and doctors authenticate chat using MongoDB; business data update via Neo4j.

---
## Environment & Setup
- OS: macOS (tested), Linux/Windows supported
- Python: 3.9+
- Neo4j: 5.x+ (`bolt://localhost:7687`), create with default user/password, schema created automatically
- MongoDB: 6.0+ (local, or use a cluster/URI)

**Python packages:**
```
pip install neo4j pymongo bcrypt python-dotenv
```

---
## Launching the App
```
python clinic_v2_enhanced.py
```
On first run, schemas/constraints and sample data will be setup if database(s) are empty.

---
## Operation Manual
### Patient Portal
- Book appointment: enter name, choose department/doctor/date
- View appointments: search by name
- Chat: load your roster of doctors, open conversations (text/image)

### Doctor Dashboard
- Login/select as doctor, view appointment roster
- Enter findings, upload files
- Manage uploaded files (download/delete)
- Run Cypher queries for research
- Chat with linked patients

---
## Data Model
### Graph Database (Neo4j nodes/relationships)
- Nodes: Clinic, Department, Doctor, Patient, Appointment, Observation, Diagnosis, MedicalFile
- Edges: `HASDEPARTMENT`, `HASDOCTOR`, `TREATS`, `HASAPPOINTMENT`, `HASOBSERVATION`, `HASDIAGNOSIS`, `HASFILE`
- Node examples:
  - Patient `{id, firstname, lastname}`
  - Appointment `{id, date}`
  - Observation `{id, type, description}`
  - MedicalFile `{id, filename, filetype, filesize, filedata (BLOB), uploaddate, description}`

### Messaging Database (MongoDB)
- `users`: `{_id, username, usertype, firstname, lastname, user_id, ...}`
- `conversations`: `{_id, participants, last_activity, message_count}`
- `messages`: `{_id, conversation_id, sender_id, message_text/image, message_type, ...}`
- `user_sessions`: `{_id, user_id, created_at, expires_at}`

---
## Neo4j vs MySQL Comparison
| Feature                   | Neo4j (Now)                                     | MySQL (Previous)                   |
|---------------------------|-------------------------------------------------|------------------------------------|
| Data Model                | Property graph (nodes, edges, Cypher query)     | Relational tables, SQL             |
| Structure Flexibility     | Highly flexible, natural for relationships      | Rigid tables, JOINs for relations  |
| Appointments/Patients     | Linked via edges, easy to traverse              | Table JOINs, needs PK/FK           |
| File Storage              | MedicalFile nodes (BLOB)                        | LONGBLOB in table                  |
| Messaging                 | MongoDB (external, for chat)                    | MongoDB (remained same)            |
| Query Language            | Cypher                                          | SQL                                |
| Schema Management         | Auto constraints, flexible migration            | Fixed tables, migrations needed    |
| Performance (graph ops)   | Fast for traversals, connected data             | Fast for atomic, simple lookups    |
| Extensibility             | Superior: easy to add new node/edge types       | Additional tables/relations needed |
| Visualization             | Suited for graph queries, rich traversals       | Good for tabular reports           |

**Key Benefits by Moving to Neo4j:**
- More natural modeling of real clinic operations: doctors-patients-appointments-referrals as edges
- Easier/faster complex queries (e.g., "find all patients with diagnosis X via relationships")
- Schema changes are lighter, nodes/edges more modular

---
## Troubleshooting
- **Neo4j connection/auth errors:**
  - Verify DB config in code or `.env`
  - Check Neo4j server and credentials
- **Messaging:**
  - MongoDB must be running/accessible
  - Users/conversations created automatically by app logic
- **File/image issues:**
  - Ensure file sizes are within limits
  - File data stored as binary in MedicalFile nodes

---
## Notes
- **Security:** Demo only (no production hardening)
- **Data init:** First startup creates constraints, counters, sample data if empty
- **Extensibility:** You can build APIs off the Neo4j and Mongo connectivity easily
