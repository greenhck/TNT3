import requests

JSON_URL = "https://raw.githubusercontent.com/Odfinity/live-events/refs/heads/main/fancode/data.json"
OUTPUT_FILE = "fancode.m3u"

res = requests.get(JSON_URL, timeout=20)
data = res.json()

matches = data.get("matches", [])

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")

    for match in matches:
        title = match.get("title")
        logo = match.get("src")
        stream = match.get("adfree_url")

        # sirf adfree_url wale matches
        if not stream:
            continue

        f.write(
            f'#EXTINF:-1 tvg-logo="{logo}" group-title="Live Sports",{title}\n'
        )
        f.write(f"{stream}\n")
