import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from azure.storage.filedatalake import DataLakeServiceClient

load_dotenv()

TARGET_JOBS = 50

LOCATIONS = [
    "Saudi Arabia",
    "Riyadh",
    "Jeddah",
    "Dammam",
    "Khobar",
    "Mecca",
    "Medina",
    "Tabuk",
    "Abha",
    "Buraydah",
    "Dhahran",
    "Jubail",
    "Yanbu",
    "Al Ahsa",
    "Khamis Mushait",
    "Hail"
]

TECH_KEYWORDS = [
    "software engineer", "software developer", "backend developer",
    "frontend developer", "full stack developer", "mobile developer",
    "data scientist", "data analyst", "data engineer",
    "machine learning", "artificial intelligence", "AI engineer",
    "devops", "cloud engineer", "cyber security", "penetration tester",
    "UI UX designer", "IT support"
]

TECH_TITLE_WORDS = [
    "engineer", "developer", "programmer", "scientist", "analyst",
    "architect", "administrator", "devops", "security", "cloud",
    "network", "database", "data", "software", "system", "it ",
    "machine learning", "ai ", "ux", "ui", "qa", "test", "cyber",
    "backend", "frontend", "full stack", "mobile", "web", "bi "
]

CLEAR_EXCLUDE_WORDS = [
    "sales representative", "sales manager", "account executive",
    "marketing manager", "financial analyst", "civil engineer",
    "mechanical engineer", "electrical technician"
]

US_STATE_INDICATORS = [
    ", oh", ", in", ", ca", ", tx", ", ny", ", pa", ", il",
    ", fl", ", ga", ", mi", ", nc", ", va", ", az", ", wa",
    "county", "ohio", "indiana", "california", "texas"
]


def create_resilient_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def upload_to_adls_gen2(jobs_to_upload, source_name="jooble"):

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

        ingest_date = datetime.now().strftime("%Y-%m-%d")
        remote_file_path = f"raw/{source_name}/ingest_date={ingest_date}/data.json"

        json_payload = json.dumps(jobs_to_upload, ensure_ascii=False, indent=2)

        file_client = file_system_client.get_file_client(remote_file_path)
        file_client.upload_data(json_payload, overwrite=True)

        print(f"🚀 تم رفع الوظائف الجديدة ({len(jobs_to_upload)} وظيفة) بنجاح إلى Azure في المسار:")
        print(f"   📂 {container_name}/{remote_file_path}")

    except Exception as e:
        print(f"❌ حدث خطأ أثناء الرفع إلى Azure ADLS Gen2: {e}")


def is_saudi_location(location: str) -> bool:
    if not location:
        return True
    loc_lower = location.lower()
    for us_signal in US_STATE_INDICATORS:
        if us_signal in loc_lower:
            return False
    return True


def is_tech_title(title: str) -> bool:
    if not title:
        return False
    title_lower = title.lower()
    for excluded in CLEAR_EXCLUDE_WORDS:
        if excluded in title_lower:
            return False
    return any(word in title_lower for word in TECH_TITLE_WORDS)


def get_jooble_jobs() -> pd.DataFrame:
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        raise ValueError("لم يتم العثور على JOOBLE_API_KEY في ملف .env")

    session = create_resilient_session()
    url = f"https://jooble.org/api/{api_key}"

    raw_jobs = []
    print(f"🔄 بدء السحب مع شرط التوقف عند جمع {TARGET_JOBS} وظائف صحيحة...\n")

    for location in LOCATIONS:
        if len(raw_jobs) >= TARGET_JOBS:
            break
        for keyword in TECH_KEYWORDS:
            if len(raw_jobs) >= TARGET_JOBS:
                break

            payload = {"keywords": keyword, "location": location, "page": 1}
            try:
                response = session.post(url, json=payload, timeout=30)
                if response.status_code != 200:
                    continue
                
                data = response.json()
                jobs = data.get("jobs", [])
                
                for job in jobs:
                    if len(raw_jobs) >= TARGET_JOBS:
                        break
                    
                    title = job.get("title", "")
                    location_val = job.get("location", "")
                    
                    # فلترة فورية لتوفير الوقت والجهد
                    if is_tech_title(title) and is_saudi_location(location_val):
                        job["_search_location"] = location
                        raw_jobs.append(job)
                        print(f"✅ تم العثور على ({len(raw_jobs)}/{TARGET_JOBS}): {title} | {location_val}")

            except Exception as e:
                print(f"⚠️ خطأ أثناء البحث عن ({keyword} | {location}): {e}")
            
            time.sleep(0.5)

    structured = []
    for job in raw_jobs:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        structured.append({
            "title": job.get("title", ""),
            "company": job.get("company"),
            "location": job.get("location"),
            "date": job.get("updated"),
            "salary": job.get("salary"),
            "snippet": job.get("snippet"),
            "url": job.get("link"),
            "source": "jooble",
            "search_location": job.get("_search_location"),
            "extracted_at": current_timestamp
        })

    df = pd.DataFrame(structured)
    return df



if __name__ == "__main__":
    new_records = get_jooble_jobs()
    
    if new_records:
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "RAW", "jooble_tech_jobs.json"
        )
        
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(new_records, f, ensure_ascii=False, indent=2)

        print(f"💾 تم حفظ الوظائف محلياً في: {json_path} (إجمالي: {len(new_records)} وظيفة)")
        
        upload_to_adls_gen2(new_records, source_name="jooble")
    else:
        print("⚠️ لم يتم جلب أي وظائف مطابقة.")