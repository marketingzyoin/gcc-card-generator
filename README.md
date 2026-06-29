# GCC Workplace Innovation Summit — "I'm Attending" Card Generator

Attendees upload their photo → background removed automatically → placed in badge → download and share.

---

## Deploy to Railway (free, no card needed)

### Step 1 — Push to GitHub
1. Create a new repo on github.com (name it `gcc-card-generator`)
2. Upload all files from this ZIP into that repo (drag and drop on GitHub works)

### Step 2 — Deploy on Railway
1. Go to https://railway.app
2. Sign up / log in with your GitHub account
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your `gcc-card-generator` repo
5. Railway auto-detects the Procfile and starts deploying
6. Wait ~3 minutes for first deploy (downloads the AI model)
7. Click **Settings** → **Domains** → **Generate Domain**
8. Copy that URL — share it with attendees ✅

---

## How it works
1. Attendee opens the link
2. Uploads any photo (selfie, professional, any background)
3. Clicks Generate
4. Server removes background using rembg (free, open source AI)
5. Person placed on purple background (RGB 142,110,157)
6. Fitted into badge zone: (106,415) to (490,913)
7. Template frame composited on top
8. Final 1080×1350 JPEG returned for download

## File structure
```
gcc-card-generator/
├── app.py              ← Flask backend
├── requirements.txt    ← Python packages
├── Procfile            ← Railway/Render start command
├── runtime.txt         ← Python 3.11
├── README.md
└── static/
    ├── index.html      ← Frontend (upload + preview + download)
    └── template.png    ← Event card template (1080×1350)
```
