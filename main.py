import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="Alexa RapidAPI Direct Streamer")

# 🔴 अपनी Google YouTube Data API v3 Key
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

# RapidAPI Credentials
RAPIDAPI_KEY = "e80e6be1dfmsh911ee44acb373a5p1a9c30jsn546f39a7cb1b"
RAPIDAPI_HOST = "youtube-mp36.p.rapidapi.com"

@app.get("/")
def home():
    return {"status": "online", "message": "Ultra-Fast Direct Audio Engine Ready!"}

def get_clean_audio_url(video_id: str):
    url = f"https://{RAPIDAPI_HOST}/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=12)
        data = res.json()
        
        # API से आने वाला ओरिजिनल mp3 लिंक
        dlink = data.get("link")
        if dlink:
            return dlink
    except Exception as e:
        print(f"Error fetching from RapidAPI: {e}")
    return None

# 🔥 यह एंडपॉइंट 0.1 सेकंड में सीधे ऑडियो सर्वर पर रीडायरेक्ट करेगा
@app.get("/play/{video_id}.mp3")
def play_audio(video_id: str):
    direct_mp3 = get_clean_audio_url(video_id)
    if not direct_mp3:
        raise HTTPException(status_code=500, detail="Song link could not be fetched")
    
    # 302 Found सीधे CDN प्लेयर पर भेजेगा
    return RedirectResponse(url=direct_mp3, status_code=302)

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query missing")

    # 1. Search on YouTube
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
        items = search_res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="Song not found on YouTube")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/play/{video_id}.mp3"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
