import os
import requests
from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI(title="Alexa YouTube Audio API")

# 🔴 अपनी Google YouTube Data API v3 Key यहाँ डालें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Alexa YouTube Music API is active!"
    }

def extract_audio_stream(video_id: str):
    yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # YouTube के ऐसे क्लाइंट्स जिन्हें JS solver / po-token की जरूरत नहीं पड़ती
    client_profiles = [
        ['tvhtml5'],
        ['android_vr'],
        ['ios'],
        ['mweb']
    ]

    for client in client_profiles:
        ydl_opts = {
            'format': 'ba/b',
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
                
                # 1. सीधा URL मिल जाए
                if info.get('url'):
                    return info['url']
                
                formats = info.get('formats', [])
                # 2. सिर्फ ऑडियो वाला फॉर्मेट (M4A / Opus)
                for f in reversed(formats):
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url'):
                        return f.get('url')

                # 3. कोई भी सीधा वर्किंग स्ट्रीम फॉर्मेट
                for f in reversed(formats):
                    if f.get('url'):
                        return f.get('url')
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

    # Step 1: Google YouTube Search API
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

    # Step 2: ऑडियो लिंक निकालना
    stream_url = extract_audio_stream(video_id)

    if not stream_url:
        raise HTTPException(status_code=500, detail="Unable to extract audio from video")

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
