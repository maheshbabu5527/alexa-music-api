from fastapi import FastAPI, HTTPException
import yt_dlp
import requests

app = FastAPI()

def extract_stream(query: str):
    # 1. Android/iOS क्लाइंट बाईपास (Bot detection bypass)
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1:',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
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
                    "title": video.get('title', 'Unknown Track'),
                    "stream_url": stream_url
                }
    except Exception as e:
        print(f"yt-dlp error: {e}")

    # 2. फ़ॉलबैक: Piped API (अगर Render की IP ब्लॉक रहे)
    try:
        search_res = requests.get(
            f"https://pipedapi.kavin.rocks/search?q={query}&filter=music_songs",
            timeout=6
        ).json()
        
        if search_res.get('items'):
            video_id = search_res['items'][0]['url'].split('v=')[-1]
            stream_res = requests.get(
                f"https://pipedapi.kavin.rocks/streams/{video_id}",
                timeout=6
            ).json()
            
            audio_streams = stream_res.get('audioStreams', [])
            if audio_streams:
                return {
                    "status": "success",
                    "title": stream_res.get('title', 'Audio Track'),
                    "stream_url": audio_streams[0].get('url')
                }
    except Exception as e:
        print(f"Fallback error: {e}")

    return None

@app.get("/get-audio")
def get_audio(query: str):
    data = extract_stream(query)
    if not data or not data.get("stream_url"):
        raise HTTPException(status_code=500, detail="Unable to fetch audio stream")
    return data
