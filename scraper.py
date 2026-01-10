import requests
from bs4 import BeautifulSoup
import json
import os
import hashlib

# ================= CONFIG =================
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

def unique_key(team1, team2):
    t1 = team1.strip()[:3].upper()
    t2 = team2.strip()[:3].upper()
    t_names = sorted([t1, t2])
    raw = f"{t_names[0]}-{t_names[1]}"
    return hashlib.md5(raw.encode()).hexdigest()

def load_existing_channels():
    channels_map = {}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for m in data.get("matches", []):
                    k = unique_key(m['teams']['home']['name'], m['teams']['away']['name'])
                    if m.get("channels"):
                        channels_map[k] = m["channels"]
        except: pass
    return channels_map

existing_channels = load_existing_channels()
SCRAPE_URLS = get_urls_from_secrets()

new_matches = []
seen_keys = set()
match_id = 1

for URL in SCRAPE_URLS:
    try:
        res = requests.get(URL, headers=HEADERS, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        cards = soup.select("app-match-card")
        for card in cards:
            wrapper = card.select_one(".match-card-wrapper")
            if not wrapper: continue

            # 1. खत्म हुए और Abandoned मैचों को फ़िल्टर करें
            text_lower = wrapper.text.lower()
            reason_node = wrapper.select_one(".reason")
            reason_text = reason_node.text.lower() if reason_node else ""

            # अगर मैच 'Won' है या 'Abandoned' या 'No Result' है, तो उसे Skip करें
            if ("won" in text_lower) or ("abandoned" in text_lower) or ("no result" in reason_text) or ("cancelled" in text_lower):
                continue 

            teams = wrapper.select(".team-name")
            logos = wrapper.select("img")
            if len(teams) < 2: continue
            
            t1_name = teams[0].text.strip()
            t2_name = teams[1].text.strip()

            status = "upcoming"
            start_time = "Upcoming"
            
            if wrapper.select_one(".liveTag") or wrapper.select_one(".team-score"):
                status = "live"
                live_text = wrapper.select_one(".liveTag")
                start_time = live_text.text.strip() if live_text else "Live"
            else:
                time_node = wrapper.select_one(".start-text")
                if time_node:
                    start_time = time_node.text.strip()

            key = unique_key(t1_name, t2_name)
            if key in seen_keys: continue
            seen_keys.add(key)

            saved_channels = existing_channels.get(key, [])

            new_matches.append({
                "match_id": match_id,
                "status": status,
                "start_time": start_time,
                "teams": {
                    "home": {"name": t1_name, "logo": logos[0]["src"] if len(logos) > 0 else ""},
                    "away": {"name": t2_name, "logo": logos[1]["src"] if len(logos) > 1 else ""}
                },
                "channels": saved_channels
            })
            match_id += 1
    except Exception as e:
        print(f"Error: {e}")

if new_matches:
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"matches": new_matches}, f, indent=2, ensure_ascii=False)
    print(f"✅ Success: {len(new_matches)} active matches saved.")
else:
    print("⚠️ No active matches found. Old data preserved.")
