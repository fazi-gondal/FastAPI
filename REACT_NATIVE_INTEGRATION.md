# React Native / Expo Integration Guide

Complete guide for integrating the Social Media Downloader API with your **React Native Expo** app.

> **Production API**: `https://fastapi-u8bm.onrender.com`

---

## 📱 How Downloads Work (Architecture)

The API uses a **server-side stream proxy** for all platforms. Your app calls two endpoints:

1. `POST /api/metadata` — get title, thumbnail, duration, uploader
2. `POST /api/get-direct-url` — get the download URL (always a `/api/stream` proxy URL)
3. `FileSystem.createDownloadResumable(direct_url, ...)` — download with native progress

### Why a Server Proxy?

TikTok, Instagram, and most CDNs **block direct mobile requests** with:
- Strict `Referer` / `Origin` header checks
- Token-based auth that blocks non-browser clients
- CORS policies that reject React Native `fetch`

The backend server acts as a transparent byte-proxy, forwarding CDN bytes to your device **without saving them to disk**. This gives you:

| Benefit | Detail |
|---|---|
| ✅ No CDN blocks | Server adds required headers |
| ✅ Content-Length forwarded | Native progress bar works |
| ✅ Forced filename | `Content-Disposition: attachment` |
| ✅ Single API call overhead | CDN URL pre-embedded in stream URL |

---

## 📦 Installation

```bash
npx expo install expo-file-system expo-media-library axios
```

---

## 🔧 API Endpoints Reference

### `POST /api/metadata`

Returns video info for display in your UI.

**Request:**
```json
{ "url": "https://www.tiktok.com/@user/video/123456" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Video title",
    "thumbnail": "https://cdn.tiktok.com/cover.jpg",
    "duration": 30,
    "uploader": "username",
    "platform": "tiktok",
    "url": "https://www.tiktok.com/..."
  }
}
```

---

### `POST /api/get-direct-url`

Returns the download URL — always points to our `/api/stream` proxy for mobile-safe download.

**Request:**
```json
{ "url": "https://www.tiktok.com/@user/video/123456" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "direct_url": "https://fastapi-u8bm.onrender.com/api/stream?url=...&direct_url=<cdn_url>",
    "filename": "video_title.mp4",
    "filesize": 5200000,
    "force_backend_stream": true,
    "needs_proxy": false,
    "use_server_download": false,
    "expires_in": 21600
  }
}
```

> **Note for mobile apps**: Always pass `direct_url` directly to `FileSystem.createDownloadResumable`. The backend has already routed TikTok/Instagram/YouTube through the correct proxy — no client-side switching needed.

---

### `GET /api/stream?url={tiktok_url}&direct_url={cdn_url}`

Server-side stream proxy. Called automatically by `FileSystem.createDownloadResumable` when you pass the `direct_url` from `/api/get-direct-url`.

- Forwards CDN bytes chunk-by-chunk (64KB chunks)
- Sets `Content-Disposition: attachment` (forces save)
- Forwards `Content-Length` from CDN when available
- No disk writes on server

---

### `GET /api/tiktok/info?url={tiktok_url}`

Returns the **full raw TikWM data** object. Use this when your app needs extra TikTok-specific data like watermarked version, music info, or stats.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "7123456789",
    "title": "Video caption text",
    "cover": "https://cdn.tiktok.com/cover.jpg",
    "play": "https://cdn.tikwm.com/video.mp4",
    "wmplay": "https://cdn.tikwm.com/wm_video.mp4",
    "hdplay": "https://cdn.tikwm.com/hd_video.mp4",
    "music": "https://cdn.tikwm.com/audio.mp3",
    "music_info": {
      "id": "...",
      "title": "Song Name",
      "author": "Artist",
      "duration": 60
    },
    "author": {
      "id": "...",
      "unique_id": "username",
      "nickname": "Display Name",
      "avatar": "https://..."
    },
    "duration": 30,
    "size": 5200000,
    "hd_size": 3800000,
    "digg_count": 10000,
    "comment_count": 500,
    "share_count": 2000,
    "create_time": 1712345678
  }
}
```

---

### `GET /api/thumbnail?url={image_url}`

CORS proxy for thumbnail images. Use this in `<Image>` components to avoid CDN CORS/403 errors.

```typescript
const thumbnailUri = `${API_URL}/api/thumbnail?url=${encodeURIComponent(metadata.thumbnail)}`;
```

---

## 💻 TypeScript Service (`services/videoDownloader.ts`)

This is the **actual service** used in the app. No changes needed — the backend is fully compatible.

```typescript
import axios from 'axios';
import * as FileSystem from 'expo-file-system/legacy';

const API_URL = 'https://fastapi-u8bm.onrender.com';

/**
 * Sanitize filename for safe filesystem storage
 */
const sanitizeFilename = (filename: string): string => {
  try { filename = decodeURIComponent(filename); } catch (e) {}
  return filename
    .replace(/[\r\n]+/g, ' ')
    .replace(/[^\w\-. ]/g, '')
    .replace(/\s+/g, '_')
    .replace(/_{2,}/g, '_')
    .replace(/^_+|_+$/g, '')
    .substring(0, 100)
    || `video_${Date.now()}.mp4`;
};

/**
 * Step 1: Fetch video metadata for UI display
 */
export const fetchVideoMetadata = async (url: string) => {
  const response = await axios.post(`${API_URL}/api/metadata`, { url });
  if (!response.data.success) throw new Error('Failed to fetch metadata');
  return response.data.data;
};

/**
 * Step 2 + 3: Get download URL and download to device
 * The backend returns an /api/stream proxy URL for all platforms —
 * no client-side platform switching needed.
 */
