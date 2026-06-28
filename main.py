import os, re, tempfile, shutil
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

MAX_SECONDS = 7 * 60

# ── bot-detection bypass options ────────────────────────────────────────
def base_opts():
    return {
        "quiet": True,
        "noplaylist": True,
        # Android client — Render IP-ებს არ ბლოკავს
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/19.09.37 "
                "(Linux; U; Android 11) gzip"
            ),
        },
    }

def extract_video_id(url: str):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None

def safe_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", title)[:80]

# ── routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html", encoding="utf-8").read()


@app.get("/info")
async def video_info(url: str = Query(...)):
    vid_id = extract_video_id(url)
    if not vid_id:
        raise HTTPException(400, "Invalid YouTube URL")

    opts = {**base_opts(), "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid_id}", download=False
            )
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
async def download_mp3(url: str = Query(...)):
    vid_id = extract_video_id(url)
    if not vid_id:
        raise HTTPException(400, "Invalid YouTube URL")

    # info check
    info_opts = {**base_opts(), "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid_id}", download=False
            )
    except Exception as e:
        raise HTTPException(500, f"Info error: {e}")

    duration = info.get("duration", 0)
    if duration > MAX_SECONDS:
        raise HTTPException(403, f"ვიდეო {duration//60}:{duration%60:02d} — 7 წუთზე მეტია")

    title = safe_filename(info.get("title", vid_id))

    # გადმოიწერა temp-ში, შემდეგ /tmp/ytmp3/-ში გადავიყვანთ რომ FileResponse-მა წაიკითხოს
    out_dir = Path("/tmp/ytmp3")
    out_dir.mkdir(exist_ok=True)
    out_path = str(out_dir / f"{vid_id}.mp3")

    dl_opts = {
        **base_opts(),
        "format":   "bestaudio/best",
        "outtmpl":  str(out_dir / f"{vid_id}.%(ext)s"),
        "postprocessors": [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "mp3",
            "preferredquality": "192",
        }],
    }
    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={vid_id}"])
    except Exception as e:
        raise HTTPException(500, f"Download error: {e}")

    mp3_file = Path(out_path)
    if not mp3_file.exists():
        candidates = list(out_dir.glob(f"{vid_id}*.mp3"))
        if not candidates:
            raise HTTPException(500, "MP3 ფაილი ვერ შეიქმნა")
        mp3_file = candidates[0]

    return FileResponse(
        path=str(mp3_file),
        media_type="audio/mpeg",
        filename=f"{title}.mp3",
        headers={"Content-Disposition": f'attachment; filename="{title}.mp3"'},
        background=None,
    )
