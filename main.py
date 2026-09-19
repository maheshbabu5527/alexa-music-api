import os
import time
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="Alexa Universal 10-Engine YouTube MP3 API")

# 🔴 अपनी वही Google YouTube Data API v3 Key यहाँ रखें
YOUTUBE_API_KEY = "AIzaSyCqpiPw4G0s2WJykCMWoVWKI99kcIfBpNE"

@app.get("/")
def home():
    return {"status": "online", "message": "10-Engine Universal YouTube API is Active!"}

def get_audio_from_mega_cluster(video_id: str):
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # ---------------- ENGINE 1: COBALT API (High-Speed Audio) ----------------
    try:
        cobalt_payload = {
            "url": yt_url,
            "downloadMode": "audio",
            "audioFormat": "mp3"
        }
        cobalt_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": headers["User-Agent"]
        }
        res = requests.post("https://api.cobalt.tools/", json=cobalt_payload, headers=cobalt_headers, timeout=4)
        if res.status_code == 200:
            d = res.json()
            if d.get("url"):
                return d["url"]
    except Exception:
        pass

    # ---------------- ENGINE 2: Y2MATE CLOUD RELAY ----------------
    try:
        y2_headers = {
            "User-Agent": headers["User-Agent"],
            "Referer": "https://www.y2mate.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
        res = requests.post(
            "https://www.y2mate.com/mates/analyzeV2/ajax",
            data={"k_query": yt_url, "k_page": "home", "hl": "en", "q_auto": "0"},
            headers=y2_headers,
            timeout=4
        ).json()
        if res.get("status") == "ok":
            links = res.get("links", {})
            mp3_links = links.get("mp3", {}) or links.get("audio", {})
            for item in mp3_links.values():
                k_key = item.get("k")
                if k_key:
                    conv = requests.post(
                        "https://www.y2mate.com/mates/convertV2/index",
                        data={"vid": video_id, "k": k_key},
                        headers=y2_headers,
                        timeout=5
                    ).json()
                    if conv.get("status") == "ok" and conv.get("dlink"):
                        return conv["dlink"]
    except Exception:
        pass

    # ---------------- ENGINE 3: YT1S API CONVERTER ----------------
    try:
        yt1s_headers = {"User-Agent": headers["User-Agent"], "Referer": "https://yt1s.com/"}
        res = requests.post(
            "https://yt1s.com/api/ajaxSearch/index",
            data={"q": yt_url, "vt": "mp3"},
            headers=yt1s_headers,
            timeout=4
        ).json()
        if res.get("status") == "ok":
            mp3_dict = res.get("links", {}).get("mp3", {})
            for item in mp3_dict.values():
                k_key = item.get("k")
                if k_key:
                    conv = requests.post(
                        "https://yt1s.com/api/ajaxConvert/index",
                        data={"vid": video_id, "k": k_key},
                        headers=yt1s_headers,
                        timeout=5
                    ).json()
                    if conv.get("status") == "ok" and conv.get("dlink"):
                        return conv["dlink"]
    except Exception:
        pass

    # ---------------- ENGINE 4: VEVIOZ MP3 DIRECT RELAY ----------------
    try:
        vev_url = f"https://api.vevioz.com/api/button/mp3/{video_id}"
        r = requests.get(vev_url, headers=headers, timeout=4)
        if r.status_code == 200:
            import re
            found = re.findall(r'href=[\'"]?(https[^\'" >]+)', r.text)
            for f in found:
                if "download" in f or "googlevideo" in f:
                    return f
    except Exception:
        pass

    # ---------------- ENGINE 5: ADMINFORGE PIPED STREAMER ----------------
    try:
        res = requests.get(f"https://pipedapi.adminforge.de/streams/{video_id}", headers=headers, timeout=4)
        if res.status_code == 200:
            streams = res.json().get("audioStreams", [])
            if streams and streams[0].get("url"):
                return streams[0]["url"]
    except Exception:
        pass

    # ---------------- ENGINE 6: KAVIN PIPED STREAMER ----------------
    try:
        res = requests.get(f"https://pipedapi.kavin.rocks/streams/{video_id}", headers=headers, timeout=4)
        if res.status_code == 200:
            streams = res.json().get("audioStreams", [])
            if streams and streams[0].get("url"):
                return streams[0]["url"]
    except Exception:
        pass

    # ---------------- ENGINE 7: NADEKO INVIDIOUS NODE ----------------
    try:
        res = requests.get(f"https://inv.nadeko.net/api/v1/videos/{video_id}", headers=headers, timeout=4)
        if res.status_code == 200:
            formats = res.json().get("adaptiveFormats", [])
            for item in formats:
                if "audio" in item.get("type", "").lower() and item.get("url"):
                    u = item["url"]
                    return f"https://inv.nadeko.net{u}" if u.startswith("/") else u
    except Exception:
        pass

    # ---------------- ENGINE 8: JING ROCKS INVIDIOUS NODE ----------------
    try:
        res = requests.get(f"https://invidious.jing.rocks/api/v1/videos/{video_id}", headers=headers, timeout=4)
        if res.status_code == 200:
            formats = res.json().get("adaptiveFormats", [])
            for item in formats:
                if "audio" in item.get("type", "").lower() and item.get("url"):
                    u = item["url"]
                    return f"https://invidious.jing.rocks{u}" if u.startswith("/") else u
    except Exception:
        pass

    # ---------------- ENGINE 9: SAVENOW (LOADER.TO) API ----------------
    try:
        loader_url = f"https://p.savenow.to/ajax/download.php?format=mp3&url={yt_url}&apikey=dfcb6d76f2f6a98d74bfde0f47170a"
        res = requests.get(loader_url, headers=headers, timeout=4).json()
        if res.get("success"):
            job_id = res.get("id")
            for _ in range(3):
                time.sleep(1)
                prog = requests.get(f"https://p.savenow.to/ajax/progress.php?id={job_id}", headers=headers, timeout=3).json()
                if prog.get("download_url"):
                    return prog["download_url"]
    except Exception:
        pass

    # ---------------- ENGINE 10: CLOUDFLARE WORKER DIRECT AUDIO TUNNEL ----------------
    try:
        tunnel = f"https://yt-dl.audio-worker.workers.dev/stream?id={video_id}"
        head_test = requests.head(tunnel, headers=headers, timeout=3)
        if head_test.status_code in [200, 302]:
            return tunnel
    except Exception:
        pass

    return None

@app.get("/stream/{video_id}")
def stream_audio(video_id: str):
    audio_stream_url = get_audio_from_mega_cluster(video_id)

    if audio_stream_url:
        return RedirectResponse(url=audio_stream_url, status_code=302)

    raise HTTPException(status_code=500, detail="All 10 Global Engines are processing high load. Please retry.")

@app.get("/get-audio")
def get_audio(request: Request, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter missing")

    # Step 1: Google YouTube Search
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    try:
        search_res = requests.get(search_url, params=params, timeout=6).json()

        if "error" in search_res:
            raise HTTPException(status_code=400, detail=f"Google API Error: {search_res['error'].get('message')}")

        items = search_res.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail="No video found on YouTube")

        video_id = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    # Step 2: Alexa के लिए सीधा स्ट्रीमिंग एंडपॉइंट
    base_url = str(request.base_url).rstrip("/")
    stream_url = f"{base_url}/stream/{video_id}"

    return {
        "status": "success",
        "title": title,
        "video_id": video_id,
        "stream_url": stream_url
    }
