# Social Media Downloader API

A powerful FastAPI-based video downloader supporting Instagram, TikTok, YouTube, and 1000+ platforms with real-time progress tracking.

## ✨ Features

* 🎥 **Multi-Platform Support**: Download from Instagram, TikTok, YouTube, Facebook, Twitter, and 1000+ sites
* 🚫 **TikTok Without Watermark**: Get clean TikTok videos
* 🎬 **Instagram HD Quality**: Download Instagram Reels/Posts in 720p+
* 📊 **Real-Time Progress**: Live download progress with Server-Sent Events
* 📱 **Mobile Ready**: Complete React Native/Expo integration
* 🌐 **CORS Enabled**: Works with web and mobile apps
* 🍪 **Cookie Support**: Bypass YouTube bot detection
* 🗑️ **Auto Cleanup**: Automatic file cleanup after download
* 🎨 **Modern UI**: Beautiful glassmorphism design

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/fazi-gondal/FastAPI.git
cd FastAPI

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Server will start at `http://localhost:8000`

### Requirements

* Python 3.11+
* FastAPI
* yt-dlp (2025.12.8)
* uvicorn
* httpx
* aiofiles

## 📋 Usage

### Web Interface

1. Open `http://localhost:8000` in your browser
2. Paste a video URL (Instagram, TikTok, YouTube, etc.)
3. Click "Get Video Info"
4. Click "Download Video"
5. Video downloads to your Downloads folder

### API Integration

See [API.md](API.md) for complete API documentation with examples.

**Quick Example**:

```javascript
// Fetch metadata
const response = await fetch('http://localhost:8000/api/metadata', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'https://www.instagram.com/reel/xxxxx/' })
});

const metadata = await response.json();
```

### React Native Integration

Complete mobile app integration guide: [REACT\_NATIVE\_INTEGRATION.md](REACT_NATIVE_INTEGRATION.md)

```bash
# Install dependencies
npx expo install expo-file-system expo-media-library axios
```

## 🌐 Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect to [Render](https://render.com)
3. Deploy with:
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### Deploy to Koyeb

See [DEPLOYMENT.md](DEPLOYMENT.md) for Koyeb deployment guide.

## 📚 Documentation

* [API.md](API.md) - Complete API documentation
* [REACT\_NATIVE\_INTEGRATION.md](REACT_NATIVE_INTEGRATION.md) - Mobile app integration
* [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guides (Render/Koyeb)
* [YOUTUBE\_COOKIES.md](YOUTUBE_COOKIES.md) - Fix YouTube bot detection
* [IMPROVEMENTS.md](IMPROVEMENTS.md) - Reliability improvements
* [RENDER\_STORAGE.md](RENDER_STORAGE.md) - Storage management on Render

## 🎯 Supported Platforms

* ✅ YouTube (with cookie support)
* ✅ Instagram (Posts, Reels, IGTV in HD)
* ✅ TikTok (watermark-free)
* ✅ Facebook
* ✅ Twitter/X
* ✅ Vimeo
* ✅ Reddit
* ✅ And 1000+ more via yt-dlp

## 🛠️ Platform-Specific Features

### TikTok

* Downloads without watermark
* Best available quality
* Multiple URL format support

### Instagram

* HD quality (720p+)
* Supports Reels, Posts, IGTV
* Thumbnail CORS proxy included

### YouTube

* Best video + audio quality merged
* Cookie support for bot detection
* MP4 output format

## 🔧 Configuration

### YouTube Cookie Setup (Optional)

For YouTube downloads, you may need to add cookies:

1. Install browser extension: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Export cookies from YouTube.com
3. Save as `cookies.txt` in project folder
4. Restart server

See [YOUTUBE\_COOKIES.md](YOUTUBE_COOKIES.md) for detailed instructions.

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metadata` | POST | Get video metadata |
| `/api/download/start` | POST | Start download (returns ID) |
| `/api/download/progress/{id}` | GET | Track progress (SSE) |
| `/api/download/file/{id}` | GET | Download completed file |
| `/api/thumbnail` | GET | Proxy thumbnail (CORS bypass) |

## 🏗️ Project Structure

```
FastAPI/
├── main.py                 # FastAPI application
├── downloader.py          # yt-dlp download logic
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version
├── Procfile              # Deployment config
├── static/               # Frontend files
│   ├── index.html
│   ├── style.css
│   └── script.js
├── temp_downloads/       # Temporary download storage
└── docs/                 # Documentation
    ├── API.md
    ├── DEPLOYMENT.md
    └── ...
```

## 🔒 Security

* ✅ CORS enabled for all origins (customize in production)
* ✅ Cookie files gitignored
* ✅ Automatic file cleanup
* ✅ No sensitive data stored
* ✅ Ephemeral storage on cloud platforms

## 🐛 Troubleshooting

### YouTube Bot Detection

See [YOUTUBE\_COOKIES.md](YOUTUBE_COOKIES.md) for cookie setup.

### Instagram Thumbnails Not Loading

App includes automatic CORS proxy for Instagram thumbnails.

### Videos Not Downloading

* Check internet connection
* Verify URL is public and accessible
* Check yt-dlp is latest version: `pip install --upgrade yt-dlp`

### Progress Bar Not Moving

Restart server to enable new progress tracking system.

## 📝 Changelog

### v2.0.0 (2026-01-02)

* ✅ Real-time progress tracking with SSE
* ✅ Three-step download process
* ✅ YouTube cookie support
* ✅ Automatic file cleanup
* ✅ Modern lifespan event handlers
* ✅ Improved error handling

### v1.0.0 (2025-12-30)

* ✅ Initial release
* ✅ Multi-platform support
* ✅ FastAPI backend
* ✅ Modern glassmorphism UI
* ✅ React Native integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Fazi Gondal**

* GitHub: [@fazi-gondal](https://github.com/fazi-gondal)
* Email: nextinpk@gmail.com

## 🙏 Acknowledgments

* [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The amazing video downloader
* [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
* [Expo](https://expo.dev/) - React Native development platform

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

***

### **Made with ❤️ by Fazi Gondal**

***
