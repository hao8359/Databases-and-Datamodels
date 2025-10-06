#!/usr/bin/env python3
"""
Clinic Graph Database Management System - Neo4j Operations
=========================================================

This module provides the core database functionality for the clinic management system
using a Neo4j graph database. It replaces the previous MySQL implementation while keeping
the same high-level API for the GUI to call.

Key concepts (nodes): Clinic, Department, Doctor, Patient, Appointment, Observation,
Diagnosis, MedicalFile

Relationships (directional):
- (Clinic)-[:HAS_DEPARTMENT]->(Department)
- (Department)-[:HAS_DOCTOR]->(Doctor)
- (Doctor)-[:TREATS]->(Patient)
- (Patient)-[:HAS_APPOINTMENT]->(Appointment)
- (Doctor)-[:HAS_APPOINTMENT]->(Appointment)
- (Appointment)-[:HAS_OBSERVATION]->(Observation)
- (Observation)-[:HAS_DIAGNOSIS]->(Diagnosis)
- (Observation)-[:HAS_FILE]->(MedicalFile)

Each domain node stores an integer `id` generated via a simple counter to preserve
compatibility with the GUI that expects integer IDs.
"""

# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
from neo4j import GraphDatabase, basic_auth
from typing import Optional, List, Tuple
import datetime
import mimetypes
import os


