from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

INVIDIOUS_NODES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://invidious.jing.rocks",
    "https://inv.tux.pizza"
]

def fetch_youtube_stream(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for base in INVIDIOUS_NODES:
        try:
            # 1. सर्च करें
            search_url = f"{base}/api/v1/search?q={requests.utils.quote(query)}&type=video"
            s_res = requests.get(search_url, headers=headers, timeout=4)
            if s_res.status_code != 200:
                continue
            
            videos = s_res.json()
            if not videos:
                continue

            video_id = videos[0].get("videoId")
            title = videos[0].get("title", query)

            # 2. ऑडियो स्ट्रीम यूआरएल निकालें
            vid_url = f"{base}/api/v1/videos/{video_id}"
            v_res = requests.get(vid_url, headers=headers, timeout=4)
            if v_res.status_code != 200:
                continue

            v_data = v_res.json()
            formats = v_data.get("adaptiveFormats", [])

            # ऑडियो फॉर्मेट्स ढूंढें (m4a या opus)
            for f in formats:
                if f.get("type", "").startswith("audio/"):
                    stream_url = f.get("url")
                    if stream_url:
                        return {
                            "status": "success",
                            "title": title,
                            "stream_url": stream_url
                        }
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = fetch_youtube_stream(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="Audio stream not found")
    return data
