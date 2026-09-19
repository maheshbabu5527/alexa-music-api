from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

# एक्टिव YouTube API एंडपॉइंट्स
ENGINES = [
    {"type": "piped", "url": "https://pipedapi.kavin.rocks"},
    {"type": "piped", "url": "https://api.piped.privacydev.net"},
    {"type": "invidious", "url": "https://inv.nadeko.net"},
    {"type": "invidious", "url": "https://invidious.nerdvpn.de"}
]

def search_and_get_stream(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for engine in ENGINES:
        base = engine["url"]
        engine_type = engine["type"]

        try:
            if engine_type == "piped":
                # 1. Piped से सर्च करें
                s_url = f"{base}/search?q={requests.utils.quote(query)}&filter=music_songs"
                s_res = requests.get(s_url, headers=headers, timeout=4).json()
                items = s_res.get("items", [])
                if not items:
                    continue

                video_id = items[0]["url"].split("v=")[-1]
                title = items[0].get("title", query)

                # 2. Piped से ऑडियो स्ट्रीम निकालें
                stream_res = requests.get(f"{base}/streams/{video_id}", headers=headers, timeout=4).json()
                audio_streams = stream_res.get("audioStreams", [])
                if audio_streams:
                    return {
                        "status": "success",
                        "title": title,
                        "stream_url": audio_streams[0]["url"]
                    }

            elif engine_type == "invidious":
                # 1. Invidious से सर्च करें
                s_url = f"{base}/api/v1/search?q={requests.utils.quote(query)}&type=video"
                s_res = requests.get(s_url, headers=headers, timeout=4).json()
                if not s_res:
                    continue

                video_id = s_res[0].get("videoId")
                title = s_res[0].get("title", query)

                # 2. Invidious से ऑडियो स्ट्रीम निकालें
                v_res = requests.get(f"{base}/api/v1/videos/{video_id}", headers=headers, timeout=4).json()
                for f in v_res.get("adaptiveFormats", []):
                    if f.get("type", "").startswith("audio/"):
                        return {
                            "status": "success",
                            "title": title,
                            "stream_url": f.get("url")
                        }
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = search_and_get_stream(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="Song stream not found")
    return data
