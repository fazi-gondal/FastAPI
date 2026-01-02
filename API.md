# Social Media Downloader API Documentation

Complete API documentation for integrating with React Native Expo apps using **axios**.

## 📦 Installation

First, install axios in your React Native/Expo project:

```bash
npm install axios
# or
yarn add axios
```

## 🌐 Base URL

**Local Development**: `http://localhost:8000`\
**Production (Render/Koyeb)**: `https://your-app-name.onrender.com`

Replace with your actual deployment URL.

***

## 📋 API Endpoints

### 1. Fetch Video Metadata

Get video information without downloading.

**Endpoint**: `POST /api/metadata`

**Request Body**:

```json
{
  "url": "https://www.instagram.com/reel/xxxxx/"
}
```

**Response** (Success - 200):

```json
{
  "success": true,
  "data": {
    "title": "Video Title",
    "thumbnail": "https://thumbnail-url.jpg",
    "duration": 45,
    "uploader": "Channel Name",
    "url": "https://www.instagram.com/reel/xxxxx/",
    "platform": "instagram"
  }
}
```

**React Native Example (using axios)**:

```javascript
import axios from 'axios';

const fetchMetadata = async (videoUrl) => {
  try {
    const response = await axios.post('https://your-app.onrender.com/api/metadata', {
      url: videoUrl
    });
    
    return response.data.data;
  } catch (error) {
    console.error('Error:', error.response?.data?.detail || error.message);
    throw error;
  }
};
```

***

### 2. Download Video with Real-Time Progress (NEW!)

Three-step process for downloading with live progress updates.

#### Step 2A: Start Download

**Endpoint**: `POST /api/download/start`

**Request Body**:

```json
{
  "url": "https://www.tiktok.com/@user/video/xxxxx"
}
```

**Response**:

```json
{
  "download_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Step 2B: Track Progress (Real-Time)

**Endpoint**: `GET /api/download/progress/{download_id}`

**Response**: Server-Sent Events (SSE) stream

**Event Stream Examples**:

```
data: {"status": "starting", "progress": 0, "filename": null, "filepath": null}

data: {"status": "downloading", "progress": 15.5, "filename": null, "filepath": null}

data: {"status": "downloading", "progress": 47.2, "filename": null, "filepath": null}

data: {"status": "downloading", "progress": 89.1, "filename": null, "filepath": null}

data: {"status": "completed", "progress": 100, "filename": "Amazing_Video.mp4", "filepath": "/path/to/file"}
```

**Error Event**:

```
data: {"status": "error", "error": "Failed to download video"}
```

#### Step 2C: Download File

**Endpoint**: `GET /api/download/file/{download_id}`

**Response**: Video file (binary)

**Headers**:

* `Content-Type`: `video/mp4`
* `Content-Disposition`: `attachment; filename="Video_Title.mp4"`

***

### 3. Complete React Native Download Example

```javascript
import axios from 'axios';

const API_URL = 'https://your-app.onrender.com';

export const VideoDownloaderAPI = {
  /**
   * Fetch video metadata
   */
  async getMetadata(videoUrl) {
    try {
      const response = await axios.post(`${API_URL}/api/metadata`, {
        url: videoUrl
      });
      return response.data.data;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch metadata';
      throw new Error(errorMsg);
    }
  },

  /**
   * Download video with real-time progress tracking
   */
  async downloadVideoWithProgress(videoUrl, onProgress = () => {}) {
    try {
      // Step 1: Start download
      const startResponse = await axios.post(`${API_URL}/api/download/start`, {
        url: videoUrl
      });
      
      const { download_id } = startResponse.data;
      
      // Step 2: Track progress using fetch (EventSource doesn't work well with axios)
      await this.trackProgress(download_id, onProgress);
      
      // Step 3: Return download URL
      return {
        success: true,
        downloadUrl: `${API_URL}/api/download/file/${download_id}`,
        downloadId: download_id
      };
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  /**
   * Track download progress with SSE
   */
  async trackProgress(downloadId, onProgress) {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`${API_URL}/api/download/progress/${downloadId}`);
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.status === 'downloading' || data.status === 'starting') {
          onProgress(data.progress || 0);
        } else if (data.status === 'completed') {
          onProgress(100);
          eventSource.close();
          resolve(data);
        } else if (data.status === 'error') {
          eventSource.close();
          reject(new Error(data.error));
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        reject(new Error('Connection lost'));
      };
    });
  },

  /**
   * Get thumbnail URL (with CORS proxy)
   */
  getThumbnailUrl(thumbnailUrl) {
    return `${API_URL}/api/thumbnail?url=${encodeURIComponent(thumbnailUrl)}`;
  }
};
```

***

### 4. Download to Mobile Device Storage

For React Native mobile apps, use expo-file-system:

```javascript
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';

