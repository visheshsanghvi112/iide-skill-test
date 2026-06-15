import pandas as pd
import sqlite3
import os

excel_path = "Skill Test - Database.xlsx"
db_path = "placement_analytics_task/placement.db"

# Remove existing database if any
if os.path.exists(db_path):
    os.remove(db_path)

print("Reading Excel sheets with strict string dtypes for identifier columns...")
# Force ID columns as strings to prevent float precision issues (e.g. 1.599e17)
enrol_df = pd.read_excel(excel_path, sheet_name="Enrolments", dtype={"Record Id": str, "CandidateId": str})
cand_df = pd.read_excel(excel_path, sheet_name="Candidates", dtype={"Candidate Id": str})
app_df = pd.read_excel(excel_path, sheet_name="Applications", dtype={"Application Id": str, "Candidate Id": str, "Job Opening Id": str})
job_df = pd.read_excel(excel_path, sheet_name="Job Openings", dtype={"Job Opening Id": str})
inter_df = pd.read_excel(excel_path, sheet_name="Interviews", dtype={"Interview Id": str, "Candidate Id": str, "Job Opening Id": str})

# Normalize empty/whitespace strings to NaN
for df in [enrol_df, cand_df, app_df, job_df, inter_df]:
    df.replace(r'^\s*$', pd.NA, regex=True, inplace=True)

# ----------------- Connect to SQLite -----------------
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Enable foreign key support in SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

print("\n--- Question 1: Creating Normalized 3NF Database Tables ---")

# 1. CANDIDATES Table
cursor.execute("""
CREATE TABLE candidates (
    candidate_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT,
    phone_number TEXT,
    email TEXT UNIQUE,
    city TEXT,
    province TEXT,
    country TEXT,
    skill_set TEXT,
    candidate_stage TEXT,
    batch_name TEXT,
    age INTEGER,
    preferred_job_location TEXT,
    gender TEXT,
    strength_area_1 TEXT,
    strength_area_2 TEXT
);
""")

# 2. ENROLMENTS Table
cursor.execute("""
CREATE TABLE enrolments (
    enrolment_id TEXT PRIMARY KEY,
    enrolment_owner TEXT,
    enrolment_name TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    email TEXT,
    batch_name TEXT,
    stage TEXT,
    candidate_id TEXT,
    created_time TEXT,
    job_role_preference_1 TEXT,
    job_role_preference_2 TEXT,
    knocked_off_reason TEXT,
    on_hold_reason TEXT,
    course_name TEXT,
    preferred_job_type TEXT,
    college_name TEXT,
    degree TEXT,
    graduation_year TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE SET NULL
);
""")

# 3. JOB OPENINGS Table
cursor.execute("""
CREATE TABLE job_openings (
    job_opening_id TEXT PRIMARY KEY,
    account_manager_id TEXT,
    job_type TEXT,
    posting_title TEXT,
    job_opening_status TEXT,
    date_opened TEXT,
    city TEXT,
    province TEXT,
    country TEXT,
    created_time TEXT,
    salary TEXT,
    profile TEXT
);
""")

# 4. APPLICATIONS Table (Redundant fields like candidate names, email, and posting title removed to achieve 3NF)
cursor.execute("""
CREATE TABLE applications (
    application_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    job_opening_id TEXT NOT NULL,
    application_stage TEXT,
    application_status TEXT,
    created_time TEXT,
    batch_name TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (job_opening_id) REFERENCES job_openings(job_opening_id) ON DELETE CASCADE
);
""")

# 5. INTERVIEWS Table (Redundant candidate_id & job_opening_id replaced by direct link to application_id)
cursor.execute("""
CREATE TABLE interviews (
    interview_id TEXT PRIMARY KEY,
    interview_owner_id TEXT,
    interview_name TEXT,
    client_id TEXT,
    application_id TEXT NOT NULL,
    from_time TEXT,
    to_time TEXT,
    interview_type TEXT,
    interview_status TEXT,
    batch_name TEXT,
    cancellation_reason TEXT,
    feedback TEXT,
    created_time TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(application_id) ON DELETE CASCADE
);
""")

