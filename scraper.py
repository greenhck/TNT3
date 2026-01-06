import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

# ================= CONFIG =================
URL = os.getenv("SCRAPE_URL") or "https://PASTE_REAL_URL_HERE"
YEAR = 2026
# ==========================================

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubBot/1.0)"
}

res = requests.get(URL, headers=headers, timeout=30)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

matches = []
match_id = 1

date_blocks = soup.select(".datewise-match-wrapper")

for block in date_blocks:
    date_node = block.select_one(".datetime")
    if not date_node:
        continue

    # "Tuesday, January 6" -> "2026-01-06"
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

        # ================= STATUS DETECTION =================
        status = None
        start_time = None

        # UPCOMING
        start_node = wrapper.select_one(".start-text")
        if start_node:
            status = "upcoming"
            start_time = start_node.text.strip()

        # LIVE
        elif wrapper.select_one(".team-score"):
            status = "live"
            start_time = "Live"

        # COMPLETED → SKIP
        elif "won" in text_lower or wrapper.select_one(".reason"):
            continue

        # Safety
        if status not in ("live", "upcoming"):
            continue
        # ====================================================

        # League
        league = "Big Bash League" if "bbl" in text_lower else "Unknown League"

        teams = wrapper.select(".team-name")
        logos = wrapper.select("img")

        if len(teams) < 2:
            continue

        match = {
            "match_id": match_id,
            "league": league,
            "status": status,
            "start_date": start_date,
            "start_time": start_time,
            "teams": {
                "home": {
                    "name": teams[0].text.strip(),
                    "logo": logos[0]["src"] if len(logos) > 0 else ""
                },
                "away": {
                    "name": teams[1].text.strip(),
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

print(f"✅ Saved {len(matches)} live/upcoming matches")
