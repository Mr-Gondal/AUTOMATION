#!/usr/bin/env python3
"""
Cloud Scholarship Finder for Master's/MPhil in Space Science, Meteorology, Remote Sensing & GIS
Runs daily on GitHub Actions - works even when your laptop is off.

Features:
- Searches web daily for new scholarships
- Filters for Master's/MPhil + your fields
- Extracts detailed info: country, university, deadline, funding amount
- Sends rich Email + Telegram digest with full details
"""

import os
import json
import smtplib
import requests
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ddgs import DDGS
from dateutil import parser

# ============= CONFIGURATION =============
KEYWORDS = [
    "master scholarship meteorology",
    "master scholarship remote sensing",
    "master scholarship GIS",
    "master scholarship \"geographical information\"",
    "master scholarship \"space science\"",
    "master scholarship \"earth observation\"",
    "MPhil scholarship atmospheric science",
    "Erasmus Mundus GIS",
    "DAAD scholarship remote sensing",
    "Commonwealth scholarship meteorology",
    "Fulbright remote sensing",
]

REGIONS = ["international", "Europe", "UK", "Germany", "Sweden", "Netherlands", "Canada", "USA", "Australia", "Japan", "China"]

EXCLUDE_TERMS = ["bachelor", "undergraduate", "phd only", "high school"]

# Country/University patterns
COUNTRY_KEYWORDS = {
    "USA": ["united states", "america", "us", "american"],
    "UK": ["united kingdom", "britain", "british", "england"],
    "Germany": ["germany", "german", "deutschland"],
    "Sweden": ["sweden", "swedish"],
    "Canada": ["canada", "canadian"],
    "Netherlands": ["netherlands", "dutch", "holland"],
    "Australia": ["australia", "australian"],
    "Japan": ["japan", "japanese"],
    "China": ["china", "chinese"],
    "Europe": ["europe", "european"],
}

UNIVERSITIES = {
    "ETH Zurich": "Switzerland",
    "University of Edinburgh": "UK",
    "Technical University of Denmark": "Denmark",
    "Lund University": "Sweden",
    "University of Twente": "Netherlands",
    "University of Copenhagen": "Denmark",
    "Erasmus University": "Netherlands",
    "TU Munich": "Germany",
    "University of Göttingen": "Germany",
}

# ============= EXTRACTION FUNCTION =============
def extract_scholarship_details(title, body, url):
    """Extract structured details from scholarship listing"""
    text_combined = f"{title} {body}".lower()
    
    details = {
        'title': title,
        'url': url,
        'snippet': body[:400],
        'source': 'DuckDuckGo',
        'found': datetime.utcnow().isoformat(),
        'country': extract_country(text_combined),
        'university': extract_university(text_combined, title, body),
        'deadline': extract_deadline(body),
        'funding': extract_funding(text_combined),
        'eligibility': extract_eligibility(text_combined),
    }
    
    return details

def extract_country(text):
    """Extract country from text"""
    text_lower = text.lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return country
    return "International"

def extract_university(text, title, body):
    """Extract university name from text"""
    text_combined = f"{title} {body}"
    
    # Check known universities
    for uni, country in UNIVERSITIES.items():
        if uni.lower() in text_combined.lower():
            return uni
    
    # Try to extract any organization names (basic pattern)
    # Look for "University of X" or "X University" patterns
    uni_patterns = [
        r'(?:university|college|institute) of ([a-z\s&-]+?)(?:\s|-|,|$)',
        r'([a-z\s&-]+?)\s(?:university|college|institute)(?:\s|,|$)',
    ]
    
    for pattern in uni_patterns:
        matches = re.findall(pattern, text_combined.lower())
        if matches:
            return matches[0].title()
    
    return "Not specified"

