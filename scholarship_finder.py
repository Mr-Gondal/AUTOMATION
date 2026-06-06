#!/usr/bin/env python3
"""
Cloud Scholarship Finder for Master's/MPhil in Space Science, Meteorology, Remote Sensing & GIS
Runs daily on GitHub Actions - works even when your laptop is off.

Features:
- Searches web daily for new scholarships
- Filters for Master's/MPhil + your fields
- Sends Email + Telegram digest
"""

import os
import json
import smtplib
import requests
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
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': body[:300],
                        'source': 'DuckDuckGo',
                        'found': datetime.utcnow().isoformat()
                    })
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
    """Manually curated scholarship pages that are always relevant"""
    return [
        {
            'title': 'USGIF Scholarship Program - $10,000 for GEOINT/Remote Sensing',
            'url': 'https://usgif.org/usgif-scholarship-program/',
            'snippet': 'Graduate scholarships for geospatial intelligence, remote sensing, earth science. Deadline April 5, 2026. Open to international students at US schools.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'ASPRS Scholarships - Remote Sensing & Photogrammetry',
            'url': 'https://www.asprs.org/education-careers/asprs-awards-and-scholarships',
            'snippet': 'Multiple awards up to $10,000 for remote sensing, GIS, photogrammetry students. Deadlines Nov 2025.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'Erasmus Mundus Joint Masters - GIS & Earth Observation',
            'url': 'https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en',
            'snippet': 'Fully funded EU masters including Copernicus Master in Digital Earth, Geo-information. Open to Pakistan.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'DAAD Scholarships - Germany MSc Meteorology/Remote Sensing',
            'url': 'https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/',
            'snippet': 'Fully funded masters in Germany. Search for Environmental Sciences, Geosciences.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'Commonwealth Masters Scholarships',
            'url': 'https://cscuk.fcdo.gov.uk/scholarships/commonwealth-masters-scholarships/',
            'snippet': 'Fully funded UK masters for Pakistan and Commonwealth countries. Includes climate, environment fields.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'Swedish Institute Scholarships for Global Professionals',
            'url': 'https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/',
            'snippet': 'Fully funded masters in Sweden - includes Lund University GIS & Remote Sensing.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
        {
            'title': 'British Council Women in STEM - UK Masters',
            'url': 'https://www.britishcouncil.pk/programmes/education/women-stem-scholarships',
            'snippet': 'Fully funded for Pakistani women in STEM including Space Science, GIS at Edinburgh, etc.',
            'source': 'Curated',
            'found': datetime.utcnow().isoformat()
        },
    ]

# ============= FORMATTING =============
def format_html(results):
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <h2 style="color: #1e40af;">🛰️ Daily Scholarship Digest - {date_str}</h2>
        <p>For <strong>Master's/MPhil in Space Science, Meteorology, Remote Sensing & GIS</strong></p>
        <p>Found {len(results)} opportunities today:</p>
        <hr>
    """
    
    for i, r in enumerate(results, 1):
        html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #3b82f6; background: #f8fafc;">
            <h3 style="margin: 0 0 8px 0;"><a href="{r['url']}" style="color: #1d4ed8; text-decoration: none;">{i}. {r['title']}</a></h3>
            <p style="margin: 5px 0; color: #475569; font-size: 14px;">{r['snippet']}</p>
            <p style="margin: 5px 0; font-size: 12px;">
                <span style="background: #dbeafe; padding: 2px 8px; border-radius: 12px;">{r['source']}</span>
                <a href="{r['url']}" style="margin-left: 10px; color: #64748b;">Open →</a>
            </p>
        </div>
        """
    
    html += """
        <hr>
        <p style="font-size: 12px; color: #64748b;">
        Automated by your GitHub Actions cloud bot. Runs daily at 8 AM PKT.<br>
        Keywords: meteorology, remote sensing, GIS, space science, earth observation
        </p>
    </body>
    </html>
    """
    return html

def format_telegram(results):
    date_str = datetime.now().strftime("%b %d")
    msg = f"🛰️ *Scholarship Digest - {date_str}*\n_Master's in Meteorology/Remote Sensing/GIS_\n\n"
    
    for i, r in enumerate(results[:15], 1):  # Telegram limit
        title = r['title'][:70] + "..." if len(r['title']) > 70 else r['title']
        msg += f"{i}. [{title}]({r['url']})\n"
    
    msg += f"\n_Total found: {len(results)} | Powered by GitHub Actions_"
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
            'disable_web_page_preview': True
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