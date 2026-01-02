# YouTube Cookies Setup Guide

## 🍪 Why Cookies Are Needed

YouTube sometimes requires authentication to verify you're not a bot. By exporting your browser cookies, you can bypass this.

## 📋 Quick Setup

### Option 1: Using Browser Extension (Easiest)

1. **Install Extension**:
   * Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   * Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export Cookies**:
   * Go to [YouTube.com](https://youtube.com)
   * **Sign in** to your YouTube account
   * Click the extension icon
   * Click "Export" or "Download"
   * Save as `cookies.txt`

3. **Add to Project**:
   * Copy `cookies.txt` to your project folder (same folder as `main.py`)
   * That's it! The app will auto-detect and use it

### Option 2: Using yt-dlp Command

```bash
# Extract cookies from your browser
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Replace `chrome` with: `firefox`, `edge`, `safari`, `brave`, etc.

## 📁 File Location

Place `cookies.txt` in the **same directory** as `main.py`:

```
FastAPI/
├── main.py
├── downloader.py
├── cookies.txt  ← Add here
├── requirements.txt
└── ...
```

## ✅ Verify It's Working

1. Add `cookies.txt` to project folder
2. Restart server
3. Try downloading YouTube video
4. You should see in terminal: `Using cookies from: /path/to/cookies.txt`

## 🔒 Security Notes

**IMPORTANT**:

* ✅ Add `cookies.txt` to `.gitignore` (already done!)
* ✅ Never commit cookies to git
* ✅ Cookies contain your session - keep them private
* ✅ Cookies expire after ~6 months (re-export if needed)

## 🐛 Troubleshooting

### "Still getting bot error"

1. **Re-export cookies** - they might be expired
2. **Make sure you're logged in** to YouTube when exporting
3. **Check file location** - must be in same folder as `main.py`
4. **Check file name** - must be exactly `cookies.txt`

### "Cookies not being detected"

1. Check terminal for: `Using cookies from: ...`
2. If not shown, verify file exists:
   ```bash
   ls cookies.txt
   # or on Windows
   dir cookies.txt
   ```

### "How to export cookies manually?"

Visit [yt-dlp FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)

## 📝 cookies.txt Format

The file should look like this:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+...
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	...
.youtube.com	TRUE	/	TRUE	1234567890	LOGIN_INFO	...
```

## 🚀 Other Platforms

**Good news**: Cookies work for **all platforms**!

* ✅ YouTube (fixes bot detection)
* ✅ Instagram (access private accounts you follow)
* ✅ TikTok (better reliability)
* ✅ Facebook (private videos)
* ✅ Twitter/X (access age-restricted content)

One `cookies.txt` file works for everything!

## 🔄 When to Re-export

Re-export cookies if you:

* Get "bot detection" errors again
* Changed your YouTube password
* Logged out of YouTube
* 6+ months have passed

## ⚙️ Alternative: Command Line

Export cookies using yt-dlp directly:

```bash
# Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://youtube.com

# Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt https://youtube.com

# Edge
yt-dlp --cookies-from-browser edge --cookies cookies.txt https://youtube.com

# Brave
yt-dlp --cookies-from-browser brave --cookies cookies.txt https://youtube.com

# Safari (Mac only)
yt-dlp --cookies-from-browser safari --cookies cookies.txt https://youtube.com
```

Then copy the generated `cookies.txt` to your project folder.

***

**Status**: ✅ Cookie support enabled\
**Auto-detection**: Yes\
**Platforms supported**: All (YouTube, Instagram, TikTok, etc.)\
**Privacy**: Cookies are gitignored and never uploaded
