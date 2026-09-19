from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

def get_stream(query: str):
    # Android Music & Web Creator Client (YouTube Music Native Engine)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'default_search': 'ytsearch1:',
        'extractor_args': {
            'youtube': {
                'player_client': ['android_music', 'android', 'web_creator'],
                'player_skip': ['configs']
            }
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
            
            # अगर सीधा URL न मिले तो formats लिस्ट से ऑडियो निकालें
            if not stream_url and 'formats' in video:
                audio_formats = [
                    f for f in video['formats'] 
                    if f.get('acodec') != 'none' and f.get('url')
                ]
                if audio_formats:
                    # सबसे अच्छी क्वालिटी का ऑडियो URL
                    stream_url = audio_formats[-1]['url']

            if stream_url:
                return {
                    "status": "success",
                    "title": video.get('title', query),
                    "stream_url": stream_url
                }
    except Exception as e:
        print(f"Extraction error: {e}")

    return None

@app.get("/get-audio")
def get_audio(query: str):
    result = get_stream(query)
    if not result or not result.get("stream_url"):
        raise HTTPException(status_code=500, detail="Audio stream not found")
    return result
