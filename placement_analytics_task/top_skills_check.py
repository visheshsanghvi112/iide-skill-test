import sqlite3

conn = sqlite3.connect('placement_analytics_task/placement.db')
c = conn.cursor()

print("=" * 60)
print("DATA INTEGRITY AUDIT")
print("=" * 60)

# 1. Row counts
print("\n[1] ROW COUNTS")
for t in ['candidates', 'enrolments', 'job_openings', 'applications', 'interviews']:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t:20s}: {c.fetchone()[0]}")

# 2. ID uniqueness check
print("\n[2] DUPLICATE ID CHECK")
for t, col in [('candidates','candidate_id'),('enrolments','enrolment_id'),
               ('applications','application_id'),('interviews','interview_id'),
               ('job_openings','job_opening_id')]:
    c.execute(f"SELECT COUNT(*) - COUNT(DISTINCT {col}) FROM {t}")
    dupes = c.fetchone()[0]
    print(f"  {t}.{col}: {dupes} duplicates {'✓' if dupes == 0 else '❌ PROBLEM'}")

# 3. Orphan FK check
print("\n[3] ORPHAN FOREIGN KEY CHECK")

c.execute("""SELECT COUNT(*) FROM enrolments 
             WHERE candidate_id IS NOT NULL 
             AND candidate_id NOT IN (SELECT candidate_id FROM candidates)""")
print(f"  Enrolments with invalid candidate_id: {c.fetchone()[0]}")

c.execute("""SELECT COUNT(*) FROM applications 
             WHERE candidate_id NOT IN (SELECT candidate_id FROM candidates)""")
print(f"  Applications with invalid candidate_id: {c.fetchone()[0]}")

c.execute("""SELECT COUNT(*) FROM applications 
             WHERE job_opening_id NOT IN (SELECT job_opening_id FROM job_openings)""")
print(f"  Applications with invalid job_opening_id: {c.fetchone()[0]}")

c.execute("""SELECT COUNT(*) FROM interviews 
             WHERE application_id NOT IN (SELECT application_id FROM applications)""")
print(f"  Interviews with invalid application_id: {c.fetchone()[0]}")

# 4. NULL checks on critical fields
print("\n[4] NULL CHECKS ON CRITICAL FIELDS")
c.execute("SELECT COUNT(*) FROM candidates WHERE email IS NULL")
print(f"  Candidates with NULL email: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM candidates WHERE first_name IS NULL")
print(f"  Candidates with NULL first_name: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM applications WHERE candidate_id IS NULL OR job_opening_id IS NULL")
print(f"  Applications missing candidate/job FK: {c.fetchone()[0]}")

# 5. Spot check: pick 3 random candidates and trace full pipeline
print("\n[5] RANDOM CANDIDATE PIPELINE TRACE (3 samples)")
c.execute("SELECT candidate_id, first_name, last_name FROM candidates ORDER BY RANDOM() LIMIT 3")
samples = c.fetchall()
for cand_id, fname, lname in samples:
    c.execute("SELECT COUNT(*) FROM applications WHERE candidate_id=?", (cand_id,))
    apps = c.fetchone()[0]
    c.execute("""SELECT COUNT(*) FROM interviews i 
                 JOIN applications a ON i.application_id = a.application_id
                 WHERE a.candidate_id=?""", (cand_id,))
    ints = c.fetchone()[0]
    c.execute("SELECT stage FROM enrolments WHERE candidate_id=?", (cand_id,))
    stage_row = c.fetchone()
    stage = stage_row[0] if stage_row else "NOT IN ENROLMENTS"
    print(f"  {fname} {lname}: stage={stage}, apps={apps}, interviews={ints}")

# 6. Interview status distribution
print("\n[6] INTERVIEW STATUS DISTRIBUTION")
c.execute("""SELECT interview_status, COUNT(*) as cnt FROM interviews 
             GROUP BY interview_status ORDER BY cnt DESC""")
for row in c.fetchall():
    print(f"  {str(row[0]):35s}: {row[1]}")

# 7. Check if any candidate has interviews but no applications
print("\n[7] INTERVIEWS WITHOUT MATCHING APPLICATION (data gap)")
c.execute("""SELECT COUNT(DISTINCT a.candidate_id) 
             FROM applications a
             JOIN interviews i ON i.application_id = a.application_id
             WHERE a.candidate_id NOT IN (SELECT candidate_id FROM candidates)""")
print(f"  Interviews linked to non-existent candidates: {c.fetchone()[0]}")

# 8. Enrolment stage vs candidate stage consistency
print("\n[8] HIRED IN ENROLMENT BUT NOT 'Hired' IN CANDIDATES")
c.execute("""SELECT e.first_name || ' ' || e.last_name, e.stage, c.candidate_stage
             FROM enrolments e
             JOIN candidates c ON e.candidate_id = c.candidate_id
             WHERE e.stage = 'Hired' AND c.candidate_stage != 'Hired'""")
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"  {r[0]}: enrolment='{r[1]}', candidate_stage='{r[2]}'")
else:
    print("  All 'Hired' enrolments match candidate stage ✓")

# 9. Applications with no interviews at all
print("\n[9] CANDIDATES WHO APPLIED BUT WERE NEVER INTERVIEWED")
c.execute("""SELECT c.first_name || ' ' || c.last_name, COUNT(DISTINCT a.application_id)
             FROM candidates c
             JOIN applications a ON c.candidate_id = a.candidate_id
             LEFT JOIN interviews i ON i.application_id = a.application_id
             WHERE i.interview_id IS NULL
             GROUP BY c.candidate_id
             ORDER BY 2 DESC LIMIT 5""")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} applications, 0 interviews")

# 10. Batch name consistency across tables
print("\n[10] DISTINCT BATCH NAMES PER TABLE")
for t in ['enrolments', 'candidates', 'applications', 'interviews']:
    c.execute(f"SELECT COUNT(DISTINCT batch_name) FROM {t}")
    print(f"  {t}: {c.fetchone()[0]} distinct batches")

conn.close()
print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
