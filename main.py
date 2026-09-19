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

def get_direct_audio_url(video_id: str):
    yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # Engine 1: Y2Mate Cloud Audio Gateway
    try:
        y2_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.y2mate.com/",
            "Origin": "https://www.y2mate.com",
            "X-Requested-With": "XMLHttpRequest"
        }
        res = requests.post(
            "https://www.y2mate.com/mates/analyzeV2/ajax",
            data={"k_query": yt_url, "k_page": "home", "hl": "en", "q_auto": "0"},
            headers=y2_headers,
            timeout=7
        ).json()

        if res.get("status") == "ok":
            links = res.get("links", {})
            mp3_links = links.get("mp3", {})
            k_key = None
            for item in mp3_links.values():
                k_key = item.get("k")
                if k_key:
                    break

            if not k_key:
                audio_links = links.get("audio", {})
                for item in audio_links.values():
                    k_key = item.get("k")
                    if k_key:
                        break

            if k_key:
                conv = requests.post(
                    "https://www.y2mate.com/mates/convertV2/index",
                    data={"vid": video_id, "k": k_key},
                    headers=y2_headers,
                    timeout=8
                ).json()
                if conv.get("status") == "ok" and conv.get("dlink"):
                    return conv["dlink"]
    except Exception:
        pass

    # Engine 2: YT1s Dedicated Audio Resolver
    try:
        yt1s_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://yt1s.com/",
            "Origin": "https://yt1s.com"
        }
        res = requests.post(
            "https://yt1s.com/api/ajaxSearch/index",
            data={"q": yt_url, "vt": "mp3"},
            headers=yt1s_headers,
            timeout=7
        ).json()

        if res.get("status") == "ok":
            links = res.get("links", {})
            mp3_dict = links.get("mp3", {})
            k_key = None
            for item in mp3_dict.values():
                k_key = item.get("k")
                if k_key:
                    break

            if k_key:
                conv = requests.post(
                    "https://yt1s.com/api/ajaxConvert/index",
                    data={"vid": video_id, "k": k_key},
                    headers=yt1s_headers,
                    timeout=8
                ).json()
                if conv.get("status") == "ok" and conv.get("dlink"):
                    return conv["dlink"]
    except Exception:
        pass

    return None

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    audio_stream_url = get_direct_audio_url(video_id)

    if audio_stream_url:
        # Alexa और ब्राउज़र को सीधे लाइव MP3 ऑडियो लिंक पर भेजें
        return RedirectResponse(url=audio_stream_url, status_code=302)

    raise HTTPException(status_code=500, detail="Audio conversion service is currently busy. Please retry.")

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

    # Alexa के लिए स्ट्रीमिंग एंडपॉइंट
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
