# Data Quality Report — Campus Placement Database
### Source: 5 raw CSV files from Zoho Recruit export
### Purpose: Complete field-by-field inconsistency log for manual or automated data cleaning

> **Raw files are NEVER modified.** This report describes what exists in the original CSVs so that a data cleaning agent or person knows exactly what to fix, where, and why.

---

## How to Read This Report

Each issue has:
- **What**: Exact description of the problem
- **Count**: How many rows are affected
- **Affected Rows**: Exact record IDs or values (where feasible)
- **Cleaning Action**: What a cleaning agent should do to fix it
- **Risk if Ignored**: What breaks downstream if left unfixed

---

## CSV 1: Enrolments (`Skill Test - Database-Enrolments.csv`)
**Total rows: 113 | Columns: 20**

---

### Issue E-1: Missing `CandidateId` (66% of rows)

- **What**: 75 out of 113 enrolment rows have a completely empty `CandidateId` field. These students exist in the enrolments tracking system but have not yet been profiled/moved into the Candidates table.
- **Count**: 75 rows
- **Why it happens**: Enrolments is a master intake list. Not all enrolled students graduate to "Candidate" status — some are still in early stages, on hold, or knocked off before being assessed.
- **Stage breakdown of missing CandidateId rows**:
  - Most are in stages like `Initiate Placement`, `Not Eligible for Placement Outreach`, `On Hold`, `Knocked Off`
  - 6 of the `Hired` stage rows DO have a CandidateId — so those are correctly linked
- **Cleaning Action**:
  - ✅ **Do NOT delete** these rows — they represent real students
  - If backfilling: look up the student by `Email` in the Candidates CSV to find the matching `Candidate Id` and fill it in
  - If no match exists in Candidates: the student has not been profiled yet — leave `CandidateId` as NULL
- **Risk if Ignored**: Joins between Enrolments and Candidates will miss 75 students. Funnel analytics will be incomplete.

---

### Issue E-2: `Stage = 'Knocked Off'` but `Knocked Off Reason` is NULL (1 row)

- **What**: Exactly 1 student is marked as knocked off the program but no reason was recorded.
- **Count**: 1 row
- **Affected Row**:
  - Identify via: `SELECT * FROM enrolments WHERE stage = 'Knocked Off' AND knocked_off_reason IS NULL`
- **Valid Reason Values** (from rest of dataset): `Dropout`, `Health / Personal Reason`, `Low Academic Course`, `No Response`
- **Cleaning Action**:
  - Contact the enrolment owner listed in the `Enrolment Owner` field for that record
  - Fill in one of the 4 valid reasons above based on actual circumstance
  - Or add a new reason `Unknown / Not Recorded` if undetermined
- **Risk if Ignored**: Knock-off reason analytics will under-count by 1. Minor impact but shows a data entry gap in process.

---

### Issue E-3: `Stage = 'Hired'` but `CandidateId` links to a candidate whose `Candidate Stage` ≠ `Hired` (5 students)

- **What**: 5 students are marked `Hired` in Enrolments but the corresponding Candidates table still shows them as `Available` or `New`. The two systems are out of sync.
- **Count**: 5 rows
- **Affected students** (Candidate Id → Current Candidate Stage):
  | Candidate Id | Name | Current Candidate Stage |
  |:---|:---|:---|
  | 159941000009047263 | Eva Hughes | New |
  | 159941000008918944 | Naomi Bennett | New |
  | 159941000008437005 | Madison Young | New |
  | 159941000008053079 | Abigail Sanchez | Available |
  | 159941000007163217 | Henry Gonzalez | Available |
- **Cleaning Action**:
  - Update `Candidate Stage` to `Hired` in the Candidates CSV for all 5 above
  - These are legitimate hires — the Candidates table was simply not updated when the Enrolment stage was set
- **Risk if Ignored**: Candidate stage reports will show these 5 as active/available when they are already placed. Misleads active pipeline view.

---

## CSV 2: Candidates (`Skill Test - Database-Candidates.csv`)
**Total rows: 38 | Columns: 16**

---

### Issue C-1: `Preferred Job Location` is NULL (34% of candidates)