# =============================================================================
# MAIN DATABASE CLASS (Neo4j)
# =============================================================================
class ClinicDatabaseNotebook:
    """
    Neo4j-backed database management class for the clinic management system.

    Provides connection management, schema initialization (constraints and counters),
    data insertion helpers, query helpers used by the GUI, and file storage methods
    mapped to MedicalFile nodes.
    """

    def __init__(self, host: str = "bolt://localhost:7687", user: str = "neo4j",
                 password: str = "clinicdatabase", database: str = "neo4j"):
        self.uri = host
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
    
    # =============================================================================
    # CONNECTION MANAGEMENT
    # =============================================================================
    def connect(self) -> bool:
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=basic_auth(self.user, self.password))
            # test
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 as ok").single()
            print(f"Successfully connected to Neo4j database: {self.database}")
            # Ensure schema and counters exist
            self._ensure_constraints_and_counters()
            return True
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            return False
    
    def disconnect(self):
        if self.driver is not None:
            self.driver.close()
            print("Neo4j connection closed.")

    # Backwards-compat API no-ops
    def create_database(self) -> bool:
        # Neo4j database assumed to exist; return True
        return True
    
    # =============================================================================
    # SCHEMA: CONSTRAINTS AND COUNTERS
    # =============================================================================
    def _ensure_constraints_and_counters(self):
        cypher_statements = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Clinic) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Doctor) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patient) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Appointment) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (x:Diagnosis) REQUIRE x.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:MedicalFile) REQUIRE f.id IS UNIQUE",
        ]
        with self.driver.session(database=self.database) as session:
            for stmt in cypher_statements:
                session.run(stmt)
            # Initialize a single Counter node if not exists
            session.run(
                "MERGE (ctr:Counter {name: 'global_ids'}) "
                "ON CREATE SET ctr.clinic=1, ctr.department=1, ctr.doctor=1, ctr.patient=1, ctr.appointment=1, ctr.observation=1, ctr.diagnosis=1, ctr.medicalfile=1"
            )

    def _next_id(self, label: str) -> int:
        field = label.lower()
        with self.driver.session(database=self.database) as session:
            rec = session.run(
                f"MATCH (ctr:Counter {{name:'global_ids'}}) "
                f"WITH ctr, ctr.{field} AS current "
                f"SET ctr.{field} = coalesce(current,1) + 1 "
                f"RETURN coalesce(current,1) AS id"
            ).single()
            return int(rec["id"]) if rec else 1
    
    # =============================================================================
    # SETUP AND SAMPLE DATA
    # =============================================================================
    def create_all_tables(self):
        # For Neo4j this means ensuring constraints; already done in connect
        self._ensure_constraints_and_counters()

    def insert_all_sample_data(self):
        with self.driver.session(database=self.database) as session:
            # Clinics
            clinic1_id = self._next_id("Clinic")
            clinic2_id = self._next_id("Clinic")
            session.run(
                "CREATE (c1:Clinic {id:$id1, name:$n1, address:$a1, phone:$p1, email:$e1})",
                id1=clinic1_id, n1="Sunshine Health Center", a1="123 Wellness Ave", p1="+46701234567", e1="contact@sunshine.com"
            )
            session.run(
                "CREATE (c2:Clinic {id:$id2, name:$n2, address:$a2, phone:$p2, email:$e2})",
                id2=clinic2_id, n2="Green Valley Clinic", a2="456 Nature Rd", p2="+46707654321", e2="info@greenvalley.com"
            )

            # Departments (attach to clinic1)
            departments = [
                "Cardiology","Pediatrics","Emergency","Internal medicine","Surgery",
                "Obstetrics & Gynecology","Orthopedics","Neurology","Oncology","ENT",
                "Psychiatry","Radiology","Ophtalmology","Laboratory","Dermatology",
                "Rehabilitation","Nutrition","Medical records","Biomedical Engineering",
                "Nephrology","Gastroenterology","Pulmonology","Urology","Plastic Surgery"
            ]
            dept_ids = []
            for name in departments:
                did = self._next_id("Department")
                dept_ids.append(did)
                session.run(
                    "MATCH (c:Clinic {id:$cid}) "
                    "CREATE (d:Department {id:$id, name:$name})<-[:HAS_DEPARTMENT]-(c)",
                    cid=clinic1_id, id=did, name=name
                )

            # Doctors: 2 per department (use sample from previous data where possible)
            doctor_names = [
                ("Anna","Johnson"),("Michael","Chen"),("Reine","Bergström"),("Erik","Andersson"),
                ("Sarah","Williams"),("James","Brown"),("Lisa","Garcia"),("Robert","Davis"),
                ("Maria","Rodriguez"),("David","Miller"),("Jennifer","Wilson"),("Christopher","Moore"),
                ("Amanda","Taylor"),("Daniel","Anderson"),("Jessica","Thomas"),("Datthew","Jackson"),
                ("Ashley","White"),("Andrew","Harris"),("Samantha","Martin"),("Joshua","Thompson"),
                ("Nicole","Garcia"),("Kevin","Martinez"),("Rachel","Robinson"),("Brian","Clark"),
                ("Lauren","Rodriguez"),("Ryan","Lewis"),("Megan","Lee"),("Tyler","Walker"),
                ("Stephanie","Hall"),("Nathan","Allen"),("Danielle","Young"),("Justin","King"),
                ("Michelle","Wright"),("Brandon","Scott"),("Kimberly","Torres"),("Jacob","Nguyen"),
                ("Angela","Hill"),("Zachary","Flores"),("Heather","Green"),("Aaron","Adams"),
                ("Rebecca","Nelson"),("Kyle","Baker"),("Victoria","Carter"),("Ethan","Mitchell"),
                ("Christina","Perez"),("Noah","Roberts"),("Kelly","Turner"),("Logan","Phillips"),
                ("Amy","Campbell")
            ]
            doctor_ids = []
            idx = 0
            for did in dept_ids:
                for _ in range(2):
                    if idx >= len(doctor_names):
                        break
                    fn, ln = doctor_names[idx]
                    idx += 1
                    doc_id = self._next_id("Doctor")
                    doctor_ids.append(doc_id)
                    session.run(
                        "MATCH (d:Department {id:$did}) "
                        "CREATE (doc:Doctor {id:$id, first_name:$fn, last_name:$ln})<-[:HAS_DOCTOR]-(d)",
                        did=did, id=doc_id, fn=fn, ln=ln
                    )

            # Patients
            p1 = self._next_id("Patient")
            p2 = self._next_id("Patient")
            session.run("CREATE (:Patient {id:$id, first_name:$fn, last_name:$ln})",
                        id=p1, fn="Lars", ln="Nilsson")
            session.run("CREATE (:Patient {id:$id, first_name:$fn, last_name:$ln})",
                        id=p2, fn="Maria", ln="Garcia")

            # Link example patients to first doctor
            if doctor_ids:
                session.run(
                    "MATCH (doc:Doctor {id:$doc}), (p1:Patient {id:$p1}), (p2:Patient {id:$p2}) "
                    "MERGE (doc)-[:TREATS]->(p1) "
                    "MERGE (doc)-[:TREATS]->(p2)",
                    doc=doctor_ids[0], p1=p1, p2=p2
                )

            # Appointments
            a1 = self._next_id("Appointment")
            a2 = self._next_id("Appointment")
            a3 = self._next_id("Appointment")
            a4 = self._next_id("Appointment")
            dates = ["2024-01-15","2024-01-16","2024-01-17","2024-01-18"]
            appts = [(a1, doctor_ids[0], p1, dates[0]), (a2, doctor_ids[1] if len(doctor_ids)>1 else doctor_ids[0], p2, dates[1]),
                     (a3, doctor_ids[0], p1, dates[2]), (a4, doctor_ids[1] if len(doctor_ids)>1 else doctor_ids[0], p2, dates[3])]
            for aid, didoc, pid, dt in appts:
                session.run(
                    "MATCH (doc:Doctor {id:$did}), (p:Patient {id:$pid}) "
                    "CREATE (a:Appointment {id:$aid, date:$date}) "
                    "MERGE (doc)-[:HAS_APPOINTMENT]->(a) "
                    "MERGE (p)-[:HAS_APPOINTMENT]->(a)",
                    did=didoc, pid=pid, aid=aid, date=dt
                )

            # Observations and Diagnoses for a1, a2, a3, a4
            observations = [
                ("Physical Examination", "Patient shows signs of elevated blood pressure and irregular heartbeat", a1),
                ("Blood Test", "Complete blood count shows elevated white blood cell count", a1),
                ("Physical Examination", "Child shows normal growth patterns and healthy vital signs", a2),
                ("X-Ray", "Chest X-ray reveals clear lungs with no abnormalities", a2),
                ("Physical Examination", "Follow-up examination shows improved blood pressure readings", a3),
                ("Blood Test", "Follow-up blood work shows normal white blood cell count", a3),
                ("Physical Examination", "Routine check-up shows excellent health status", a4)
            ]
            obs_ids = []
            for t, desc, appt in observations:
                oid = self._next_id("Observation")
                obs_ids.append(oid)
                session.run(
                    "MATCH (a:Appointment {id:$aid}) "
                    "CREATE (o:Observation {id:$id, type:$type, description:$desc})<-[:HAS_OBSERVATION]-(a)",
                    aid=appt, id=oid, type=t, desc=desc
                )

            diagnoses = [
                ("Hypertension - Stage 1", obs_ids[0]),
                ("Possible infection - requires further monitoring", obs_ids[1]),
                ("Healthy child - no medical concerns", obs_ids[2]),
                ("Normal chest examination", obs_ids[3]),
                ("Blood pressure under control with medication", obs_ids[4]),
                ("Infection resolved - normal blood work", obs_ids[5]),
                ("Excellent health - no medical issues", obs_ids[6])
            ]
            for desc, oid in diagnoses:
                did = self._next_id("Diagnosis")
                session.run(
                    "MATCH (o:Observation {id:$oid}) "
                    "CREATE (x:Diagnosis {id:$id, description:$desc})<-[:HAS_DIAGNOSIS]-(o)",
                    oid=oid, id=did, desc=desc
                )

            print("Sample data inserted into Neo4j.")
    
    # =============================================================================
    # FILE STORAGE USING MedicalFile NODES
    # =============================================================================
    def store_file(self, file_path: str, observation_id: int = None, description: str = None) -> Optional[int]:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            filename = os.path.basename(file_path)
            file_size = len(data)
            file_type, _ = mimetypes.guess_type(file_path)
            if not file_type:
                file_type = os.path.splitext(filename)[1].lower()
            fid = self._next_id("MedicalFile")
            with self.driver.session(database=self.database) as session:
                session.run(
                    "CREATE (mf:MedicalFile {id:$id, filename:$fn, file_type:$ft, file_size:$fs, file_data:$data, upload_date:$ud, description:$desc})",
                    id=fid, fn=filename, ft=file_type, fs=file_size, data=data,
                    ud=datetime.datetime.now().isoformat(), desc=description
                )
                if observation_id is not None:
                    session.run(
                        "MATCH (o:Observation {id:$oid}), (mf:MedicalFile {id:$fid}) "
                        "MERGE (o)-[:HAS_FILE]->(mf)",
                        oid=observation_id, fid=fid
                    )
            print(f"File '{filename}' stored successfully with ID: {fid}")
            return fid
        except Exception as e:
            print(f"Error storing file: {e}")
            return None

    def retrieve_file(self, file_id: int) -> Optional[dict]:
        try:
            with self.driver.session(database=self.database) as session:
                rec = session.run(
                    "MATCH (mf:MedicalFile {id:$id}) RETURN mf",
                    id=file_id
                ).single()
                if not rec:
                    return None
                mf = rec["mf"]
                # Find observation if linked
                obs = session.run(
                    "MATCH (o:Observation)-[:HAS_FILE]->(mf:MedicalFile {id:$id}) RETURN o.id AS oid",
                    id=file_id
                ).single()
                return {
                    'file_id': mf["id"],
                    'filename': mf.get("filename"),
                    'file_type': mf.get("file_type"),
                    'file_size': mf.get("file_size"),
                    'file_data': mf.get("file_data"),
                    'upload_date': mf.get("upload_date"),
                    'observation_id': (obs["oid"] if obs else None),
                    'description': mf.get("description")
                }
        except Exception as e:
            print(f"Error retrieving file: {e}")
            return None
    
    def save_file_to_disk(self, file_id: int, output_path: str = None) -> bool:
        try:
            info = self.retrieve_file(file_id)
            if not info:
                return False
            if not output_path:
                output_path = info['filename'] or f"file_{file_id}"
            with open(output_path, 'wb') as f:
                f.write(info['file_data'] or b"")
            print(f"File saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving file to disk: {e}")
            return False
    
    def get_files_by_observation(self, observation_id: int) -> List[dict]:
        try:
            with self.driver.session(database=self.database) as session:
                res = session.run(
                    "MATCH (o:Observation {id:$oid})-[:HAS_FILE]->(mf:MedicalFile) "
                    "RETURN mf ORDER BY mf.upload_date DESC",
                    oid=observation_id
                )
            files = []
            for r in res:
                mf = r["mf"]
            files.append({
                    'file_id': mf["id"],
                    'filename': mf.get("filename"),
                    'file_type': mf.get("file_type"),
                    'file_size': mf.get("file_size"),
                    'upload_date': mf.get("upload_date"),
                    'description': mf.get("description")
            })
            return files
        except Exception as e:
            print(f"Error retrieving files for observation: {e}")
            return []
    
    def delete_file(self, file_id: int) -> bool:
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(
                    "MATCH (mf:MedicalFile {id:$id}) DETACH DELETE mf RETURN 1",
                    id=file_id
                ).single()
                return bool(result)
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    # =============================================================================
    # GUI-FACING QUERY/COMMAND HELPERS
    # =============================================================================
    def get_departments(self) -> List[Tuple[int, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run("MATCH (d:Department) RETURN d.id as id, d.name as name ORDER BY name")
            return [(int(r["id"]), r["name"]) for r in res]

    def get_doctors_by_department(self, department_id: int) -> List[Tuple[int, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (:Department {id:$id})-[:HAS_DOCTOR]->(doc:Doctor) "
                "RETURN doc.id AS id, doc.first_name AS fn, doc.last_name AS ln ORDER BY fn, ln",
                id=department_id
            )
            return [(int(r["id"]), r["fn"], r["ln"]) for r in res]

    def get_doctors(self) -> List[Tuple[int, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run("MATCH (doc:Doctor) RETURN doc.id AS id, doc.first_name AS fn, doc.last_name AS ln ORDER BY fn, ln")
            return [(int(r["id"]), r["fn"], r["ln"]) for r in res]

    def get_patient_by_name(self, first_name: str, last_name: str) -> Optional[Tuple[int, str, str]]:
        with self.driver.session(database=self.database) as session:
            rec = session.run(
                "MATCH (p:Patient {first_name:$fn, last_name:$ln}) RETURN p.id as id, p.first_name as fn, p.last_name as ln",
                fn=first_name, ln=last_name
            ).single()
            if not rec:
                return None
            return (int(rec["id"]), rec["fn"], rec["ln"])

    def create_patient(self, first_name: str, last_name: str, doctor_id: Optional[int] = None) -> int:
        pid = self._next_id("Patient")
        with self.driver.session(database=self.database) as session:
            session.run("CREATE (:Patient {id:$id, first_name:$fn, last_name:$ln})", id=pid, fn=first_name, ln=last_name)
            if doctor_id is not None:
                session.run(
                    "MATCH (doc:Doctor {id:$did}), (p:Patient {id:$pid}) MERGE (doc)-[:TREATS]->(p)",
                    did=doctor_id, pid=pid
                )
        return pid

    def create_appointment(self, doctor_id: int, date_str: str, patient_id: int) -> int:
        aid = self._next_id("Appointment")
        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (doc:Doctor {id:$did}), (p:Patient {id:$pid}) "
                "CREATE (a:Appointment {id:$aid, date:$date}) "
                "MERGE (doc)-[:HAS_APPOINTMENT]->(a) "
                "MERGE (p)-[:HAS_APPOINTMENT]->(a)",
                did=doctor_id, pid=patient_id, aid=aid, date=date_str
            )
        return aid

    def get_appointments_for_patient(self, first_name: str, last_name: str) -> List[Tuple[int, str, str, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (p:Patient {first_name:$fn, last_name:$ln})-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(d:Doctor) "
                "MATCH (d)<-[:HAS_DOCTOR]-(dept:Department) "
                "RETURN a.id AS aid, a.date AS date, d.first_name AS dfn, d.last_name AS dln, dept.name AS dept "
                "ORDER BY date",
                fn=first_name, ln=last_name
            )
            return [(int(r["aid"]), r["date"], r["dfn"], r["dln"], r["dept"]) for r in res]

    def get_appointments_for_doctor(self, doctor_id: int) -> List[Tuple[int, str, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (d:Doctor {id:$did})-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient) "
                "RETURN a.id AS aid, a.date AS date, p.first_name AS pfn, p.last_name AS pln ORDER BY date",
                did=doctor_id
            )
            return [(int(r["aid"]), r["date"], r["pfn"], r["pln"]) for r in res]

    def create_observation(self, appointment_id: int, obs_type: str, description: str) -> int:
        oid = self._next_id("Observation")
        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (a:Appointment {id:$aid}) "
                "CREATE (o:Observation {id:$id, type:$type, description:$desc})<-[:HAS_OBSERVATION]-(a)",
                aid=appointment_id, id=oid, type=obs_type, desc=description
            )
        return oid

    def link_file_to_observation(self, file_id: int, observation_id: int) -> None:
        with self.driver.session(database=self.database) as session:
            session.run(
                "MATCH (o:Observation {id:$oid}), (f:MedicalFile {id:$fid}) MERGE (o)-[:HAS_FILE]->(f)",
                oid=observation_id, fid=file_id
            )

    def list_files(self) -> List[Tuple[int, str, str, int, str, Optional[int]]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (mf:MedicalFile) "
                "OPTIONAL MATCH (o:Observation)-[:HAS_FILE]->(mf) "
                "RETURN mf.id AS id, mf.filename AS filename, mf.file_type AS file_type, mf.file_size AS file_size, mf.upload_date AS upload_date, o.id AS observation_id "
                "ORDER BY upload_date DESC"
            )
            return [
                (int(r["id"]), r["filename"], r["file_type"], int(r["file_size"] or 0), r["upload_date"], (int(r["observation_id"]) if r["observation_id"] is not None else None))
                for r in res
            ]

    def get_doctors_for_patient(self, patient_id: int) -> List[Tuple[int, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (p:Patient {id:$pid})-[:HAS_APPOINTMENT]->(:Appointment)<-[:HAS_APPOINTMENT]-(d:Doctor) "
                "RETURN DISTINCT d.id AS id, d.first_name AS fn, d.last_name AS ln ORDER BY fn, ln",
                pid=patient_id
            )
            return [(int(r["id"]), r["fn"], r["ln"]) for r in res]

    def get_patients_for_doctor(self, doctor_id: int) -> List[Tuple[int, str, str]]:
        with self.driver.session(database=self.database) as session:
            res = session.run(
                "MATCH (d:Doctor {id:$did})-[:HAS_APPOINTMENT]->(:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient) "
                "RETURN DISTINCT p.id AS id, p.first_name AS fn, p.last_name AS ln ORDER BY fn, ln",
                did=doctor_id
            )
            return [(int(r["id"]), r["fn"], r["ln"]) for r in res]

# =============================================================================
    # DEMO OUTPUT
# =============================================================================
    def run_sample_queries(self):
        with self.driver.session(database=self.database) as session:
            print("\n=== Clinics ===")
            for r in session.run("MATCH (c:Clinic) RETURN c.id as id, c.name as name ORDER BY id"):
                print(r["id"], r["name"])
            print("\n=== Departments ===")
            for r in session.run("MATCH (d:Department) RETURN d.id as id, d.name as name ORDER BY name"):
                print(r["id"], r["name"])
            print("\n=== Doctors ===")
            for r in session.run("MATCH (doc:Doctor) RETURN doc.id as id, doc.first_name as fn, doc.last_name as ln ORDER BY fn, ln"):
                print(r["id"], r["fn"], r["ln"])
            print("\n=== Patients ===")
            for r in session.run("MATCH (p:Patient) RETURN p.id as id, p.first_name as fn, p.last_name as ln ORDER BY fn, ln"):
                print(r["id"], r["fn"], r["ln"])
            print("\n=== Appointments (Patient - Doctor - Date) ===")
            q = (
                "MATCH (p:Patient)-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(d:Doctor) "
                "RETURN p.first_name AS pfn, p.last_name AS pln, d.first_name AS dfn, d.last_name AS dln, a.date AS date ORDER BY date"
            )
            for r in session.run(q):
                print(f"Patient: {r['pfn']} {r['pln']} | Doctor: {r['dfn']} {r['dln']} | Date: {r['date']}")


def main():
    print("Clinic Graph Database (Neo4j) - Demo Setup")
    db = ClinicDatabaseNotebook()
    try:
        if not db.connect():
            print("Failed to connect to Neo4j")
            return
        db.create_all_tables()
        db.insert_all_sample_data()
        db.run_sample_queries()
    finally:
        db.disconnect()


if __name__ == "__main__":
    main()

