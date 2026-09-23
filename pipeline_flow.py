"""
pipeline_flow.py
------------------
نقطة الدخول الرئيسية للأتمتة عبر Prefect — متوافقة مع البنية الحالية:

    1. استخراج البيانات من 4 مصادر (Jooble, JSearch, FreeHire, Tanqeeb)
       -> كل سكربت يحفظ محليًا + يرفع لـ ADLS Gen2 (raw/<source>/ingest_date=.../data.json)
    2. تحميل الملفات الجديدة من ADLS إلى جداول Snowflake RAW (عبر COPY INTO)
       -> Snowflake يتجاهل تلقائيًا أي ملف حمّله سابقًا (بدون تكرار)
    3. تنظيف كل مصدر (transformation.py)
       -> يقرأ من RAW بشكل تزايدي (بس الجديد منذ آخر تشغيلة، حسب LOADED_AT)
       -> ينظف، يحفظ محليًا، ويضيف (append) لجداول STG_* بـ Snowflake STAGING
       -> يحدّث جدول PIPELINE_WATERMARKS تلقائيًا بعد كل نجاح

المتطلبات:
    pip install prefect

قبل أول تشغيلة:
    - شغّل setup_adls_to_snowflake.sql مرة واحدة بـ Snowflake
      (يضيف عمود LOADED_AT، ينشئ الـ Stage والـ Watermark table)
    - تأكد من وجود .env يحتوي كل مفاتيح Snowflake + Azure + مصادر الاستخراج
"""

import sys
from pathlib import Path

from prefect import flow, task, get_run_logger

PROJECT_ROOT = Path(__file__).parent
INGESTION_DIR = PROJECT_ROOT / "Ingestion"
TRANSFORMATION_DIR = PROJECT_ROOT / "Transformation"

sys.path.append(str(INGESTION_DIR))
sys.path.append(str(TRANSFORMATION_DIR))


# ============================================================
# Tasks: مرحلة الاستخراج (Extraction) -> ADLS Gen2
# ============================================================

@task(name="extract-jooble", retries=1, retry_delay_seconds=30)
def extract_jooble():
    logger = get_run_logger()
    from jooble_api import get_jooble_jobs, merge_and_save_jobs

    raw_dir = PROJECT_ROOT / "data" / "RAW"
    json_path = str(raw_dir / "jooble_tech_jobs.json")

    df = get_jooble_jobs()
    if df.empty:
        logger.warning("Jooble: لم يتم سحب أي بيانات")
        return
    merge_and_save_jobs(df, json_path)
    logger.info("Jooble: اكتمل الاستخراج والرفع لـ ADLS")


@task(name="extract-jsearch", retries=1, retry_delay_seconds=30)
def extract_jsearch():
    logger = get_run_logger()
    from jsearch_api import main
    main()
    logger.info("JSearch: اكتمل الاستخراج والرفع لـ ADLS")


@task(name="extract-freehire", retries=1, retry_delay_seconds=30)
def extract_freehire():
    logger = get_run_logger()
    from freehire import get_tech_jobs_50
    get_tech_jobs_50()
    logger.info("FreeHire: اكتمل الاستخراج والرفع لـ ADLS")


@task(name="extract-tanqeeb", retries=1, retry_delay_seconds=30)
def extract_tanqeeb():
    logger = get_run_logger()
    from tanqeeb_scraper import main
    main()
    logger.info("Tanqeeb: اكتمل الاستخراج والرفع لـ ADLS")


# ============================================================
# Task: تحميل الملفات الجديدة من ADLS إلى Snowflake RAW
# ============================================================

