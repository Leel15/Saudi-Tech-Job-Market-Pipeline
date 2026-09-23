import re
import os
import json
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from typing import List, Set

TECHNICAL_SKILLS = {
    'python', 'java', 'c#', '.net', 'c++', 'javascript', 'typescript', 'sql', 'html', 'css', 'php', 'ruby', 'golang',
    'rust', 'swift', 'kotlin', 'scala', 'matlab', 'perl', 'groovy', 'bash', 'shell', 'powershell',
    'react', 'vue', 'angular', 'angularjs', 'next.js', 'nuxt', 'svelte', 'ember', 'backbone', 'jquery', 'bootstrap',
    'tailwind', 'webpack', 'babel', 'gulp', 'grunt', 'npm', 'yarn', 'pnpm', 'rest api', 'graphql', 'websocket', 'http',
    'ajax', 'json', 'xml', 'soap', 'wsdl',
    'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot', 'hibernate', 'sqlalchemy', 'mongodb',
    'mysql', 'postgresql', 'oracle', 'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'couchdb', 'firestore', 'aws',
    'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'ci/cd',
    'sql server', 'mariadb', 'sqlite', 'neo4j', 'memcached', 'rabbitmq', 'kafka', 'activemq', 'apachespark', 'hadoop',
    'hive', 'pig',
    'git', 'svn', 'jenkins', 'gitlab', 'github', 'bitbucket', 'terraform', 'ansible', 'puppet', 'chef', 'vagrant',
    'docker-compose', 'helm', 'prometheus', 'grafana', 'logstash', 'kibana', 'elk',
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'pandas', 'numpy',
    'scipy', 'matplotlib', 'seaborn', 'nlp', 'natural language processing', 'computer vision', 'opencv', 'cvat', 'yolo',
    'rcnn', 'lstm', 'rnn', 'cnn', 'xgboost', 'lightgbm', 'catboost', 'reinforcement learning', 'llm',
    'large language model', 'gpt', 'bert', 'transformer',
    'cybersecurity', 'information security', 'network security', 'firewall', 'ccna', 'ccnp', 'ccna collaboration',
    'networking', 'vpn', 'ssl', 'tls', 'ssh', 'https', 'dns', 'dhcp', 'ldap', 'kerberos', 'oauth', 'saml', 'encryption',
    'cryptography', 'penetration testing', 'vulnerability', 'governance',
    'amazon web services', 's3', 'ec2', 'lambda', 'rds', 'sqs', 'sns', 'cloudformation', 'microsoft azure',
    'app service', 'sql database', 'cosmos db', 'google cloud platform', 'app engine', 'cloud functions',
    'cloud storage', 'bigquery', 'dataflow',
    'devops', 'devsecops', 'sre', 'site reliability engineering', 'openshift', 'rancher', 'argocd', 'flux',
    'containerization', 'containers', 'azure devops', 'aws devops', 'pulumi', 'github actions', 'circleci', 'travis ci',
    'buildkite',
    'siem', 'soar', 'soc', 'edr', 'xdr', 'ids', 'ips', 'waf', 'zero trust', 'zero trust architecture', 'iam', 'pam',
    'privileged access management', 'vulnerability management', 'security operations', 'security monitoring',
    'threat intelligence', 'threat hunting', 'digital forensics', 'malware analysis', 'secure coding',
    'application security', 'cloud security', 'endpoint security', 'security testing', 'burp suite', 'wireshark',
    'nmap', 'metasploit', 'owasp', 'owasp top 10',
    'android', 'ios', 'flutter', 'react native', 'ionic', 'xamarin', 'native development', 'mobile development',
    'appium',
    'agile', 'microsoft sql server', 'pl/sql', 't-sql', 'postgres', 'oracle database', 'oracle sql', 'mongodb atlas',
    'database administration', 'dba', 'database design', 'database optimization', 'database performance',
    'stored procedures',
    'apache airflow', 'airflow', 'dbt', 'databricks', 'snowflake', 'azure data factory', 'adf', 'aws glue', 'aws emr',
    'kinesis', 'flink', 'spark', 'pyspark', 'data engineering', 'data engineering', 'data pipeline', 'data lakehouse',
    'data modeling', 'etl', 'elt', 'data ingestion', 'data integration', 'data quality', 'data governance',
    'oracle fusion', 'oracle erp', 'odoo', 'enterprise resource planning', 'business intelligence', 'dwh',
    'power bi', 'tableau', 'looker', 'qlik', 'microstrategy', 'cognos', 'sisense', 'google analytics', 'ga4',
    'google tag manager', 'gtm', 'adobe analytics', 'mixpanel', 'amplitude', 'segment', 'analytics',
    'unreal engine', 'unity', 'blender', '3ds max', 'maya',
    'microsoft dynamics', 'power apps', 'power automate', 'power query', 'dataverse', 'fhir', 'hl7',
    'health information exchange',
    'wordpress', 'drupal', 'joomla', 'shopify', 'magento', 'woocommerce', 'adobe commerce', 'cms',
    'content management system', 'headless cms',
    'microservices', 'serverless', 'identity access management', 'oauth2', 'jwt', 'api gateway', 'service mesh',
    'istio', 'envoy', 'circuit breaker', 'load balancing', 'cdn', 'content delivery', 'message queue',
    'event streaming', 'event-driven', 'cqrs', 'saga', 'outsystems', 'low-code', 'no-code', 'rpa',
    'robotic process automation', 'artificial intelligence', 'gen ai', 'generative ai', 'prompt engineering', 'algolia',
    'solr', 'search engine', 'full-text search',
    'hugging face', 'huggingface', 'transformers', 'langchain', 'llamaindex', 'rag', 'retrieval augmented generation',
    'fine tuning', 'fine-tuning', 'embeddings', 'vector database', 'vector databases', 'pinecone', 'weaviate', 'chroma',
    'faiss', 'mlflow', 'kubeflow', 'onnx', 'generative artificial intelligence', 'genai', 'ai agents', 'agentic ai',
    'network administration', 'network engineering', 'network infrastructure', 'tcp/ip', 'ipv4', 'ipv6', 'bgp', 'ospf',
    'vlan', 'wan', 'lan', 'wlan', 'load balancer', 'proxy', 'reverse proxy', 'fortigate', 'palo alto', 'cisco',
    'juniper', 'arista', 'sdn', 'sd-wan',
    'object oriented programming', 'oop', 'functional programming', 'design patterns', 'solid principles',
    'software architecture', 'system design', 'clean architecture', 'clean code', 'unit testing', 'integration testing',
    'end-to-end testing', 'tdd', 'bdd', 'code review', 'version control', 'api development', 'api integration',
    'software development lifecycle', 'sdlc',
    'qa', 'quality assurance', 'quality control', 'software testing', 'automation testing', 'test automation',
    'selenium', 'cypress', 'playwright', 'postman', 'junit', 'testng', 'pytest', 'jest', 'mocha', 'jmeter',
    'load testing', 'performance testing', 'regression testing', 'api testing',
    'asp.net', 'asp.net core', '.net framework', 'entity framework', 'entity framework core', 'ef core', 'blazor',
    'microsoft sql', 'sharepoint', 'power platform', 'active directory', 'azure active directory', 'entra id',
    'microsoft 365', 'office 365', 'ui', 'ux',
    'android studio', 'jetpack compose', 'kotlin multiplatform', 'objective-c', 'swiftui', 'capacitor', 'cordova'
}

