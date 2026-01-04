import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta, timezone

URL = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/all"

# -----------------------------
# Load or create matches.json
# -----------------------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {
        "posters": [
            {
                "poster_id": 1,
                "type": "text",
                "text": "Welcome to the Ruby Player. It is a smart level Streaming app."
            },
            {
                "poster_id": 2,
                "type": "image",
                "image": "https://assets-in.bmscdn.com/discovery-catalog/events/et00478875-hgnrkhfvpf-landscape.jpg"
            },
            {
                "poster_id": 3,
                "type": "image",
                "image": "https://www.thecricketpanda.com/wp-content/uploads/2024/10/BBL-2024-25_-Everything-You-Need-to-Know.png"
            }
        ],
        "matches": []
    }

matches = data.get("matches", [])
last_id = max([m["match_id"] for m in matches], default=0)

# -----------------------------
# Date logic
# -----------------------------
today = datetime.now(timezone.utc).date()
end_date = today + timedelta(days=5)

headers = {"User-Agent": "Mozilla/5.0"}
html = requests.get(URL, headers=headers, timeout=20).text
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

    if "(" in title_text and ")" in title_text:
        series = title_text.split("(")[-1].replace(")", "")
        teams = title_text.split("(")[0].strip()
    else:
        series = "Cricket Match"
        teams = title_text

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

print("✅ Matches updated successfully")
