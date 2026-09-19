import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="Alexa RapidAPI YouTube MP3 Engine")

# 🔴 अपनी Google YouTube Data API v3 Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

# RapidAPI Credentials
RAPIDAPI_KEY = "e80e6be1dfmsh911ee44acb373a5p1a9c30jsn546f39a7cb1b"
RAPIDAPI_HOST = "youtube-mp36.p.rapidapi.com"

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "RapidAPI High-Speed Music Engine is active!"
    }

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    url = f"https://{RAPIDAPI_HOST}/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=12)
        res_data = response.json()

        # API से सीधा MP3 लिंक निकालना
        audio_link = res_data.get("link")

        if audio_link:
            return RedirectResponse(url=audio_link, status_code=302)

        # अगर पहली बार में प्रोसेसिंग में हो
        if res_data.get("status") == "processing":
            raise HTTPException(status_code=503, detail="Audio is converting, please retry in 2 seconds.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"RapidAPI Fetch Error: {e}")

    raise HTTPException(status_code=500, detail="Unable to get audio link from RapidAPI.")

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

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

    # 2. Alexa के लिए स्ट्रीमिंग एंडपॉइंट
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