- **What**: 13 of 38 candidates have no value for `Preferred Job Location`. The only valid values in this field are `On Site / Work from office` and `Remote`.
- **Count**: 13 rows
- **Affected candidates**:
  | Candidate Id | Name | Batch Name |
  |:---|:---|:---|
  | *(run: `SELECT candidate_id, first_name, last_name FROM candidates WHERE preferred_job_location IS NULL`)* | | |
- **Cleaning Action**:
  - Add this field to the candidate intake form going forward
  - For existing records: contact candidates to fill in preference, or default to `On Site / Work from office` if office-based training was completed
- **Risk if Ignored**: Location-preference pie chart will only reflect 25/38 candidates (65.7% coverage). Filtering candidates by location type will miss 34%.

---

### Issue C-2: `Skill Set` is a comma-separated blob (all 38 rows)

- **What**: Every candidate has ALL their skills packed into a single text field as a comma-separated string (e.g., `"Google Ads, SEMrush, Canva, Content Strategy, Social Media Marketing, ..."`). This is not queryable at the individual skill level using standard SQL `GROUP BY`.
- **Count**: 38 rows — structural issue, not a NULL issue
- **Example value**: `"SEMrush, Google Analytics, Client Satisfaction, Microsoft Project, Advertising Strategy, Click-Through Rates, Marketing, Microsoft Teams, Trello, Website Design, Lead Generation, Content Marketing, Management..."`
- **Top 12 individual skills** (extracted by splitting on comma):
  | Skill | Count of candidates who have it |
  |:---|:---|
  | Google Ads | 24 |
  | eMarketing | 23 |
  | Search Engine Optimisation | 19 |
  | Keyword Research | 19 |
  | Marketing | 18 |
  | Canva | 16 |
  | Social Media | 16 |
  | Social Media Marketing | 14 |
  | Content Strategy | 14 |
  | Google Analytics | 14 |
  | Adaptability | 13 |
  | Competitor Analysis | 12 |
- **Cleaning Action**:
  - **Ideal fix**: Normalize into a separate `candidate_skills` table with one row per skill per candidate: `(candidate_id, skill_name)`
  - **Interim fix for SQL**: Use `LIKE '%Google Ads%'` queries — confirmed working approach
  - Do NOT `GROUP BY "Skill Set"` — it gives count = 1 per person since every string is unique
- **Risk if Ignored**: Any SQL-based skill analytics gives nonsense results. Top skills chart cannot be built correctly.

---

## CSV 3: Applications (`Skill Test - Database-Applications.csv`)
**Total rows: 782 | Columns: 12**

---

### Issue A-1: Redundant personal data columns (3NF violation, all 782 rows)

- **What**: The Applications CSV duplicates 4 personal data fields from the Candidates CSV in every single row. This means if a candidate changes their email, it must be updated in 782 places.
- **Count**: 4 columns × 782 rows = 3,128 redundant cells
- **Redundant columns** (all 782 non-null):
  | Column | Should come from | Rows with data |
  |:---|:---|:---|
  | `First Name` | `Candidates.First Name` | 782 |
  | `Last Name` | `Candidates.Last Name` | 782 |
  | `Email` | `Candidates.Email` | 782 |
  | `Phone` | `Candidates.Phone Number` | 782 |
- **Cleaning Action**:
  - Drop these 4 columns from Applications entirely
  - Fetch them via JOIN on `Candidate Id` when needed
  - Before dropping: cross-check that email/name in Applications matches the Candidates record (data drift check)
- **Risk if Ignored**: Data drift — if a candidate updates contact info in Candidates but Applications is not updated, reports pulling from Applications show stale info.

---

### Issue A-2: No `Application Id` column in Interviews CSV (structural)

- **What**: The Interviews CSV does not contain `Application Id`. This means you cannot directly join Interviews → Applications in Zoho or any SQL tool. Interviews only carry `Candidate Id` and `Job Opening Id`.
- **Cleaning Action**:
  - In SQL: join via `candidate_id AND job_opening_id` together (both columns must match)
  - Do NOT join on `Candidate Id` alone — this inflates interview counts since one candidate may have applied to multiple jobs
  - In Zoho Analytics: see the corrected Step 18 SQL in `zoho_analytics_guide.md`
- **Risk if Ignored**: Interview count queries return 0 or grossly inflated numbers depending on join approach.

