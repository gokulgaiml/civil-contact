import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
from core.extractor import BusinessLeadExtractor
from data.india_data import CONSTRUCTION_CATEGORIES

test_urls = [
    'https://www.bluemoonconstruction.in/',
    'https://dir.indiamart.com/chennai/civil-contractors.html',
    'https://www.sulekha.com/building-contractors/avadi-chennai',
    'https://www.jlakshwinbuilder.com/best-consulting-civil-engineer-contractor-in-avadi-chennai',
    'https://www.asklaila.com/category/Chennai/avadi/civil-and-building-contractor/interior-designers-decorators/?category=205'
]

ext = BusinessLeadExtractor(log_callback=print)
cat = CONSTRUCTION_CATEGORIES[0]

for url in test_urls:
    print(f"\n==========================================")
    print(f"Testing URL: {url}")
    cand = {'url': url, 'title': 'Test Title'}
    lead = ext.scrape_business_site(cand, cat, 'Tamil Nadu', 'Chennai', 'Avadi')
    print("RESULT:", lead)
