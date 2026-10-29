# PAN-INDIA CIVIL & CONSTRUCTION BUSINESS LEAD EXTRACTION SYSTEM

An enterprise-grade, autonomous web scraping and lead intelligence system built with **Python, Flask, HTML5, CSS3, and JavaScript**. 

Designed specifically for the Indian construction and civil contracting ecosystem to extract verified business contacts across all 28 States, 8 Union Territories, and 780+ districts without any paid APIs, API keys, or databases.

---

## 🌟 Key Features

1. **Complete PAN-India Coverage**:
   - All 28 States and 8 Union Territories with verified official districts.
   - Cascading State–District selector with Multi-Select, Select All, and instant presets (e.g., *Only Erode*, *Tamil Nadu*, *All India*).
   - Optional specific City / Town / Locality filtering (e.g., Perundurai, Bhavani).

2. **Strict Construction Industry Taxonomy**:
   - Civil Contractors & Infrastructure Developers
   - Building Contractors & Commercial Builders
   - Architects & Architectural Planners
   - Structural Engineers & RCC Consultants
   - Interior Contractors & Fit-Out Specialists
   - Road, Highway & Paving Contractors
   - MEP, Electrical & Plumbing Contractors
   - Painting & Waterproofing Contractors
   - Government Approved (PWD/CPWD/Class-1) Contractors
   - Earthmoving, Demolition & Foundation Contractors
   - Ready Mix Concrete (RMC) & Material Suppliers

3. **Multi-Source Discovery Engine (Zero Paid APIs / Zero API Keys)**:
   - Automated query generation targeting public web pages.
   - Multi-engine fallback: DDGS, Bing search scraping with base64 uncloaking, Yahoo search, public directories.
   - Discovers authentic company websites, domain landing pages, and authorized public listings.

4. **Deep Child-Page Crawling**:
   - For every discovered business domain, the crawler analyzes internal links and automatically visits child pages:
     - `/contact`, `/contact-us`, `/about`, `/about-us`, `/reach-us`, `/locations`, `/branches`
   - Aggregates mobile numbers, landlines, emails, and address lines across all pages.

5. **Strict Indian Contact & Category Verification**:
   - **Indian Mobile Validation**: +91 / 10-digit formats starting with 6, 7, 8, or 9 verified using Google's `phonenumbers` library.
   - **Office / Landline Numbers**: Verified Indian STD codes (e.g. `0424` for Erode, `044` for Chennai).
   - **Email Validation**: Strict regex discarding placeholder domains (`example.com`, `domain.com`) and static asset extensions (`.png@`, `.jpg@`).
   - **Strict Category Filtering**: Compares page content against specific domain keywords, discarding irrelevant pages (e.g. Wikipedia, job listings).
   - **Exact Source URL**: Captures the exact URL where each lead was discovered.

6. **Genuine Deduplication**:
   - Tracks phone numbers, emails, and domains to eliminate duplicates while preserving distinct physical branches.

7. **Full Execution Controls & Live Monitoring**:
   - Working **Start**, **Pause**, **Resume**, and **Stop** controls.
   - Real-time progress bar, task counter, and live website crawl monitor.
   - Live streaming terminal log feed.
   - Searchable live leads preview data grid.

8. **Corporate Excel (.xlsx) & CSV Export**:
   - Beautifully styled Excel export with styled headers, alternating rows, auto-sized columns, and clickable links.
   - Metadata audit sheet guaranteeing verified public data.

---

## 🚀 How to Run

1. Open PowerShell or Command Prompt in `g:\civil`.
2. Run the application:
   ```powershell
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

## 🏗️ Project Architecture

```
g:\civil\
├── app.py                      # Flask server, REST APIs & routes
├── requirements.txt            # Python dependencies
├── core\
│   ├── extractor.py            # Discovery, child page crawler, contact validator
│   ├── task_manager.py         # Threaded runner, Start/Pause/Resume/Stop, live logs
│   └── exporter.py             # OpenPyXL & CSV export with styling & metadata
├── data\
│   └── india_data.py           # 36 States/UTs, 780+ districts, category taxonomy
├── static\
│   ├── css\
│   │   └── style.css           # Executive responsive dashboard styling
│   └── js\
│       └── app.js              # State cascade, live polling, table updates
├── templates\
│   └── index.html              # Modern single-page application interface
└── exports\                    # Generated Excel & CSV downloads
```
