import json, requests
import time
  
def fetch_all_genres():
    genres, offset, limit = [], 0, 100
    while True:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/genre/all",
            params={"limit": limit, "offset": offset, "fmt": "json"},
            headers={"User-Agent": "vestibule-radio/0.1 (pixl.808 on discord)"},
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("genres", [])
        genres.extend(g["name"] for g in batch)
        if len(genres) >= data["genre-count"]:
            break
        offset += limit
        time.sleep(1)
    return genres
      
with open("scraper/downloader/genres.json", "w") as f:
    json.dump(sorted(fetch_all_genres()), f, indent=2)
