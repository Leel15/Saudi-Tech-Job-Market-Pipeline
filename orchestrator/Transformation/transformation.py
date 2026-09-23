import os
import pandas as pd
import snowflake.connector
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from cleaning import (
    clean_company_name, clean_job_title, clean_job_title_from_location,
    clean_city, clean_employment_type, extract_education, clean_description, format_date, extract_tech_skills,
    deduplicate_by_content, merge_and_save_processed, parse_relative_date, clean_jsearch_location, clean_html_text,
    is_valid_tech_job, normalize_skill, check_if_tech_job)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "RAW")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "STAGING")

UNIFIED_COLUMNS = [
    "title", "company", "location", "posted_date", "salary",
    "skills", "experience_required", "description", "employment_type",
    "url", "source", "repost_count",
]


def get_snowflake_connection(schema=None):
    """اتصال موحّد يُستخدم بكل دوال Snowflake بهذا الملف."""
    account_val = os.getenv("SNOWFLAKE_ACCOUNT") or os.getenv("SNOWFLAFE_ACCOUNT")
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=account_val,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=schema or os.getenv("SNOWFLAKE_SCHEMA")
    )


def get_watermark(source_name: str):
    """
    يجيب آخر تاريخ (Watermark) تمت معالجته لهذا المصدر بصيغة 'YYYY-MM-DD'.
    """
    conn = None
    cursor = None

    try:
        conn = get_snowflake_connection(schema="STAGING")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT LAST_PROCESSED_SOURCE
            FROM JOB_MARKET_DB.STAGING.PIPELINE_WATERMARKS
            WHERE SOURCE_NAME = %s
            """,
            (source_name,)
        )

        row = cursor.fetchone()
        if row and row[0]:
            return str(row[0]).strip()  # يرجّع التاريخ كـ '2026-09-15'

        return None

    except Exception as e:
        print(f"⚠️ تعذّر جلب الـ watermark لـ {source_name}: {e} — سيتم اعتبار كل البيانات جديدة")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_watermark(source_name: str, new_date_str):
    """
    يحدّث الـ watermark بآخر تاريخ تم إنجازه بنجاح (مثلاً '2026-09-17').
    """
    if not new_date_str:
        return

    conn = None
    cursor = None

    try:
        conn = get_snowflake_connection(schema="STAGING")
        cursor = conn.cursor()

        cursor.execute(
            """
            MERGE INTO JOB_MARKET_DB.STAGING.PIPELINE_WATERMARKS AS target
            USING (
                SELECT
                    %s AS SOURCE_NAME,
                    %s AS LAST_PROCESSED_SOURCE
            ) AS src
            ON target.SOURCE_NAME = src.SOURCE_NAME
            WHEN MATCHED THEN
                UPDATE SET
                    LAST_PROCESSED_SOURCE = src.LAST_PROCESSED_SOURCE
            WHEN NOT MATCHED THEN
                INSERT (
                    SOURCE_NAME,
                    LAST_PROCESSED_SOURCE
                )
                VALUES (
                    src.SOURCE_NAME,
                    src.LAST_PROCESSED_SOURCE
                )
            """,
            (source_name, new_date_str)
        )

        conn.commit()
        print(f"🕒 تم تحديث الـ watermark لـ {source_name} إلى التاريخ: {new_date_str}")

    except Exception as e:
        print(f"❌ خطأ أثناء تحديث الـ watermark لـ {source_name}: {e}")
        if conn:
            conn.rollback()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_raw_from_snowflake(table_name: str, since_date=None):
    """
    يقرأ السجلات بناءً على عمود INGEST_DATE بشكل مباشر وسريع (أكبر من تاريخ الـ Watermark).
    """
    conn = None
    cursor = None
    full_table = f"JOB_MARKET_DB.RAW.{table_name}"

    try:
        conn = get_snowflake_connection(schema="RAW")
        cursor = conn.cursor()

        if since_date:
            print(f"☁️ جاري قراءة البيانات الجديدة فقط من {full_table}\n  بعد التاريخ: {since_date}")
            query = f"""
                SELECT RAW_DATA, SOURCE_FILE, INGEST_DATE
                FROM {full_table}
                WHERE INGEST_DATE > TO_DATE(%s, 'YYYY-MM-DD')
                ORDER BY INGEST_DATE ASC, SOURCE_FILE ASC
            """
            cursor.execute(query, (since_date,))
        else:
            print(f"☁️ جاري قراءة كل البيانات من Snowflake: {full_table}...")
            query = f"""
                SELECT RAW_DATA, SOURCE_FILE, INGEST_DATE
                FROM {full_table}
                ORDER BY INGEST_DATE ASC, SOURCE_FILE ASC
            """
            cursor.execute(query)

        rows = cursor.fetchall()
        records = []
        max_ingest_date = since_date

        for row in rows:
            payload = row[0]
            ingest_date = row[2]  # عمود الـ DATE الصريح في جدول الـ RAW

            if payload is not None:
                if isinstance(payload, str):
                    payload = json.loads(payload)
                records.append(payload)

            if ingest_date:
                date_str = str(ingest_date)
                if max_ingest_date is None or date_str > max_ingest_date:
                    max_ingest_date = date_str

        df = pd.DataFrame(records)
        print(f"✅ تم تحميل {len(df)} سجل جديد من Snowflake")

        # تخزين أحدث تاريخ للـ watermark في الـ attributes
        df.attrs["max_ingest_date"] = max_ingest_date
        return df

    except Exception as e:
        print(f"❌ خطأ أثناء قراءة البيانات من Snowflake ({full_table}): {e}")
        empty_df = pd.DataFrame()
        empty_df.attrs["max_ingest_date"] = since_date
        return empty_df

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def save_cleaned_to_snowflake(df: pd.DataFrame, table_name: str, csv_filename: str):
    """
    حفظ البيانات النظيفة الجديدة (فقط) كـ CSV محلياً، وإضافتها (append)
    لجدول Staging بـ Snowflake — بدون TRUNCATE، عشان يتوافق مع القراءة
    التزايدية من RAW (كل تشغيلة تضيف بس الجديد، ما تمسح القديم وتعيد كتابته).
    """
    if df.empty:
        print(f"⚠️ الجدول {table_name} فارغ، لا توجد بيانات للرفع.")
        return

    df = df.where(pd.notnull(df), None)

    csv_path = os.path.join(PROCESSED_DIR, csv_filename)

    df_to_save = df.copy()
    if 'skills' in df_to_save.columns:
        df_to_save['skills'] = df_to_save['skills'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_to_save.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"📁 تم حفظ ملف الـ CSV محلياً: {csv_path}")

    conn = None
    cursor = None
    try:
        conn = get_snowflake_connection(schema="STAGING")
        cursor = conn.cursor()

        insert_query = f"""
            INSERT INTO JOB_MARKET_DB.STAGING.{table_name} (
                job_title, company_name, city, country, 
                posted_date, employment_type, education, 
                job_description, skills, job_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        def clean_val(val):
            if val is None or pd.isna(val) or str(val).strip().lower() in ['nan', 'nat', 'none']:
                return None
            return val

        records_to_insert = []
        for _, row in df_to_save.iterrows():
            records_to_insert.append((
                clean_val(row.get('job_title')),
                clean_val(row.get('company_name')),
                clean_val(row.get('city')),
                clean_val(row.get('country')),
                clean_val(row.get('posted_date')),
                clean_val(row.get('employment_type')),
                clean_val(row.get('education')),
                clean_val(row.get('job_description')),
                clean_val(row.get('skills')),
                clean_val(row.get('job_url'))
            ))

        cursor.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"☁️✅ تم إضافة {len(records_to_insert)} سجل جديد بنجاح لجدول Staging بـ Snowflake: {table_name}\n")

    except Exception as e:
        print(f"❌ خطأ أثناء إرسال البيانات إلى جدول Staging ({table_name}): {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def process_tapneo() -> pd.DataFrame:
    last_watermark = get_watermark("TAPNEO")
    df = load_raw_from_snowflake("RAW_TEPNEO_JOBS", since_date=last_watermark)
    new_watermark = df.attrs.get("max_ingest_date", last_watermark)

    if df.empty:
        print("✨ لا توجد بيانات Tapneo جديدة منذ آخر تشغيلة")
        return pd.DataFrame()

    standardized_jobs = []

    print(f"Processing {len(df)} records from Tapneo...")

    for _, item in df.iterrows():
        company_raw = item.get('CompanyName', '') or item.get('company_name', '')
        company_name = clean_company_name(company_raw)

        raw_desc_content = item.get('JobDescription', '') or item.get('job_description', '')
        job_description = clean_description(raw_desc_content)

        job_title = clean_job_title(raw_desc_content, company_name)
        if job_title == "Technical Professional":
            continue

        if job_title == "Project Manager" and company_name == "AtkinsR":
            continue

        city = clean_city(clean_jsearch_location(item.get('job_location') or item.get('job_city')))
        country = "Saudi Arabia"
        posted_date = format_date(item.get('PostedAt') or item.get('posted_date'))
        employment_type = clean_employment_type(item.get('EmploymentType') or item.get('employment_type'),
                                                raw_desc_content)
        skills = extract_tech_skills(job_description)
        education = extract_education(raw_desc_content)

        job_url = item.get('source_url') or item.get('job_url')

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": skills,
            "job_url": job_url
        }
        standardized_jobs.append(common_schema_item)

    df_temp = pd.DataFrame(standardized_jobs)

    if not df_temp.empty:
        df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
        df_temp = df_temp.where(pd.notnull(df_temp), None)

    output_path = os.path.join(PROCESSED_DIR, "tapneo_tech_jobs_cleaned.json")
    merge_and_save_processed(df_temp, output_path, key_cols=["company_name", "city", "job_description"], fresh=False)

    save_cleaned_to_snowflake(df_temp, "STG_TEPNEO_JOBS", "csv/tapneo_tech_jobs_cleaned.csv")
    update_watermark("TAPNEO", new_watermark)

    print(f"✅ اكتملت معالجة Tapneo بنجاح وإجمالي الوظائف النظيفة الجديدة: {len(df_temp)}")
    return df_temp


