import json
import os
import time
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from dotenv import load_dotenv

from azure.storage.filedatalake import DataLakeServiceClient

load_dotenv()

API_URL = "https://freehire.me/api/v1/jobs/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://freehire.me/?countries=sa",
}

TARGET_COUNT = 150

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "RAW")
JSON_PATH = os.path.join(RAW_DIR, "freehire_tech_jobs.json")


def load_existing_jobs():
    """قراءة الوظائف الموجودة محلياً مسبقاً لتجنب التكرار."""
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def create_resilient_session() -> requests.Session:
    """ينشئ session واحدة مع إعادة محاولة تلقائية عند أخطاء السيرفر المؤقتة."""
    session = requests.Session()

    retry_strategy = Retry(
        total=2,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def upload_to_adls_gen2(jobs_to_upload, source_name="freehire"):
    if not jobs_to_upload:
        print("✨ لا توجد وظائف جديدة لرفعها إلى Azure في هذه الجلسة.")
        return

    account_name = os.getenv("AZURE_STORAGE_ACCOUNT", "datajobpipline")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "data")
    sas_token = os.getenv("AZURE_SAS_TOKEN")

    if not sas_token:
        print("⚠️ لم يتم العثور على AZURE_SAS_TOKEN في ملف .env، تعذر الرفع لـ Azure.")
        return

    try:
        account_url = f"https://{account_name}.dfs.core.windows.net"
        if not sas_token.startswith("?"):
            sas_token = f"?{sas_token}"

        service_client = DataLakeServiceClient(account_url=f"{account_url}{sas_token}")
        file_system_client = service_client.get_file_system_client(container_name)

        # مسار مجلد اليوم الحالي
        ingest_date = datetime.now().strftime("%Y-%m-%d")
        remote_file_path = f"raw/{source_name}/ingest_date={ingest_date}/data.json"

        # تحويل الوظائف الجديدة فقط إلى JSON
        json_payload = json.dumps(jobs_to_upload, ensure_ascii=False, indent=2)

        file_client = file_system_client.get_file_client(remote_file_path)
        file_client.upload_data(json_payload, overwrite=True)

        print(f"🚀 تم رفع الوظائف الجديدة ({len(jobs_to_upload)} وظيفة) بنجاح إلى Azure في المسار:")
        print(f"   📂 {container_name}/{remote_file_path}")

    except Exception as e:
        print(f"❌ حدث خطأ أثناء الرفع إلى Azure ADLS Gen2: {e}")


def get_tech_jobs_50(target_count=TARGET_COUNT):
    session = create_resilient_session()

    existing_jobs = load_existing_jobs()
    existing_urls = {job.get("source_url") for job in existing_jobs if job.get("source_url")}
    print(f"📊 عدد الوظائف الموجودة محلياً مسبقاً: {len(existing_jobs)}")

    new_fetched_jobs = []
    limit = 20
    offset = 0

    print(f"🚀 جاري سحب الوظائف التقنية من FreeHire...")

    while len(new_fetched_jobs) < target_count:
        params = {
            "countries": "sa",
            "is_tech": "tech",
            "limit": limit,
            "offset": offset,
        }

        try:
            response = session.get(API_URL, headers=HEADERS, params=params, timeout=30)

            if response.status_code != 200:
                print(f"❌ خطأ أثناء الاتصال: {response.status_code}")
                break

            payload = response.json()
            raw_jobs = payload.get("data", [])

            if not raw_jobs:
                print("⚠️ انتهت النتائج المتاحة.")
                break

            for item in raw_jobs:
                job_url = item.get("url", "")

                if job_url in existing_urls:
                    continue

                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                record = {
                    "job_title": item.get("title", "غير محدد"),
                    "company_name": item.get("company", "غير محدد"),
                    "location": item.get("location", "Saudi Arabia"),
                    "cities": item.get("cities", []),
                    "posted_date": item.get("posted_at") or item.get("created_at", "غير محدد"),
                    "category": item.get("enrichment", {}).get("category", "tech"),
                    "skills": item.get("skills", []),
                    "job_description": item.get("description", ""),
                    "source_url": job_url,
                    "original_source": item.get("source", "freehire"),
                    "extracted_at": current_timestamp
                }
                new_fetched_jobs.append(record)
                existing_urls.add(job_url)

                if len(new_fetched_jobs) >= target_count:
                    break

            print(f"📦 تم جمع {len(new_fetched_jobs)} وظيفة جديدة حتى الآن...")
            offset += limit
            time.sleep(1)

        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ فشل الاتصال: {e}")
            break
        except requests.exceptions.Timeout:
            print("⏱️ انتهت مهلة الاتصال")
            break
        except Exception as e:
            print(f"❌ حدث خطأ: {e}")
            break

    if not new_fetched_jobs:
        print("✨ لا توجد وظائف جديدة، لم يتم رفع أي ملف جديد اليوم.")
        return

    combined_jobs = existing_jobs + new_fetched_jobs

    # 1. الحفظ المحلي (يحفظ الأرشيف كاملاً للرجوع له محلياً)
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(combined_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n🎯 اكتملت العملية بنجاح! إجمالي الوظائف المحفوظة محلياً: {len(combined_jobs)}")

    upload_to_adls_gen2(new_fetched_jobs)


if __name__ == "__main__":
    get_tech_jobs_50()