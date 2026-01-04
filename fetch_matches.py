import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone

URL = "https://cricketdata.org/cricket-data-formats/schedule"

# ---------------- LOAD JSON ----------------
if os.path.exists("matches.json"):
    with open("matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"posters": [], "matches": []}

matches = data.get("matches", [])
existing_titles = {m["title"] for m in matches}
last_id = max([m.get("match_id", 0) for m in matches], default=0)

# ---------------- FETCH PAGE ----------------
resp = requests.get(URL, timeout=30)
soup = BeautifulSoup(resp.text, "html.parser")

table = soup.find("table", class_="table table-striped bg-white")
if not table:
    print("❌ Match table not found")
    exit(0)

tbody = table.find("tbody")
rows = tbody.find_all("tr")

print("Total rows found:", len(rows))

current_date = None
added = 0

for tr in rows:
    # Date row
    th = tr.find("th", colspan="3")
    if th:
        current_date = th.text.strip()  # "04 Jan 2026 (Sunday)"
        continue

    tds = tr.find_all("td")
    if len(tds) != 3 or not current_date:
        continue

    # Series name
    series_tag = tds[0].find("a")
    series_name = series_tag.text.strip() if series_tag else "Unknown Series"

    # Teams
    imgs = tds[1].find_all("img")
    if len(imgs) < 2:
        continue

    team1 = imgs[0].get("title", "Team A")
    team2 = imgs[1].get("title", "Team B")

    title = f"{team1} vs {team2} ({series_name})"

    # Duplicate check
    if title in existing_titles:
        continue

    # Date → ISO Z
    try:
        d = datetime.strptime(current_date.split("(")[0].strip(), "%d Jan %Y")
        start_time = d.replace(hour=15, minute=0, tzinfo=timezone.utc)
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