@task(name="load-adls-to-snowflake-raw", retries=1, retry_delay_seconds=30)
def load_adls_to_raw():
    """
    ينفذ أوامر COPY INTO لكل جدول RAW، عشان يسحب أي ملفات جديدة
    اترفعت لـ ADLS بالخطوة السابقة. Snowflake يتذكر الملفات المحمّلة
    من قبل تلقائيًا، فما فيه تكرار حتى لو شغّلناها كل مرة.
    """
    import os
    import snowflake.connector
    from dotenv import load_dotenv
    load_dotenv()

    logger = get_run_logger()

    account_val = os.getenv("SNOWFLAKE_ACCOUNT") or os.getenv("SNOWFLAFE_ACCOUNT")
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=account_val,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="RAW"
    )
    cursor = conn.cursor()

    copy_commands = [
        ("RAW_JOOBLE_JOBS", "jooble"),
        ("RAW_JSEARCH_JOBS", "jsearch"),
        ("RAW_FREEHIRE_JOBS", "freehire"),
        ("RAW_TANQEEB_JOBS", "tanqeeb"),
    ]

    try:
        for table_name, source_folder in copy_commands:
            query = f"""
                COPY INTO {table_name} (RAW_DATA, SOURCE_FILE, INGEST_DATE)
                FROM (
                    SELECT $1, METADATA$FILENAME, CURRENT_DATE()
                    FROM @adls_stage/{source_folder}/
                )
                FILE_FORMAT = (FORMAT_NAME = json_format)
                PATTERN = '.*data[.]json'
                ON_ERROR = 'CONTINUE'
            """
            cursor.execute(query)
            result = cursor.fetchall()
            loaded_files = len(result)
            logger.info(f"COPY INTO {table_name}: تمت معالجة {loaded_files} ملف (جديد أو متجاهَل)")
    finally:
        cursor.close()
        conn.close()


# ============================================================
# Tasks: مرحلة التنظيف (Cleaning / Staging) — تزايدية تلقائيًا
# ============================================================

@task(name="clean-jooble", retries=1, retry_delay_seconds=30)
def clean_jooble():
    logger = get_run_logger()
    from transformation import process_jooble
    df = process_jooble()
    logger.info(f"Jooble Cleaning: {len(df)} سجل جديد تم تنظيفه ورفعه")
    return len(df)


@task(name="clean-jsearch", retries=1, retry_delay_seconds=30)
def clean_jsearch():
    logger = get_run_logger()
    from transformation import process_jsearch
    df = process_jsearch()
    logger.info(f"JSearch Cleaning: {len(df)} سجل جديد تم تنظيفه ورفعه")
    return len(df)


@task(name="clean-freehire", retries=1, retry_delay_seconds=30)
def clean_freehire():
    logger = get_run_logger()
    from transformation import process_freehire
    df = process_freehire()
    logger.info(f"FreeHire Cleaning: {len(df)} سجل جديد تم تنظيفه ورفعه")
    return len(df)


@task(name="clean-tanqeeb", retries=1, retry_delay_seconds=30)
def clean_tanqeeb():
    logger = get_run_logger()
    from transformation import process_tanqeeb
    df = process_tanqeeb()
    logger.info(f"Tanqeeb Cleaning: {len(df)} سجل جديد تم تنظيفه ورفعه")
    return len(df)


# ============================================================
# Flow الرئيسي
# ============================================================

@flow(name="job-data-pipeline")
def job_data_pipeline():
    logger = get_run_logger()
    logger.info("=" * 60)
    logger.info("بدء تشغيل job-data-pipeline")
    logger.info("=" * 60)

    # ---- 1) الاستخراج -> ADLS ----
    jooble_extract = extract_jooble()
    jsearch_extract = extract_jsearch()
    freehire_extract = extract_freehire()
    tanqeeb_extract = extract_tanqeeb()

    # ---- 2) تحميل ADLS -> Snowflake RAW (ينتظر انتهاء كل الاستخراج) ----
    load_raw = load_adls_to_raw(
        wait_for=[jooble_extract, jsearch_extract, freehire_extract, tanqeeb_extract]
    )

    # ---- 3) التنظيف (يعتمد على اكتمال التحميل لـ RAW) ----
    clean_jooble(wait_for=[load_raw])
    clean_jsearch(wait_for=[load_raw])
    clean_freehire(wait_for=[load_raw])
    clean_tanqeeb(wait_for=[load_raw])

    logger.info("=" * 60)
    logger.info("اكتمل تشغيل job-data-pipeline بنجاح")
    logger.info("=" * 60)


if __name__ == "__main__":
    job_data_pipeline()