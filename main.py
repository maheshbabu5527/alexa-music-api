import os
import requests
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Alexa YouTube Music API")

# 🔴 अपनी वही Google YouTube Data API Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

# इनविडियस पब्लिक इंस्टेंस की लिस्ट (ऑडियो स्ट्रीम के लिए)
INVIDIOUS_INSTANCES = [
    "https://yewtu.be",
    "https://iv.nboeck.de",
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
    "https://invidious.jing.rocks"
]

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Alexa YouTube Music API is active!"
    }

def get_audio_from_invidious(video_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for instance in INVIDIOUS_INSTANCES:
        try:
            url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code != 200:
                continue

            data = res.json()
            
            # 1. सबसे पहले सीधे ऑडियो-ओनली फॉर्मैट (m4a / webm) ढूँढें
            formats = data.get("adaptiveFormats", [])
            for f in formats:
                mime_type = f.get("type", "").lower()
                if "audio" in mime_type and f.get("url"):
                    stream_url = f.get("url")
                    # अगर रिलेटिव URL है तो डोमेन जोड़ें
                    if stream_url.startswith("/"):
                        stream_url = f"{instance}{stream_url}"
                    return stream_url

            # 2. अगर ऑडियो-ओनली नहीं मिला तो कंबाइंड फॉर्मैट लें
            regular_formats = data.get("formatStreams", [])
            if regular_formats and regular_formats[0].get("url"):
                stream_url = regular_formats[0].get("url")
                if stream_url.startswith("/"):
                    stream_url = f"{instance}{stream_url}"
                return stream_url

        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

    # Step 1: YouTube Official API से वीडियो खोजना
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        search_res = requests.get(search_url, params=params, timeout=5).json()
        
        if "error" in search_res:
            raise HTTPException(status_code=400, detail=f"Google API Error: {search_res['error'].get('message')}")
        
        items = search_res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No video found on YouTube")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # Step 2: स्ट्रीम निकालना
    stream_url = get_audio_from_invidious(video_id)

    if not stream_url:
        raise HTTPException(status_code=500, detail="Unable to extract audio from video")

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