def process_jsearch() -> pd.DataFrame:
    last_watermark = get_watermark("JSEARCH")

    df = load_raw_from_snowflake(
        "RAW_JSEARCH_JOBS",
        since_date=last_watermark
    )

    new_watermark = df.attrs.get(
        "max_ingest_date",
        last_watermark
    )

    if df.empty:
        print("✨ لا توجد بيانات JSearch جديدة منذ آخر تشغيلة")
        return pd.DataFrame()

    print(f"Processing {len(df)} records from JSearch...")

    standardized_jobs = []
    skipped_us = 0
    skipped_short_desc = 0
    skipped_bad_url = 0
    skipped_non_tech = 0

    platforms_blacklist = ["linkedin", "foundit", "gulftalent", "bayt", "wuzzuf", "naukrigulf", "jobleads",
                           "arabianreccom", "indeed", "glassdoor"]

    for _, item in df.iterrows():
        desc_check = str(item.get('job_description', item.get('snippet', ''))).lower()
        loc_check = str(item.get('job_location', item.get('location', ''))).lower()

        if "united states" in desc_check or "united states" in loc_check or "u.s. citizen" in desc_check or "us citizen" in desc_check:
            skipped_us += 1
            continue

        company_name = clean_company_name(item.get('employer_name') or item.get('company'))

        raw_desc = item.get('job_description', '') or item.get('snippet', '')
        job_description = clean_html_text(raw_desc)
        job_description = clean_description(job_description)

        if len(job_description) < 50:
            skipped_short_desc += 1
            continue

        job_url = item.get('job_apply_link') or item.get('url')
        if not job_url or not str(job_url).strip().lower().startswith('http'):
            skipped_bad_url += 1
            continue

        raw_title = item.get('job_title') or item.get('title', '')
        job_title = clean_job_title_from_location(raw_title)

        if not is_valid_tech_job(job_title, job_description):
            skipped_non_tech += 1
            continue

        raw_loc = item.get('job_city') or item.get('city') or item.get('job_location') or item.get('location')
        city = clean_city(raw_loc)
        if city and str(city).strip().lower() in platforms_blacklist:
            city = None

        country = "Saudi Arabia"
        posted_date = parse_relative_date(item.get('job_posted_at') or item.get('date'))

        employment_type = clean_employment_type(item.get('job_employment_type') or item.get('employment_type'),
                                                job_description)
        education = extract_education(job_description)
        skills = extract_tech_skills(job_description)

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": skills,
            "job_url": job_url
        }

        standardized_jobs.append(common_schema_item)

    print(f"Skipped {skipped_us} US/Foreign jobs.")
    print(f"Skipped {skipped_short_desc} jobs with descriptions under 50 characters.")
    print(f"Skipped {skipped_bad_url} jobs with invalid or missing URLs.")
    print(f"Skipped {skipped_non_tech} non-tech or corrupted jobs.")

    df_temp = pd.DataFrame(standardized_jobs)

    if not df_temp.empty:
        df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
        df_temp = df_temp.where(pd.notnull(df_temp), None)

    output_path = os.path.join(PROCESSED_DIR, "jsearch_tech_jobs_cleaned.json")
    merge_and_save_processed(df_temp, output_path, key_cols=["company_name", "city", "job_description"], fresh=False)
    save_cleaned_to_snowflake(df_temp, "STG_JSEARCH_JOBS", "csv/jsearch_tech_jobs_cleaned.csv")

    update_watermark("JSEARCH", new_watermark)

    print(f"✅ اكتملت معالجة JSearch بنجاح وإجمالي الوظائف النظيفة: {len(df_temp)}\n")
    return df_temp


