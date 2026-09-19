from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

# 🔴 अपनी वही Google API Key यहाँ रहने दें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

def get_stream_from_video_id(video_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. Piped API से डायरेक्ट ऑडियो स्ट्रीम लिंक निकालना
    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacy.com.de",
        "https://piped-api.garudalinux.org"
    ]

    for instance in piped_instances:
        try:
            r = requests.get(f"{instance}/streams/{video_id}", headers=headers, timeout=3.5)
            if r.status_code == 200:
                data = r.json()
                audio_streams = data.get("audioStreams", [])
                if audio_streams:
                    # सबसे अच्छी क्वालिटी वाला ऑडियो लिंक
                    return audio_streams[-1].get("url")
        except Exception:
            continue

    # 2. Cobalt API बैकअप
    try:
        c_res = requests.post(
            "https://api.cobalt.tools/",
            json={"url": f"https://www.youtube.com/watch?v={video_id}", "downloadMode": "audio"},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=4.0
        ).json()
        if c_res.get("url"):
            return c_res.get("url")
    except Exception:
        pass

    return None

@app.get("/get-audio")
def get_audio(query: str):
    # 1. Google YouTube API से सर्च
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        res = requests.get(search_url, params=params, timeout=5).json()
        if "error" in res:
            raise HTTPException(status_code=400, detail=f"Google API Error: {res['error'].get('message')}")
        
        items = res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No video found")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # 2. ऑडियो स्ट्रीम निकालना
    stream_url = get_stream_from_video_id(video_id)

    if not stream_url:
        raise HTTPException(status_code=500, detail="Audio stream servers busy, please try again")

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
