# Zoho Analytics — Complete Step-by-Step Dashboard Guide
### Campus Placement Analytics (Question 2 Answer)

This is the exact sequence of steps to replicate our placement analytics dashboard inside Zoho Analytics. Follow each phase in order. No steps are skipped.

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
5. You are now inside your empty workspace. All your tables and dashboards will live here.

---

## PHASE 2: Import the 5 CSV Files

> [!IMPORTANT]
> You must import ALL 5 files below. The order matters because we'll link them together.
> Your CSV files are located in your project folder:
> `d:\iide-skill-test\Skill Test - Database-Applications - DUMP,...`

### Step 3 — Import Enrolments Table
1. Inside your workspace, click **"Import Data"** (or click **Create → Import Data**).
2. Choose **"From a File"** → **"CSV File"**.
3. Upload: `Skill Test - Database-Enrolments.csv`
4. In the **Column Type Configuration** screen that appears:
   - Find `Record Id` → Change type to **Plain Text**
   - Find `CandidateId` (or `Candidate Id`) → Change type to **Plain Text**
5. Set the table name to: `Enrolments`
6. Click **Import**.

### Step 4 — Import Candidates Table
1. Click **Import Data** again.
2. Upload: `Skill Test - Database-Candidates.csv`
3. In Column Type Configuration:
   - Find `Candidate Id` → Change type to **Plain Text**
4. Set the table name to: `Candidates`
5. Click **Import**.

### Step 5 — Import Job Openings Table
1. Click **Import Data** again.
2. Upload: `Skill Test - Database-Job Openings.csv`
3. In Column Type Configuration:
   - Find `Job Opening Id` → Change type to **Plain Text**
4. Set the table name to: `JobOpenings`
5. Click **Import**.

### Step 6 — Import Applications Table
1. Click **Import Data** again.
2. Upload: `Skill Test - Database-Applications.csv`
3. In Column Type Configuration:
   - Find `Application Id` → Change to **Plain Text**
   - Find `Candidate Id` → Change to **Plain Text**
   - Find `Job Opening Id` → Change to **Plain Text**
4. Set the table name to: `Applications`
5. Click **Import**.

### Step 7 — Import Interviews Table
1. Click **Import Data** again.
2. Upload: `Skill Test - Database-Interviews.csv`
3. In Column Type Configuration:
   - Find `Interview Id` → Change to **Plain Text**
   - Find `Candidate Id` → Change to **Plain Text**
   - Find `Job Opening Id` → Change to **Plain Text**
   - Find `Application Id` → Change to **Plain Text**
4. Set the table name to: `Interviews`
5. Click **Import**.

> [!WARNING]
> **CRITICAL — Why Plain Text?**
> The ID columns in these files are 18-digit numbers (e.g. `159941000007258288`).
> If Zoho treats them as numbers, it rounds them to `159941000007258270`, which BREAKS all the joins.
> Setting them to **Plain Text** fixes this completely.

---

## PHASE 3: Create Table Relationships (Lookup Columns)

This step tells Zoho Analytics how the tables are connected to each other — exactly like our relational schema.

### Step 8 — Link Enrolments → Candidates
1. Open the **Enrolments** table (click it from the workspace).
2. In the toolbar at the top, click **"Add" → "Lookup Column"**.
3. In the dialog that opens:
   - **Column Name**: `Candidate Name Lookup`
   - **Select Table**: `Candidates`
   - **Lookup Column**: `Candidate Id`
   - **Referenced Column in Enrolments**: `CandidateId`
4. Click **Save**.

### Step 9 — Link Candidates → Applications
1. Open the **Applications** table.
2. Click **"Add" → "Lookup Column"**.
3. In the dialog:
   - **Column Name**: `Candidate Lookup`
   - **Select Table**: `Candidates`
   - **Lookup Column**: `Candidate Id`
   - **Referenced Column in Applications**: `Candidate Id`
4. Click **Save**.

### Step 10 — Link JobOpenings → Applications
1. Stay in the **Applications** table.
2. Click **"Add" → "Lookup Column"** again.
3. In the dialog:
   - **Column Name**: `Job Opening Lookup`
   - **Select Table**: `JobOpenings`
   - **Lookup Column**: `Job Opening Id`
   - **Referenced Column in Applications**: `Job Opening Id`
4. Click **Save**.

