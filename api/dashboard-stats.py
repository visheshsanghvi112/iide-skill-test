from http.server import BaseHTTPRequestHandler
import sqlite3
import json
import os
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'placement_analytics_task', 'placement.db')

def query_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM enrolments;")
    total_registered = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM candidates;")
    total_eligible = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT candidate_id) FROM applications;")
    total_applied = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT a.candidate_id) FROM interviews i JOIN applications a ON i.application_id = a.application_id;")
    total_interviewed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM enrolments WHERE stage = 'Hired';")
    total_placed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM job_openings;")
    total_jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM job_openings WHERE job_opening_status = 'In-progress';")
    active_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT e.first_name || ' ' || e.last_name as name,
               e.candidate_id, e.stage,
               COUNT(DISTINCT a.application_id) as app_count,
               COUNT(DISTINCT i.interview_id) as interview_count
        FROM enrolments e
        LEFT JOIN candidates c ON e.candidate_id = c.candidate_id
        LEFT JOIN applications a ON c.candidate_id = a.candidate_id
        LEFT JOIN interviews i ON i.application_id = a.application_id
        WHERE e.stage = 'Hired'
        GROUP BY e.candidate_id, name, e.stage
        HAVING COUNT(DISTINCT a.application_id) = 0 OR COUNT(DISTINCT i.interview_id) = 0
        ORDER BY app_count ASC;
    """)
    discrepancies = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM interviews WHERE interview_status IS NULL;")
    null_interview_status = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM enrolments e
        JOIN candidates c ON e.candidate_id = c.candidate_id
        WHERE e.stage = 'Hired' AND c.candidate_stage != 'Hired';
    """)
    stage_mismatch_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM enrolments WHERE stage = 'Knocked Off' AND knocked_off_reason IS NULL;")
    ko_no_reason = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM candidates WHERE preferred_job_location IS NULL;")
    null_location = cursor.fetchone()[0]

    cursor.execute("""
        SELECT c.first_name || ' ' || c.last_name as name,
               COUNT(DISTINCT a.application_id) as app_count,
               COUNT(DISTINCT i.interview_id) as interview_count
        FROM candidates c
        JOIN applications a ON c.candidate_id = a.candidate_id
        LEFT JOIN interviews i ON i.application_id = a.application_id
        WHERE i.interview_id IS NULL
        GROUP BY c.candidate_id ORDER BY app_count DESC LIMIT 6;
    """)
    neglected_candidates = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT knocked_off_reason, COUNT(*) as count FROM enrolments
        WHERE knocked_off_reason IS NOT NULL AND knocked_off_reason != ''
        GROUP BY knocked_off_reason ORDER BY count DESC;
    """)
    knock_off_reasons = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT cancellation_reason, COUNT(*) as count FROM interviews
        WHERE cancellation_reason IS NOT NULL AND cancellation_reason != ''
        GROUP BY cancellation_reason ORDER BY count DESC;
    """)
    interview_cancellations = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(job_opening_status, 'Unspecified') as status, COUNT(*) as count
        FROM job_openings GROUP BY status ORDER BY count DESC;
    """)
    job_statuses = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(preferred_job_location, 'Not Specified') as location, COUNT(*) as count
        FROM candidates GROUP BY location ORDER BY count DESC;
    """)
    location_dist = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT skill_set FROM candidates WHERE skill_set IS NOT NULL;")
    all_skills = []
    for row in cursor.fetchall():
        all_skills.extend([s.strip() for s in row[0].split(',') if s.strip()])
    skill_counts = [{"skill": k, "count": v} for k, v in Counter(all_skills).most_common(12)]

    cursor.execute("""
        SELECT batch_name,
               COUNT(*) as registered,
               SUM(CASE WHEN candidate_id IS NOT NULL THEN 1 ELSE 0 END) as eligible,
               SUM(CASE WHEN stage = 'Hired' THEN 1 ELSE 0 END) as hired
        FROM enrolments GROUP BY batch_name ORDER BY registered DESC;
    """)
    batch_performance = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(posting_title, 'Not Specified') as role, COUNT(*) as count
        FROM job_openings WHERE job_opening_status = 'In-progress'
        GROUP BY role ORDER BY count DESC LIMIT 8;
    """)
    top_roles = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(interview_status, 'No Status Recorded') as status, COUNT(*) as count
        FROM interviews GROUP BY interview_status ORDER BY count DESC;
    """)
    interview_statuses = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "funnel": {"registered": total_registered, "eligible": total_eligible,
                   "applied": total_applied, "interviewed": total_interviewed, "placed": total_placed},
        "jobs": {"total": total_jobs, "active": active_jobs},
        "data_quality": {"null_interview_status": null_interview_status,
                         "stage_mismatch_count": stage_mismatch_count,
                         "ko_no_reason": ko_no_reason, "null_location": null_location},
        "discrepancies": discrepancies,
        "neglected_candidates": neglected_candidates,
        "knock_off_reasons": knock_off_reasons,
        "interview_cancellations": interview_cancellations,
        "job_statuses": job_statuses,
        "location_dist": location_dist,
        "skill_counts": skill_counts,
        "batch_performance": batch_performance,
        "top_roles": top_roles,
        "interview_statuses": interview_statuses
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = query_db()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            error = json.dumps({"error": str(e)}).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error)

    def log_message(self, format, *args):
        pass  # suppress default request logging
