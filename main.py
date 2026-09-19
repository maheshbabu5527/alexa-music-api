from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

def get_audio_from_youtube(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. YouTube से सबसे सटीक वीडियो ID निकालना
    video_id = None
    title = query
    
    try:
        search_url = f"https://invidious.nerdvpn.de/api/v1/search?q={requests.utils.quote(query)}&type=video"
        s_res = requests.get(search_url, headers=headers, timeout=5).json()
        if s_res and len(s_res) > 0:
            video_id = s_res[0].get("videoId")
            title = s_res[0].get("title", query)
    except Exception:
        pass

    if not video_id:
        try:
            # बैकअप सर्च
            s_url2 = f"https://pipedapi.kavin.rocks/search?q={requests.utils.quote(query)}&filter=music_songs"
            s2 = requests.get(s_url2, headers=headers, timeout=5).json()
            items = s2.get("items", [])
            if items:
                video_id = items[0]["url"].split("v=")[-1]
                title = items[0].get("title", query)
        except Exception:
            pass

    if not video_id:
        return None

    # 2. Cobalt API से डायरेक्ट MP3/M4A ऑडियो स्ट्रीम निकालना (No API Key Required)
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    cobalt_servers = [
        "https://api.cobalt.tools",
        "https://cobalt-api.kwiatekm.com",
        "https://cobalt.api.sc"
    ]

    cobalt_payload = {
        "url": yt_url,
        "downloadMode": "audio",
        "audioFormat": "mp3"
    }

    c_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    for server in cobalt_servers:
        try:
            r = requests.post(f"{server}/", json=cobalt_payload, headers=c_headers, timeout=6)
            data = r.json()
            stream_link = data.get("url")
            if stream_link:
                return {
                    "status": "success",
                    "title": title,
                    "stream_url": stream_link
                }
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = get_audio_from_youtube(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="Song stream not found")
    return data
