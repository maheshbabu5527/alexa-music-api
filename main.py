import os
import requests
import yt_dlp
from fastapi import FastAPI, HTTPException

app = FastAPI()

# 🔴 अपनी Google YouTube API Key यहाँ इनवर्टेड कॉमा (" ") के अंदर डालें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

def extract_stream_direct(video_id: str):
    # iOS / Safari Web Client: बोट डिटेक्शन से सुरक्षित और डायरेक्ट ऑडियो लिंक
    ydl_opts = {
        'format': 'ba/b',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'safari']
            }
        }
    }

    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            
            # डायरेक्ट ऑडियो URL निकालना
            stream_url = info.get('url')
            if not stream_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        stream_url = f.get('url')
                        break
            return stream_url
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

@app.get("/get-audio")
def get_audio(query: str):
    # 1. Google YouTube API v3 से वीडियो खोजना
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        res = requests.get(search_url, params=params, timeout=6).json()
        
        # Google API की तरफ से कोई एरर चेक करना
        if "error" in res:
            raise HTTPException(status_code=400, detail=f"Google API Error: {res['error'].get('message')}")
        
        items = res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No video found on YouTube")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # 2. इन-हाउस इंजन से सीधा ऑडियो लिंक निकालना
    stream_url = extract_stream_direct(video_id)

    if not stream_url:
        raise HTTPException(status_code=500, detail="Audio extraction failed")

    # Alexa के लिए फाइनल रिस्पॉन्स
    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