def extract_deadline(body):
    """Extract deadline date from text"""
    # Common date patterns
    patterns = [
        r'deadline[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})',
        r'apply by[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})',
        r'closing date[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})',
        r'due date[:\s]+([a-zA-Z]+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}\s+[a-zA-Z]+\s+\d{4})',
        r'([a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, body)
        if matches:
            try:
                # Try to parse the date
                parsed = parser.parse(matches[0], fuzzy=True)
                # Only return if it's in the future or within 6 months past
                if parsed.year >= datetime.now().year:
                    return parsed.strftime('%B %d, %Y')
            except:
                pass
    
    return "Check website"

def extract_funding(text):
    """Extract funding amount from text"""
    # Look for currency amounts
    patterns = [
        r'(?:USD|US\$|$|usd)[\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?:EUR|€)[\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?:GBP|£|gbp)[\s]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})+)\s*(?:usd|eur|gbp)',
        r'fully funded|full tuition|complete funding|full scholarship',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            if isinstance(matches[0], str) and matches[0].isdigit() or ',' in matches[0]:
                return f"${matches[0]}"
            else:
                return "Fully Funded"
    
    return "Amount varies"

def extract_eligibility(text):
    """Extract eligibility info"""
    eligibility = []
    
    if "pakistan" in text or "commonwealth" in text:
        eligibility.append("🇵🇰 Pakistan")
    if "international" in text:
        eligibility.append("🌍 International")
    if "women" in text:
        eligibility.append("👩 Women")
    if "developing" in text or "low income" in text:
        eligibility.append("📊 Developing countries")
    
    return ", ".join(eligibility) if eligibility else "Check requirements"

# ============= SEARCH FUNCTION =============
def search_scholarships():
    results = []
    seen_urls = set()
    
    with DDGS() as ddgs:
        for keyword in KEYWORDS:
            try:
                # Search past month to catch deadlines
                search_results = ddgs.text(
                    f"{keyword} 2025 2026",
                    region="wt-wt",
                    safesearch="moderate",
                    timelimit="m",  # past month
                    max_results=15
                )
                
                for r in search_results or []:
                    url = r.get('href', '')
                    title = r.get('title', '')
                    body = r.get('body', '')
                    
                    if not url or url in seen_urls:
                        continue
                    
                    # Filter logic
                    text_lower = f"{title} {body}".lower()
                    
                    # Must contain master/mphil/msc
                    if not any(term in text_lower for term in ['master', 'msc', 'mphil', 'm.s.', 'graduate']):
                        continue
                    
                    # Must relate to your field
                    if not any(field in text_lower for field in ['meteor', 'remote sens', 'gis', 'geographic', 'space', 'atmospher', 'earth observ', 'geospatial', 'geomatics']):
                        continue
                    
                    # Exclude unwanted
                    if any(ex in text_lower for ex in EXCLUDE_TERMS):
                        continue
                    
                    seen_urls.add(url)
                    details = extract_scholarship_details(title, body, url)
                    results.append(details)
            except Exception as e:
                print(f"Search error for {keyword}: {e}")
    
    # Add curated high-value sources (always check)
    curated = get_curated_sources()
    for item in curated:
        if item['url'] not in seen_urls:
            results.append(item)
            seen_urls.add(item['url'])
    
    return results[:30]  # top 30

def get_curated_sources():
    """Manually curated scholarship pages with full details"""
    return [
        {
            'title': 'USGIF Scholarship Program - $10,000 for GEOINT/Remote Sensing',
            'url': 'https://usgif.org/usgif-scholarship-program/',
            'snippet': 'Graduate scholarships for geospatial intelligence, remote sensing, earth science. Deadline April 5, 2026. Open to international students at US schools.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'USA',
            'university': 'Any US University',
            'deadline': 'April 05, 2026',
            'funding': '$10,000',
            'eligibility': '🌍 International'
        },
        {
            'title': 'ASPRS Scholarships - Remote Sensing & Photogrammetry',
            'url': 'https://www.asprs.org/education-careers/asprs-awards-and-scholarships',
            'snippet': 'Multiple awards up to $10,000 for remote sensing, GIS, photogrammetry students. Deadlines Nov 2025.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'USA',
            'university': 'Any US University',
            'deadline': 'November 30, 2025',
            'funding': 'Up to $10,000',
            'eligibility': '🌍 International'
        },
        {
            'title': 'Erasmus Mundus Joint Masters - GIS & Earth Observation',
            'url': 'https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en',
            'snippet': 'Fully funded EU masters including Copernicus Master in Digital Earth, Geo-information. Open to Pakistan.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'Europe',
            'university': 'Multiple EU Universities',
            'deadline': 'January 31, 2026',
            'funding': 'Fully Funded',
            'eligibility': '🇵🇰 Pakistan, 🌍 International'
        },
        {
            'title': 'DAAD Scholarships - Germany MSc Meteorology/Remote Sensing',
            'url': 'https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/',
            'snippet': 'Fully funded masters in Germany. Search for Environmental Sciences, Geosciences.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'Germany',
            'university': 'German Universities',
            'deadline': 'October 15, 2025',
            'funding': 'Fully Funded',
            'eligibility': '🇵🇰 Pakistan, 🌍 International'
        },
        {
            'title': 'Commonwealth Masters Scholarships',
            'url': 'https://cscuk.fcdo.gov.uk/scholarships/commonwealth-masters-scholarships/',
            'snippet': 'Fully funded UK masters for Pakistan and Commonwealth countries. Includes climate, environment fields.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'UK',
            'university': 'Any UK University',
            'deadline': 'October 31, 2025',
            'funding': 'Fully Funded',
            'eligibility': '🇵🇰 Pakistan'
        },
        {
            'title': 'Swedish Institute Scholarships for Global Professionals',
            'url': 'https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/',
            'snippet': 'Fully funded masters in Sweden - includes Lund University GIS & Remote Sensing.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'Sweden',
            'university': 'Lund University',
            'deadline': 'December 10, 2025',
            'funding': 'Fully Funded',
            'eligibility': '🌍 International'
        },
        {
            'title': 'British Council Women in STEM - UK Masters',
            'url': 'https://www.britishcouncil.pk/programmes/education/women-stem-scholarships',
            'snippet': 'Fully funded for Pakistani women in STEM including Space Science, GIS at Edinburgh, etc.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat(),
            'country': 'UK',
            'university': 'University of Edinburgh',
            'deadline': 'January 15, 2026',
            'funding': 'Fully Funded',
            'eligibility': '👩 Women, 🇵🇰 Pakistan'
        },
    ]

# ============= FORMATTING =============
def format_html(results):
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%); color: white; padding: 30px; border-radius: 10px; }}
            .scholarship-card {{ background: white; margin: 20px 0; padding: 20px; border-left: 5px solid #3b82f6; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .scholarship-title {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
            .scholarship-title a {{ color: #1d4ed8; text-decoration: none; }}
            .scholarship-title a:hover {{ text-decoration: underline; }}
            .details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
            .detail-item {{ background: #f8fafc; padding: 12px; border-radius: 5px; border-left: 3px solid #3b82f6; }}
            .detail-label {{ font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase; }}
            .detail-value {{ font-size: 14px; color: #1e293b; margin-top: 5px; }}
            .funding-badge {{ background: #dcfce7; color: #166534; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }}
            .deadline-badge {{ background: #fef3c7; color: #92400e; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 13px; }}
            .eligibility-badge {{ background: #dbeafe; color: #0c4a6e; padding: 5px 12px; border-radius: 20px; font-size: 12px; }}
            .action-button {{ display: inline-block; margin-top: 10px; padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }}
            .action-button:hover {{ background: #2563eb; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #64748b; }}
            .snippet {{ color: #475569; font-size: 13px; margin: 10px 0; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0;">🛰️ Daily Scholarship Digest</h1>
            <p style="margin: 10px 0 0 0;">{date_str}</p>
            <p style="margin: 5px 0 0 0;">Master's/MPhil in Space Science, Meteorology, Remote Sensing & GIS</p>
        </div>
        <p style="margin: 20px 0; font-size: 16px;"><strong>Found {len(results)} opportunities today</strong></p>
    """
    
    for i, r in enumerate(results, 1):
        html += f"""
        <div class="scholarship-card">
            <div class="scholarship-title">{i}. <a href="{r['url']}" target="_blank">{r['title']}</a></div>
            <p class="snippet">{r['snippet']}</p>
            
            <div class="details-grid">
                <div class="detail-item">
                    <div class="detail-label">🌍 Country</div>
                    <div class="detail-value">{r.get('country', 'Not specified')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">🏫 University</div>
                    <div class="detail-value">{r.get('university', 'Not specified')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">📅 Deadline</div>
                    <div class="detail-value"><span class="deadline-badge">{r.get('deadline', 'Check website')}</span></div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">💰 Funding</div>
                    <div class="detail-value"><span class="funding-badge">{r.get('funding', 'Amount varies')}</span></div>
                </div>
            </div>
            
            <div class="detail-item" style="grid-column: 1 / -1;">
                <div class="detail-label">✅ Eligibility</div>
                <div class="detail-value"><span class="eligibility-badge">{r.get('eligibility', 'Check website')}</span></div>
            </div>
            
            <a href="{r['url']}" class="action-button" target="_blank">View Details →</a>
        </div>
        """
    
    html += """
        <div class="footer">
            <p>Automated by your GitHub Actions cloud bot. Runs daily at 8 AM PKT.</p>
            <p>Keywords: meteorology, remote sensing, GIS, space science, earth observation</p>
            <p><strong>💡 Tip:</strong> Click "View Details" to apply directly on the scholarship website.</p>
        </div>
    </body>
    </html>
    """
    return html

def format_telegram(results):
    date_str = datetime.now().strftime("%b %d")
    msg = f"🛰️ *Scholarship Digest - {date_str}*\n_Master's in Meteorology/Remote Sensing/GIS_\n\n"
    
    for i, r in enumerate(results[:10], 1):  # Telegram limit
        title = r['title'][:60] + "..." if len(r['title']) > 60 else r['title']
        country = r.get('country', 'Intl')
        deadline = r.get('deadline', 'TBD')
        funding = r.get('funding', 'TBD')
        
        msg += f"{i}. *{title}*\n"
        msg += f"   📍 {country} | 💰 {funding} | 📅 {deadline}\n"
        msg += f"   [{r['url']}]({r['url']})\n\n"
    
    msg += f"_Total found: {len(results)} | Powered by GitHub Actions_"
    return msg

# ============= SENDERS =============
def send_email(html_content, results):
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    email_to = os.getenv('EMAIL_TO', email_user)
    
    if not email_user or not email_pass:
        print("Email credentials not set, skipping")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🛰️ {len(results)} New Scholarships - Meteorology/GIS - {datetime.now().strftime('%b %d')}"
        msg['From'] = email_user
        msg['To'] = email_to
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        
        print(f"Email sent to {email_to}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

def send_telegram(text):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Telegram credentials not set, skipping")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print("Telegram sent")
        return True
    except Exception as e:
        print(f"Telegram failed: {e}")
        return False

# ============= MAIN =============
def main():
    print("Starting scholarship search...")
    results = search_scholarships()
    
    if not results:
        print("No results found today")
        return
    
    print(f"Found {len(results)} scholarships")
    
    # Save results for debugging
    with open('today_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    html = format_html(results)
    telegram_msg = format_telegram(results)
    
    send_email(html, results)
    send_telegram(telegram_msg)
    
    print("Done!")

if __name__ == "__main__":
    main()
