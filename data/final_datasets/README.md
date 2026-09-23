# Final Datasets Documentation

This directory contains the final exported Mart tables (Star Schema) generated from the Saudi Job Market Data Pipeline. All datasets represent structured, cleaned, and modeled data ready for analytics and visualization.

---

## Dataset Overview & Schemas

### 1. Fact Job Skills (`fct_job_skills.csv`)
* **Description:** Fact table mapping technical job postings to their extracted skills, linking various dimensions.
* **Row Count:** 6,833 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `JOB_POSTING_KEY` (VARCHAR(32)) - Foreign key to job postings.
  * `SKILL_KEY` (VARCHAR(32)) - Foreign key to skills dimension.
  * `COMPANY_KEY` (VARCHAR(32)) - Foreign key to company dimension.
  * `LOCATION_KEY` (VARCHAR(32)) - Foreign key to location dimension.
  * `JOB_ATTRIBUTES_KEY` (VARCHAR(32)) - Foreign key to job attributes dimension.
  * `DATE_KEY` (VARCHAR(32)) - Foreign key to date dimension.

---

### 2. Fact Job Postings (`fct_job_postings.csv`)
* **Description:** Fact table containing core information and metrics for each unique job posting.
* **Row Count:** 1,196 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `JOB_POSTING_KEY` (VARCHAR(32)) - Primary key / unique identifier for the job posting.
  * `COMPANY_KEY` (VARCHAR(32)) - Foreign key to company.
  * `LOCATION_KEY` (VARCHAR(32)) - Foreign key to location.
  * `JOB_ATTRIBUTES_KEY` (VARCHAR(32)) - Foreign key to job attributes.
  * `DATE_KEY` (VARCHAR(32)) - Foreign key to date.
  * `TITLE` (VARCHAR) - Job title.
  * `URL` (VARCHAR) - Original link to the job posting.
  * `SEEN_ON_SOURCES` (VARCHAR) - Platforms where the job was detected.
  * `SOURCE_COUNT` (NUMBER(18,0)) - Number of sources tracking this job.
  * `JOB_POSTING_COUNT` (NUMBER(1,0)) - Count indicator metric.

---

### 3. Dimension Skill (`dim_skill.csv`)
* **Description:** Dimension table containing unique technical skills extracted from job descriptions.
* **Row Count:** 685 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `SKILL_KEY` (VARCHAR(32)) - Primary key.
  * `SKILL_NAME` (VARCHAR) - Name of the technical skill (e.g., Python, SQL, Snowflake).

---

### 4. Dimension Location (`dim_location.csv`)
* **Description:** Dimension table for geographic locations of job opportunities.
* **Row Count:** 15 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `LOCATION_KEY` (VARCHAR(32)) - Primary key.
  * `CITY` (VARCHAR) - City name.
  * `COUNTRY` (VARCHAR) - Country name.
  * `LOCATION` (VARCHAR) - Full location descriptor.

---

### 5. Dimension Job Attributes (`dim_job_attributes.csv`)
* **Description:** Dimension table detailing employment types, education requirements, seniority, and categories.
* **Row Count:** 75 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `JOB_ATTRIBUTES_KEY` (VARCHAR(32)) - Primary key.
  * `EMPLOYMENT_TYPE` (VARCHAR) - Type of employment (e.g., Full-time).
  * `EDUCATION` (VARCHAR) - Required educational degree.
  * `SENIORITY_LEVEL` (VARCHAR(15)) - Experience level (e.g., Junior, Senior).
  * `JOB_CATEGORY` (VARCHAR(21)) - Professional category.

---

### 6. Dimension Date (`dim_date.csv`)
* **Description:** Calendar dimension table supporting time-series analysis and aggregations.
* **Row Count:** 1,461 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `DATE_KEY` (VARCHAR(32)) - Primary key.
  * `DATE_DAY` (DATE) - Calendar date.
  * `DAY_OF_MONTH` (NUMBER(2,0)) - Day number in the month.
  * `DAY_OF_WEEK` (NUMBER(2,0)) - Day index of the week.
  * `DAY_NAME` (VARCHAR) - Name of the day (e.g., Monday).
  * `MONTH` (NUMBER(2,0)) - Month number.
  * `MONTH_NAME` (VARCHAR) - Name of the month.
  * `QUARTER` (NUMBER(2,0)) - Year quarter.
  * `YEAR` (NUMBER(4,0)) - Year value.
  * `IS_WEEKEND` (BOOLEAN) - Flag indicating if the day falls on a weekend.

---

### 7. Dimension Company (`dim_company.csv`)
* **Description:** Dimension table containing employing organizations and companies.
* **Row Count:** 650 rows
* **Generated At:** 2026-09-23
* **Columns:**
  * `COMPANY_KEY` (VARCHAR(32)) - Primary key.
  * `COMPANY_NAME` (VARCHAR) - Name of the hiring company.
