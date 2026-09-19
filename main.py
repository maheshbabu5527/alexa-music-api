import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, RedirectResponse

app = FastAPI(title="Alexa Universal YouTube Audio API")

# 🔴 अपनी वही Google YouTube Data API v3 Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

# एक्टिव इनविडियस ऑडियो प्रॉक्सी मिरर्स
INVIDIOUS_MIRRORS = [
    "https://inv.nadeko.net",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://iv.nboeck.de"
]

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Alexa YouTube Music API is active and ready!"
    }

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # सभी मिरर्स से डायरेक्ट ऑडियो लिंक ढूँढना
    for mirror in INVIDIOUS_MIRRORS:
        try:
            api_url = f"{mirror}/api/v1/videos/{video_id}"
            res = requests.get(api_url, headers=headers, timeout=4)
            if res.status_code != 200:
                continue

            data = res.json()
            adaptive = data.get("adaptiveFormats", [])
            
            # ऑडियो स्ट्रीम निकालना
            for f in adaptive:
                if "audio" in f.get("type", "").lower() and f.get("url"):
                    stream_url = f["url"]
                    if stream_url.startswith("/"):
                        stream_url = f"{mirror}{stream_url}"
                    # Alexa को सीधे ऑडियो पर रीडायरेक्ट करें
                    return RedirectResponse(url=stream_url, status_code=302)

            format_streams = data.get("formatStreams", [])
            if format_streams and format_streams[0].get("url"):
                stream_url = format_streams[0]["url"]
                if stream_url.startswith("/"):
                    stream_url = f"{mirror}{stream_url}"
                return RedirectResponse(url=stream_url, status_code=302)

        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Audio mirror unavailable")

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Step 1: Google YouTube API v3 से YouTube पर दुनिया का कोई भी गाना खोजना
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

    # Step 2: Alexa के लिए सीधा ऑडियो स्ट्रीम URL तैयार करना
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
