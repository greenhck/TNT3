import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import hashlib

# ================= CONFIG (वही पुराना) =================
YEAR = 2026
URL_ENV_KEYS = ["SURL1", "SURL2", "SURL3", "SURL4", "SURL5"]
JSON_FILE = "matches.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_urls_from_secrets():
    urls = []
    for key in URL_ENV_KEYS:
        val = os.getenv(key)
        if val and val.startswith("http"):
            urls.append(val)
    return urls

def unique_key(start_date, team1, team2, league):
    # वही पुरानी Key ताकि ऐप को डेटा ढूंढने में दिक्कत न हो
    raw = f"{start_date}-{team1}-{team2}-{league}"
    return hashlib.md5(raw.encode()).hexdigest()

def load_existing_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"matches": []}
    return {"matches": []}

# पुराना डेटा लोड करें ताकि चैनल्स सुरक्षित रहें
existing_data = load_existing_data()
existing_channels_map = {}
for m in existing_data.get("matches", []):
    k = unique_key(m['start_date'], m['teams']['home']['name'], m['teams']['away']['name'], m['league'])
    if m.get("channels"):
        existing_channels_map[k] = m["channels"]

SCRAPE_URLS = get_urls_from_secrets()
new_matches = []
seen_keys = set()
match_id = 1

for URL in SCRAPE_URLS:
    try:
        res = requests.get(URL, headers=HEADERS, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        date_blocks = soup.select(".datewise-match-wrapper")

        for block in date_blocks:
            date_node = block.select_one(".datetime")
            if not date_node: continue
            try:
                parsed_date = datetime.strptime(date_node.text.strip(), "%A, %B %d")
                start_date = parsed_date.replace(year=YEAR).strftime("%Y-%m-%d")
            except: continue

            cards = block.select("app-match-card")
            for card in cards:
                wrapper = card.select_one(".match-card-wrapper")
                if not wrapper: continue

                # --- 1. CLEANUP (पुराने मैच हटाना) ---
                text_lower = wrapper.text.lower()
                # अगर मैच में 'Won', 'Result' या 'Abandoned' है तो उसे छोड़ दें
                if any(x in text_lower for x in [" won ", "won by", "result", "abandoned", "no result"]):
                    continue

                status, start_time = None, None
                start_node = wrapper.select_one(".start-text")
                if start_node:
                    status, start_time = "upcoming", start_node.text.strip()
                elif wrapper.select_one(".team-score") or wrapper.select_one(".liveTag"):
                    status, start_time = "live", "Live"

                if status not in ("live", "upcoming"): continue

                league = "Big Bash League" if "bbl" in text_lower else "Unknown League"
                teams = wrapper.select(".team-name")
                logos = wrapper.select("img")
                if len(teams) < 2: continue

                t1_name = teams[0].text.strip()
                t2_name = teams[1].text.strip()
                
                key = unique_key(start_date, t1_name, t2_name, league)
                if key in seen_keys: continue
                seen_keys.add(key)

                # --- 2. DATA PRESERVATION (मैन्युअल डेटा बचाना) ---
                saved_channels = existing_channels_map.get(key, [])

                match = {
                    "match_id": match_id,
                    "league": league,
                    "status": status,
                    "start_date": start_date,
                    "start_time": start_time,
                    "teams": {
                        "home": {"name": t1_name, "logo": logos[0]["src"] if len(logos) > 0 else ""},
                        "away": {"name": t2_name, "logo": logos[1]["src"] if len(logos) > 1 else ""}
                    },
                    "channels": saved_channels
                }
                new_matches.append(match)
                match_id += 1
    except: continue

# --- 3. SAFETY SAVE (सबसे जरूरी) ---
# अगर स्क्रैपिंग में कोई मैच मिला, तभी फाइल सेव करें, वरना नहीं
if len(new_matches) > 0:
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"matches": new_matches}, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON Updated. {len(new_matches)} matches.")
else:
    print("⚠️ Scraping failed or no active matches. Old JSON kept as is.")
