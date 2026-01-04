import http.client
import json
import os
from datetime import datetime, timedelta, timezone

# ---------------- CONFIG ----------------
RAPID_HOST = "cricket-api-free-data.p.rapidapi.com"
RAPID_KEY = "YOUR_RAPIDAPI_KEY"   # 🔴 replace with GitHub secret
ENDPOINT = "/cricket-matches-upcoming"

# ---------------- LOAD / CREATE JSON ----------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
last_id = max([m["match_id"] for m in matches], default=0)

today = datetime.now(timezone.utc)
end_day = today + timedelta(days=5)

# ---------------- API CALL ----------------
conn = http.client.HTTPSConnection(RAPID_HOST)
headers = {
    "x-rapidapi-key": RAPID_KEY,
    "x-rapidapi-host": RAPID_HOST
}

conn.request("GET", ENDPOINT, headers=headers)
res = conn.getresponse()
raw = res.read().decode("utf-8")

api_data = json.loads(raw)

# ---------------- PARSE MATCHES ----------------
for m in api_data.get("data", []):
    start_str = m.get("dateTimeGMT")

    if not start_str:
        continue

    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

    if not (today <= start_time <= end_day):
        continue

    team1 = m.get("team1")
    team2 = m.get("team2")
    series = m.get("series", "Cricket Match")

    if not team1 or not team2:
        continue

    last_id += 1

    matches.append({
        "match_id": last_id,
        "title": f"{team1} vs {team2} ({series})",
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