async downloadToDevice(videoUrl, onProgress = () => {}) {
  try {
    // Get download URL with progress
    const { downloadUrl } = await VideoDownloaderAPI.downloadVideoWithProgress(
      videoUrl,
      onProgress
    );
    
    // Download to device
    const filename = `video_${Date.now()}.mp4`;
    const downloadPath = `${FileSystem.documentDirectory}${filename}`;
    
    const downloadResumable = FileSystem.createDownloadResumable(
      downloadUrl,
      downloadPath
    );
    
    const result = await downloadResumable.downloadAsync();
    
    // Request permissions
    const { status } = await MediaLibrary.requestPermissionsAsync();
    if (status !== 'granted') {
      throw new Error('Permission denied');
    }
    
    // Save to gallery
    const asset = await MediaLibrary.createAssetAsync(result.uri);
    await MediaLibrary.createAlbumAsync('Downloads', asset, false);
    
    return { success: true, asset };
  } catch (error) {
    throw error;
  }
}
```

**Installation**:

```bash
npx expo install expo-file-system expo-media-library
```

***

### 5. Get Thumbnail (Proxy)

**Endpoint**: `GET /api/thumbnail`

**Query Parameters**:

* `url` (required): The thumbnail URL to proxy

**Example**:

```
GET /api/thumbnail?url=https%3A%2F%2Finstagram.com%2Fthumbnail.jpg
```

**React Native Example**:

```javascript
<Image 
  source={{ uri: VideoDownloaderAPI.getThumbnailUrl(metadata.thumbnail) }}
  style={{ width: 200, height: 150 }}
/>
```

***

## 🎯 Platform-Specific Features

### TikTok

* ✅ Downloads **without watermark**
* ✅ Best available quality
* Platform identifier: `"tiktok"`

### Instagram

* ✅ Downloads in **HD quality** (720p+)
* ✅ Supports: Posts, Reels, IGTV
* Platform identifier: `"instagram"`

### YouTube

* ✅ Best video + audio quality
* ✅ Merged to MP4 format
* Platform identifier: `"youtube"`

### Supported Platforms

* YouTube, Instagram, TikTok, Facebook, Twitter/X, Vimeo
* 1000+ more via yt-dlp

***

## 🛠️ Error Handling

```javascript
import axios from 'axios';

try {
  const metadata = await VideoDownloaderAPI.getMetadata(url);
} catch (error) {
  if (axios.isAxiosError(error)) {
    const errorDetail = error.response?.data?.detail || error.message;
    
    if (errorDetail.includes('Invalid URL')) {
      alert('Please enter a valid video URL');
    } else if (errorDetail.includes('Failed to fetch metadata')) {
      alert('This platform is not supported');
    } else if (error.code === 'ERR_NETWORK') {
      alert('Network error. Please check your connection.');
    } else {
      alert(`Error: ${errorDetail}`);
    }
  } else {
    alert('An unexpected error occurred');
  }
}
```

***

## 📦 Response Time Expectations

| Operation | Expected Time |
|-----------|---------------|
| Metadata fetch | 2-5 seconds |
| Video download (short) | 5-15 seconds |
| Video download (long) | 30-60 seconds |
| Progress updates | Real-time (500ms intervals) |

***

## 🔒 CORS Configuration

API has CORS enabled for all origins - works with React Native and web apps.

***

## 🚀 Best Practices

1. **Show Loading States** during API calls
2. **Real-Time Progress** - Use SSE for smooth updates
3. **Error Handling** - Wrap in try-catch
4. **Validate URLs** before sending
5. **Timeout Handling** - Set reasonable timeouts
6. **Offline Detection** - Check network before download

***

**API Version**: 2.0 (with real-time progress)\
**Last Updated**: 2026-01-02\
**yt-dlp Version**: 2025.12.8
