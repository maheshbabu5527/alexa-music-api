from fastapi import FastAPI, HTTPException
import yt_dlp
import requests

app = FastAPI()

def get_stream(query: str):
    # 1. तगड़ा कॉन्फ़िगरेशन: Android TV & iOS Music Client Emulation
    # YouTube को लगता है कि यह Smart TV या Official Music App है
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'default_search': 'ytsearch1:',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'tv', 'ios'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(query, download=False)
            if 'entries' in res and len(res['entries']) > 0:
                video = res['entries'][0]
            else:
                video = res

            stream_url = video.get('url')
            if stream_url:
                return {
                    "status": "success",
                    "title": video.get('title', query),
                    "stream_url": stream_url
                }
    except Exception as e:
        print(f"Native TV client failed: {e}")

    # 2. सेकंड लेयर बैकअप: Piped API (डिसेंट्रलाइज्ड YouTube म्यूजिक गेटवे)
    piped_gateways = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacydev.net"
    ]
    for gateway in piped_gateways:
        try:
            s_req = requests.get(
                f"{gateway}/search?q={requests.utils.quote(query)}&filter=music_songs",
                timeout=4
            ).json()
            items = s_req.get("items", [])
            if items:
                v_id = items[0]["url"].split("v=")[-1]
                v_title = items[0].get("title", query)
                st_req = requests.get(f"{gateway}/streams/{v_id}", timeout=4).json()
                audios = st_req.get("audioStreams", [])
                if audios:
                    return {
                        "status": "success",
                        "title": v_title,
                        "stream_url": audios[0]["url"]
                    }
        except Exception:
            continue

    return None

@app.get("/get-audio")
def get_audio(query: str):
    result = get_stream(query)
    if not result or not result.get("stream_url"):
        raise HTTPException(status_code=500, detail="Audio stream not found")
    return result