def process_jooble() -> pd.DataFrame:
    last_watermark = get_watermark("JOOBLE")
    df = load_raw_from_snowflake("RAW_JOOBLE_JOBS", since_date=last_watermark)
    new_watermark = df.attrs.get("max_ingest_date", last_watermark)

    if df.empty:
        print("✨ لا توجد بيانات Jooble جديدة منذ آخر تشغيلة")
        return pd.DataFrame()

    print(f"Processing {len(df)} records from Jooble...")

    standardized_jobs = []
    skipped_short_desc = 0
    skipped_bad_url = 0
    skipped_non_tech = 0

    for _, item in df.iterrows():
        company_name = clean_company_name(item.get('company'))

        raw_desc = item.get('snippet', '')
        job_description = clean_html_text(raw_desc)
        job_description = clean_description(job_description)

        if len(job_description) < 50:
            skipped_short_desc += 1
            continue

        job_url = item.get('url')
        if not job_url or not str(job_url).strip().lower().startswith('http'):
            skipped_bad_url += 1
            continue

        raw_title = item.get('title', '')
        job_title = clean_job_title_from_location(raw_title)

        if not is_valid_tech_job(job_title, job_description):
            skipped_non_tech += 1
            continue

        raw_loc = item.get('location') or item.get('search_location')
        city = clean_city(raw_loc)
        country = "Saudi Arabia"

        posted_date = format_date(item.get('date'))

        employment_type = clean_employment_type(item.get('employment_type', ''), job_description)
        if not employment_type:
            employment_type = "Full-time"

        education = extract_education(job_description)
        skills = extract_tech_skills(job_description)

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": skills,
            "job_url": job_url
        }

        standardized_jobs.append(common_schema_item)

    print(f"Skipped {skipped_short_desc} jobs with descriptions under 50 characters.")
    print(f"Skipped {skipped_bad_url} jobs with invalid or missing URLs.")
    print(f"Skipped {skipped_non_tech} non-tech or corrupted jobs.")

    df_temp = pd.DataFrame(standardized_jobs)

    if not df_temp.empty:
        common_cols = [
            "job_title", "company_name", "city", "country",
            "posted_date", "employment_type", "education",
            "job_description", "skills", "job_url"
        ]
        df_temp = df_temp[[c for c in common_cols if c in df_temp.columns]]

        df_temp.drop_duplicates(subset=['company_name', 'job_title'], keep='first', inplace=True)
        df_temp = df_temp.where(pd.notnull(df_temp), None)

    output_path = os.path.join(PROCESSED_DIR, "jooble_tech_jobs_cleaned.json")
    merge_and_save_processed(df_temp, output_path, key_cols=["company_name", "city", "job_description"], fresh=False)

    save_cleaned_to_snowflake(df_temp, "STG_JOOBLE_JOBS", "csv/jooble_tech_jobs_cleaned.csv")
    update_watermark("JOOBLE", new_watermark)

    print(f"✅ اكتملت معالجة Jooble بنجاح وإجمالي الوظائف النظيفة: {len(df_temp)}\n")
    return df_temp


