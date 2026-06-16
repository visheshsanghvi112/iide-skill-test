# Step-by-Step Zoho Analytics Implementation Guide

This guide provides the exact steps, SQL queries, and chart configurations to replicate our placement analytics dashboard directly in Zoho Analytics.

---

## Step 1: Import the CSVs into Zoho Analytics

Create a new workspace in Zoho Analytics (e.g., **Placement Analytics**) and import your 5 CSV files from the raw data folder:

1. **Enrolments**: Import `Skill Test - Database-Enrolments.csv` as table `Enrolments`.
2. **Candidates**: Import `Skill Test - Database-Candidates.csv` as table `Candidates`.
3. **Job Openings**: Import `Skill Test - Database-Job Openings.csv` as table `JobOpenings`.
4. **Applications**: Import `Skill Test - Database-Applications.csv` as table `Applications`.
5. **Interviews**: Import `Skill Test - Database-Interviews.csv` as table `Interviews`.

> [!IMPORTANT]
> **Data Type Override during Import**:
> During the import wizard, check the column datatypes for all identifier fields:
> * In **Enrolments**: Set `CandidateId` and `Record Id` to **Plain Text**.
> * In **Candidates**: Set `Candidate Id` to **Plain Text**.
> * In **Applications**: Set `Application Id`, `Candidate Id`, and `Job Opening Id` to **Plain Text**.
> * In **JobOpenings**: Set `Job Opening Id` to **Plain Text**.
> * In **Interviews**: Set `Interview Id`, `Candidate Id`, and `Job Opening Id` to **Plain Text**.
>
> *This prevents Zoho from converting these 18-digit IDs to scientific numbers and losing precision.*

---

## Step 2: Create SQL Query Tables

Zoho Analytics allows you to write SQL queries to merge your data tables. In your workspace, click **Create** $\rightarrow$ **New Query Table** to build the following 3 reports:

### Query Table A: Placement Funnel Stats
This calculates the candidate conversion rates for each step of the pipeline.
```sql
SELECT 
    (SELECT COUNT(*) FROM "Enrolments") as "Registered",
    (SELECT COUNT(*) FROM "Candidates") as "Eligible",
    (SELECT COUNT(*) FROM "Applications") as "Applied",
    (SELECT COUNT(DISTINCT "application_id") FROM "Interviews") as "Interviewed",
    (SELECT COUNT(*) FROM "Enrolments" WHERE "stage" = 'Hired') as "Placed"
```

### Query Table B: Recruiter Compliance Discrepancy Audit
This identifies candidates who are marked as "Hired" but lack complete workflows (missing applications or missing updates).
```sql
SELECT 
    e."first_name" || ' ' || e."last_name" as "StudentName",
    e."stage" as "EnrolmentStage",
    COUNT(a."application_id") as "ApplicationsCount",
    COUNT(i."interview_id") as "InterviewsCount"
FROM "Enrolments" e
LEFT JOIN "Candidates" c ON e."candidate_id" = c."candidate_id"
LEFT JOIN "Applications" a ON c."candidate_id" = a."candidate_id"
LEFT JOIN "Interviews" i ON a."application_id" = i."application_id"
WHERE e."stage" = 'Hired'
GROUP BY 
    "StudentName", 
    "EnrolmentStage"
HAVING 
    COUNT(a."application_id") = 0 
    OR COUNT(i."interview_id") = 0
```

### Query Table C: Interview Cancellations Analysis
This extracts the reasons and counts for cancelled rounds.
```sql
SELECT 
    "cancellation_reason" as "CancellationReason",
    COUNT("interview_id") as "CancelledCount"
FROM "Interviews"
WHERE "interview_status" = 'Cancelled' 
  AND "cancellation_reason" IS NOT NULL
GROUP BY "CancellationReason"
ORDER BY "CancelledCount" DESC
```

---

## Step 3: Create the Dashboard Visualizations

Click **Create** $\rightarrow$ **New Chart** or **New Dashboard** to construct the layout:

### 1. KPI Cards (Widgets)
Create 3 numerical KPI widgets using the **Placement Funnel Stats** query table:
* **Total Registered**: Field: `Registered` (Summary Type: Sum).
* **Placement Eligible**: Field: `Eligible` (Summary Type: Sum).
* **Placed**: Field: `Placed` (Summary Type: Sum).

### 2. Funnel Chart (Stage Conversion)
* **Type**: Horizontal or Vertical Bar Chart.
* **X-Axis**: Drag in the stage names manually (or create a custom series using custom columns: Registered $\rightarrow$ Eligible $\rightarrow$ Applied $\rightarrow$ Interviewed $\rightarrow$ Placed).
* **Y-Axis**: Count of candidates.

### 3. Interview Cancellations Bar Chart
* **Source Table**: `Query Table C: Interview Cancellations Analysis`
* **Type**: Horizontal Bar Chart.
* **X-Axis**: `CancelledCount`.
* **Y-Axis**: `CancellationReason`.

### 4. Recruiter Discrepancy Audit Table
* **Type**: Tabular View.
* **Columns**: Drag in `StudentName`, `EnrolmentStage`, `ApplicationsCount`, and `InterviewsCount` from `Query Table B`.
* This will display the exact candidates (like Naomi Bennett, Eva Hughes, Madison Young) who were marked "Hired" but have no applications/interviews logged.
