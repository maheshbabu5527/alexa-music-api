from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch1:',
}

@app.get("/")
def home():
    return {"status": "alive"}

@app.get("/get-audio")
def get_audio(query: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
            else:
                video = info
            
            return {
                "status": "success",
                "title": video.get('title', 'Unknown Track'),
                "stream_url": video.get('url')
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
