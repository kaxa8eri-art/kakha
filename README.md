# 🎵 YT MP3 სერვერი

FastAPI + yt-dlp სერვერი YouTube ვიდეოების MP3-ად გადასაყვანად.
≤7 წუთიანი ვიდეოები მხოლოდ.

---

## 🚀 Render.com-ზე გაშვება (უფასო, 5 წუთი)

1. **GitHub-ზე ატვირთე** ეს საქაღალდე:
   - შექმენი ახალი repo: https://github.com/new
   - ატვირთე ყველა ფაილი

2. **Render.com-ზე:**
   - გადადი: https://render.com → Sign up (GitHub-ით)
   - "New +" → "Web Service"
   - აირჩიე შენი GitHub repo
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
   - "Create Web Service" დაჭირება

3. **ffmpeg Render-ზე:**
   Render-ის Free tier-ზე ffmpeg წინასწარ დაინსტალირებულია ✓

4. **მზადაა!** შენი სერვერი იქნება:
   ```
   https://yt-mp3-server.onrender.com
   ```

---

## 💻 ლოკალურად გაშვება

```bash
# 1. დაინსტალირე dependencies
pip install -r requirements.txt

# 2. ffmpeg (Windows)
# https://ffmpeg.org/download.html → გადმოიწერე და PATH-ში ჩამატე

# 3. გაუშვი სერვერი
uvicorn main:app --reload

# 4. გახსენი ბრაუზერში
# http://localhost:8000
```

---

## 📡 API Endpoints

| Method | Path | აღწერა |
|--------|------|--------|
| `GET` | `/` | ვებ ინტერფეისი |
| `GET` | `/info?url=...` | ვიდეოს ინფო (JSON) |
| `GET` | `/download?url=...` | MP3 გადმოტვირთვა |

---

## ⚠️ შენიშვნა

გამოიყენე Creative Commons / Public Domain კონტენტისთვის.
