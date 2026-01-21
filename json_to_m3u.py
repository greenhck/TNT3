import json
import requests
from datetime import datetime

# URL of your JSON
JSON_URL = "https://raw.githubusercontent.com/drmlive/sliv-live-events/main/sonyliv.json"

# Output M3U file
OUTPUT_FILE = "sonyliv.m3u"

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def generate_m3u(data):
    lines = ["#EXTM3U"]
    
    for match in data.get("matches", []):
        if match.get("isLive"):
            name = match.get("match_name", "Unknown Match")
            channel = match.get("broadcast_channel", "Unknown Channel")
            url = match.get("video_url")
            lines.append(f'#EXTINF:-1 tvg-name="{channel}" group-title="{match.get("event_category")}",{name}')
            lines.append(url)
    
    return "\n".join(lines)

def main():
    data = fetch_json(JSON_URL)
    m3u_content = generate_m3u(data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"{OUTPUT_FILE} updated at {datetime.now()}")

if __name__ == "__main__":
    main()
