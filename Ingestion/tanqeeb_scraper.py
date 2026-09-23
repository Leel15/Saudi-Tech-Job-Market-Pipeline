import json
import os
import re
import random
import time
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from datetime import datetime

from azure.storage.filedatalake import DataLakeServiceClient

load_dotenv()
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
BASE_URL = "https://saudi.tanqeeb.com"

NUMBER_OF_JOBS = 5 
MAX_PAGES = 100  

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "RAW")
os.makedirs(RAW_DIR, exist_ok=True)

JOBS_FILE = os.path.join(RAW_DIR, "tanqeeb_tech_jobs.json")


def get_scrapeops_url(url, render_js=False):
    payload = {
        "api_key": SCRAPEOPS_API_KEY,
        "url": url,
    }
    if render_js:
        payload["render_js"] = "true"
        
    return "https://proxy.scrapeops.io/v1/?" + urlencode(payload)


def get_page(url, render_js=False):
    try:
        target_url = get_scrapeops_url(url, render_js=render_js) if SCRAPEOPS_API_KEY else url
        response = requests.get(target_url, timeout=90)

        print("STATUS:", response.status_code)

        if response.status_code == 200:
            print("✅ تم تحميل الصفحة بنجاح")
            return response.text

        print(f"❌ فشل تحميل الصفحة: {response.status_code}")
        return None

    except requests.RequestException as e:
        print(f"❌ خطأ أثناء تحميل الصفحة: {e}")
        return None


def upload_to_adls_gen2(jobs_to_upload, source_name="tanqeeb"):
    if not jobs_to_upload:
        print("✨ لا توجد بيانات لرفعها إلى Azure في هذه الجلسة.")
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

        print(f"🚀 تم رفع البيانات الخام ({len(jobs_to_upload)} سجل) بنجاح إلى Azure في المسار:")
        print(f"   📂 {container_name}/{remote_file_path}")

    except Exception as e:
        print(f"❌ حدث خطأ أثناء الرفع إلى Azure ADLS Gen2: {e}")


def save_jobs(jobs):
    try:
        os.makedirs(RAW_DIR, exist_ok=True)
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"\n   💾 تم حفظ {len(jobs)} سجل في:")
        print(f"      {JOBS_FILE}")
        print(f"   ✅ الملف محفوظ بنجاح!")
    except Exception as e:
        print(f"   ❌ خطأ في حفظ الملف: {e}")


def get_job_links():
    print("\n🔍 جاري تصفح قسم تقنية المعلومات واستخراج الروابط...")

    job_links = set()
    page = 1

    while page <= MAX_PAGES:
        if page == 1:
            page_url = f"{BASE_URL}/s/jobs/IT-jobs"
        else:
            page_url = f"{BASE_URL}/s/jobs/IT-jobs/page/{page}"

        print(f"\n📄 جاري البحث في الصفحة {page}:")
        print(page_url)

        html = get_page(page_url, render_js=True)

        if not html:
            print(f"⚠️ تعذر تحميل الصفحة {page} - سيتم تجربة الصفحة التالية")
            page += 1
            time.sleep(2)
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_links = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()

            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(BASE_URL, href).split("?")[0]

            if "saudi.tanqeeb.com" not in full_url:
                continue

            ignored_parts = [
                "/search", "/privacy", "/terms", "/contact",
                "/about", "/login", "/register", "/companies",
                "/categories", "/sites/"
            ]

            if any(part in full_url for part in ignored_parts):
                continue

            if any(domain in full_url for domain in [
                "facebook.com", "twitter.com", "linkedin.com",
                "whatsapp.com", "sharer"
            ]):
                continue

            if re.search(r"/jobs/\d+\.html$", full_url):
                page_links.add(full_url)

        print(f"📌 عدد روابط الوظائف المكتشفة في الصفحة {page}: {len(page_links)}")

        if page_links:
            new_links_in_page = page_links - job_links

            print(f"🆕 روابط جديدة في هذه الصفحة: {len(new_links_in_page)}")
            job_links.update(new_links_in_page)

            print(f"📊 إجمالي الروابط التي سيتم سحبها: {len(job_links)}")
        else:
            print(f"⚠️ لم يتم العثور على روابط في الصفحة {page}")

        if len(job_links) >= NUMBER_OF_JOBS:
            print(f"\n🎯 تم الوصول إلى العدد المطلوب ({NUMBER_OF_JOBS}) من الروابط.")
            break

        print(f"⏭️ الانتقال للصفحة التالية...")
        page += 1
        time.sleep(2)

    print(f"\n🎯 إجمالي الروابط المستخرجة: {len(job_links)}")
    return list(job_links)


