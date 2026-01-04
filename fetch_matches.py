import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone

URL = "https://cricketdata.org/cricket-data-formats/schedule"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# ---------------- LOAD OR CREATE matches.json ----------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
existing_titles = {m["title"] for m in matches}
last_id = max([m.get("match_id", 0) for m in matches], default=0)

# ---------------- FETCH HTML ----------------
resp = requests.get(URL, headers=HEADERS, timeout=30)
html = resp.text

print("HTML length:", len(html))

soup = BeautifulSoup(html, "html.parser")

table = soup.find("table", class_="table table-striped bg-white")
if not table:
    print("❌ Match table not found")
    exit(0)

tbody = table.find("tbody")
if not tbody:
    print("❌ tbody not found")
    exit(0)

rows = tbody.find_all("tr")
print("Total rows found:", len(rows))

current_date = None
added = 0

for tr in rows:
    # Date row
    th = tr.find("th", colspan="3")
    if th:
        current_date = th.text.strip()  # e.g. 04 Jan 2026 (Sunday)
        continue

    tds = tr.find_all("td")
    if len(tds) != 3 or not current_date:
        continue

    # Series
    series_tag = tds[0].find("a")
    series_name = series_tag.text.strip() if series_tag else "Unknown Series"

    # Teams
    imgs = tds[1].find_all("img")
    if len(imgs) < 2:
        continue

    team1 = imgs[0].get("title", "Team A")
    team2 = imgs[1].get("title", "Team B")

    title = f"{team1} vs {team2} ({series_name})"

    # Skip duplicates
    if title in existing_titles:
        continue

    # Date → ISO Z
    try:
        date_clean = current_date.split("(")[0].strip()
        match_date = datetime.strptime(date_clean, "%d %b %Y")
        start_time = match_date.replace(hour=15, minute=0, tzinfo=timezone.utc)
    except:
        start_time = datetime.now(timezone.utc)

    last_id += 1
    added += 1

    matches.append({
        "match_id": last_id,
        "title": title,
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

    existing_titles.add(title)

# ---------------- SAVE ----------------
data["matches"] = matches

with open("matches.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Matches added: {added}")
