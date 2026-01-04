import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone

URL = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/all"

# Load existing JSON
with open("matches.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matches = data.get("matches", [])

# Get last match_id
last_id = max([m["match_id"] for m in matches], default=0)

# Date window
today = datetime.now(timezone.utc).date()
end_date = today + timedelta(days=5)

# Fetch page
headers = {"User-Agent": "Mozilla/5.0"}
html = requests.get(URL, headers=headers).text
soup = BeautifulSoup(html, "html.parser")

for match in soup.select(".cb-schdl"):
    title_el = match.select_one(".cb-schdl-tm")
    time_el = match.select_one(".cb-col-25")

    if not title_el or not time_el:
        continue

    title_text = title_el.get_text(" ", strip=True)
    time_text = time_el.get_text(strip=True)

    try:
        start_time = datetime.strptime(time_text, "%d %b %Y %H:%M").replace(tzinfo=timezone.utc)
    except:
        continue

    if not (today <= start_time.date() <= end_date):
        continue

    last_id += 1

    # Extract series/league name
    if "(" in title_text and ")" in title_text:
        series = title_text.split("(")[-1].replace(")", "")
        teams = title_text.split("(")[0].strip()
    else:
        series = "International / Domestic"
        teams = title_text

    match_obj = {
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
    }

    matches.append(match_obj)

data["matches"] = matches

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Matches updated successfully")
