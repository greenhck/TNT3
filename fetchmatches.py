import requests
import json
import os
from datetime import datetime, timezone

MATCHES_FILE = "matche.json"
API_URL = "https://crickapi.com/fixture"

# ---------------- Load existing matches ----------------
if os.path.exists(MATCHES_FILE):
    with open(MATCHES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

existing_titles = {m["title"] for m in data.get("matches", [])}
next_match_id = max([m["match_id"] for m in data.get("matches", [])], default=0) + 1

added = 0
page = 1

# ---------------- Pagination loop ----------------
while True:
    payload = {
        "tl": [0, 0, 0],
        "type": "0",
        "page": page,
        "wise": "1",
        "lang": "en",
        "formatType": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/121.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
    except Exception as e:
        print(f"❌ Error fetching page {page}: {e}")
        break

    matches = json_data.get("data", [])
    if not matches:
        break  # no more matches, exit loop

    for m in matches:
        team1 = m.get("t1", "").strip()
        team2 = m.get("t2", "").strip()
        series = m.get("series", "Unknown Series").strip()

        if not team1 or not team2:
            continue

        title = f"{team1} vs {team2} ({series})"
        if title in existing_titles:
            continue

        ts = m.get("timestamp") or m.get("start_time")  # depends on API
        start_time = None
        if ts:
            try:
                start_time = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")
            except:
                start_time = None

        match_entry = {
            "match_id": next_match_id,
            "title": title,
            "thumbnail": "https://example.com/placeholder.jpg",
            "status": "upcoming",
            "format": series,
            "start_time": start_time,
            "channels": [
                {
                    "channel_id": 1,
                    "name": "Sample Channel",
                    "stream_url": "https://example.com/sample/stream"
                }
            ]
        }

        data["matches"].append(match_entry)
        existing_titles.add(title)
        next_match_id += 1
        added += 1

    page += 1  # go to next page

# ---------------- Save JSON ----------------
with open(MATCHES_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Matches added: {added}")
