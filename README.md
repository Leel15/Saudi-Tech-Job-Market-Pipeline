# Job Data Pipeline (Saudi Arabia Tech Market Analytics)

A modular, scalable, and collaborative data pipeline designed to collect, aggregate, and structure tech job market data across Saudi Arabia.
---

## 🏗️ Directory Structure

```
Job-Data-Pipeline/
├── Ingestion/                          <-- Scraper scripts and API fetchers for raw job boards
│   ├── Tanqeeb.py                     
│   ├── freehire.py                   
│   ├── jooble_api.py                   
│   └── jsearch.py                     
├── Transformation/                     <-- Standardization, cleaning, and transformation pipelines
├── data/                               <-- Medallion architecture storage layers (Bronze, Silver, Gold)
│   ├── MARTS/                        <-- Gold layer for analytics-ready datasets, aggregates & metrics
│   ├── STAGING/                      <-- Silver layer for cleaned, deduplicated & standardized files
│   └── RAW/                            <-- Bronze layer for raw, untransformed scraper and API dumps
├── .env.example                        <-- Template file outlining required environment variables
├── .gitignore                         
└── README.md                           <-- Project documentation and setup guide                            
```

---


## 📋 Phase 0: Source Inventory & Selection Reasoning

As part of our initial project investigation phase, we evaluated multiple job platforms to establish a robust and comprehensive dataset for the Saudi technology market

## Overview
We identified and integrated 5 primary data sources covering the Saudi job market from different collection methods:

# 📊 Data Sources - Initial Extraction Rate

| Source | URL/Identifier | Collection Method | Format |
|:---:|:---:|:---:|:---:|
| **Tanqeeb** | https://saudi.tanqeeb.com | Web Scraping | JSON |
| **JSearch** | https://rapidapi.com/letscrape | API with Key | JSON | 
| **FreeHire** | https://freehire.me/jobs | Direct Endpoint | JSON | 
| **Tapneo** | https://tapneo-data.com | File-based source | CSV/JSON 
| **Jooble** | https://sa.jooble.org | API with Key | JSON 

---


## Selection Reasoning

We implemented a multi-source hybrid extraction strategy combining reliable, structured API providers (Jooble, JSearch, FreeHire) with targeted web scraping (Tanqeeb) and file-based ingestion (Tapneo). This ensures broad coverage of tech job postings across the Kingdom while avoiding platform limitations. Other potential sources with heavy login walls or strict rate limits were dropped after initial access testing.

## 🚀 Getting Started

### **1. Clone the Repository**

Clone the project repository to your local machine:

```bash
git clone https://github.com/Leel15/Job-Data-Pipeline.git
cd Job-Data-Pipeline
```

### **2. Install Dependencies**

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### **3. Configure Environment Variables**

Create a file named `.env` in the root project directory (`Job-Data-Pipeline/`).

Add your private API keys in the following format:

```
SCRAPEOPS_API_KEY=your_scrapeops_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

---

## 🛡️ Deduplication Strategy

The scrapers are configured to automatically read existing records from the Raw Data JSON files (`_tech.json`) pushed exclusively to GitHub.

When team members pull the latest updates and run a scraper, the system automatically detects previously saved links and skips them, completely preventing duplicate data without requiring local cache files to be committed.

---


## ⚙️ Configuration


### Git Ignore Rules

The `.gitignore` file protects:
- `.env` (local secrets)
- Local cache and temporary files
- System-specific files


---

## ⚠️ Important Notes

- **Never commit `.env`** — it contains sensitive API keys
- **Pull before pushing** to avoid merge conflicts
- **Keep scrapers modular** for easy maintenance and scaling