def scrape_job(job_url):
    print("\n" + "-" * 70)
    print(f"جاري سحب (Raw): {job_url}")

    html = get_page(job_url, render_js=True)
    if not html:
        print("❌ فشل تحميل الصفحة، سيتم حفظ سجل فارغ أو تخطيه بالكامل كـ فشل اتصال")
        # في حالة الـ Raw الصارم، لو الصفحة ما حملت ممكن نرجع سجل يوضح الخطأ، أو نتخطاه إذا ما فيه HTML أصلاً
        return {
            "job_title": "Failed to Fetch",
            "company_name": "Not Specified",
            "location": "Not Specified",
            "posted_date": "Not Specified",
            "employment_type": "Not Specified",
            "job_description": "",
            "job_url": job_url,
            "source": "tanqeeb",
            "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    soup = BeautifulSoup(html, "html.parser")
    json_ld = soup.find("script", type="application/ld+json")
    ld_data = {}

    if json_ld:
        try:
            raw_json = json.loads(json_ld.string)
            if isinstance(raw_json, list):
                for item in raw_json:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        ld_data = item
                        break
            elif isinstance(raw_json, dict) and raw_json.get("@type") == "JobPosting":
                ld_data = raw_json
        except Exception:
            pass

    title_elem = soup.find("h3", class_="job-title-text") or soup.find("h1")
    job_title = (
        ld_data.get("title")
        or (title_elem.get_text(strip=True) if title_elem else None)
        or "Not Specified"
    )

    comp_elem = soup.find("a", class_="job-meta-company")
    hiring_org = ld_data.get("hiringOrganization", {})
    ld_company = hiring_org.get("name") if isinstance(hiring_org, dict) else None

    company_name = (
        ld_company
        or (comp_elem.get_text(strip=True) if comp_elem else None)
        or "Not Specified"
    )

    location = "Saudi Arabia"
    loc_elem = soup.find("div", class_="job-meta-item")
    if loc_elem:
        extracted_location = loc_elem.get_text(" ", strip=True)
        if extracted_location:
            location = extracted_location

    location = re.sub(r"\s+", " ", location).strip()

    posted_date = ld_data.get("datePosted", "Not Specified")
    if posted_date and "T" in posted_date:
        posted_date = posted_date.split("T")[0]

    desc_body = soup.find("div", id="jobDescriptionBody") or soup.find("div", {"data-jb-field": "description"})
    if desc_body:
        full_description = desc_body.get_text(separator="\n", strip=True)
    else:
        raw_desc = ld_data.get("description", "")
        full_description = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n", strip=True) if raw_desc else ""

    full_description = re.sub(r"\n\s*\n", "\n", full_description).strip()

    employment_type = ld_data.get("employmentType", "Not Specified")
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # [Raw Pure]: تم إزالة الشروط التي تحذف الوظائف (مثل طول العنوان أو فراغ الوصف)
    job_record = {
        "job_title": job_title,
        "company_name": company_name,
        "location": location,
        "posted_date": posted_date,
        "employment_type": employment_type,
        "job_description": full_description,
        "job_url": job_url,
        "source": "tanqeeb",
        "extracted_at": current_timestamp
    }

    print(f"📥 تم سحب السجل الخام: {job_title} | {company_name}")
    return job_record


def main():
    print("=" * 70)
    print("Tanqeeb Saudi - Pure Raw Jobs Extractor (Bronze Layer)")
    print("=" * 70)
    
    new_job_links = get_job_links()

    if not new_job_links:
        print("❌ لم يتم العثور على روابط جديدة.")
        return

    random.shuffle(new_job_links)
    selected_links = new_job_links[:NUMBER_OF_JOBS]

    print(f"\n🎲 تم اختيار {len(selected_links)} روابط للسحب الخام...")

    raw_jobs = []
    
    for index, job_url in enumerate(selected_links, start=1):
        print(f"\n[{index}/{len(selected_links)}]")
        
        job = scrape_job(job_url)
        if job:
            raw_jobs.append(job)
        time.sleep(1.5)

    if not raw_jobs:
        print("\n✨ لم يتم جمع أي بيانات.")
        return

    print(f"\n💾 جاري حفظ البيانات الخام محلياً...")
    save_jobs(raw_jobs)

    upload_to_adls_gen2(raw_jobs, source_name="tanqeeb")

    print("\n" + "=" * 70)
    print(f"✅ تم الانتهاء بنجاح (Bronze Layer)!")
    print(f"   • إجمالي السجلات الخام المسحوبة: {len(raw_jobs)}")
    print(f"   • المسار المحلي: {JOBS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()