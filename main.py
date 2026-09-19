from fastapi import FastAPI, HTTPException
import yt_dlp
import requests

app = FastAPI()

def get_youtube_audio(query: str):
    # 1. YouTube Android TV / VR Client (बॉट डिटेक्शन बाईपास)
    ydl_opts = {
        'format': 'bestaudio/ba/b',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1:',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_downgraded', 'android_vr', 'web_creator']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
            else:
                video = info

            stream_url = video.get('url')
            if stream_url:
                return {
                    "status": "success",
                    "title": video.get('title', query),
                    "stream_url": stream_url
                }
    except Exception as e:
        print(f"yt-dlp TV bypass failed: {e}")

    # 2. फ़ॉलबैक: YouTube सर्च + Cobalt / Invidious API
    try:
        # YouTube से वीडियो सर्च
        search_api = f"https://invidious.nerdvpn.de/api/v1/search?q={requests.utils.quote(query)}&type=video"
        s_res = requests.get(search_api, timeout=5).json()

        if s_res and len(s_res) > 0:
            vid_id = s_res[0].get("videoId")
            vid_title = s_res[0].get("title", query)

            # Cobalt API से सीधा YouTube ऑडियो स्ट्रीम लिंक
            cobalt_payload = {
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "downloadMode": "audio"
            }
            c_res = requests.get(
                f"https://invidious.nerdvpn.de/api/v1/videos/{vid_id}",
                timeout=5
            ).json()

            formats = c_res.get("adaptiveFormats", [])
            for f in formats:
                if "audio" in f.get("type", ""):
                    return {
                        "status": "success",
                        "title": vid_title,
                        "stream_url": f.get("url")
                    }
    except Exception as e:
        print(f"Fallback bypass failed: {e}")

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = get_youtube_audio(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="YouTube stream not found")
    return data