STOP_WORDS = {
    'and', 'or', 'the', 'a', 'an', 'with', 'without', 'for', 'to', 'of', 'in',
    'experience', 'knowledge', 'skill', 'skills', 'required', 'preferred',
    'ability', 'strong', 'expertise', 'proficiency', 'advanced', 'basic',
    'understanding', 'hands-on', 'proven', 'excellent', 'good', 'very',
    'must', 'should', 'can', 'will', 'would', 'could', 'have', 'has',
    'working', 'work', 'project', 'projects', 'team', 'teams',
    'key', 'main', 'primary', 'secondary', 'supporting',
}

SPECIAL_SKILL_PATTERNS = {
    'ai': r'\b(?:ai|artificial intelligence)\b',
    'r': r'\bR\s+(?:programming|language|studio)\b',
    'go': r'\b(?:golang|go\s+(?:programming|language|developer|development))\b',
    'bi': r'\b(?:BI|business intelligence)\b',
}


def normalize_skill(skill: str) -> str:
    if not skill:
        return ""
    skill = skill.lower().strip()
    skill = re.sub(r'[\(\)\[\]\{\}<>]', '', skill)
    skill = re.sub(r'\.+', '', skill)
    skill = re.sub(r'\s+', ' ', skill).strip()
    skill = skill.replace('-', ' ')
    corrections = {
        'c #': 'c#', 'c # ': 'c#', '.net core': '.net', 'node .js': 'node.js',
        'nodejs': 'node.js', 'nextjs': 'next.js', 'asp .net': 'asp.net',
        'machine_learning': 'machine learning', 'deep_learning': 'deep learning',
        'natural_language_processing': 'nlp', 'computer_vision': 'computer vision',
    }
    for wrong, correct in corrections.items():
        if wrong in skill:
            skill = skill.replace(wrong, correct)
    return skill


