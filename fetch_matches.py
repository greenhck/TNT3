import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone

# ---------------- LOAD / CREATE JSON ----------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
last_id = max([m["match_id"] for m in matches], default=0)

# ---------------- SCRAPE HTML ----------------
url = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/all"
resp = requests.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

tbody = soup.find("tbody")
current_date = None

for tr in tbody.find_all("tr"):
    th = tr.find("th", colspan="3")
    if th:
        current_date = th.text.strip()  # e.g., "04 Jan 2026 (Sunday)"
        continue
    
    tds = tr.find_all("td")
    if len(tds) >= 3:
        # series
        series_tag = tds[0].find("a")
        series_name = series_tag.text.strip() if series_tag else "Unknown Series"
        
        # teams
        team_imgs = tds[1].find_all("img")
        if len(team_imgs) >= 2:
            team1 = team_imgs[0]["title"]
            team2 = team_imgs[1]["title"]
        else:
            team1 = team2 = "Unknown"
        
        # parse date
        try:
            match_date = datetime.strptime(current_date.split("(")[0].strip(), "%d %b %Y")
            match_datetime = match_date.replace(hour=15, minute=0, tzinfo=timezone.utc)  # default 15:00 UTC
        except:
            match_datetime = datetime.now(timezone.utc)
        
        last_id += 1
        
        # append match
        matches.append({
            "match_id": last_id,
            "title": f"{team1} vs {team2} ({series_name})",
            "thumbnail": "https://via.placeholder.com/300x170.png?text=Cricket+Match",
            "status": "upcoming",
            "format": series_name,
            "start_time": match_datetime.isoformat().replace("+00:00", "Z"),
            "channels": [
                {
                    "channel_id": 1,
                    "name": "Sample Channel",
                    "stream_url": "https://example.com/sample/stream"
                }
            ]
        })

data["matches"] = matches

# ---------------- SAVE JSON ----------------
with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Matches added: {len(matches)}")