def process_freehire() -> pd.DataFrame:
    # 1. جلب الـ watermark كـ تاريخ (مثل '2026-09-15')
    last_watermark = get_watermark("FREEHIRE")

    # 2. قراءة البيانات الجديدة بناءً على التاريخ من جدول RAW الجديد
    df = load_raw_from_snowflake("RAW_FREEHIRE_JOBS", since_date=last_watermark)

    # 3. التقاط أحدث تاريخ تم جلبه
    new_watermark = df.attrs.get("max_ingest_date", last_watermark)

    if df.empty:
        print("✨ لا توجد بيانات Freehire جديدة منذ آخر تشغيلة")
        return pd.DataFrame()

    print(f"Processing {len(df)} records from Freehire...")

    standardized_jobs = []
    skipped_short_desc = 0
    skipped_bad_url = 0
    skipped_non_tech = 0

    platforms_blacklist = ["linkedin", "foundit", "gulftalent", "bayt", "wuzzuf", "naukrigulf", "jobleads",
                           "arabianreccom", "indeed", "glassdoor"]

    for _, item in df.iterrows():
        company_name = clean_company_name(item.get('company_name'))

        raw_title = item.get('job_title', '')
        job_title = clean_job_title_from_location(raw_title)

        title_lower = job_title.lower()
        forbidden_keywords = [
            "design manager", "planning", "urban", "graphic designer",
            "civil", "structural", "mechanical", "electrical",
            "construction", "architect", "onsite project manager",
            "real estate", "hospitality", "interior"
        ]
        if any(kw in title_lower for kw in forbidden_keywords):
            skipped_non_tech += 1
            continue

        raw_desc = item.get('job_description', '')
        job_description = clean_html_text(raw_desc)
        job_description = clean_description(job_description)

        if len(job_description) < 50:
            skipped_short_desc += 1
            continue

        job_url = item.get('source_url')
        if not job_url or not str(job_url).strip().lower().startswith('http'):
            skipped_bad_url += 1
            continue

        if not is_valid_tech_job(job_title, job_description):
            skipped_non_tech += 1
            continue

        cities_list = item.get('cities', [])
        raw_loc = cities_list[0] if isinstance(cities_list, list) and len(cities_list) > 0 else item.get('location')

        city = clean_city(raw_loc)
        if not city:
            city = clean_city(job_description)

        if city and str(city).strip().lower() in platforms_blacklist:
            city = None

        country = "Saudi Arabia"
        posted_date = format_date(item.get('posted_date'))

        employment_type = clean_employment_type(item.get('category', ''), job_description)
        if not employment_type:
            employment_type = "Full-time"

        education = extract_education(job_description)

        api_skills = item.get('skills', [])
        extracted_skills = extract_tech_skills(job_description)

        combined_skills = sorted(
            list(set([normalize_skill(str(s).lower().strip()) for s in api_skills + extracted_skills if s])))
        combined_skills = [s for s in combined_skills if s]

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": combined_skills,
            "job_url": job_url
        }

        standardized_jobs.append(common_schema_item)

    print(f"Skipped {skipped_short_desc} jobs with descriptions under 50 characters.")
    print(f"Skipped {skipped_bad_url} jobs with invalid or missing URLs.")
    print(f"Skipped {skipped_non_tech} non-tech or corrupted jobs.")

    df_temp = pd.DataFrame(standardized_jobs)

    if not df_temp.empty:
        common_cols = [
            "job_title", "company_name", "city", "country",
            "posted_date", "employment_type", "education",
            "job_description", "skills", "job_url"
        ]
        df_temp = df_temp[[c for c in common_cols if c in df_temp.columns]]

        df_temp['city'] = df_temp['city'].apply(
            lambda x: None if pd.isna(x) or str(x).strip() in ['NaN', 'nan', ''] else x
        )
        df_temp['education'] = df_temp['education'].apply(
            lambda x: None if pd.isna(x) or str(x).strip() in ['NaN', 'nan', ''] else x
        )

        df_temp.drop_duplicates(subset=['company_name', 'city', 'job_description'], keep='first', inplace=True)
        df_temp = df_temp.where(pd.notnull(df_temp), None)

    output_path = os.path.join(PROCESSED_DIR, "freehire_tech_jobs_cleaned.json")
    merge_and_save_processed(df_temp, output_path, key_cols=["company_name", "city", "job_description"], fresh=False)

    # حفظ محلياً كـ CSV وإضافة الجديد لجدول Snowflake Staging
    save_cleaned_to_snowflake(df_temp, "STG_FREEHIRE_JOBS", "csv/freehire_tech_jobs_cleaned.csv")

    # 4. تحديث الـ watermark بالتاريخ الجديد
    update_watermark("FREEHIRE", new_watermark)

    print(f"✅ اكتملت معالجة Freehire بنجاح وإجمالي الوظائف النظيفة: {len(df_temp)}\n")
    return df_temp


