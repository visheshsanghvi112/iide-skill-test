# Placement & Data Analytics — Skill Test Submission

---

## Executive Summary

This submission designs a normalized relational database for the five placement datasets and outlines an executive dashboard built in Zoho Analytics to monitor placement performance and identify bottlenecks.

**Data quality note:** Candidate IDs are 18-digit values that spreadsheet tools silently truncate when read as numbers (e.g. `159941000007258288` becomes `159941000007258272`). All ID fields were treated as text throughout to preserve referential integrity across every join.

---

## Question 1: Data Architecture & Relational Schema Design

### Approach

The placement process follows a natural lifecycle:

**Enrollment → Candidate Eligibility → Job Application → Interview Process → Hiring Outcome**

The five datasets were normalized into a Third Normal Form (3NF) relational schema — every fact stored once, no redundant columns, referential integrity enforced via foreign keys.

The source workbook includes both raw DUMP exports and cleaned tabs for each entity. The DUMP tabs served as the ingestion source, with type validation, null handling, and ID standardization applied programmatically. Raw files were never modified.

---

### Entity Relationships

```
ENROLMENTS
└── candidate_id  ──► CANDIDATES (nullable FK — not all enrolled students become candidates)
                           │
                           └── candidate_id ──► APPLICATIONS ◄── job_opening_id ──  JOB OPENINGS
                                                      │
                                                      └── application_id ──► INTERVIEWS
```

| Relationship | Cardinality |
|:---|:---|
| Enrolments → Candidates | 1 : 0..1 |
| Candidates → Applications | 1 : N |
| Job Openings → Applications | 1 : N |
| Applications → Interviews | 1 : N |

---

### Schema Summary

| Table | Primary Key | Foreign Keys | Purpose |
|:---|:---|:---|:---|
| `enrolments` | `enrolment_id` | `candidate_id → candidates` (nullable) | Master student intake |
| `candidates` | `candidate_id` | — | Placement-eligible subset |
| `job_openings` | `job_opening_id` | — | Corporate job postings |
| `applications` | `application_id` | `candidate_id`, `job_opening_id` | Candidate-to-job mapping (junction table) |
| `interviews` | `interview_id` | `application_id` | Interview rounds per application |

---

### Key Design Decisions

**Separate Enrolments and Candidates**
66% of enrolled students (75 of 113) have no candidate profile — they are early-stage or ineligible. Merging both entities into one table would mean leaving placement columns NULL for the majority of rows. Keeping them separate preserves clean business logic.

**Applications as a junction table**
A candidate can apply to multiple job openings; a job can receive applications from multiple candidates. Applications resolves this M:N relationship and provides an anchor for application-specific attributes (stage, status, timestamp).

**Interviews linked to application_id, not candidate_id**
The source CSV linked interviews directly to `Candidate Id + Job Opening Id`, with no `Application Id` reference. This was corrected — interviews are logically children of a specific application, not of a candidate in isolation. The missing FK was resolved at ingestion via a lookup join on `(candidate_id, job_opening_id)`.

**3NF fix on Applications**
The raw Applications CSV duplicated candidate name, email, and phone in every row (782 rows × 4 columns = 3,128 redundant cells). These were removed from the schema and fetched via JOIN when needed.

**Text-based identifiers**
All IDs stored as VARCHAR. Prevents precision loss from Zoho Recruit's 18-digit numeric identifiers.

---

### Query Performance

Indexes created on all foreign key columns: `candidate_id`, `job_opening_id`, `application_id`, `enrolment_id`. These directly improve dashboard query response times on filtered and joined reports.

---

### Sample SQL Queries

**Placement Rate by Batch**
```sql
SELECT
    batch_name,
    COUNT(*) AS total_students,
    SUM(CASE WHEN stage = 'Hired' THEN 1 ELSE 0 END) AS hired,
    ROUND(SUM(CASE WHEN stage = 'Hired' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS placement_rate_pct
FROM enrolments
GROUP BY batch_name
ORDER BY placement_rate_pct DESC;
```

**Placement Activity Overview**
```sql
SELECT 'Enrollments'          AS stage, COUNT(*) AS total FROM enrolments
UNION ALL
SELECT 'Eligible Candidates',           COUNT(*)           FROM candidates
UNION ALL
SELECT 'Applications',                  COUNT(*)           FROM applications
UNION ALL
SELECT 'Interviews',                    COUNT(*)           FROM interviews;
```

**Interview Outcome Breakdown**
```sql
SELECT interview_status, COUNT(*) AS count
FROM interviews
WHERE interview_status IS NOT NULL
GROUP BY interview_status
ORDER BY count DESC;
```

**Knock-Off Reason Analysis**
```sql
SELECT knocked_off_reason, COUNT(*) AS students_affected
FROM enrolments
WHERE stage = 'Knocked Off' AND knocked_off_reason IS NOT NULL
GROUP BY knocked_off_reason
ORDER BY students_affected DESC;
```

---

## Question 2: Dashboard Visualization & Executive Insights

### Implementation

The dashboard was built in **Zoho Analytics** by ingesting the five CSV files, creating joins via **Query Tables**, and building visual reports and KPI widgets. The relational structure from Question 1 is reflected directly in the query layer.

---

### KPI Cards

| Metric | Value |
|:---|:---|
| Total Enrolled Students | 113 |
| Eligible Candidates | 38 |
| Total Applications | 782 |
| Interviews Conducted | 121 |
| Active Job Openings | 289 (of 7,708 historical) |
| Placement Rate | 14.16% |

> Active Job Openings shows only *In-progress* postings. 96.3% of the 7,708 total records are historical (Cancelled, Inactive, Filled) — surfacing the raw total as a KPI would mislead stakeholders.

---

### Visualizations

**Placement Activity Overview**
Shows candidate volume at each lifecycle stage. Applications (782) exceed candidate count (38) because one candidate can apply to multiple roles — this is an activity volume view, not a linear conversion funnel.

**Placement Rate by Batch**
Compares hired-to-enrolled ratios across cohorts to identify which batches are performing best.

**Interview Outcome Distribution**
Breaks down interview results: Hired, Rejected, Cancelled, Move to Next Round, On Hold, Rescheduled. Key finding: 67 of 121 rounds were cancelled (55.4%) — "Candidate not available" and "No response" are the primary bottlenecks.

**Candidate Stage Distribution**
Live view of where candidates currently sit in the pipeline (New, Available, Engaged, Hired, Rejected).

**Knock-Off Analysis**
Shows the most common reasons students exited before placement: Dropout, No Response, Health/Personal Reason.

**Candidate Location & Job Type Distribution**
Geographic spread of candidates and breakdown of role types (Full Time, Internship, PPO).

**Top Candidate Skills**
Extracted from the skill set field. Top skills: Google Ads, eMarketing, SEO, Keyword Research, Canva, Content Strategy.

**Recruiter Compliance Audit**
Flags candidates marked *Hired* in Enrolments with incomplete recruiter trails:
- 3 candidates hired with zero applications or interviews logged (off-platform placements)
- 3 candidates with applications submitted but zero interviews recorded

---

### Business Value

The schema and dashboard together give the placement team a single, reliable source of truth — accurate KPIs, clear pipeline visibility, and surfaced bottlenecks — without the noise of 7,708 historical job records inflating the numbers.