### Step 11 — Link Applications → Interviews
1. Open the **Interviews** table.
2. Click **"Add" → "Lookup Column"**.
3. In the dialog:
   - **Column Name**: `Application Lookup`
   - **Select Table**: `Applications`
   - **Lookup Column**: `Application Id`
   - **Referenced Column in Interviews**: `Application Id`
4. Click **Save**.

> [!NOTE]
> After setting up Lookup Columns, Zoho Analytics will **auto-join** these tables whenever you build a report — you won't need to write JOINs manually for basic charts.

---

## PHASE 4: Create SQL Query Tables (For Complex Analytics)

Some of our charts need custom calculations. For these we use **Query Tables**.

### Step 12 — Create the Funnel Stats Query Table
1. In your workspace, click **"Create" → "Query Table"**.
2. A SQL editor opens. Paste this SQL:

```sql
SELECT 
    (SELECT COUNT(*) FROM "Enrolments") as "Registered",
    (SELECT COUNT(*) FROM "Candidates") as "Eligible",
    (SELECT COUNT(*) FROM "Applications") as "Applied",
    (SELECT COUNT(DISTINCT "Application Id") FROM "Interviews") as "Interviewed",
    (SELECT COUNT(*) FROM "Enrolments" WHERE "Stage" = 'Hired') as "Placed"
```

3. Click **"Execute Query"** — verify you see 5 columns with numbers.
4. Click **Save** and name it: `Funnel Stats`

### Step 13 — Create the Batch Performance Query Table
1. Click **"Create" → "Query Table"** again.
2. Paste this SQL:

```sql
SELECT 
    e."Batch Name",
    COUNT(*) as "Registered",
    SUM(CASE WHEN e."Stage" = 'Placement Eligible' OR e."Stage" = 'Hired' THEN 1 ELSE 0 END) as "Eligible",
    SUM(CASE WHEN e."Stage" = 'Hired' THEN 1 ELSE 0 END) as "Hired",
    ROUND(100.0 * SUM(CASE WHEN e."Stage" = 'Hired' THEN 1 ELSE 0 END) / COUNT(*), 1) as "PlacedPercent"
FROM "Enrolments" e
GROUP BY e."Batch Name"
ORDER BY "Hired" DESC
```

3. Click **Execute Query**, verify it returns batch-wise rows.
4. Save as: `Batch Performance`

### Step 14 — Create the Interview Cancellations Query Table
1. Click **"Create" → "Query Table"**.
2. Paste this SQL:

```sql
SELECT 
    "Cancellation Reason",
    COUNT("Interview Id") as "CancelledCount"
FROM "Interviews"
WHERE "Interview Status" = 'Cancelled' 
  AND "Cancellation Reason" IS NOT NULL
  AND "Cancellation Reason" != ''
GROUP BY "Cancellation Reason"
ORDER BY "CancelledCount" DESC
```

3. Execute, verify, and Save as: `Cancellation Reasons`

### Step 15 — Create the Recruiter Discrepancy Audit Query Table
1. Click **"Create" → "Query Table"**.
2. Paste this SQL:

```sql
SELECT 
    e."First Name" || ' ' || e."Last Name" as "Student Name",
    e."Stage" as "Enrolment Stage",
    COUNT(a."Application Id") as "Applications Count",
    COUNT(i."Interview Id") as "Interviews Count"
FROM "Enrolments" e
LEFT JOIN "Candidates" c ON e."CandidateId" = c."Candidate Id"
LEFT JOIN "Applications" a ON c."Candidate Id" = a."Candidate Id"
LEFT JOIN "Interviews" i ON a."Application Id" = i."Application Id"
WHERE e."Stage" = 'Hired'
GROUP BY "Student Name", "Enrolment Stage"
HAVING COUNT(a."Application Id") = 0 OR COUNT(i."Interview Id") = 0
```

3. Execute, verify (should show 5 students like Naomi Bennett, Eva Hughes, Madison Young).
4. Save as: `Discrepancy Audit`

### Step 16 — Create the Knock-off Reasons Query Table
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Knocked Off Reason",
    COUNT("Record Id") as "Count"
FROM "Enrolments"
WHERE "Knocked Off Reason" IS NOT NULL 
  AND "Knocked Off Reason" != ''