export const downloadVideo = async (
  videoUrl: string,
  metadata: any,
  onProgress?: (progress: { totalBytes: number; downloadedBytes: number; percentage: number }) => void
): Promise<string> => {
  // Get the proxied stream URL from backend
  const response = await axios.post(`${API_URL}/api/get-direct-url`, { url: videoUrl });
  if (!response.data.success) throw new Error('Failed to get download URL');

  const { direct_url, filename } = response.data.data;
  const sanitizedFilename = sanitizeFilename(filename || `${Date.now()}_video.mp4`);
  const fileUri = `${FileSystem.documentDirectory}${sanitizedFilename}`;

  // Clean up any partial file from a previous failed attempt
  await FileSystem.deleteAsync(fileUri, { idempotent: true }).catch(() => {});

  // Download using Expo FileSystem — Content-Length forwarded for real progress
  const downloadResumable = FileSystem.createDownloadResumable(
    direct_url,
    fileUri,
    {},
    (downloadProgress) => {
      onProgress?.({
        totalBytes: downloadProgress.totalBytesExpectedToWrite,
        downloadedBytes: downloadProgress.totalBytesWritten,
        percentage: downloadProgress.totalBytesExpectedToWrite > 0
          ? (downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite) * 100
          : 0,
      });
    }
  );

  const result = await downloadResumable.downloadAsync();
  if (!result) throw new Error('Download failed');
  return result.uri;
};

/**
 * Proxy thumbnail URL through backend to bypass CDN CORS
 */
export const getThumbnailUrl = (thumbnailUrl: string): string =>
  `${API_URL}/api/thumbnail?url=${encodeURIComponent(thumbnailUrl)}`;
```

---

## 📱 Full TikTok Info (Optional)

For apps that need detailed TikTok metadata (e.g. show watermarked vs HD option, display music):

```typescript
export const fetchTikTokInfo = async (url: string) => {
  const response = await axios.get(`${API_URL}/api/tiktok/info`, {
    params: { url }
  });
  if (!response.data.success) throw new Error('Failed to fetch TikTok info');
  return response.data.data;
  // Returns: { hdplay, play, wmplay, cover, author, music_info, duration, ... }
};
```

---

## 🔄 Download Flow in Your React Native App

```
User pastes TikTok URL
        │
        ▼
POST /api/metadata          ← displays thumbnail, title, uploader
        │
        ▼
handleDownload() called
        │
        ▼
POST /api/get-direct-url    ← backend calls TikWM API (single call)
        │ returns: direct_url = "/api/stream?url=...&direct_url=<cdn>"
        ▼
FileSystem.createDownloadResumable(direct_url, fileUri, {}, onProgress)
        │
        ▼
GET /api/stream             ← server proxies CDN bytes, forwards Content-Length
        │
        ▼
result.uri (local file)     ← MediaLibrary.createAssetAsync() → saved to gallery
```

---

## 🧩 Home Screen Integration Example

```typescript
import { downloadVideo, fetchVideoMetadata, getThumbnailUrl } from '../services/videoDownloader';
import * as MediaLibrary from 'expo-media-library';

const handleDownload = async () => {
  setStatus('downloading');
  setProgress(0);

  try {
    const localUri = await downloadVideo(videoUrl, metadata, (p) => {
      setProgress(p.percentage);
    });

    // Save to device gallery
    const { status } = await MediaLibrary.getPermissionsAsync();
    if (status === 'granted') {
      await MediaLibrary.createAssetAsync(localUri);
    }

    setStatus('completed');
  } catch (error) {
    setStatus('error');
    setErrorMessage(error.message);
  }
};
```

---

## 🐛 Troubleshooting

### Progress stuck at 0% (TikTok)

TikTok CDN sometimes uses chunked encoding (no `Content-Length`). In this case:
- `totalBytesExpectedToWrite` will be `-1`
- `percentage` calculation returns `0`
- Show a spinner or received-MB label instead

```typescript
const pct = progress.totalBytes > 0 ? progress.percentage : null;
// If null, show: `${(progress.downloadedBytes / 1024 / 1024).toFixed(1)} MB downloaded`
```

### Download fails with network error

- CDN token expired (TikTok URLs expire in ~6 hrs) — re-call `/api/get-direct-url`
- Server cold start on Render free tier — wait ~30s then retry
- Check `console.error` for Axios error response detail

### Video saved but no audio

This means yt-dlp returned a DASH video-only stream. This is rare — if it happens, use `/api/server-stream` instead (merges audio+video on server).

### Permission denied (Android)

```typescript
const { status } = await MediaLibrary.requestPermissionsAsync();
if (status !== 'granted') {
  Alert.alert('Permission needed', 'Please grant gallery access in Settings.');
}
```

---

## 📊 Bandwidth Usage

| Scenario | Per Download |
|---|---|
| API metadata call | ~1 KB |
| API get-direct-url call | ~1 KB |
| Video stream (via proxy) | = video file size (e.g. 5–30 MB) |

> TikTok and Instagram go through our proxy server — this uses Render bandwidth. YouTube/Twitter with `force_backend_stream=false` stream directly from CDN (zero Render bandwidth).

---

## ✅ Tested On

- ✅ Android (Expo Go + bare workflow)
- ✅ iOS (Expo Go + bare workflow)
- ✅ TikTok (`tiktok.com`, `vm.tiktok.com`, `vt.tiktok.com`)
- ✅ Instagram (Reels, Posts)
- ✅ YouTube
- ✅ Twitter/X

---

**Status**: Production ready ✅  
**API**: `https://fastapi-u8bm.onrender.com`  
**Mobile Progress**: Real-time via `Content-Length` headers  
**TikTok**: No watermark, HD quality via TikWM  
**Zero mobile app changes needed** — backend handles all routing