# Create indexes for speed and query performance
cursor.execute("CREATE INDEX idx_enrolments_candidate ON enrolments(candidate_id);")
cursor.execute("CREATE INDEX idx_applications_candidate ON applications(candidate_id);")
cursor.execute("CREATE INDEX idx_applications_job ON applications(job_opening_id);")
cursor.execute("CREATE INDEX idx_interviews_application ON interviews(application_id);")

# ----------------- Clean & Insert Data -----------------

# 1. Populate CANDIDATES
print("Populating 'candidates' table...")
for _, row in cand_df.iterrows():
    cursor.execute("""
    INSERT INTO candidates (
        candidate_id, first_name, last_name, phone_number, email, city, province, country,
        skill_set, candidate_stage, batch_name, age, preferred_job_location, gender,
        strength_area_1, strength_area_2
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        str(row['Candidate Id']).strip(),
        row['First Name'],
        row['Last Name'] if pd.notna(row['Last Name']) else None,
        str(int(row['Phone Number'])) if pd.notna(row['Phone Number']) else None,
        row['Email'],
        row['City'] if pd.notna(row['City']) else None,
        row['Province'] if pd.notna(row['Province']) else None,
        row['Country'] if pd.notna(row['Country']) else None,
        row['Skill Set'] if pd.notna(row['Skill Set']) else None,
        row['Candidate Stage'] if pd.notna(row['Candidate Stage']) else None,
        row['Batch Name'] if pd.notna(row['Batch Name']) else None,
        int(row['Age']) if pd.notna(row['Age']) else None,
        row['Preferred Job Location'] if pd.notna(row['Preferred Job Location']) else None,
        row['Gender'] if pd.notna(row['Gender']) else None,
        row['Personal Strength Area 1'] if pd.notna(row['Personal Strength Area 1']) else None,
        row['Personal Strength Area 2'] if pd.notna(row['Personal Strength Area 2']) else None
    ))

# 2. Populate ENROLMENTS
print("Populating 'enrolments' table...")
for _, row in enrol_df.iterrows():
    cand_id = row['CandidateId']
    if pd.notna(cand_id):
        # Clean the candidate ID string (remove .0 if float conversion seeped in previously)
        cand_id_str = str(cand_id).split('.')[0].strip()
        # Verify it exists in candidates table, else set null to maintain FK integrity
        cursor.execute("SELECT 1 FROM candidates WHERE candidate_id = ?", (cand_id_str,))
        if not cursor.fetchone():
            cand_id_str = None
    else:
        cand_id_str = None

    cursor.execute("""
    INSERT INTO enrolments (
        enrolment_id, enrolment_owner, enrolment_name, first_name, last_name, email, batch_name, stage,
        candidate_id, created_time, job_role_preference_1, job_role_preference_2, knocked_off_reason,
        on_hold_reason, course_name, preferred_job_type, college_name, degree, graduation_year
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        str(row['Record Id']).strip(),
        row['Enrolment Owner'],
        row['Enrolment Name'],
        row['First Name'],
        row['Last Name'] if pd.notna(row['Last Name']) else None,
        row['Email'] if pd.notna(row['Email']) else None,
        row['Batch Name'],
        row['Stage'],
        cand_id_str,
        str(row['Created Time']),
        row['Job Role Preference 1'] if pd.notna(row['Job Role Preference 1']) else None,
        row['Job Role Preference 2'] if pd.notna(row['Job Role Preference 2']) else None,
        row['Knocked Off Reason'] if pd.notna(row['Knocked Off Reason']) else None,
        row['On Hold Reason'] if pd.notna(row['On Hold Reason']) else None,
        row['Course Name'],
        row['Preferred Job Type'] if pd.notna(row['Preferred Job Type']) else None,
        row['College Name'] if pd.notna(row['College Name']) else None,
        row['Degree'] if pd.notna(row['Degree']) else None,
        str(row['Graduation Year']) if pd.notna(row['Graduation Year']) else None
    ))