GROUP BY "Knocked Off Reason"
ORDER BY "Count" DESC
```

3. Execute, verify, Save as: `Knockoff Reasons`

### Step 17 — Create the Top Skills Query Table
1. Click **"Create" → "Query Table"**.
2. Paste:

```sql
SELECT 
    "Skill Set" as "Skill",
    COUNT("Candidate Id") as "Count"
FROM "Candidates"
WHERE "Skill Set" IS NOT NULL AND "Skill Set" != ''
GROUP BY "Skill Set"
ORDER BY "Count" DESC
LIMIT 10
```

3. Execute, verify, Save as: `Top Skills`

---

## PHASE 5: Build Individual Charts (Reports)

Each chart below is built as a **Report** first. You'll then drag them all onto the Dashboard in Phase 6.

### Step 18 — Funnel Bar Chart (Placement Ingestion)
1. Open the **Funnel Stats** query table.
2. Click **"Create" → "Chart View"** in the top toolbar.
3. In the **Chart Designer**:
   - This table has 5 columns (`Registered`, `Eligible`, `Applied`, `Interviewed`, `Placed`).
   - Since this is aggregated data (single row), you'll display it as a bar chart manually.
   - Drag each column value to the Y-Axis (you may need to create a **Pivot Table** or use multiple series).
   - **Alternative approach**: Change chart type to **Bar Chart**, select all 5 columns as Y-Axis series.
4. Change chart type to **"Bar Chart"** using the chart icons in the top-right toolbar.
5. Customize colors to match each stage (blue → cyan → green → orange → red).
6. Click **Save**, name it: `Placement Funnel Chart`

### Step 19 — Batch Performance Grouped Bar Chart
1. Open the **Batch Performance** query table.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer:
   - **X-Axis**: Drag `Batch Name`
   - **Y-Axis**: Drag `Registered`, `Eligible`, `Hired` (3 series = grouped bars)
4. Change chart type to **"Grouped Bar Chart"**.
5. Click **Save**, name it: `Batch Performance Chart`

### Step 20 — Doughnut Chart: Knock-off Reasons
1. Open the **Knockoff Reasons** query table.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer:
   - **Color (Legend)**: Drag `Knocked Off Reason`
   - **Y-Axis**: Drag `Count`
4. Change chart type to **"Pie Chart"** then switch to **"Ring/Doughnut"** using the chart type toolbar.
5. Click **Save**, name it: `Dropout Reasons Chart`

### Step 21 — Horizontal Bar Chart: Cancellation Reasons
1. Open the **Cancellation Reasons** query table.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer:
   - **X-Axis**: Drag `Cancellation Reason`
   - **Y-Axis**: Drag `CancelledCount`
4. Change chart type to **"Bar Chart"** and then flip to horizontal by clicking the **"Switch Axes"** button.
5. Click **Save**, name it: `Cancellation Reasons Chart`

### Step 22 — Bar Chart: Top Candidate Skills
1. Open the **Top Skills** query table.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer:
   - **X-Axis**: Drag `Skill`
   - **Y-Axis**: Drag `Count`
4. Change chart type to **"Bar Chart"** (horizontal).
5. Click **Save**, name it: `Top Skills Chart`

### Step 23 — Pie Chart: Preferred Job Location
1. Open the **Candidates** table directly.
2. Click **"Create" → "Chart View"**.
3. In Chart Designer:
   - **Color (Legend)**: Drag `Preferred Job Location`
   - **Y-Axis**: Drag `Candidate Id` → set Aggregate to **Count**
4. Change chart type to **"Pie Chart"**.
5. Click **Save**, name it: `Location Preference Chart`

### Step 24 — Table View: Recruiter Discrepancy Audit
1. Open the **Discrepancy Audit** query table.
2. Click **"Create" → "Table / Pivot View"**.
3. Select **"Table View"**.
4. In the column selector:
   - Drag in: `Student Name`, `Enrolment Stage`, `Applications Count`, `Interviews Count`
5. Click **Save**, name it: `Discrepancy Audit Table`

---

## PHASE 6: Build the KPI Widgets

KPI widgets show big single-number metrics at the top of your dashboard.

### Step 25 — Total Registered KPI
1. Go to your workspace home.
2. Click **"Create" → "Dashboard"** (or open your dashboard if you already created one).
3. In the Dashboard editor, click **"Widget"** in the top toolbar.
4. Select **"KPI Widget"** → **"Single Number"**.
5. In the Widget Editor:
   - **Base Table**: `Funnel Stats`
   - **Data Column**: `Registered`
   - **Aggregate**: Sum
   - **Label**: `Total Enrolments`
6. Click **Apply**.

### Step 26 — Placement Eligible KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. In the Widget Editor:
   - **Base Table**: `Funnel Stats`
   - **Data Column**: `Eligible`
   - **Aggregate**: Sum
   - **Label**: `Placement Eligible`
3. Click **Apply**.

### Step 27 — Placed / Hired KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. In the Widget Editor:
   - **Base Table**: `Funnel Stats`
   - **Data Column**: `Placed`
   - **Aggregate**: Sum
   - **Label**: `Hired & Placed`
3. Click **Apply**.

### Step 28 — Total Job Openings KPI
1. Click **"Widget"** → **"KPI Widget"** → **"Single Number"**.
2. In the Widget Editor:
   - **Base Table**: `JobOpenings`
   - **Data Column**: `Job Opening Id`
   - **Aggregate**: Count
   - **Label**: `Total Job Openings`
3. Click **Apply**.

---

## PHASE 7: Assemble the Dashboard

### Step 29 — Create the Dashboard Canvas
1. In your workspace, click **"Create" → "Dashboard"**.
2. Name it: `Placement Executive Dashboard`
3. You are now in the drag-and-drop dashboard builder.

### Step 30 — Add KPI Widgets (Top Row)
1. Your 4 KPI widgets from Phase 6 should appear in the left **Widgets** panel.
2. **Drag each KPI widget** onto the top row of the canvas.
3. Resize them so all 4 sit side by side in a single row (drag the edges to resize).

### Step 31 — Add Charts (Main Body)
In the left panel, look for the **"Reports"** tab — all saved charts from Phase 5 appear here:

**Row 2 (two-column layout):**
- Drag `Placement Funnel Chart` → Place it as a wide 2/3-width card on the left.
- Drag `Dropout Reasons Chart` → Place it as 1/3-width card on the right.

**Row 3 (two-column layout):**
- Drag `Batch Performance Chart` → Wide 2/3-width card left.
- Drag `Cancellation Reasons Chart` → 1/3-width card right.

**Row 4 (three-column layout):**
- Drag `Top Skills Chart`
- Drag `Location Preference Chart`
- Drag `Top Job Postings Chart` *(if you built one from JobOpenings)*

**Row 5 (full width):**
- Drag `Discrepancy Audit Table` → Full-width card spanning the whole row.

### Step 32 — Final Polish & Save
1. Click on any chart to **rename** it — add proper title text.
2. Use the **Theme** option in the dashboard settings to pick a light/corporate color theme.
3. Click the **"Filters"** button to add a global **Batch Name filter** so viewers can slice by batch.
4. Click **"Save"** (top-right corner).
5. Click **"Publish"** or **"Share"** to generate a shareable link if needed.

---

## Quick Reference: What Each Report Answers

| Report Name | Source Table | Answers |
|:---|:---|:---|
| `Placement Funnel Chart` | Funnel Stats | How many students drop off at each stage? |
| `Batch Performance Chart` | Batch Performance | Which batches produced the most placements? |
| `Dropout Reasons Chart` | Knockoff Reasons | Why do students get knocked off the program? |
| `Cancellation Reasons Chart` | Cancellation Reasons | Why do interview rounds get cancelled? |
| `Top Skills Chart` | Top Skills | What skills do eligible candidates have? |
| `Location Preference Chart` | Candidates | Where do candidates prefer to work? |
| `Discrepancy Audit Table` | Discrepancy Audit | Which "Hired" students have no application trail? |
| KPI Widgets x4 | Funnel Stats, JobOpenings | High-level headline numbers |

---

## Common Troubleshooting

| Problem | Fix |
|:---|:---|
| IDs are showing as scientific notation (e.g. `1.6e+17`) | Go back to the table → Edit Column → Change type to **Plain Text** |
| SQL Query Table throws an error | Check exact column names by opening the raw table first — Zoho is case-sensitive |
| Chart shows no data | Make sure Lookup Columns are correctly set up (Phase 3) |
| Dashboard charts are too small | Drag the edges of each chart card to resize them in the dashboard editor |
| Lookup column not working | Verify both ID columns are **Plain Text** type on both sides of the relationship |
