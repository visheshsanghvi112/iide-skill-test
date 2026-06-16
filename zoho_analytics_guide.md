# Zoho Analytics — Complete Step-by-Step Dashboard Guide
### Campus Placement Analytics (Question 2 Answer)

> All column names, stage values, and SQL queries in this guide are **verified directly against the raw CSV files**.

---

## Verified Column Reference (from actual CSVs)

| Table | Key Columns |
|:---|:---|
| **Enrolments** | `Record Id`, `First Name`, `Last Name`, `Email`, `Batch Name`, `Stage`, `CandidateId`, `Knocked Off Reason`, `Preferred Job Type`, `Expected Salary` |
| **Candidates** | `Candidate Id`, `First Name`, `Last Name`, `Phone Number`, `Email`, `City`, `Skill Set`, `Candidate Stage`, `Batch Name`, `Preferred Job Location` |
| **Applications** | `Application Id`, `Candidate Id`, `Job Opening Id`, `Posting Title`, `Application Stage`, `Application Status`, `Batch Name` |
| **Interviews** | `Interview Id`, `Candidate Id`, `Job Opening Id`, `Interview Type`, `Interview Status`, `Cancellation Reason`, `Batch Name` *(no Application Id)* |
| **Job Openings** | `Job Opening Id`, `Posting Title`, `Job Opening Status`, `Job Type`, `City`, `Salary`, `Profile` |

### Verified Distinct Values Used in SQL

| Table | Column | Actual Values |
|:---|:---|:---|
| Enrolments | `Stage` | `Hired`, `Initiate Placement`, `Knocked Off`, `Not Eligible for Placement Outreach`, `On Hold`, `Outreach Initiated` |
| Enrolments | `Knocked Off Reason` | `Dropout`, `Health / Personal Reason`, `Low Academic Course`, `No Response` |
| Interviews | `Interview Status` | `Cancelled`, `Hired`, `Move to Next Round/Process`, `Needs More Mentoring`, `On-Hold`, `Rejected`, `Rescheduled` |
| Interviews | `Cancellation Reason` | `Candidate no-show`, `Candidate not available`, `Job opening closed`, `Others` |
| Job Openings | `Job Opening Status` | `In-progress`, `Filled`, `Cancelled`, `Declined`, `Inactive`, `On-Hold`, `Unverified` |
| Candidates | `Preferred Job Location` | `On Site / Work from office`, `Remote` |

---

## PHASE 1: Account & Workspace Setup

