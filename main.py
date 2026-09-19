from fastapi import FastAPI, HTTPException
import requests
import json

app = FastAPI()

def fetch_direct_youtube_audio(query: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json"
    }

    # 1. YouTube Official Web Search API
    search_url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.00.00",
                "hl": "en",
                "gl": "IN"
            }
        },
        "query": query
    }

    try:
        s_res = requests.post(search_url, json=payload, headers=headers, timeout=6).json()
        sections = s_res.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        
        video_id = None
        title = query

        for sec in sections:
            items = sec.get("itemSectionRenderer", {}).get("contents", [])
            for it in items:
                v = it.get("videoRenderer")
                if v and "videoId" in v:
                    video_id = v["videoId"]
                    title = v.get("title", {}).get("runs", [{}])[0].get("text", query)
                    break
            if video_id:
                break

        if not video_id:
            return None

        # 2. YouTube Official Player API (Android Client Emulation - No bot block)
        player_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
        player_payload = {
            "context": {
                "client": {
                    "clientName": "ANDROID",
                    "clientVersion": "19.05.36",
                    "androidSdkVersion": 30,
                    "hl": "en",
                    "gl": "IN"
                }
            },
            "videoId": video_id
        }

        p_res = requests.post(player_url, json=player_payload, headers=headers, timeout=6).json()
        streaming_data = p_res.get("streamingData", {})
        formats = streaming_data.get("adaptiveFormats", []) + streaming_data.get("formats", [])

        # ऑडियो स्ट्रीम ढूंढें (जिसमें url मौजूद हो)
        for f in formats:
            mime = f.get("mimeType", "")
            if "audio" in mime and "url" in f:
                return {
                    "status": "success",
                    "title": title,
                    "stream_url": f["url"]
                }

    except Exception as e:
        print(f"Direct Innertube Error: {e}")

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = fetch_direct_youtube_audio(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="Song stream not found")
    return data
