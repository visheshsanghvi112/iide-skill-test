import pandas as pd
import glob, os
from collections import Counter

data_dir = glob.glob("Skill Test - Database-Applications - DUMP*")[0]
def load(name): 
    return pd.read_csv(os.path.join(data_dir, name), dtype=str)

results = {}

# ── ENROLMENTS ──────────────────────────────────────────────
df_enrol = load("Skill Test - Database-Enrolments.csv")

# Missing CandidateId - get their names and stages
missing_cid = df_enrol[df_enrol['CandidateId'].isna() | (df_enrol['CandidateId'].str.strip() == '')]
results['enrol_missing_cid'] = missing_cid[['Record Id','First Name','Last Name','Stage','Batch Name']].values.tolist()

# Knocked off with no reason
ko_no_reason = df_enrol[(df_enrol['Stage'] == 'Knocked Off') & (df_enrol['Knocked Off Reason'].isna())]
results['ko_no_reason'] = ko_no_reason[['Record Id','First Name','Last Name','Stage']].values.tolist()

# Stage mismatch: Hired in enrolments
hired_enrol = df_enrol[df_enrol['Stage'] == 'Hired'][['Record Id','First Name','Last Name','CandidateId','Batch Name']].values.tolist()
results['hired_enrol'] = hired_enrol

# ── CANDIDATES ──────────────────────────────────────────────
df_cand = load("Skill Test - Database-Candidates.csv")

# NULL preferred job location
null_loc = df_cand[df_cand['Preferred Job Location'].isna()][['Candidate Id','First Name','Last Name','Batch Name']].values.tolist()
results['cand_null_loc'] = null_loc

# ── INTERVIEWS ──────────────────────────────────────────────
df_int = load("Skill Test - Database-Interviews.csv")

# NULL status
null_status = df_int[df_int['Interview Status'].isna()][['Interview Id','Candidate Id','Job Opening Id','Interview Type','Batch Name']].values.tolist()
results['int_null_status'] = null_status

# ── JOB OPENINGS ────────────────────────────────────────────
df_job = load("Skill Test - Database-Job Openings.csv")

# Content duplicates - top groups
dup_groups = df_job.groupby(['Posting Title','City','Job Type']).filter(lambda x: len(x) > 1)
dup_summary = df_job.groupby(['Posting Title','City','Job Type']).size().reset_index(name='count')
dup_summary = dup_summary[dup_summary['count'] > 1].sort_values('count', ascending=False).head(20)
results['job_dup_groups'] = dup_summary.values.tolist()

# Fully identical rows
dup_full = df_job.groupby(['Posting Title','City','Province','Country','Job Type','Salary','Profile']).filter(lambda x: len(x) > 1)
dup_full_summary = df_job.groupby(['Posting Title','City','Province','Country','Job Type','Salary','Profile']).size().reset_index(name='count')
dup_full_summary = dup_full_summary[dup_full_summary['count'] > 1].sort_values('count', ascending=False).head(15)
results['job_full_dups'] = dup_full_summary.values.tolist()

# NULL salary - sample
null_sal = df_job[df_job['Salary'].isna()][['Job Opening Id','Posting Title','City','Job Opening Status']].head(10).values.tolist()
results['job_null_salary_sample'] = null_sal

# NULL city
null_city = df_job[df_job['City'].isna()][['Job Opening Id','Posting Title','Job Type','Job Opening Status']].head(10).values.tolist()
results['job_null_city_sample'] = null_city

# NULL title
null_title = df_job[df_job['Posting Title'].isna()][['Job Opening Id','City','Job Opening Status']].values.tolist()
results['job_null_title'] = null_title

# Status breakdown
status_breakdown = df_job['Job Opening Status'].value_counts(dropna=False).to_dict()
results['job_status'] = status_breakdown

# Candidate stage mismatch (check against enrolments)
hired_cand_ids = df_enrol[df_enrol['Stage']=='Hired']['CandidateId'].dropna().tolist()
stage_mismatch = df_cand[df_cand['Candidate Id'].isin(hired_cand_ids) & (df_cand['Candidate Stage'] != 'Hired')]
results['stage_mismatch'] = stage_mismatch[['Candidate Id','First Name','Last Name','Candidate Stage']].values.tolist()

# Print all for use in doc writing
import json
print(json.dumps(results, indent=2, default=str))
