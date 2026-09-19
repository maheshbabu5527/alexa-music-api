import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="Alexa Universal YouTube Audio API")

# 🔴 अपनी वही Google YouTube Data API v3 Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {"status": "online", "message": "Alexa YouTube Music API is active!"}

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. Piped & Invidious के सबसे ताज़ा और वर्किंग एक्टिव गेटवे
    active_stream_endpoints = [
        f"https://api.piped.private.coffee/streams/{video_id}",
        f"https://pipedapi.tokhmi.xyz/streams/{video_id}",
        f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}",
        f"https://inv.nadeko.net/api/v1/videos/{video_id}"
    ]

    for ep in active_stream_endpoints:
        try:
            res = requests.get(ep, headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()

            # Piped Format से ऑडियो लिंक
            audio_streams = data.get("audioStreams", [])
            if audio_streams and audio_streams[0].get("url"):
                return RedirectResponse(url=audio_streams[0]["url"], status_code=302)

            # Invidious Format से ऑडियो लिंक
            adaptive = data.get("adaptiveFormats", [])
            for f in adaptive:
                if "audio" in f.get("type", "").lower() and f.get("url"):
                    u = f["url"]
                    if u.startswith("/"):
                        base = ep.split("/api/v1")[0]
                        u = f"{base}{u}"
                    return RedirectResponse(url=u, status_code=302)

        except Exception:
            continue

    # 2. बैकअप डायरेक्ट कनवर्टर गेटवे (यदि सभी नोड्स बिज़ी हों)
    backup_url = f"https://api.vevioz.com/api/button/mp3/{video_id}"
    try:
        r = requests.get(backup_url, headers=headers, timeout=5)
        if r.status_code == 200 and "href" in r.text:
            import re
            links = re.findall(r'href=[\'"]?(https[^\'" >]+)', r.text)
            for l in links:
                if "download" in l or "googlevideo" in l:
                    return RedirectResponse(url=l, status_code=302)
    except Exception:
        pass

    raise HTTPException(status_code=500, detail="Audio stream currently busy, please retry")

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Step 1: Google YouTube Data API v3 से वीडियो खोजना
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
            raise HTTPException(status_code=404, detail="No video found on YouTube")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # Step 2: Alexa के लिए सीधा ऑडियो स्ट्रीम URL बनाना
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
