import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta, timezone

URL = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/all"

# ------------------ LOAD OR CREATE JSON ------------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
last_id = max([m["match_id"] for m in matches], default=0)

today = datetime.now(timezone.utc)
end_day = today + timedelta(days=5)

headers = {"User-Agent": "Mozilla/5.0"}
html = requests.get(URL, headers=headers).text
soup = BeautifulSoup(html, "html.parser")

# ------------------ SCRAPE ------------------
for row in soup.select(".cb-col-100.cb-col"):
    text = row.get_text(" ", strip=True)

    # Must contain vs
    if " vs " not in text:
        continue

    # Dummy time (Cricbuzz exact parse unreliable)
    start_time = today.replace(hour=12, minute=0)

    if not (today.date() <= start_time.date() <= end_day.date()):
        continue

    last_id += 1

    # Try extracting series
    if "-" in text:
        teams = text.split("-")[0].strip()
        series = text.split("-")[1].strip()
    else:
        teams = text
        series = "Cricket Match"

    matches.append({
        "match_id": last_id,
        "title": f"{teams} ({series})",
        "thumbnail": "https://via.placeholder.com/300x170.png?text=Cricket+Match",
        "status": "upcoming",
        "format": series,
        "start_time": start_time.isoformat().replace("+00:00", "Z"),
        "channels": [
            {
                "channel_id": 1,
                "name": "Sample Channel",
                "stream_url": "https://example.com/sample/stream"
            }
        ]
    })

data["matches"] = matches

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Matches added:", len(matches))
