import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://crex.com/series/1VD/big-bash-league-2025-26/matches"

res = requests.get(URL, headers={
    "User-Agent": "Mozilla/5.0"
})
soup = BeautifulSoup(res.text, "html.parser")

matches = []
match_id = 1

date_blocks = soup.select(".datewise-match-wrapper")

for block in date_blocks:
    date_text = block.select_one(".datetime")
    if not date_text:
        continue

    # Convert "Tuesday, January 6" → "2026-01-06"
    parsed_date = datetime.strptime(date_text.text.strip(), "%A, %B %d")
    start_date = parsed_date.replace(year=2026).strftime("%Y-%m-%d")

    cards = block.select("app-match-card")

    for card in cards:
        wrapper = card.select_one(".match-card-wrapper")

        league_text = wrapper.select_one(".match-info").text.strip()
        league = "Big Bash League" if "BBL" in league_text else "Unknown League"

        start_time = wrapper.select_one(".start-text")
        start_time = start_time.text.strip() if start_time else "TBD"

        teams = wrapper.select(".team-name")
        logos = wrapper.select("img")

        if len(teams) < 2:
            continue

        match = {
            "match_id": match_id,
            "league": league,
            "status": "upcoming",
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

final_json = {
    "matches": matches
}

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent=2, ensure_ascii=False)

print("✅ matches.json saved")
