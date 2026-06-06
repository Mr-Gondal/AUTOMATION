# 🛰️ Cloud Scholarship Automation

**Fully automated daily alerts for Master's/MPhil scholarships in Meteorology, Remote Sensing, GIS & Space Science**

Runs 24/7 on GitHub Actions - even when your laptop is OFF.

✅ Sends to **Email + Telegram** daily at 8 AM PKT
✅ Searches 30+ sources automatically
✅ Filters for your Space Science background
✅ 100% free forever

---

## What It Finds

Based on your 4-year Bachelor's in Space Science, it monitors:

- **Meteorology & Atmospheric Science** masters
- **Remote Sensing & Earth Observation**
- **GIS, Geomatics, Geospatial Intelligence**
- **Space Science applications**

Curated high-value scholarships included:
- USGIF ($10,000) [1](https://usgif.org/usgif-scholarship-program/)
- ASPRS Remote Sensing ($10,000) [1](https://scholarshipsandgrants.us/other/geo-spatial-intelligence-remote-sensing-scholarships-2026-guide/)
- Erasmus Mundus (fully funded EU)
- DAAD Germany
- Commonwealth Masters (UK)
- Swedish Institute
- British Council Women in STEM Pakistan [2](https://study.ed.ac.uk/programmes/postgraduate-taught/1146-geographical-information-science-and-earth-observation)

---

## Setup (15 minutes, one-time)

### Step 1: Create GitHub Repo
1. Go to github.com → New repository → Name: `scholarship-bot`
2. Upload these 3 files: `scholarship_finder.py`, `requirements.txt`, `.github/workflows/daily-scholarships.yml`

### Step 2: Setup Email (Gmail)
1. Enable 2-factor on Gmail
2. Create App Password: myaccount.google.com/apppasswords → "Mail" → copy 16-char password
3. In GitHub repo → Settings → Secrets and variables → Actions → New repository secret:
   - `EMAIL_USER` = your@gmail.com
   - `EMAIL_PASS` = your 16-char app password
   - `EMAIL_TO` = where to send (can be same)

### Step 3: Setup Telegram (2 mins)
1. Open Telegram → search `@BotFather` → /newbot → name it → copy token
2. Search your new bot → Start
3. Get your Chat ID: message `@userinfobot` → copy "Id"
4. Add GitHub secrets:
   - `TELEGRAM_BOT_TOKEN` = token from BotFather
   - `TELEGRAM_CHAT_ID` = your numeric ID

### Step 4: Test
- GitHub → Actions → "Daily Scholarship Finder" → Run workflow
- Check email & Telegram in 1 minute!

---

## How It Works

Every day at 3 AM UTC:
1. Searches DuckDuckGo for 11 keyword combinations
2. Filters for Master's/MPhil + your fields
3. Adds curated permanent scholarships
4. Sends beautiful HTML email + Telegram list
5. Saves results as artifact

**Cost:** $0 (GitHub Actions free tier = 2,000 minutes/month, this uses ~30)

---

## Customize

Edit `scholarship_finder.py`:
- Line 15-25: Add more KEYWORDS
- Line 27: Add specific countries to REGIONS
- Line 85: Change `timelimit="m"` to `"w"` for weekly only

Change schedule: Edit `.github/workflows/daily-scholarships.yml` line 5:
- `'0 3 * * *'` = 8 AM PKT daily
- `'0 3 * * 1'` = Mondays only

---

## Example Output

**Email:** Beautiful cards with title, snippet, direct link
**Telegram:**
```
🛰️ Scholarship Digest - Jun 06
_Master's in Meteorology/Remote Sensing/GIS_

1. [USGIF Scholarship Program - $10,000...](link)
2. [Erasmus Mundus Joint Masters...](link)
...
```

---

## Troubleshooting

**No email?** Check spam, verify app password, check Actions logs
**No Telegram?** Make sure you started the bot first
**Want fewer results?** Increase filtering in line 50

---

Built for Space Science graduates targeting 2025-2026 intakes. Runs forever in the cloud.