def extract_tech_skills(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'[^\w\s\-\.\/\+#]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    found_skills: Set[str] = set()

    for key, pattern in SPECIAL_SKILL_PATTERNS.items():
        if re.search(pattern, text):
            found_skills.add(normalize_skill(key))

    for skill in sorted(TECHNICAL_SKILLS, key=len, reverse=True):
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            found_skills.add(normalize_skill(skill))

    compound_skills = [
        r'machine\s+learning', r'deep\s+learning', r'natural\s+language\s+processing',
        r'computer\s+vision', r'reinforcement\s+learning', r'feature\s+engineering',
        r'data\s+science', r'data\s+analysis', r'api\s+gateway', r'service\s+mesh',
        r'api\s+integration', r'cloud\s+computing', r'edge\s+computing', r'quantum\s+computing',
        r'blockchain\s+technology', r'iot\s+development', r'web\s+development',
        r'mobile\s+development', r'full[\s\-]?stack', r'front[\s\-]?end', r'back[\s\-]?end',
        r'devops', r'dev\s+ops', r'mlops', r'ml\s+ops', r'enterprise\s+resource\s+planning',
        r'business\s+intelligence', r'content\s+management', r'learning\s+management',
        r'relationship\s+management', r'identity\s+and\s+access', r'risk\s+management',
        r'project\s+management', r'information\s+security', r'network\s+security',
        r'cyber\s+security', r'penetration\s+testing', r'vulnerability\s+assessment',
        r'incident\s+response', r'disaster\s+recovery', r'business\s+continuity',
    ]
    for pattern in compound_skills:
        match = re.search(pattern, text)
        if match:
            skill_text = normalize_skill(match.group())
            if skill_text and skill_text not in STOP_WORDS:
                found_skills.add(skill_text)

    final_skills = []
    for skill in found_skills:
        if (skill and len(skill) > 1 and skill not in STOP_WORDS and not skill.isdigit()):
            final_skills.append(skill)
    return sorted(list(set(final_skills)))


def clean_company_name(company_str):
    if pd.isna(company_str) or not str(company_str).strip():
        return None
    cleaned = re.sub(r'^(client of\s+)', '', str(company_str).strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def clean_job_title(job_description="", company_name=""):
    if pd.isna(job_description) or not str(job_description).strip():
        return "Technical Professional"

    desc_str = str(job_description).strip()
    desc_lower = desc_str.lower()
    comp_lower = str(company_name).lower()

    non_tech_titles = [
        "pmc electrical engineer", "pmc mechanical engineer", "pmc process engineer",
        "pmc piping engineer", "pmc civil structural engineer", "pmc instrumentation control engineer",
        "Sales Engineer",
        "estimation design engineer", "production engineer", "survey engineer", "data collector",
        "Data Center Mechanical Engineer"
    ]

    for title in non_tech_titles:
        if title in desc_lower:
            return "Technical Professional"

    common_roles_list = [
        "senior specialist reporting", "Senior Forward Deploy Engineer", "database application security specialist",
        "data strategist", "enterprise architect",
        "Specialist Reporting", "technical support engineer", "The Lead Engineer System Integration",
        "AI Data Collection", "Develop and maintain responsive web applications", "Business Analytics",
        "Software Quality Engineer", "Personal Data Protection", "Senior Business Intelligence Specialist",
        "Mining Technology Engineer",
        "developer intern", "system admin engineer", "senior system engineer", "senior data engineer",
        "AWS Infrastructure Services",
        "staff data engineer", "principal data engineer", "data engineer ii", "data engineer",
        "Senior Security Engineer", "Shopper Insights Manager",
        "senior data analyst", "business data analyst", "data analyst", "senior data scientist", "data scientist",
        "Operations Engineer",
        "machine learning engineer", "machine learning scientist", "ai engineer", "ai specialist", "analytics engineer",
        "business intelligence analyst", "business intelligence developer", "senior software engineer",
        "software engineer", "Media Search Analyst",
        "software developer", "full stack developer", "full stack engineer", "frontend developer", "frontend engineer",
        "Identity Security Engineer",
        "backend developer", "backend engineer", "mobile developer", "application developer", "cloud engineer",
        "cloud architect", "devops engineer", "platform engineer", "solutions architect",
        "cybersecurity engineer", "data security engineer", "security engineer", "cybersecurity analyst",
        "security analyst", "Systems Engineer",
        "information security analyst", "soc analyst", "product manager", "project manager",
        "technical project manager",
        "program manager", "engineering manager", "business analyst", "systems analyst", "systems administrator",
        "Payment Systems Engineer",
        "integration specialist", "sap consultant", "sap ec consultant", "sap successfactors consultant",
        "Data Collector", "Software Support Engineer",
        "flight data monitoring analyst", "data platform engineer", "observability engineer",
        "Business Intelligence Engineer", "Analyze RFPs RFQs", "Data Center Engineering Operations Engineer",
        "qa engineer", "software quality assurance engineer", "sales engineer", "solutions engineer",
        "Business Intelligence Senior Specialist", "Source Code Management", "CT System Engineer", "Junior Engineer"
    ]

    for role in sorted(set(common_roles_list), key=len, reverse=True):
        if role.lower() in desc_lower:
            return role.title()

    inline_title_match = re.search(
        r'job\s*title[:\s\-]*([A-Za-z0-9/&,\-\s]{3,45})(?=location|position|about|summary|requirements|$)', desc_str,
        re.IGNORECASE)
    if inline_title_match:
        t = inline_title_match.group(1).strip()
        t = re.sub(r'\b(location|position|about|summary|requirements|onsite|remote)\b.*$', '', t,
                   flags=re.IGNORECASE).strip()
        if len(t.split()) <= 6:
            return t.title()

    return "Technical Professional"


def clean_job_title_from_location(job_title):
    if not job_title or not isinstance(job_title, str):
        return job_title

    locations = ["الرياض", "جدة", "الدمام", "الخبر", "الجبيل", "Riyadh", "Jeddah", "Dammam", "Al Khobar", "Al Jubail",
                 "Tabuk", "Abha", "Buraydah", "Al Qassim", "Qassim", "Saudi Arabia", "KSA", "Saudi National", "Saudi"]

    cleaned = job_title
    cleaned = re.sub(r'\s*[\-\–\,]?\s*(?:posted|منذ)\s+.*$', '', cleaned, flags=re.IGNORECASE)

    loc_pattern_start = r'^(?:' + '|'.join(re.escape(loc) for loc in locations) + r')[\s\,\-\•\–]+'
    for _ in range(3):
        cleaned = re.sub(loc_pattern_start, '', cleaned, flags=re.IGNORECASE)

    loc_pattern_end = r'\s*[\-\–,]\s*(?:' + '|'.join(
        re.escape(loc) for loc in locations) + r')(?:\s*[\-\–,]\s*(?:' + '|'.join(
        re.escape(loc) for loc in locations) + r'))*$'
    cleaned = re.sub(loc_pattern_end, '', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(
        r'\s*\([^)]*(?:' + '|'.join(re.escape(loc) for loc in locations) + r'|Part Time|Without Accommodation)[^)]*\)$',
        '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^[,\-\s]+|[,\-\s]+$', '', cleaned).strip()

    return cleaned if cleaned else job_title


def is_valid_tech_job(job_title: str, job_description: str) -> bool:
    if not job_description or not job_title:
        return False

    desc_str = str(job_description).lower()
    title_lower = str(job_title).lower()

    if "???" in desc_str or desc_str.count('?') > 5:
        return False

    non_tech_keywords = [
        "sales engineer", "electronics engineer", "structural engineer",
        "civil engineer", "mechanical engineer", "electrical engineer",
        "health quality", "nurse", "accountant", "hr specialist",
        "supply chain", "logistics", "procurement", "architect",
        "graphic designer", "graphic design", "visual designer",
        "planning and design", "urban planning", "interior design",
        "construction", "onsite project manager", "civil project manager",
        "design manager", "real estate", "hospitality"
    ]

    for kw in non_tech_keywords:
        if kw in title_lower:
            return False

    return True


def check_if_tech_job(job_title, description, skills):
    title_lower = str(job_title).lower()
    desc_lower = str(description).lower()

    infra_keywords = [
        "نظم تشغيل", "systems specialist", "system specialist", "backup",
        "disaster recovery", "سيرفرات", "network", "IT", "Information Technology"
                                                         "sysadmin", "system administrator", "cloud", "devops",
        "systems"
    ]

    if any(keyword in title_lower or keyword in desc_lower for keyword in infra_keywords):
        return True

    strict_blocklist = [
        "طبيب", "استشاري أمراض جلدية", "صيدلي", "تمريض", "doctor", "dermatologist", "medical", "nurse",
        "استقطاب المواهب", "موظف استقطاب", "مورد بشري", "hr", "talent acquisition", "recruiter", "recruitment",
        "هيدروليكية", "ميكانيكي", "فني أنظمة", "حفر", "مفتش مراقبة الجودة", "hydraulic", "mechanic", "technician",
        "civil", "structural",
        "محتوى رياضي", "توطين المحتوى", "مصمم جرافيك", "مترجم", "content", "translation", "graphic designer",
        "sports content",
        "تطوير أعمال", "مبيعات", "مدير حسابات", "business development", "sales", "account manager",
        "Enterprise Architec"
    ]

    for word in strict_blocklist:
        if word in title_lower or word in desc_lower:
            return False

    tech_degrees = [
        "علوم الحاسب", "تقنية المعلومات", "هندسة البرمجيات", "هندسة الحاسب",
        "نظم المعلومات", "الأمن السيبراني", "الذكاء الاصطناعي", "علم البيانات",
        "computer science", "information technology", "software engineering",
        "computer engineering", "information systems", "cybersecurity",
        "artificial intelligence", "data science"
    ]

    if any(deg in desc_lower for deg in tech_degrees):
        return True

    if skills and len(skills) > 0:
        return True

    return False


def clean_city(location_str):
    if pd.isna(location_str) or not str(location_str).strip():
        return None

    loc_lower = str(location_str).strip().lower()

    blacklisted_platforms = {
        "linkedin", "foundit", "gulftalent", "bayt", "wuzzuf",
        "naukrigulf", "jobleads", "arabianreccom", "indeed", "glassdoor"
    }

    if loc_lower in blacklisted_platforms or any(p in loc_lower for p in blacklisted_platforms):
        return None

    city_mapping = {
        "الرياض": "Riyadh", "riyadh": "Riyadh",
        "جدة": "Jeddah", "jeddah": "Jeddah",
        "المدينة المنورة": "Medina", "medina": "Medina", "madinah": "Medina",
        "مكة المكرمة": "Mecca", "مكة": "Mecca", "makkah": "Mecca", "mecca": "Mecca",
        "الدمام": "Dammam", "dammam": "Dammam",
        "الخبر": "Al Khobar", "khobar": "Al Khobar", "al khobar": "Al Khobar",
        "الجبيل": "Al Jubail", "jubail": "Al Jubail", "al jubail": "Al Jubail",
        "ينبع": "Yanbu", "yanbu": "Yanbu",
        "القصيم": "Al Qasim", "qassim": "Al Qasim", "al qasim": "Al Qasim", "بريدة": "Buraydah", "buraydah": "Buraydah",
        "الظهران": "Dhahran", "dhahran": "Dhahran",
        "تبوك": "Tabuk", "tabuk": "Tabuk",
        "أبها": "Abha", "abha": "Abha", "خميس مشيط": "Khamis Mushait",
        "حائل": "Hail", "hail": "Hail",
        "نجران": "Najran", "najran": "Najran",
        "جازان": "Jazan", "jazan": "Jazan",
        "الطائف": "Taif", "taif": "Taif"
    }

    for key, val in city_mapping.items():
        if key in loc_lower:
            return val

    if loc_lower in {"saudi arabia", "ksa", "kingdom of saudi arabia", "eastern province", "السعودية"}:
        return None

    return None


def clean_employment_type(emp_type, desc_str=""):
    combined_text = f"{str(emp_type)} {str(desc_str)}".lower()

    if "part-time" in combined_text or "part time" in combined_text or "دوام جزئي" in combined_text:
        return "Part-time"
    elif "contract" in combined_text or "عقد" in combined_text or "freelance" in combined_text:
        return "Contract"
    elif "full-time" in combined_text or "full time" in combined_text or "دوام كامل" in combined_text:
        return "Full-time"

    return "Full-time"


def extract_education(desc_str):
    if pd.isna(desc_str) or not str(desc_str).strip():
        return None

    desc_lower = str(desc_str).lower()

    if any(term in desc_lower for term in
           ["bachelor", "bachelors", "bsc", "b.sc", "بكالوريوس", "b.tech", "البكالوريوس"]):
        return "Bachelor"
    elif any(term in desc_lower for term in ["master", "masters", "ماجستير", "mba"]):
        return "Master"
    elif any(term in desc_lower for term in ["phd", "ph.d", "دكتوراه", "doctorate"]):
        return "PhD"
    elif any(term in desc_lower for term in ["high school", "ثانوي", "دبلوم", "diploma"]):
        return "High School / Diploma"

    return None


def clean_jsearch_location(raw_location) -> str:
    if not raw_location or not isinstance(raw_location, str):
        return None
    translated = raw_location.replace("•", "-")
    translated = re.sub(r"\s{2,}", " ", translated).strip()
    return clean_city(translated)


def parse_relative_date(posted_str):
    if not posted_str or pd.isna(posted_str):
        return datetime.now().strftime('%Y-%m-%d')
    posted_str = str(posted_str).strip()
    today = datetime.now()
    numbers = re.findall(r'\d+', posted_str)
    if numbers:
        days_ago = int(numbers[0])
        approx_date = today - timedelta(days=days_ago)
        return approx_date.strftime('%Y-%m-%d')
    return today.strftime('%Y-%m-%d')


def clean_html_text(raw_text: str) -> str:
    if not raw_text or pd.isna(raw_text):
        return ""
    soup = BeautifulSoup(str(raw_text), "html.parser")
    return soup.get_text(separator=" ", strip=True)


def clean_description(desc, job_title=""):
    if pd.isna(desc) or not str(desc).strip():
        return ""

    clean_text = re.sub(r'<[^<]+?>', '', str(desc))

    clean_text = clean_text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")

    if job_title:
        clean_text = re.sub(rf'^(?:job title:|وصف الوظيفة:?)\s*{re.escape(job_title)}\s*', '', clean_text,
                            flags=re.IGNORECASE)

    intro_phrases = [
        r'وصف الوظيفة', r'Job Summary', r'About the Role', r'About the job',
        r'Job Purpose', r'Position Overview', r'Job Description', r'متطلبات الوظيفة',
        r'المهارات المطلوبة', r'Required Qualifications', r'Company Description',
        r'About the Company', r'Job Description :'
    ]

    for phrase in intro_phrases:
        pattern = rf'^(?:[\s\-\:\•\📍\|]*{phrase})[\s\-\:\•\📍\|]*'
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)

    clean_text = re.sub(r'[\*\•\❖\✔\#\—\–]', ' ', clean_text)

    clean_text = re.sub(r'View email address on [^\s]+', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'#J-\d+-[a-zA-Z]+', '', clean_text)

    clean_text = re.sub(r'[\r\n\t]+', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


def format_date(date_val):
    if pd.isna(date_val):
        return None
    try:
        parsed_date = pd.to_datetime(date_val)
        return parsed_date.strftime("%Y-%m-%d")
    except Exception:
        return None


def deduplicate_by_content(df, subset_cols: list, date_col: str = "posted_date"):
    df = df.copy()
    df["repost_count"] = df.groupby(subset_cols)[subset_cols[-1]].transform("count")
    df = df.sort_values(date_col, na_position="last").drop_duplicates(
        subset=subset_cols, keep="last"
    ).reset_index(drop=True)
    return df


def _build_record_key(record: dict, key_cols: list) -> str:
    return "||".join(str(record.get(col, "")) for col in key_cols)


def load_existing_processed(json_path: str, key_cols: list) -> dict:
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing_list = json.load(f)
        return {_build_record_key(rec, key_cols): rec for rec in existing_list}
    except Exception:
        return {}


def merge_and_save_processed(new_df, json_path: str, key_cols: list, fresh: bool = False):
    now = datetime.now(timezone.utc).isoformat()
    base_dir = os.path.dirname(json_path)
    json_dir = os.path.join(base_dir, "json")
    csv_dir = os.path.join(base_dir, "csv")

    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    filename = os.path.basename(json_path)
    actual_json_path = os.path.join(json_dir, filename)
    csv_filename = filename.rsplit(".", 1)[0] + ".csv"
    actual_csv_path = os.path.join(csv_dir, csv_filename)

    if fresh and os.path.exists(actual_json_path):
        os.remove(actual_json_path)

    existing = load_existing_processed(actual_json_path, key_cols) if not fresh else {}

    for record in new_df.to_dict(orient="records"):
        key = _build_record_key(record, key_cols)
        if key in existing:
            record["first_seen"] = existing[key].get("first_seen", now)
            record["last_seen"] = now
        else:
            record["first_seen"] = now
            record["last_seen"] = now
        existing[key] = record

    final_list = list(existing.values())
    final_df = pd.DataFrame(final_list)

    with open(actual_json_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2, default=str)

    with open(actual_json_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    file_content = re.sub(
        r'("skills":\s*)\[\s*([^\]]+?)\s*\]',
        lambda m: m.group(1) + '[' + ', '.join(
            [s.strip() for s in m.group(2).replace('\n', '').split(',') if s.strip()]) + ']',
        file_content,
        flags=re.DOTALL
    )

    with open(actual_json_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    print(f"💾 تم حفظ JSON  في: {actual_json_path}")
    final_df.to_csv(actual_csv_path, index=False, encoding="utf-8-sig")
    print(f"💾 تم حفظ CSV في: {actual_csv_path}")