---

## CSV 4: Interviews (`Skill Test - Database-Interviews.csv`)
**Total rows: 121 | Columns: 14**

---

### Issue I-1: `Interview Status` is NULL (22.3% of rows)

- **What**: 27 of 121 interview records have no status. These are interviews that were scheduled and occurred but the outcome was never entered.
- **Count**: 27 rows (22.3%)
- **Valid status values** (from the other 94 rows): `Cancelled`, `Hired`, `Move to Next Round/Process`, `Needs More Mentoring`, `On-Hold`, `Rejected`, `Rescheduled`
- **Cleaning Action**:
  - Add mandatory `Interview Status` field validation at point of interview scheduling tool
  - For existing 27 rows: contact the `Interview Owner Id` for each record to get actual outcome
  - As a temporary classification: tag them as `Status Unknown / Pending Update`
- **Risk if Ignored**: Interview outcome analytics (pass rate, rejection rate, conversion to hire) are based on only 78% of interviews. Results are skewed.

---

### Issue I-2: No `Application Id` column (structural — same as A-2)

- **What**: The Interviews table links to candidates and jobs directly via `Candidate Id` + `Job Opening Id` — there is no `Application Id` column.
- **Cleaning Action**: Same as Issue A-2. Use dual-column join in all SQL queries.

---

## CSV 5: Job Openings (`Skill Test - Database-Job Openings.csv`)
**Total rows: 7,708 | Columns: 12**

---

### Issue J-1: Massive content-level duplicate job postings

- **What**: The recruiting system (Zoho Recruit) created new job postings for the same role repeatedly, each with a unique `Job Opening Id` but identical content. This is likely caused by the recruiter clicking "Create New" instead of "Re-open" or "Duplicate check" not being enabled in Zoho.
- **Count**: 3,150 rows belong to content-duplicate groups (same Title + City + Job Type)
- **Top duplicate groups** (Title | City | Type → copies):
  | Posting Title | City | Type | Count |
  |:---|:---|:---|:---|
  | Social Media Executive | Mumbai | Full time | **177×** |
  | Social Media Manager | Mumbai | Full time | 94× |
  | Digital Marketing Executive | Mumbai | Full time | 93× |
  | Social Media Intern | Mumbai | Internship | 64× |
  | Social Media Marketing Intern | Mumbai | Internship | 63× |
  | Performance Marketing Executive | Mumbai | Full time | 59× |
  | Digital Marketing Intern | Mumbai | Internship | 43× |
  | Influencer Marketing Executive | Mumbai | Full time | 38× |
  | Social Media Marketing Intern | Mumbai | Full time | 34× |
  | SEO Executive | Mumbai | Full time | 33× |
  | Influencer Marketing Intern | Mumbai | Internship | 31× |
  | Digital Marketing Intern | Mumbai | Full time | 30× |
  | Social Media Internship | Mumbai | Internship | 27× |
  | Marketing Intern | Mumbai | Internship | 25× |
  | Paid Media Executive | Mumbai | Full time | 24× |
- **Cleaning Action**:
  - Enable duplicate detection in Zoho Recruit before creating new postings
  - For deduplication: keep the **most recent `Date Opened`** record for each (Title + City + Job Type) group and mark the rest as `Cancelled`
  - Do NOT hard-delete — historical applications may reference old IDs
- **Risk if Ignored**: KPI showing "7,708 job openings" is misleading. True unique roles are far fewer (~500 estimated). Candidate matching appears inflated.

---

### Issue J-2: 151 fully identical rows (every field same, different ID)

- **What**: 151 job records are 100% identical in ALL content fields — same title, city, province, salary, profile — only the `Job Opening Id` is different. Pure duplicates created by the system.
- **Top fully-identical groups**:
  | Title | City | Province | Salary | Profile | Count |
  |:---|:---|:---|:---|:---|:---|
  | Digital Marketing Executive | Mumbai | Maharashtra | Not Defined | Digital Marketing (All-Rounder) | 11× |
  | Social Media Executive | Mumbai | Maharashtra | Not Defined | Social Media | 9× |
  | Social Media Executive | Mumbai | Maharashtra | 20-30K | Social Media | 9× |
  | Digital Marketing Executive | Mumbai | Maharashtra | 20-30K | Digital Marketing (All-Rounder) | 7× |
  | Social Media Intern | Mumbai | Maharashtra | Not Defined | Social Media | 6× |
  | SEO Executive | Mumbai | Maharashtra | 20-30K | SEO | 6× |