### Step 1 — Sign In / Sign Up
1. Go to **[analytics.zoho.com](https://analytics.zoho.com)**
2. Sign in with your Zoho account (or create a free account).
3. You land on the **Zoho Analytics Home** page.

### Step 2 — Create a New Workspace
1. Click the **"+ Create"** button (top-left area of the home page).
2. Select **"New Workspace"**.
3. Name it: `Campus Placement Analytics`
4. Click **Create**.

---

## PHASE 2: Import the 5 CSV Files

> [!IMPORTANT]
> During import, Zoho will auto-detect numeric types. The ID columns are **18-digit numbers** that will be rounded/corrupted if stored as numbers. You MUST manually override them to **Plain Text**.

### Step 3 — Import Enrolments Table
1. Inside your workspace, click **"Import Data"** → **"From a File"** → **"CSV File"**.
2. Upload: `Skill Test - Database-Enrolments.csv`
3. In the **Column Type Configuration** screen:
   - `Record Id` → **Plain Text**
   - `CandidateId` → **Plain Text**
4. Set the table name to: `Enrolments`
5. Click **Import**.

### Step 4 — Import Candidates Table
1. Click **"Import Data"** → CSV.
2. Upload: `Skill Test - Database-Candidates.csv`
3. Column overrides:
   - `Candidate Id` → **Plain Text**
4. Table name: `Candidates` → Click **Import**.

### Step 5 — Import Job Openings Table
1. Click **"Import Data"** → CSV.
2. Upload: `Skill Test - Database-Job Openings.csv`
3. Column overrides:
   - `Job Opening Id` → **Plain Text**
   - `Account Manager Id` → **Plain Text**
4. Table name: `JobOpenings` → Click **Import**.

### Step 6 — Import Applications Table
1. Click **"Import Data"** → CSV.
2. Upload: `Skill Test - Database-Applications.csv`
3. Column overrides:
   - `Application Id` → **Plain Text**
   - `Candidate Id` → **Plain Text**
   - `Job Opening Id` → **Plain Text**
4. Table name: `Applications` → Click **Import**.

### Step 7 — Import Interviews Table
1. Click **"Import Data"** → CSV.
2. Upload: `Skill Test - Database-Interviews.csv`
3. Column overrides:
   - `Interview Id` → **Plain Text**
   - `Candidate Id` → **Plain Text**
   - `Job Opening Id` → **Plain Text**
   - `Client Id` → **Plain Text**
   - `Interview Owner Id` → **Plain Text**
4. Table name: `Interviews` → Click **Import**.

> [!WARNING]
> The **Interviews** table has **NO `Application Id` column**. It links to candidates via `Candidate Id` and to jobs via `Job Opening Id` directly.

---

## PHASE 3: Create Table Relationships (Lookup Columns) — SKIP THIS PHASE

> [!IMPORTANT]
> **You can skip this entire phase.** If Zoho gives you a **"Cyclic Relationship"** error when trying to add a Lookup Column, that's Zoho blocking the direction of the join — it's a known Zoho Analytics limitation.
>
> **Why it doesn't matter:** Every single report and chart in this dashboard is built from **SQL Query Tables** (Phase 4), which write the `JOIN` logic directly in SQL. Zoho's Lookup Column feature is only needed for its basic drag-and-drop auto-join — we are not using that at all.
>
> **Go straight to Phase 4.**

### Why the Cyclic Error Happens (For Reference)
Zoho Analytics prevents you from creating a Lookup Column if it detects that adding the relationship would form a loop between tables (A → B → A). Our 5 tables have a chain structure (`Enrolments → Candidates → Applications → Interviews`) and Zoho can sometimes misread this as cyclic depending on the order you import tables.

Since all our charts use SQL Query Tables with explicit `LEFT JOIN` / `INNER JOIN` statements, Zoho's internal relationship graph is irrelevant — **the SQL handles everything directly**.

---

---

## PHASE 4: Create SQL Query Tables

### Step 13 — Funnel Stats (5 headline KPI numbers)
1. Click **"Create" → "Query Table"** in your workspace.
2. Paste this SQL:

```sql
SELECT 
    (SELECT COUNT(*) FROM "Enrolments") AS "Registered",
    (SELECT COUNT(*) FROM "Candidates") AS "Eligible",
    (SELECT COUNT(*) FROM "Applications") AS "Applied",
    (SELECT COUNT("Interview Id") FROM "Interviews") AS "Interviewed",
    (SELECT COUNT(*) FROM "Enrolments" WHERE "Stage" = 'Hired') AS "Placed"
```

3. Click **Execute Query** — you should see 1 row with 5 numbers.
4. Save as: `Funnel Stats`

### Step 14 — Batch Performance (hired rate per training batch)
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Batch Name",
    COUNT(*) AS "Registered",
    SUM(CASE WHEN "Stage" IN ('Initiate Placement', 'Outreach Initiated', 'Hired') THEN 1 ELSE 0 END) AS "Eligible",
    SUM(CASE WHEN "Stage" = 'Hired' THEN 1 ELSE 0 END) AS "Hired"
FROM "Enrolments"
GROUP BY "Batch Name"
ORDER BY "Hired" DESC
```

3. Execute, verify rows show batch names. Save as: `Batch Performance`

### Step 15 — Interview Cancellations (why rounds are cancelled)
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Cancellation Reason",
    COUNT("Interview Id") AS "CancelledCount"
FROM "Interviews"
WHERE "Interview Status" = 'Cancelled'
  AND "Cancellation Reason" IS NOT NULL
  AND "Cancellation Reason" != ''
GROUP BY "Cancellation Reason"
ORDER BY "CancelledCount" DESC
```

3. Execute — expect 4 rows: `Candidate no-show`, `Candidate not available`, `Job opening closed`, `Others`.
4. Save as: `Cancellation Reasons`

### Step 16 — Knock-off Reasons (why students are removed)
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Knocked Off Reason",
    COUNT("Record Id") AS "Count"
FROM "Enrolments"
WHERE "Stage" = 'Knocked Off'
  AND "Knocked Off Reason" IS NOT NULL
  AND "Knocked Off Reason" != ''
GROUP BY "Knocked Off Reason"
ORDER BY "Count" DESC
```

3. Execute — expect 4 reasons: `No Response`, `Dropout`, `Health / Personal Reason`, `Low Academic Course`.
4. Save as: `Knockoff Reasons`

### Step 17 — Top Skills (from eligible candidates)
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Skill Set" AS "Skill",
    COUNT("Candidate Id") AS "Count"
FROM "Candidates"
WHERE "Skill Set" IS NOT NULL
  AND "Skill Set" != ''
GROUP BY "Skill Set"
ORDER BY "Count" DESC
```

3. Execute, verify results. Save as: `Top Skills`

### Step 18 — Recruiter Discrepancy Audit
*(Hired in Enrolments but no matching applications/interviews)*
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    e."First Name" || ' ' || e."Last Name" AS "Student Name",
    e."Stage" AS "Enrolment Stage",
    COUNT(DISTINCT a."Application Id") AS "Applications Count",
    COUNT(DISTINCT i."Interview Id") AS "Interviews Count"
FROM "Enrolments" e
LEFT JOIN "Candidates" c ON e."CandidateId" = c."Candidate Id"
LEFT JOIN "Applications" a ON c."Candidate Id" = a."Candidate Id"
LEFT JOIN "Interviews" i ON c."Candidate Id" = i."Candidate Id"
WHERE e."Stage" = 'Hired'
GROUP BY "Student Name", "Enrolment Stage"
HAVING COUNT(DISTINCT a."Application Id") = 0
    OR COUNT(DISTINCT i."Interview Id") = 0
```

3. Execute — should return 5 students (Naomi Bennett, Eva Hughes, Madison Young, Henry Gonzalez, Abigail Sanchez).
4. Save as: `Discrepancy Audit`

---

## PHASE 5: Build Individual Charts (Reports)

> Build each chart separately, save it, then add it to the dashboard in Phase 7.

### Step 19 — Funnel Bar Chart
1. Open the **Funnel Stats** query table.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer — this table is a single row with 5 columns. To plot it as a bar chart:
   - Switch chart type to **"Bar Chart"**
   - Add all 5 columns (`Registered`, `Eligible`, `Applied`, `Interviewed`, `Placed`) as separate **Y-Axis** series with a manual X-axis label per series.
4. Save as: `Placement Funnel Chart`

### Step 20 — Batch Grouped Bar Chart
1. Open the **Batch Performance** query table.
2. Click **"Create" → "Chart View"**.
3. Chart Designer:
   - **X-Axis**: `Batch Name`
   - **Y-Axis**: Drag `Registered`, `Eligible`, `Hired` (3 separate series)
4. Change type to **Grouped Bar Chart**.
5. Save as: `Batch Performance Chart`

### Step 21 — Doughnut: Knock-off Reasons
1. Open the **Knockoff Reasons** query table.
2. Click **"Create" → "Chart View"**.
3. Chart Designer:
   - **Color/Slice**: `Knocked Off Reason`
   - **Y-Axis**: `Count`
4. Change type to **Pie** → switch to **Ring** in the toolbar.
5. Save as: `Dropout Reasons Chart`

### Step 22 — Horizontal Bar: Cancellation Reasons
1. Open the **Cancellation Reasons** query table.
2. Click **"Create" → "Chart View"**.
3. Chart Designer:
   - **X-Axis**: `Cancellation Reason`
   - **Y-Axis**: `CancelledCount`
4. Change type to **Bar**, then click **Switch Axes** to make it horizontal.
5. Save as: `Cancellation Reasons Chart`

### Step 23 — Horizontal Bar: Top Skills
1. Open the **Top Skills** query table.
2. Click **"Create" → "Chart View"**.
3. Chart Designer:
   - **X-Axis**: `Skill`
   - **Y-Axis**: `Count`
4. Change type to horizontal **Bar Chart**.
5. Save as: `Top Skills Chart`

### Step 24 — Pie: Preferred Job Location
1. Open the **Candidates** table directly.
2. Click **"Create" → "Chart View"**.
3. Chart Designer:
   - **Color/Slice**: `Preferred Job Location`
   - **Y-Axis**: `Candidate Id` → Aggregate: **Count**
4. Change type to **Pie Chart**.
5. Save as: `Location Preference Chart`

> Expected slices: `On Site / Work from office` and `Remote`

### Step 25 — Table View: Discrepancy Audit
1. Open the **Discrepancy Audit** query table.
2. Click **"Create" → "Pivot / Table View"** → select **Table View**.
3. Drag in columns: `Student Name`, `Enrolment Stage`, `Applications Count`, `Interviews Count`.
4. Save as: `Discrepancy Audit Table`

---

## PHASE 6: Build the KPI Widgets

### Step 26 — Create the Dashboard first
1. Click **"Create" → "Dashboard"**.
2. Name it: `Placement Executive Dashboard`.
3. You are now in the drag-and-drop dashboard builder.

### Step 27 — Total Enrolments KPI
1. In the dashboard editor, click **"Widget"** in the toolbar.
2. Select **"KPI Widget"** → **"Single Number"**.
3. Configure:
   - **Base Table**: `Funnel Stats`
   - **Data Column**: `Registered` | **Aggregate**: Sum
   - **Label**: `Total Enrolments`
4. Click **Apply**.

### Step 28 — Placement Eligible KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. Configure:
   - **Base Table**: `Funnel Stats` | **Column**: `Eligible` | **Aggregate**: Sum
   - **Label**: `Placement Eligible`
3. Click **Apply**.

### Step 29 — Hired & Placed KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. Configure:
   - **Base Table**: `Funnel Stats` | **Column**: `Placed` | **Aggregate**: Sum
   - **Label**: `Hired & Placed`
3. Click **Apply**.

### Step 30 — Total Job Openings KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. Configure:
   - **Base Table**: `JobOpenings` | **Column**: `Job Opening Id` | **Aggregate**: Count
   - **Label**: `Total Job Openings`
3. Click **Apply**.

---

## PHASE 7: Assemble the Dashboard Layout

### Step 31 — Arrange the Layout
In the left **Reports** panel, drag each saved chart onto the canvas:

**Row 1 — KPI strip (4 widgets side by side):**
- `Total Enrolments` | `Placement Eligible` | `Hired & Placed` | `Total Job Openings`

**Row 2 — two columns:**
- Left (2/3 width): `Placement Funnel Chart`
- Right (1/3 width): `Dropout Reasons Chart`

**Row 3 — two columns:**
- Left (2/3 width): `Batch Performance Chart`
- Right (1/3 width): `Cancellation Reasons Chart`

**Row 4 — three columns:**
- `Top Skills Chart` | `Location Preference Chart` | *(leave blank or add a top roles chart)*

**Row 5 — full width:**
- `Discrepancy Audit Table`

### Step 32 — Polish & Save
1. Click any chart title to rename it.
2. Click **"Theme"** in dashboard settings → pick a light corporate palette.
3. Add a **Global Filter** on `Batch Name` (works across all charts).
4. Click **Save** → **Publish** to generate a shareable link.

---

## Quick Reference: All Reports

| Report | Source | Visualisation | What It Shows |
|:---|:---|:---|:---|
| Placement Funnel Chart | Funnel Stats | Bar | Dropout at each stage |
| Batch Performance Chart | Batch Performance | Grouped Bar | Registered vs Eligible vs Hired per batch |
| Dropout Reasons Chart | Knockoff Reasons | Doughnut | Why students are knocked off |
| Cancellation Reasons Chart | Cancellation Reasons | Horizontal Bar | Why interview rounds cancel |
| Top Skills Chart | Top Skills | Horizontal Bar | Most common candidate skills |
| Location Preference Chart | Candidates | Pie | On-site vs Remote preference |
| Discrepancy Audit Table | Discrepancy Audit | Table | Hired students with no application trail |
| KPI Widgets ×4 | Funnel Stats + JobOpenings | Number | Headline metrics |

---

## Troubleshooting

| Problem | Fix |
|:---|:---|
| IDs show as `1.6e+17` | Edit Column → change type to **Plain Text** |
| SQL throws "column not found" | Column names are case-sensitive — copy exact names from the reference table at the top of this guide |
| Knockoff Reasons query returns 0 rows | Make sure the `WHERE` clause uses `'Knocked Off'` exactly (verified stage value) |
| Interviews join returns wrong data | Interviews links via `Candidate Id` and `Job Opening Id` — there is **no** `Application Id` in that table |
| Lookup column gives no matches | Confirm both sides are **Plain Text** type — a Text vs Number mismatch silently produces 0 matches |
| Dashboard charts too small | Drag the corner handles to resize in the dashboard editor |
