import requests
import json
import os
from datetime import datetime, timedelta, timezone

API_URL = "https://www.cricbuzz.com/api/cricket-schedule"

# ---------------- LOAD OR CREATE JSON ----------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
last_id = max([m["match_id"] for m in matches], default=0)

today = datetime.now(timezone.utc)
end_day = today + timedelta(days=5)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

resp = requests.get(API_URL, headers=headers, timeout=20)
schedule = resp.json()

# ---------------- PARSE MATCHES ----------------
for day in schedule.get("matchScheduleMap", []):
    for series in day.get("seriesMatches", []):
        series_name = series.get("seriesAdWrapper", {}).get("seriesName")
        matches_list = series.get("seriesAdWrapper", {}).get("matches", [])

        for m in matches_list:
            info = m.get("matchInfo", {})
            start_ms = info.get("startDate")

            if not start_ms:
                continue

            start_time = datetime.fromtimestamp(int(start_ms) / 1000, tz=timezone.utc)

            if not (today <= start_time <= end_day):
                continue

            team1 = info.get("team1", {}).get("teamName", "")
            team2 = info.get("team2", {}).get("teamName", "")

            if not team1 or not team2:
                continue

            last_id += 1

            matches.append({
                "match_id": last_id,
                "title": f"{team1} vs {team2} ({series_name})",
                "thumbnail": "https://via.placeholder.com/300x170.png?text=Cricket+Match",
                "status": "upcoming",
                "format": series_name,
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
