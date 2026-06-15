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
    # Registered -> Eligible -> Applied -> Interviewed -> Placed
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
    
    # 2. Candidate Placement Discrepancies
    # Hired in Enrolments but no Hired application or zero applications
    cursor.execute("""
        SELECT enrolment_id, first_name || ' ' || last_name as name, candidate_id, stage
        FROM enrolments 
        WHERE stage = 'Hired' AND candidate_id NOT IN (
            SELECT candidate_id FROM applications WHERE application_status = 'Hired' OR application_stage = 'Hired'
        );
    """)
    discrepancies = [dict(row) for row in cursor.fetchall()]
    
    # 3. Knocked Off / Dropout Reasons
    cursor.execute("""
        SELECT knocked_off_reason, COUNT(*) as count 
        FROM enrolments 
        WHERE knocked_off_reason IS NOT NULL AND knocked_off_reason != ''
        GROUP BY knocked_off_reason 
        ORDER BY count DESC;
    """)
    knock_off_reasons = [dict(row) for row in cursor.fetchall()]
    
    # 4. Interview Cancellations
    cursor.execute("""
        SELECT cancellation_reason, COUNT(*) as count 
        FROM interviews 
        WHERE cancellation_reason IS NOT NULL AND cancellation_reason != ''
        GROUP BY cancellation_reason 
        ORDER BY count DESC;
    """)
    interview_cancellations = [dict(row) for row in cursor.fetchall()]
    
    # 5. Job Openings Status
    cursor.execute("""
        SELECT COALESCE(job_opening_status, 'Unspecified') as status, COUNT(*) as count 
        FROM job_openings 
        GROUP BY status 
        ORDER BY count DESC;
    """)
    job_statuses = [dict(row) for row in cursor.fetchall()]
    
    # 6. Demographics
    cursor.execute("SELECT gender, COUNT(*) as count FROM candidates GROUP BY gender;")
    gender_dist = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT COALESCE(preferred_job_location, 'Not Specified') as location, COUNT(*) as count 
        FROM candidates 
        GROUP BY location 
        ORDER BY count DESC;
    """)
    location_dist = [dict(row) for row in cursor.fetchall()]
    
    # 7. Skill Word Cloud Ingestion
    cursor.execute("SELECT skill_set FROM candidates WHERE skill_set IS NOT NULL;")
    skills_data = cursor.fetchall()
    all_skills = []
    for row in skills_data:
        skills_list = [s.strip() for s in row[0].split(',') if s.strip()]
        all_skills.extend(skills_list)
    skill_counts = [{"skill": k, "count": v} for k, v in Counter(all_skills).most_common(20)]
    
    # 8. Batch Performance Metrics
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

    # 9. Top Job Roles Posting Titles
    cursor.execute("""
        SELECT COALESCE(posting_title, 'Not Specified') as role, COUNT(*) as count 
        FROM job_openings 
        GROUP BY role 
        ORDER BY count DESC 
        LIMIT 10;
    """)
    top_roles = [dict(row) for row in cursor.fetchall()]
    
    # 10. Active Account Managers (Top Job Providers)
    cursor.execute("""
        SELECT account_manager_id, COUNT(*) as count 
        FROM job_openings 
        GROUP BY account_manager_id 
        ORDER BY count DESC 
        LIMIT 10;
    """)
    top_account_managers = [dict(row) for row in cursor.fetchall()]

    conn.close()
    
    return jsonify({
        "funnel": {
            "registered": total_registered,
            "eligible": total_eligible,
            "applied": total_applied,
            "interviewed": total_interviewed,
            "placed": total_placed
        },
        "discrepancies": discrepancies,
        "knock_off_reasons": knock_off_reasons,
        "interview_cancellations": interview_cancellations,
        "job_statuses": job_statuses,
        "gender_dist": gender_dist,
        "location_dist": location_dist,
        "skill_counts": skill_counts,
        "batch_performance": batch_performance,
        "top_roles": top_roles,
        "top_account_managers": top_account_managers
    })

@app.route('/api/query', methods=['POST'])
def run_query():
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400
        
    # Security: Limit write operations to protect testing database (optional but nice)
    query_lower = query.lower()
    for verb in ['delete ', 'drop ', 'alter ', 'update ']:
        if verb in query_lower:
            return jsonify({"error": f"Write operations ({verb.strip().upper()}) are disabled in this query editor."}), 403
            
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        # If it's a SELECT query, return rows and columns
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
