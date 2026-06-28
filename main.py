import os, re, tempfile, asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(title="YT MP3 Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

MAX_SECONDS = 7 * 60  # 420 წამი

# ── helpers ─────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def safe_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", title)[:80]

# ── routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html", encoding="utf-8").read()


@app.get("/info")
async def video_info(url: str = Query(..., description="YouTube URL")):
    """ვიდეოს მეტადატა (სათაური, ხანგრძლივობა, thumbnail)"""
    vid_id = extract_video_id(url)
    if not vid_id:
        raise HTTPException(400, "Invalid YouTube URL")

    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid_id}", download=False)
    except Exception as e:
        raise HTTPException(500, f"yt-dlp error: {e}")

    duration = info.get("duration", 0)
    return {
        "id":        vid_id,
        "title":     info.get("title", ""),
        "duration":  duration,
        "thumbnail": info.get("thumbnail", ""),
        "channel":   info.get("uploader", ""),
        "eligible":  duration <= MAX_SECONDS,
    }


@app.get("/download")
async def download_mp3(url: str = Query(..., description="YouTube URL")):
    """MP3-ად გარდაქმნა და გადმოგზავნა"""
    vid_id = extract_video_id(url)
    if not vid_id:
        raise HTTPException(400, "Invalid YouTube URL")

    # ჯერ ვამოწმებ ხანგრძლივობას
    ydl_info_opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid_id}", download=False)
    except Exception as e:
        raise HTTPException(500, f"Info error: {e}")

    duration = info.get("duration", 0)
    if duration > MAX_SECONDS:
        raise HTTPException(403, f"ვიდეო {duration//60}:{duration%60:02d} — 7 წუთზე მეტია")

    title = safe_filename(info.get("title", vid_id))

    # temp dir-ში გადმოვიწერ
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, f"{title}.mp3")
        ydl_dl_opts = {
            "quiet":     True,
            "format":    "bestaudio/best",
            "outtmpl":   out_path,
            "noplaylist": True,
            "postprocessors": [{
                "key":            "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_dl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={vid_id}"])
        except Exception as e:
            raise HTTPException(500, f"Download error: {e}")

        # yt-dlp ზოგჯერ .mp3 სუფიქსს ამატებს ავტომატურად
        mp3_file = Path(out_path)
        if not mp3_file.exists():
            candidates = list(Path(tmpdir).glob("*.mp3"))
            if not candidates:
                raise HTTPException(500, "MP3 ფაილი ვერ შეიქმნა")
            mp3_file = candidates[0]

        # ვაბრუნებთ ფაილს — FastAPI წაიკითხავს სანამ temp dir-ი წაიშლება
        return FileResponse(
            path=str(mp3_file),
            media_type="audio/mpeg",
            filename=f"{title}.mp3",
            headers={"Content-Disposition": f'attachment; filename="{title}.mp3"'}
        )
