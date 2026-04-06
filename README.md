# Social Media Downloader API

A powerful FastAPI-based video downloader supporting Instagram, TikTok, YouTube, and 1000+ platforms — with zero-disk streaming, server-side proxy, and real-time progress tracking.

## ✨ Features

- 🎥 **Multi-Platform Support**: Download from Instagram, TikTok, YouTube, Facebook, Twitter/X, and 1000+ sites via yt-dlp
- 🚫 **TikTok Without Watermark**: HD no-watermark downloads powered by the TikWM API
- 🎬 **Instagram HD Quality**: Download Instagram Reels/Posts in 720p+
- 📊 **Real-Time Progress**: Live download progress via XHR (web) and `expo-file-system` (mobile)
- 📱 **Mobile Ready**: Zero-change React Native/Expo integration — works out of the box
- 🌐 **CORS Enabled**: Works with web browsers, mobile apps, and Expo Go
- 🔄 **Server-Side Stream Proxy**: Bypasses TikTok CDN blocking on mobile & mobile web
- 🍪 **Cookie Support**: Bypass YouTube bot detection
- 🗑️ **Auto Cleanup**: Automatic temp file cleanup after download
- 🎨 **Modern UI**: Glassmorphism dark-mode web interface with live progress bar
- ☁️ **Production Ready**: Deployed on Render with zero-disk-storage streaming
- 📥 **Force Download**: `Content-Disposition: attachment` triggers Save-As on all platforms
- 📈 **Native Progress**: `Content-Length` headers forwarded from CDN for native mobile progress bars
- ⚡ **Optimized**: Single TikWM API call per request (no double fetches)

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/fazi-gondal/FastAPI.git
cd FastAPI
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`

### Requirements

- Python 3.11+
- FastAPI, uvicorn, httpx, yt-dlp, aiofiles

## 📋 Usage

### Web Interface

1. Open `http://localhost:8000`
2. Paste a TikTok, Instagram, YouTube, or any supported video URL
3. Hit **Get Video** — metadata loads automatically
4. Download starts with real-time progress bar

### API Integration

See [API.md](API.md) for full API documentation.

```javascript
// Fetch metadata
const res = await fetch('/api/metadata', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'https://www.tiktok.com/@user/video/123' })
});
const { data } = await res.json();
// { title, thumbnail, duration, uploader, platform }
```

### React Native / Expo Integration

See [REACT_NATIVE_INTEGRATION.md](REACT_NATIVE_INTEGRATION.md) for the complete guide.

```bash
npx expo install expo-file-system expo-media-library axios
```

## 🌐 Deployment

### Render (Recommended)

