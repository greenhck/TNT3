import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os
import sys

URL = "https://crickapi.com/"
MATCHES_FILE = "matche.json"
DEBUG_HTML = "debug_page.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
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
print("🌐 Fetching page:", URL)
resp = requests.get(URL, headers=HEADERS, timeout=30)

print("📡 Status Code:", resp.status_code)
print("📦 Response length:", len(resp.text))

# Save HTML for inspection
with open(DEBUG_HTML, "w", encoding="utf-8") as f:
    f.write(resp.text)

print(f"📝 HTML saved to {DEBUG_HTML}")

if resp.status_code != 200 or len(resp.text) < 5000:
    print("❌ Page content looks blocked or incomplete")
    sys.exit(1)

soup = BeautifulSoup(resp.text, "html.parser")

# ---------------- FIND JSON SCRIPTS ----------------
scripts = soup.find_all("script")
print(f"🔍 Total <script> tags found: {len(scripts)}")

found_json = False
state = None

for idx, script in enumerate(scripts):
    content = script.string or script.text or ""
    if "fixture" in content.lower() or "match" in content.lower():
        print(f"➡️ Possible data script at index {idx} (length {len(content)})")

    if '"getFixture"' in content or "getFixture" in content:
        try:
            raw = content.replace("&q;", '"')
            state = json.loads(raw)
            found_json = True
            print("✅ Fixture JSON parsed successfully")
            break
        except Exception as e:
            print("⚠️ JSON parse failed:", e)

if not found_json:
    print("❌ No embedded fixture JSON found")
    print("👉 Open debug_page.html from GitHub Actions artifacts and search:")
    print('   keywords: getFixture, fixture, __NEXT_DATA__, app-root')
    sys.exit(1)

# ---------------- EXTRACT FIXTURES ----------------
fixtures = None
for k, v in state.items():
    if "fixture" in k.lower() and isinstance(v, list):
        fixtures = v
        break

if not fixtures:
    print("❌ Fixture list not found inside JSON")
    sys.exit(1)

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
