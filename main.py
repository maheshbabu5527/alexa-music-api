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
    yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # 1. Cobalt API Instances (YouTube ऑडियो के लिए सबसे तेज़ और सुरक्षित)
    cobalt_nodes = [
        "https://api.cobalt.tools",
        "https://cobalt.api.sc-0.fun",
        "https://cobalt.canine.tools"
    ]

    cobalt_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    cobalt_payload = {
        "url": yt_url,
        "downloadMode": "audio",
        "audioFormat": "mp3"
    }

    for node in cobalt_nodes:
        try:
            res = requests.post(f"{node}/", json=cobalt_payload, headers=cobalt_headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # अगर डायरेक्ट ऑडियो लिंक मिला
                if data.get("url"):
                    return RedirectResponse(url=data["url"], status_code=302)
                # कुछ इंस्टेंस stream URL लौटाते हैं
                if data.get("stream"):
                    return RedirectResponse(url=data["stream"], status_code=302)
        except Exception:
            continue

    # 2. बैकअप: डायरेक्ट इनविडियस ऑडियो CDN रिले
    invidious_backup = [
        "https://yt.artemislena.eu",
        "https://invidious.jing.rocks"
    ]
    for inv in invidious_backup:
        try:
            r = requests.get(f"{inv}/api/v1/videos/{video_id}", timeout=5)
            if r.status_code == 200:
                formats = r.json().get("adaptiveFormats", [])
                for f in formats:
                    if "audio" in f.get("type", "").lower() and f.get("url"):
                        u = f["url"]
                        if u.startswith("/"):
                            u = f"{inv}{u}"
                        return RedirectResponse(url=u, status_code=302)
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Unable to fetch audio stream. Please retry.")

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