# 3. Populate JOB OPENINGS
print("Populating 'job_openings' table...")
for _, row in job_df.iterrows():
    cursor.execute("""
    INSERT INTO job_openings (
        job_opening_id, account_manager_id, job_type, posting_title, job_opening_status,
        date_opened, city, province, country, created_time, salary, profile
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        str(row['Job Opening Id']).strip(),
        row['Account Manager Id'],
        row['Job Type'],
        row['Posting Title'] if pd.notna(row['Posting Title']) else None,
        row['Job Opening Status'] if pd.notna(row['Job Opening Status']) else None,
        str(row['Date Opened']) if pd.notna(row['Date Opened']) else None,
        row['City'] if pd.notna(row['City']) else None,
        row['Province'] if pd.notna(row['Province']) else None,
        row['Country'] if pd.notna(row['Country']) else None,
        str(row['Created Time']),
        row['Salary'] if pd.notna(row['Salary']) else None,
        row['Profile'] if pd.notna(row['Profile']) else None
    ))

# 4. Populate APPLICATIONS
print("Populating 'applications' table (eliminating redundant name/title details)...")
for _, row in app_df.iterrows():
    cand_id = str(row['Candidate Id']).strip()
    job_id = str(row['Job Opening Id']).strip()

    # Enforce foreign key validation
    cursor.execute("SELECT 1 FROM candidates WHERE candidate_id = ?", (cand_id,))
    if not cursor.fetchone():
        print(f"Warning: Candidate {cand_id} not found in candidates table. Skipping application {row['Application Id']}.")
        continue

    cursor.execute("SELECT 1 FROM job_openings WHERE job_opening_id = ?", (job_id,))
    if not cursor.fetchone():
        print(f"Warning: Job opening {job_id} not found in job_openings table. Skipping application {row['Application Id']}.")
        continue

    cursor.execute("""
    INSERT INTO applications (
        application_id, candidate_id, job_opening_id, application_stage, application_status,
        created_time, batch_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        str(row['Application Id']).strip(),
        cand_id,
        job_id,
        row['Application Stage'] if pd.notna(row['Application Stage']) else None,
        row['Application Status'] if pd.notna(row['Application Status']) else None,
        str(row['Created Time']),
        row['Batch Name']
    ))

# 5. Populate INTERVIEWS
print("Populating 'interviews' table (mapping candidate and job openings to unique application_id)...")
for _, row in inter_df.iterrows():
    cand_id = str(row['Candidate Id']).strip()
    job_id = str(row['Job Opening Id']).strip()

    # Find the corresponding application_id
    cursor.execute("""
    SELECT application_id FROM applications 
    WHERE candidate_id = ? AND job_opening_id = ?
    """, (cand_id, job_id))
    result = cursor.fetchone()

    if not result:
        print(f"Warning: No matching application found for Interview {row['Interview Id']} (Candidate: {cand_id}, Job: {job_id}). Skipping.")
        continue

    app_id = result[0]

    cursor.execute("""
    INSERT INTO interviews (
        interview_id, interview_owner_id, interview_name, client_id, application_id,
        from_time, to_time, interview_type, interview_status, batch_name,
        cancellation_reason, feedback, created_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        str(row['Interview Id']).strip(),
        row['Interview Owner Id'],
        row['Interview Name'],
        row['Client Id'],
        app_id,
        str(row['From']),
        str(row['To']),
        row['Interview Type'],
        row['Interview Status'] if pd.notna(row['Interview Status']) else None,
        row['Batch Name'],
        row['Cancellation Reason'] if pd.notna(row['Cancellation Reason']) else None,
        row['Feedback'] if pd.notna(row['Feedback']) else None,
        str(row['Created Time'])
    ))

conn.commit()

# Verify counts
print("\n--- Ingestion Verification ---")
for table in ['candidates', 'enrolments', 'job_openings', 'applications', 'interviews']:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"Table '{table}': {count} records successfully loaded.")

conn.close()
print("\nDatabase build complete! SQLite database created at:", db_path)
