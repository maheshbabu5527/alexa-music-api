import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="Alexa Universal YouTube Audio API")

# 🔴 अपनी Google YouTube Data API v3 Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {"status": "online", "message": "Alexa Universal Music API Ready!"}

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. उच्च अपटाइम वाले सत्यापित Piped API इंस्टेंसेस
    piped_gateways = [
        "https://pipedapi.adminforge.de",
        "https://pipedapi.kavin.rocks",
        "https://api.piped.yt",
        "https://pipedapi.drgns.space"
    ]

    for base in piped_gateways:
        try:
            url = f"{base}/streams/{video_id}"
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                data = res.json()
                audio_streams = data.get("audioStreams", [])
                if audio_streams:
                    # सबसे पहला वैध ऑडियो स्ट्रीम URL
                    for a in audio_streams:
                        if a.get("url"):
                            return RedirectResponse(url=a["url"], status_code=302)
        except Exception:
            continue

    # 2. बैकअप: Invidious API इंस्टेंस
    invidious_gateways = [
        "https://invidious.adminforge.de",
        "https://inv.nadeko.net"
    ]

    for base in invidious_gateways:
        try:
            url = f"{base}/api/v1/videos/{video_id}"
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("adaptiveFormats", []):
                    if "audio" in item.get("type", "").lower() and item.get("url"):
                        u = item["url"]
                        if u.startswith("/"):
                            u = f"{base}{u}"
                        return RedirectResponse(url=u, status_code=302)
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Audio mirror connection timeout. Please retry.")

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

    # YouTube Data API v3 Search
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        search_res = requests.get(search_url, params=params, timeout=6).json()

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

    # Alexa के लिए सीधा स्ट्रीमिंग पाथ
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
