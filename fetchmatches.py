import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os

URL = "https://crickapi.com/"
MATCHES_FILE = "matche.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# ---------------- LOAD EXISTING JSON ----------------
if os.path.exists(MATCHES_FILE):
    with open(MATCHES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

existing_titles = {m["title"] for m in data.get("matches", [])}
next_match_id = max([m["match_id"] for m in data.get("matches", [])], default=0) + 1

# ---------------- FETCH PAGE ----------------
resp = requests.get(URL, headers=HEADERS, timeout=20)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# ---------------- FIND EMBEDDED JSON ----------------
state = None

for script in soup.find_all("script", type="application/json"):
    if not script.string:
        continue

    raw = script.string.strip()

    # fix HTML entities
    raw = raw.replace("&q;", '"')

    if "getFixture" in raw or "fixture" in raw:
        try:
            state = json.loads(raw)
            break
        except Exception:
            continue

if not state:
    print("❌ Embedded fixture JSON not found in any script tag")
    exit(1)

# ---------------- FIND FIXTURE DATA ----------------
fixtures = None

if isinstance(state, dict):
    for k, v in state.items():
        if "getFixture" in k or "fixture" in k:
            if isinstance(v, list):
                fixtures = v
                break

if not fixtures:
    print("❌ Fixture list not found in parsed JSON")
    exit(1)

# ---------------- PARSE FIXTURES ----------------
added = 0

for fx in fixtures:
    team1 = (fx.get("t1") or "").strip()
    team2 = (fx.get("t2") or "").strip()
    series = (fx.get("series") or "Unknown Series").strip()

    if not team1 or not team2:
        continue

    title = f"{team1} vs {team2} ({series})"
    if title in existing_titles:
        continue

    ts = fx.get("timestamp")
    start_time = None
    if ts:
        start_time = datetime.fromtimestamp(
            int(ts), tz=timezone.utc
        ).isoformat().replace("+00:00", "Z")

    match = {
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

    data["matches"].append(match)
    existing_titles.add(title)
    next_match_id += 1
    added += 1

# ---------------- SAVE ----------------
with open(MATCHES_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Matches added: {added}")
