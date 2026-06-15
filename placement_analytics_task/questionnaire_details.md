# Skill Test Questionnaire: Placement & Data Analytics

## Instructions
Please review the scenario below and answer the subsequent technical and analytical questions. Ensure your responses demonstrate a strong understanding of database architecture, relational data mapping, and executive-level dashboard design.

---

## Question 1: Data Architecture & Relational Schema Design
You have been provided with five separate datasets (in CSV format) managed by a campus placement department.

Demonstrate how you would design a scalable relational database structure to connect these five distinct datasets. Your answer should ensure data integrity, eliminate redundancy, and support complex query performance.

**Database Link:** [Google Sheets Link](https://docs.google.com/spreadsheets/d/1QxtTPptxEh6i9Faj3VuWDtd52avztCX78fLRrMiJJSc/edit?usp=sharing)

**Database Details:**
- **Enrollments:** Master database containing records of all students registered in the institution.
- **Candidate:** A subset of the enrollments database, filtering for students who meet the strict eligibility criteria for active placements.
- **Job Opening:** Job roles procured by the corporate relations team to be mapped to eligible candidates.
- **Application:** The central transactional database tracking which candidates have been mapped to specific job openings.
- **Interview:** The progressive database logging individual interview rounds and selection statuses for each application.

---

## Question 2: Dashboard Visualization & Executive Insights
The Core Management team requires a high-level analytics dashboard to monitor placement performance, identify bottlenecks, and make strategic operational decisions.

**Note:** You are expected to simulate or outline this implementation using BI tools such as Zoho Analytics. You can ingest the CSV data, write SQL Query Tables to join the datasets, and build custom visual reports.
