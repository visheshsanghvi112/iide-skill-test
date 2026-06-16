from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
from collections import Counter

app = Flask(__name__, static_folder='.')
DB_PATH = os.path.join(os.path.dirname(__file__), 'placement.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory(app.static_folder, 'style.css')

@app.route('/app.js')
def js():
    return send_from_directory(app.static_folder, 'app.js')

@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Funnel Stats
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

    # 2. Job Openings — Active vs Total (audit: only 3.7% are active)
    cursor.execute("SELECT COUNT(*) FROM job_openings;")
    total_jobs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM job_openings WHERE job_opening_status = 'In-progress';")
    active_jobs = cursor.fetchone()[0]

    # 3. Discrepancy Audit — Hired with missing recruiter workflow
    cursor.execute("""
        SELECT e.first_name || ' ' || e.last_name as name,
               e.candidate_id,
               e.stage,
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

    # 4. Data Quality Alerts (from audit findings)
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

    # 5. Neglected Candidates — many apps, zero interviews
    cursor.execute("""
        SELECT c.first_name || ' ' || c.last_name as name,
               COUNT(DISTINCT a.application_id) as app_count,
               COUNT(DISTINCT i.interview_id) as interview_count
        FROM candidates c
        JOIN applications a ON c.candidate_id = a.candidate_id
        LEFT JOIN interviews i ON i.application_id = a.application_id
        WHERE i.interview_id IS NULL
        GROUP BY c.candidate_id
        ORDER BY app_count DESC
        LIMIT 6;
    """)
    neglected_candidates = [dict(row) for row in cursor.fetchall()]

    # 6. Knock-off Reasons
    cursor.execute("""
        SELECT knocked_off_reason, COUNT(*) as count
        FROM enrolments
        WHERE knocked_off_reason IS NOT NULL AND knocked_off_reason != ''
        GROUP BY knocked_off_reason
        ORDER BY count DESC;
    """)
    knock_off_reasons = [dict(row) for row in cursor.fetchall()]

    # 7. Interview Cancellations
    cursor.execute("""
        SELECT cancellation_reason, COUNT(*) as count
        FROM interviews
        WHERE cancellation_reason IS NOT NULL AND cancellation_reason != ''
        GROUP BY cancellation_reason
        ORDER BY count DESC;
    """)
    interview_cancellations = [dict(row) for row in cursor.fetchall()]

    # 8. Job Opening Status breakdown
    cursor.execute("""
        SELECT COALESCE(job_opening_status, 'Unspecified') as status, COUNT(*) as count
        FROM job_openings
        GROUP BY status
        ORDER BY count DESC;
    """)
    job_statuses = [dict(row) for row in cursor.fetchall()]

    # 9. Location preference distribution
    cursor.execute("""
        SELECT COALESCE(preferred_job_location, 'Not Specified') as location, COUNT(*) as count
        FROM candidates
        GROUP BY location
        ORDER BY count DESC;
    """)
    location_dist = [dict(row) for row in cursor.fetchall()]

    # 10. Skill counts (split comma-separated blob in Python)
    cursor.execute("SELECT skill_set FROM candidates WHERE skill_set IS NOT NULL;")
    skills_data = cursor.fetchall()
    all_skills = []
    for row in skills_data:
        skills_list = [s.strip() for s in row[0].split(',') if s.strip()]
        all_skills.extend(skills_list)
    skill_counts = [{"skill": k, "count": v} for k, v in Counter(all_skills).most_common(12)]

    # 11. Batch Performance
    cursor.execute("""
        SELECT
            batch_name,
            COUNT(*) as registered,
            SUM(CASE WHEN candidate_id IS NOT NULL THEN 1 ELSE 0 END) as eligible,
            SUM(CASE WHEN stage = 'Hired' THEN 1 ELSE 0 END) as hired
        FROM enrolments
        GROUP BY batch_name
        ORDER BY registered DESC;
    """)
    batch_performance = [dict(row) for row in cursor.fetchall()]

    # 12. Top Active Job Roles (active only — total is inflated by duplicates)
    cursor.execute("""
        SELECT COALESCE(posting_title, 'Not Specified') as role, COUNT(*) as count
        FROM job_openings
        WHERE job_opening_status = 'In-progress'
        GROUP BY role
        ORDER BY count DESC
        LIMIT 8;
    """)
    top_roles = [dict(row) for row in cursor.fetchall()]

    # 13. Interview Status Breakdown
    cursor.execute("""
        SELECT COALESCE(interview_status, 'No Status Recorded') as status, COUNT(*) as count
        FROM interviews
        GROUP BY interview_status
        ORDER BY count DESC;
    """)
    interview_statuses = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "funnel": {
            "registered": total_registered,
            "eligible": total_eligible,
            "applied": total_applied,
            "interviewed": total_interviewed,
            "placed": total_placed
        },
        "jobs": {
            "total": total_jobs,
            "active": active_jobs
        },
        "data_quality": {
            "null_interview_status": null_interview_status,
            "stage_mismatch_count": stage_mismatch_count,
            "ko_no_reason": ko_no_reason,
            "null_location": null_location
        },
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
    })

@app.route('/api/query', methods=['POST'])
def run_query():
    data = request.json
    query = data.get('query', '').strip()

    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    query_lower = query.lower()
    for verb in ['delete ', 'drop ', 'alter ', 'update ']:
        if verb in query_lower:
            return jsonify({"error": f"Write operations ({verb.strip().upper()}) are disabled in this query editor."}), 403

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = [list(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify({
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            })
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return jsonify({
                "message": "Query executed successfully.",
                "row_count": affected
            })

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    print("Starting Placement Analytics Dashboard Server on http://127.0.0.1:5000...")
    app.run(debug=True, port=5000)