- **Cleaning Action**:
  - Safe to deduplicate: keep 1 row per group (lowest/oldest `Job Opening Id`), mark others `Cancelled`
  - Check that no active applications reference the records being cancelled before doing so

---

### Issue J-3: `City` is NULL (15.4% of rows)

- **What**: 1,188 job postings have no city specified.
- **Count**: 1,188 of 7,708 (15.4%)
- **Sample affected records**:
  | Job Opening Id | Posting Title | Job Type | Status |
  |:---|:---|:---|:---|
  | Zrecruit_159941000009804822 | Account management-Digital Marketing Intern | Internship with PPO | In-progress |
  | Zrecruit_159941000009788381 | Senior Digital Marketing Executive | Full time | Inactive |
  | Zrecruit_159941000009626225 | Junior Meta Media Buyer | Full time | In-progress |
  | Zrecruit_159941000009369796 | Digital Marketing Expert (Performance & Growth) | Full time | In-progress |
  | Zrecruit_159941000009304530 | Growth Generalist- Remote | Full time | Inactive |
- **Cleaning Action**:
  - For roles with `"Remote"` or `"WFH"` in the title: set `City = 'Remote'`
  - For others: contact the `Account Manager Id` to fill in the location
  - Add mandatory city validation in Zoho Recruit job creation form going forward
- **Risk if Ignored**: Location-based job matching fails. Candidate city preference cannot be matched to job city for 15% of roles.

---

### Issue J-4: `Salary` is NULL (21.8% of rows)

- **What**: 1,680 job postings have no salary range.
- **Count**: 1,680 of 7,708 (21.8%)
- **Valid salary values** (from filled records): `5 - 10 K`, `10 - 20 K`, `20 - 30 K`, `30 - 40 K`, `40 - 50 K`, `Not Defined`
- **Sample affected**:
  | Job Opening Id | Title | City | Status |
  |:---|:---|:---|:---|
  | Zrecruit_159941000002425777 | Ad Operations Intern | WFH | Inactive |
  | Zrecruit_159941000002425304 | Social Media Executive | Mumbai | On-Hold |
  | Zrecruit_159941000002425224 | Social Media Executive | Mumbai | Unverified |
- **Cleaning Action**:
  - Add mandatory salary range selection in Zoho Recruit job creation form
  - For existing NULL records: backfill based on role type (e.g., Internship → `5 - 10 K`, Executive → `20 - 30 K`)
  - Or set to `Not Defined` as a catch-all valid value
- **Risk if Ignored**: Salary-based filtering and candidate matching on salary expectations cannot work for 22% of jobs.

---

### Issue J-5: `Posting Title` is NULL (2 rows)

- **What**: 2 job postings have no title at all — they are essentially anonymous entries in the system.
- **Count**: 2 rows
- **Affected records**:
  | Job Opening Id | City | Status |
  |:---|:---|:---|
  | Zrecruit_159941000005509002 | Ghaziabad | On-Hold |
  | Zrecruit_159941000001990650 | Delhi | Cancelled |
- **Cleaning Action**:
  - For `Cancelled` status: safe to archive/ignore
  - For `On-Hold` (Ghaziabad): contact Account Manager Id on that record to fill in the role title
- **Risk if Ignored**: Minor — these 2 rows appear as blank entries in any title-based report.

---

### Issue J-6: `Job Opening Status` is NULL (1 row)

- **What**: 1 job posting has no status at all.
- **Count**: 1 row
- **Cleaning Action**: Set to `Unverified` (matches the pattern of newly created/incomplete postings)
- **Risk if Ignored**: Negligible — 1 row in 7,708.

---

### Issue J-7: Only 3.7% of job openings are active

