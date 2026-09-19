from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

# 🔴 अपनी API Key को इन दोनों इनवर्टेड कॉमा के बीच पेस्ट करें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/get-audio")
def get_audio(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. Google YouTube API से सर्च
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    video_id = None
    title = query

    try:
        res = requests.get(search_url, params=params, timeout=6).json()
        
        if "error" in res:
            raise HTTPException(status_code=400, detail=f"Google API Error: {res['error'].get('message')}")

        items = res.get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            title = items[0]["snippet"]["title"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search request failed: {e}")

    if not video_id:
        raise HTTPException(status_code=404, detail="No video found on YouTube for this query")

    # 2. डायरेक्ट ऑडियो स्ट्रीम नोड्स
    stream_nodes = [
        f"https://inv.nadeko.net/latest_version?id={video_id}&itag=140&local=true",
        f"https://invidious.nerdvpn.de/latest_version?id={video_id}&itag=140&local=true",
        f"https://invidious.jing.rocks/latest_version?id={video_id}&itag=140&local=true"
    ]

    for stream_url in stream_nodes:
        try:
            chk = requests.head(stream_url, headers=headers, timeout=3, allow_redirects=True)
            if chk.status_code in [200, 206, 302]:
                return {
                    "status": "success",
                    "title": title,
                    "video_id": video_id,
                    "stream_url": stream_url
                }
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Audio stream could not be loaded")
