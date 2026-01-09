import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import hashlib

# ================= CONFIG =================
YEAR = 2026
URL_ENV_KEYS = ["SURL1", "SURL2", "SURL3", "SURL4", "SURL5"]
JSON_FILE = "matches.json"
# =========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubBot/1.0)"
}

def get_urls_from_secrets():
    urls = []
    for key in URL_ENV_KEYS:
        val = os.getenv(key)
        if val and val.startswith("http"):
            urls.append(val)
    return urls

def unique_key(start_date, team1, team2, league):
    # मैच की विशिष्ट पहचान बनाने के लिए (ताकि डेटा मर्ज हो सके)
    raw = f"{start_date}-{team1}-{team2}-{league}"
    return hashlib.md5(raw.encode()).hexdigest()

# --- पुरानी फ़ाइल से डेटा लोड करने का फंक्शन ---
def load_existing_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"matches": []}
    return {"matches": []}

existing_data = load_existing_data()
# पुराने चैनल्स को उनके यूनिक की (Key) के साथ मैप में स्टोर करें
existing_channels_map = {}
for m in existing_data.get("matches", []):
    k = unique_key(m['start_date'], m['teams']['home']['name'], m['teams']['away']['name'], m['league'])
    if m.get("channels"):
        existing_channels_map[k] = m["channels"]

SCRAPE_URLS = get_urls_from_secrets()
if not SCRAPE_URLS:
    print("⚠️ No scrape URLs found. Using empty list.")
    SCRAPE_URLS = []

new_matches = []
seen_keys = set()
match_id = 1

for URL in SCRAPE_URLS:
    print(f"🔍 Scraping: {URL}")
    try:
        res = requests.get(URL, headers=HEADERS, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Failed {URL}: {e}")
        continue

    soup = BeautifulSoup(res.text, "html.parser")
    date_blocks = soup.select(".datewise-match-wrapper")

    for block in date_blocks:
        date_node = block.select_one(".datetime")
        if not date_node: continue

        try:
            parsed_date = datetime.strptime(date_node.text.strip(), "%A, %B %d")
            start_date = parsed_date.replace(year=YEAR).strftime("%Y-%m-%d")
        except Exception: continue

        cards = block.select("app-match-card")
        for card in cards:
            wrapper = card.select_one(".match-card-wrapper")
            if not wrapper: continue

            text_lower = wrapper.text.lower()
            if " won " in text_lower or "won by" in text_lower or "match ended" in text_lower or wrapper.select_one(".reason"):
                continue

            status, start_time = None, None
            start_node = wrapper.select_one(".start-text")
            if start_node:
                status, start_time = "upcoming", start_node.text.strip()
            elif wrapper.select_one(".team-score"):
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

            # --- यहाँ हम पुराना चैनल डेटा वापस डाल रहे हैं ---
            # अगर पुरानी फ़ाइल में इस मैच के लिए चैनल्स थे, तो उन्हें इस्तेमाल करें
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
                "channels": saved_channels  # पुराना डेटा यहाँ सुरक्षित है
            }
            new_matches.append(match)
            match_id += 1

# ================= SAVE JSON =================
final_json = {"matches": new_matches}

with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print(f"✅ Updated {len(new_matches)} matches. Manual channel data preserved.")