- **What**: Despite 7,708 total records, only 289 are `In-progress` (actively hiring). The headline KPI of "7,708 Job Openings" covers all historical records.
- **Status breakdown**:
  | Status | Count | % of Total |
  |:---|:---|:---|
  | Cancelled | 2,926 | 37.9% |
  | Unverified | 1,524 | 19.8% |
  | Inactive | 1,005 | 13.0% |
  | Filled | 796 | 10.3% |
  | Declined | 751 | 9.7% |
  | On-Hold | 416 | 5.4% |
  | **In-progress** | **289** | **3.7%** |
  | NULL | 1 | 0.01% |
- **Cleaning Action**:
  - No data cleaning needed — statuses are correct
  - **Dashboard recommendation**: Show `289 active` as the primary KPI, with `7,708 total (historical)` as secondary context
- **Risk if Ignored**: Stakeholders may misread "7,708 openings" as current demand when 96.3% are closed/cancelled.

---

## Cross-Table Issues

---

### Issue X-1: Interviews have no `Application Id` — dual-join required

- **Affects**: Interviews ↔ Applications relationship across all queries
- **What**: The Interviews CSV only has `Candidate Id` and `Job Opening Id`. To get interview counts per application, you must join on BOTH fields:
  ```sql
  LEFT JOIN "Interviews" i 
    ON a."Candidate Id" = i."Candidate Id"
    AND a."Job Opening Id" = i."Job Opening Id"
  ```
- **Wrong approach** (gives broken counts): `JOIN Interviews ON Candidate Id` alone
- **Cleaning Action**: Add an `Application Id` lookup column to Interviews in Zoho Analytics — or use the dual-join SQL in all queries.

---

### Issue X-2: Recruiter Workflow Discrepancies — 6 `Hired` students with incomplete trails

- **What**: 6 students are marked `Hired` in the Enrolments stage but have broken or missing recruiter activity records.
- **Type A — No application or interview at all (3 students)**:
  | Name | Candidate Id | Apps | Interviews |
  |:---|:---|:---|:---|
  | Eva Hughes | 159941000009047263 | 0 | 0 |
  | Madison Young | 159941000008437005 | 0 | 0 |
  | Naomi Bennett | 159941000008918944 | 0 | 0 |
  > These are off-platform placements — hired through a channel not tracked in Zoho Recruit.
- **Type B — Has applications but 0 interviews logged (3 students)**:
  | Name | Candidate Id | Apps | Interviews |
  |:---|:---|:---|:---|
  | Henry Gonzalez | 159941000007163217 | 3 | 0 |
  | Penelope Mitchell | 159941000008075071 | 9 | 0 |
  | Aria Martin | 159941000009280012 | 24 | 0 |
  > Applied through the system, but no interview rounds were ever scheduled or recorded.
- **Cleaning Action**:
  - For Type A: add a note/tag in Enrolments: `Placement Source = Off-Platform`
  - For Type B: check if interviews happened via phone/WhatsApp but were never logged in Zoho Recruit — if so, backfill with a single interview record per application with status `Hired`
- **Risk if Ignored**: Funnel analytics show 0 interviews for hired candidates — undermines the reliability of the entire placement pipeline report.

---

## Summary: Priority Cleaning Order

| Priority | Issue | Effort | Impact |
|:---|:---|:---|:---|
| 🔴 High | J-1: Job opening content duplicates (3,150 rows) | High | KPI accuracy, matching quality |
| 🔴 High | E-3: Candidate Stage not updated for 5 hired students | Low | Stage consistency |
| 🔴 High | X-2: 6 hired students with missing recruiter trail | Medium | Audit compliance |
| 🟡 Medium | I-1: 27 interviews with NULL status | Medium | Interview analytics |
| 🟡 Medium | C-2: Skill Set normalization | High | Skill-based reporting |
| 🟡 Medium | J-3: NULL City (1,188 rows) | High | Location matching |
| 🟡 Medium | J-4: NULL Salary (1,680 rows) | Medium | Salary filtering |
| 🟢 Low | E-1: Missing CandidateId (75 rows) | High (backfill) | Join completeness |
| 🟢 Low | E-2: 1 Knocked Off with no reason | Very Low | Reason analytics |
| 🟢 Low | A-1: Redundant columns in Applications | Medium | Storage/3NF |
| 🟢 Low | J-5/J-6: 2 NULL titles, 1 NULL status | Very Low | Minor display issue |
