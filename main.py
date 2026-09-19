import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import yt_dlp

app = FastAPI(title="Alexa YouTube Audio API")

# 🔴 अपनी Google YouTube Data API v3 Key यहाँ डालें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Alexa YouTube Audio API is running successfully!",
        "endpoint": "/get-audio?query=<song_name>"
    }

def get_audio_stream_fallback(video_id: str):
    # Method 1: yt-dlp with Android client (data-center friendly)
    ydl_opts = {
        'format': 'ba/b',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web_embedded']
            }
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            if 'url' in info:
                return info['url']
            if 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        return f.get('url')
    except Exception:
        pass

    # Method 2: Public Invidious Stream Proxy fallback
    invidious_instances = [
        "https://inv.tux.pizza",
        "https://invidious.nerdvpn.de",
        "https://yt.artemislena.eu"
    ]
    for instance in invidious_instances:
        try:
            url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(url, timeout=4).json()
            formats = res.get("adaptiveFormats", [])
            for f in formats:
                if "audio" in f.get("type", "").lower() and f.get("url"):
                    return f.get("url")
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Step 1: YouTube Search via Official Google API
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
            raise HTTPException(status_code=404, detail="No video found")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # Step 2: Extract Stream URL
    stream_url = get_audio_stream_fallback(video_id)
    if not stream_url:
        raise HTTPException(status_code=500, detail="Unable to extract audio stream at this moment")

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
