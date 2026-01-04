import http.client
import json
import os
from datetime import datetime, timedelta, timezone

# ---------------- CONFIG ----------------
RAPID_HOST = "cricket-api-free-data.p.rapidapi.com"
ENDPOINT = "/cricket-matches-upcoming"
RAPID_KEY = os.getenv("RAPIDAPI_KEY")  # Must set as GitHub secret

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

# ---------------- DEBUG PRINT ----------------
print("========== RAW API RESPONSE ==========")
print(raw)

try:
    api_data = json.loads(raw)
except Exception as e:
    print("❌ Failed to parse JSON:", e)
    api_data = {}

print("========== PARSED JSON ==========")
print(json.dumps(api_data, indent=2))

# ---------------- PARSE MATCHES ----------------
match_list = api_data.get("data") or api_data.get("matches") or []

for m in match_list:
    # try multiple possible keys
    start_str = (
        m.get("dateTimeGMT") or m.get("startTime") or m.get("start_date") or m.get("date")
    )
    if not start_str:
        continue

    try:
        start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    except:
        continue

    if not (today <= start_time <= end_day):
        continue

    team1 = (
        m.get("team1") or m.get("teamA") or (m.get("teams")[0] if isinstance(m.get("teams"), list) else None)
    )
    team2 = (
        m.get("team2") or m.get("teamB") or (m.get("teams")[1] if isinstance(m.get("teams"), list) and len(m.get("teams")) > 1 else None)
    )

    if not team1 or not team2:
        continue

    series = m.get("series") or m.get("league") or m.get("competition") or "Cricket Match"

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
