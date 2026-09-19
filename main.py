import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="Alexa Universal Live Audio Streamer")

# 🔴 अपनी Google YouTube Data API v3 Key
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

# RapidAPI Credentials
RAPIDAPI_KEY = "e80e6be1dfmsh911ee44acb373a5p1a9c30jsn546f39a7cb1b"
RAPIDAPI_HOST = "youtube-mp36.p.rapidapi.com"

@app.get("/")
def home():
    return {"status": "online", "message": "Live Audio Player Streamer is Ready!"}

def get_rapid_mp3_download_url(video_id: str):
    url = f"https://{RAPIDAPI_HOST}/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=12)
        data = res.json()
        return data.get("link")
    except Exception as e:
        print(f"RapidAPI Error: {e}")
        return None

# 🔥 यह एंडपॉइंट डाउनलोड को लाइव प्ले में बदलता है (Live Streaming Audio)
@app.get("/play/{video_id}.mp3")
def play_audio(video_id: str):
    raw_mp3_url = get_rapid_mp3_download_url(video_id)
    if not raw_mp3_url:
        raise HTTPException(status_code=500, detail="Audio link unavailable")

    def audio_stream_generator():
        headers = {"User-Agent": "Mozilla/5.0"}
        with requests.get(raw_mp3_url, headers=headers, stream=True, timeout=15) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=32768):
                if chunk:
                    yield chunk

    # Alexa के लिए सख्त Streaming हेडर: inline (प्ले करो, डाउनलोड मत करो)
    return StreamingResponse(
        audio_stream_generator(),
        media_type="audio/mpeg",
        headers={
            "Content-Type": "audio/mpeg",
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes"
        }
    )

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query missing")

    # 1. YouTube Search
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
            raise HTTPException(status_code=404, detail="Song not found")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # 2. Alexa को सीधा लाइव प्ले होने वाला .mp3 लिंक देना
    base_url = str(request.base_url).rstrip("/")
    live_play_url = f"{base_url}/play/{video_id}.mp3"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": live_play_url
    }
