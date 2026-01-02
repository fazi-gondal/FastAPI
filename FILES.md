# Project Files Overview

Complete list of all project files and their purposes.

## 📁 Core Application Files

### Backend

* **main.py** - FastAPI application with all API endpoints
* **downloader.py** - yt-dlp download logic with retry mechanism
* **requirements.txt** - Python dependencies
* **runtime.txt** - Python version for deployment (3.11)
* **Procfile** - Deployment configuration for Render/Koyeb

### Frontend

* **static/index.html** - Main web interface
* **static/style.css** - Glassmorphism UI styling
* **static/script.js** - Download functionality with real-time progress

### Configuration

* **.gitignore** - Git ignore patterns
* **.gitattributes** - GitHub language detection (ensures Python project)
* **cookies.txt** - (Optional) Browser cookies for YouTube
* **LICENSE** - MIT License

## 📚 Documentation Files

### User Guides

* **README.md** - Project overview and quick start
* **API.md** - Complete API documentation
* **REACT\_NATIVE\_INTEGRATION.md** - Mobile app integration guide
* **DEPLOYMENT.md** - Render/Koyeb deployment instructions
* **YOUTUBE\_COOKIES.md** - Cookie setup for YouTube bot detection

### Technical Documentation

* **IMPROVEMENTS.md** - Reliability improvements and changes
* **RENDER\_STORAGE.md** - Storage management on cloud platforms
* **FILES.md** - This file

## 🗂️ Generated Folders

### Runtime

* **temp\_downloads/** - Temporary video storage (auto-cleanup)
* ****pycache**/** - Python bytecode cache

## 🎯 File Purpose Summary

| File | Purpose | Required |
|------|---------|----------|
| main.py | API server | ✅ Yes |
| downloader.py | Download logic | ✅ Yes |
| requirements.txt | Dependencies | ✅ Yes |
| runtime.txt | Python version | ✅ Deployment only |
| Procfile | Deployment config | ✅ Deployment only |
| .gitattributes | Language detection | ✅ Yes |
| static/*.* | Web interface | ✅ For web UI |
| cookies.txt | YouTube auth | ⚠️ Optional |
| README.md | Documentation | ✅ Yes |
| LICENSE | Legal | ✅ Yes |

## 📝 Notes

### Essential Files for Deployment

1. main.py
2. downloader.py
3. requirements.txt
4. runtime.txt
5. Procfile
6. static/ folder (for web UI)

### Optional But Recommended

* cookies.txt (for YouTube)
* All documentation files
* LICENSE
* .gitattributes (for GitHub display)

### Auto-Generated (Don't Commit)

* temp\_downloads/
* **pycache**/
* \*.pyc files
* cookies.txt (if using)

## 🔄 File Flow

```
User Request
    ↓
main.py (API endpoints)
    ↓
downloader.py (yt-dlp integration)
    ↓
temp_downloads/ (temporary storage)
    ↓
User's Device (download complete)
    ↓
Auto cleanup (file deleted from server)
```

## 📊 File Sizes (Approximate)

* main.py: ~8KB
* downloader.py: ~6KB
* requirements.txt: <1KB
* static/: ~30KB total
* Documentation: ~100KB total

**Total Project Size**: ~150KB (excluding dependencies)

***

**Author**: Fazi Gondal\
**License**: MIT\
**Version**: 2.0.0
