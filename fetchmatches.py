import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os

URL = "https://crickapi.com/fixtures"  # jis page me ye script tag hai
MATCHES_FILE = "matches1.json"

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

script = soup.find("script", id="app-root-state")
if not script:
    print("❌ app-root-state JSON not found")
    exit(1)

# HTML entities (&q;) fix
raw_json = script.string.replace("&q;", '"')

state = json.loads(raw_json)

# API key inside JSON
fixture_key = next(k for k in state.keys() if "getFixture" in k)
fixtures = state[fixture_key]

added = 0

# ---------------- PARSE FIXTURES ----------------
for fx in fixtures:
    team1 = fx.get("t1", "")
    team2 = fx.get("t2", "")
    series = fx.get("series", "Unknown Series")

    title = f"{team1} vs {team2} ({series})"
    if title in existing_titles:
        continue

    # Time → ISO Z format
    ts = fx.get("timestamp")
    if ts:
        start_time = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        start_time = None

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