1. Push to GitHub
2. Connect repo on [Render](https://render.com)
3. Set:
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Production URL: `https://fastapi-u8bm.onrender.com`

See [DEPLOYMENT.md](DEPLOYMENT.md) for Koyeb and other platforms.

## 📊 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/metadata` | POST | Get video title, thumbnail, duration, uploader |
| `/api/get-direct-url` | POST | Resolve download URL (proxy or CDN) |
| `/api/stream` | GET | **Server-side proxy stream** — for TikTok & CDN-blocked platforms |
| `/api/tiktok/info` | GET | Full TikWM data: `hdplay`, `play`, `wmplay`, `cover`, `author`, `music_info` |
| `/api/proxy-stream` | POST | Lightweight CDN proxy (POST variant) |
| `/api/server-stream` | POST | yt-dlp server-download + stream (DASH/merged) |
| `/api/download/start` | POST | Start background download, returns ID |
| `/api/download/progress/{id}` | GET | SSE progress stream |
| `/api/download/file/{id}` | GET | Serve completed download file |
| `/api/thumbnail` | GET | CORS proxy for CDN thumbnails |

## 🔁 Download Flow Architecture

### TikTok (no-watermark HD)

```
Web/Mobile  →  POST /api/get-direct-url
Backend     →  TikWM API (hd=1) — single call
Backend     ←  { direct_url: "/api/stream?url=...&direct_url=<cdn>" }
Web/Mobile  →  GET /api/stream?url=...&direct_url=<cdn>  (fast path, no 2nd API call)
Backend     →  Proxy TikWM CDN bytes → Client (with Content-Length)
```

### Instagram

```
Web/Mobile  →  POST /api/get-direct-url  →  yt-dlp extracts URL
Backend     ←  { direct_url: "/api/stream?url=..." }
Client      →  GET /api/stream  →  yt-dlp CDN → Client
```

### YouTube / Twitter / Others

```
Web/Mobile  →  POST /api/get-direct-url  →  yt-dlp extracts CDN URL
Backend     ←  { direct_url: "https://cdn.example.com/...", force_backend_stream: true }
Client      →  GET /api/stream  →  Proxied stream → Client
```

## 🎯 Supported Platforms

- ✅ YouTube (with cookie support)
- ✅ Instagram (Posts, Reels, IGTV in HD)
- ✅ TikTok (watermark-free, HD via TikWM API)
- ✅ Facebook
- ✅ Twitter/X
- ✅ Vimeo
- ✅ Reddit
- ✅ 1000+ more via yt-dlp

## 🛠️ Platform-Specific Features

### TikTok

- **TikWM API**: `hd=1` for HD no-watermark, falls back to `play` (SD)
- **Zero double-calls**: pre-resolved CDN URL embedded in the stream proxy URL
- **Mobile safe**: server-side proxy bypasses TikTok CDN CORS blocks on all clients
- **URL formats**: `tiktok.com`, `vm.tiktok.com`, `vt.tiktok.com`

### Instagram

- HD quality (720p+), supports Reels, Posts, IGTV
- CORS thumbnail proxy included
- Server-side merge for DASH streams

### YouTube

- Best video + audio quality merged (MP4)
- Cookie support for bot detection bypass

## 🔧 Configuration

### YouTube Cookie Setup (Optional)

1. Install [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Export cookies from YouTube.com
3. Save as `cookies.txt` in project root
4. Restart the server

See [YOUTUBE_COOKIES.md](YOUTUBE_COOKIES.md) for details.

## 🏗️ Project Structure

```
FastAPI/
├── main.py              # FastAPI app — all endpoints
├── downloader.py        # yt-dlp + TikWM download logic
├── requirements.txt
├── runtime.txt
├── Procfile
├── static/
│   ├── index.html       # Glassmorphism dark UI
│   ├── style.css
│   └── script.js        # XHR-based download with live progress
└── temp_downloads/      # Auto-cleaned temp files
```

## 🔒 Security

- CORS open for all origins (restrict in production as needed)
- `cookies.txt` gitignored
- Auto temp file cleanup (on startup + after serve)
- No video data stored beyond TTL

## 🐛 Troubleshooting

### TikTok returning 500

- Check server logs — likely a CDN token expiry (re-fetch URL)
- Ensure `httpx` is up to date: `pip install --upgrade httpx`

### YouTube Bot Detection

See [YOUTUBE_COOKIES.md](YOUTUBE_COOKIES.md).

### Progress Bar Stuck at 0%

TikTok CDN may not return `Content-Length` (chunked encoding). Progress shows received MB instead of percentage. This is normal.

### Video Has No Audio (Instagram)

Use `/api/server-stream` — it runs yt-dlp to merge DASH streams with audio.

## 📝 Changelog

### v2.2.0 (2026-04-06)

- ✅ **Fixed 500 error on `/api/stream`**: replaced invalid `await client.stream()` with correct `await client.send(request, stream=True)` (httpx API fix)
- ✅ **Eliminated double TikWM API call**: pre-resolved CDN URL embedded in stream URL via `direct_url` query param
- ✅ **Web frontend TikTok fix**: added `force_backend_stream` routing with XHR-based `downloadViaBackendStream()` and real progress bar
- ✅ **New `/api/tiktok/info` endpoint**: returns full TikWM data object (`hdplay`, `play`, `wmplay`, `cover`, `author`, `music_info`) for React Native apps
- ✅ **New `get_tiktok_info()` function** in `downloader.py`
- ✅ **No mobile app changes required** — backend changes are fully backward-compatible

### v2.1.0 (2026-04-01)

- ✅ TikWM API integration for HD no-watermark TikTok downloads
- ✅ Mobile stability fixes — resolved React Native video crashes
- ✅ `Content-Length` headers for native progress bars
- ✅ Zero-disk streaming for TikTok and Instagram
- ✅ `Content-Disposition: attachment` forced on all proxied streams

### v2.0.0 (2026-01-02)

- ✅ Real-time progress tracking with SSE
- ✅ Three-step download process
- ✅ YouTube cookie support
- ✅ Automatic file cleanup
- ✅ Modern lifespan event handlers

### v1.0.0 (2025-12-30)

- ✅ Initial release — multi-platform support, FastAPI backend, glassmorphism UI

## 🤝 Contributing

PRs welcome! Please open an issue first for major changes.

## 📄 License

MIT License — see [LICENSE](LICENSE).

## 👤 Author

**Fazi Gondal**

- GitHub: [@fazi-gondal](https://github.com/fazi-gondal)
- Email: nextinpk@gmail.com

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — The amazing video downloader
- [TikWM](https://www.tikwm.com) — TikTok no-watermark API
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [Expo](https://expo.dev/) — React Native development platform

---

### **Made with ❤️ by Fazi Gondal**
