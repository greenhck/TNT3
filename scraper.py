import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import hashlib

# ================= CONFIG =================
YEAR = 2026

URL_ENV_KEYS = ["SURL1", "SURL2"]
# =========================================

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubBot/1.0)"
}

matches = []
seen_keys = set()
match_id = 1

def unique_key(start_date, team1, team2, league):
    raw = f"{start_date}-{team1}-{team2}-{league}"
    return hashlib.md5(raw.encode()).hexdigest()

def get_urls_from_secrets():
    urls = []
    for key in URL_ENV_KEYS:
        val = os.getenv(key)
        if val and val.startswith("http"):
            urls.append(val)
    return urls

SCRAPE_URLS = get_urls_from_secrets()

if not SCRAPE_URLS:
    raise Exception("❌ No scrape URLs found in secrets (SURL1, SURL2, ...)")

for URL in SCRAPE_URLS:
    print(f"🔍 Scraping: {URL}")

    try:
        res = requests.get(URL, headers=headers, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Failed {URL}: {e}")
        continue

    soup = BeautifulSoup(res.text, "html.parser")

    date_blocks = soup.select(".datewise-match-wrapper")

    for block in date_blocks:
        date_node = block.select_one(".datetime")
        if not date_node:
            continue

        try:
            parsed_date = datetime.strptime(date_node.text.strip(), "%A, %B %d")
            start_date = parsed_date.replace(year=YEAR).strftime("%Y-%m-%d")
        except Exception:
            continue

        cards = block.select("app-match-card")

        for card in cards:
            wrapper = card.select_one(".match-card-wrapper")
            if not wrapper:
                continue

            text_lower = wrapper.text.lower()

            # -------- STATUS DETECTION --------
            status = None
            start_time = None

            if wrapper.select_one(".start-text"):
                status = "upcoming"
                start_time = wrapper.select_one(".start-text").text.strip()

            elif wrapper.select_one(".team-score"):
                status = "live"
                start_time = "Live"

            elif "won" in text_lower or wrapper.select_one(".reason"):
                continue  # skip completed

            if status not in ("live", "upcoming"):
                continue
            # ---------------------------------

            league = "Big Bash League" if "bbl" in text_lower else "Unknown League"

            teams = wrapper.select(".team-name")
            logos = wrapper.select("img")

            if len(teams) < 2:
                continue

            team1 = teams[0].text.strip()
            team2 = teams[1].text.strip()

            key = unique_key(start_date, team1, team2, league)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            match = {
                "match_id": match_id,
                "league": league,
                "status": status,
                "start_date": start_date,
                "start_time": start_time,
                "teams": {
                    "home": {
                        "name": team1,
                        "logo": logos[0]["src"] if len(logos) > 0 else ""
                    },
                    "away": {
                        "name": team2,
                        "logo": logos[1]["src"] if len(logos) > 1 else ""
                    }
                },
                "channels": []
            }

            matches.append(match)
            match_id += 1

# ================= SAVE JSON =================
final_json = {
    "matches": matches
}

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print(f"✅ Total matches saved: {len(matches)}")