def process_tanqeeb() -> pd.DataFrame:
    # 1. جلب الـ watermark الحالي كـ تاريخ
    last_watermark = get_watermark("TANQEEB")

    # 2. تحميل البيانات الجديدة بناءً على التاريخ
    df = load_raw_from_snowflake("RAW_TANQEEB_JOBS", since_date=last_watermark)

    # 3. التقاط أحدث تاريخ تم جلبه لتحديث اللاحق
    new_watermark = df.attrs.get("max_ingest_date", last_watermark)

    if df.empty:
        print("✨ لا توجد بيانات Tanqeeb جديدة منذ آخر تشغيلة")
        return pd.DataFrame()

    print(f"Deep cleaning and filtering {len(df)} records from Tanqeeb...")

    standardized_jobs = []
    non_tech_count = 0
    arabic_filtered_count = 0  # عداد الوظائف المحذوفة بسبب نسبة اللغة العربية

    for _, item in df.iterrows():
        company_name = clean_company_name(item.get('company_name'))

        job_title = item.get('job_title', '').strip()
        job_title = re.sub(r'[^\w\s\/\-\(\)\.\,\+]+', '', job_title).strip()

        raw_desc = item.get('job_description', '')
        job_description = clean_description(raw_desc)

        # --- شرط الفلترة: التحقق من نسبة اللغة العربية في الوصف ---
        if job_description:
            # حساب عدد الحروف العربية مقارنة بإجمالي الحروف في الوصف
            arabic_chars = sum(1 for c in job_description if '\u0600' <= c <= '\u06ff')
            total_chars = len(job_description.replace(" ", ""))  # حساب الحرف بدون المسافات لتقييم أدق

            if total_chars > 0:
                arabic_percentage = (arabic_chars / total_chars) * 100

                # إذا كانت نسبة الحروف العربية 40% أو أكثر (والمطلوب استبعادها)
                if arabic_percentage >= 40:
                    arabic_filtered_count += 1
                    continue
        # ----------------------------------------------------

        city = clean_city(item.get('location'))
        country = "Saudi Arabia"
        posted_date = format_date(item.get('posted_date'))

        employment_type = clean_employment_type(item.get('employment_type'), job_description)
        education = extract_education(job_description)

        skills = extract_tech_skills(job_description)

        is_tech = check_if_tech_job(job_title, job_description, skills)
        if not is_tech:
            non_tech_count += 1
            continue

        common_schema_item = {
            "job_title": job_title,
            "company_name": company_name,
            "city": city,
            "country": country,
            "posted_date": posted_date,
            "employment_type": employment_type,
            "education": education,
            "job_description": job_description,
            "skills": skills,
            "job_url": item.get('job_url') or item.get('url')
        }

        standardized_jobs.append(common_schema_item)

    df_temp = pd.DataFrame(standardized_jobs)
    print(f"Total non-tech jobs excluded: {non_tech_count}")
    print(f"Total jobs excluded due to Arabic content >= 40%: {arabic_filtered_count}")

    if not df_temp.empty:
        df_temp.drop_duplicates(subset=['company_name', 'job_title', 'job_description'], keep='first', inplace=True)
        df_temp = df_temp.where(pd.notnull(df_temp), None)

    output_path = os.path.join(PROCESSED_DIR, "tanqeeb_tech_jobs_cleaned.json")
    merge_and_save_processed(df_temp, output_path, key_cols=["company_name", "city", "job_description"], fresh=False)

    save_cleaned_to_snowflake(df_temp, "STG_TANQEEB_JOBS", "csv/tanqeeb_tech_jobs_cleaned.csv")

    # 4. تحديث الـ watermark بالتاريخ الجديد
    update_watermark("TANQEEB", new_watermark)

    print(f"✅ اكتملت معالجة Tanqeeb بنجاح وإجمالي الوظائف النظيفة: {len(df_temp)}\n")
    return df_temp


if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("=" * 50)
    print("🔄 بدء تنظيف جميع المصادر")
    print("=" * 50 + "\n")

    tapneo_df = process_tapneo()
    jsearch_df = process_jsearch()
    jooble_df = process_jooble()
    freehire_df = process_freehire()
    tanqeeb_df = process_tanqeeb()

    print("=" * 50)
    print("✅ اكتمل تنظيف جميع المصادر بنجاح!")
    print(
        f"tapneo: {len(tapneo_df)} | jsearch: {len(jsearch_df)} | jooble: {len(jooble_df)} | freehire: {len(freehire_df)} | tanqeeb: {len(tanqeeb_df)} ")
    print("=" * 50)