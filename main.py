import os
import requests
from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI(title="Alexa Global YouTube Music API")

# 🔴 अपनी Google YouTube Data API v3 Key यहाँ डालें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Alexa YouTube Music API is active!",
        "usage": "/get-audio?query=<song_name>"
    }

def extract_stream_multi_engine(video_id: str):
    yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # Engine 1: Android TV / Embedded Clients (डेटासेंटर बाइपास के लिए सर्वश्रेष्ठ)
    client_configs = [
        ['android_tv'],
        ['android'],
        ['web_embedded']
    ]

    for client in client_configs:
        ydl_opts = {
            'format': 'bestaudio/ba/b',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': client,
                    'skip': ['configs', 'webpage']
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_url, download=False)
                if 'url' in info:
                    return info['url']
                if 'formats' in info:
                    for f in reversed(info['formats']):
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            return f.get('url')
        except Exception:
            continue

    # Engine 2: Open Relay Fast Endpoints
    relay_endpoints = [
        f"https://api.download-lagu-mp3.com/@api/json/mp3/{video_id}",
    ]
    for endpoint in relay_endpoints:
        try:
            res = requests.get(endpoint, timeout=4).json()
            if "url" in res:
                return res["url"]
            if "link" in res:
                return res["link"]
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

    # 1. Google YouTube API v3 से सर्च (दुनिया का कोई भी वीडियो)
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

    # 2. मल्टी-इंजन से ऑडियो स्ट्रीम निकालना
    stream_url = extract_stream_multi_engine(video_id)

    if not stream_url:
        raise HTTPException(status_code=500, detail="Audio extraction failed across all engines")

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
