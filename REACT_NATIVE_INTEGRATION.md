# React Native Mobile Integration Guide

Complete guide for integrating the video downloader API with your React Native Expo app with **real-time progress tracking**.

## 📱 Installation

```bash
npx expo install expo-file-system expo-media-library axios
```

## 🔧 Setup

### 1. Configure app.json

Add media library permissions:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-media-library",
        {
          "photosPermission": "Allow $(PRODUCT_NAME) to save videos to your gallery.",
          "savePhotosPermission": "Allow $(PRODUCT_NAME) to save videos to your gallery."
        }
      ]
    ],
    "android": {
      "permissions": [
        "WRITE_EXTERNAL_STORAGE",
        "READ_EXTERNAL_STORAGE"
      ]
    }
  }
}
```

### 2. Create API Service

Create `services/videoDownloader.js`:

```javascript
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';

const API_URL = 'https://your-app.onrender.com'; // Replace with your deployment URL

export const VideoDownloaderService = {
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
      throw new Error(error.response?.data?.detail || 'Failed to fetch metadata');
    }
  },

  /**
   * Download video with real-time progress to device storage
   */
  async downloadToDevice(videoUrl, onProgress = () => {}) {
    try {
      // Step 1: Start download on server
      onProgress(0, 'Starting download...');
      const startResponse = await axios.post(`${API_URL}/api/download/start`, {
        url: videoUrl
      });
      
      const { download_id } = startResponse.data;
      
      // Step 2: Track server-side download progress
      onProgress(0, 'Processing video...');
      await this.trackServerProgress(download_id, (percent) => {
        onProgress(percent * 0.5, 'Processing video...'); // Server download is 0-50%
      });
      
      // Step 3: Download file to device
      onProgress(50, 'Downloading to device...');
      const downloadUrl = `${API_URL}/api/download/file/${download_id}`;
      const filename = `video_${Date.now()}.mp4`;
      const downloadPath = `${FileSystem.documentDirectory}${filename}`;
      
      const downloadResumable = FileSystem.createDownloadResumable(
        downloadUrl,
        downloadPath,
        {},
        (downloadProgress) => {
          const progress = downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite;
          onProgress(50 + (progress * 40), 'Downloading to device...'); // Device download is 50-90%
        }
      );
      
      const result = await downloadResumable.downloadAsync();
      
      if (!result || !result.uri) {
        throw new Error('Download failed');
      }
      
      // Step 4: Save to gallery
      onProgress(90, 'Saving to gallery...');
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Media library permission denied');
      }
      
      const asset = await MediaLibrary.createAssetAsync(result.uri);
      
      try {
        await MediaLibrary.createAlbumAsync('Downloads', asset, false);
      } catch (e) {
        // Album might already exist
      }
      
      onProgress(100, 'Complete!');
      
      return {
        success: true,
        localUri: result.uri,
        asset: asset,
        filename: filename
      };
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  /**
   * Track server-side download progress with SSE
   */
  async trackServerProgress(downloadId, onProgress) {
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
          reject(new Error(data.error || 'Download failed'));
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        reject(new Error('Connection to server lost'));
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

### 3. Create Download Component

Create `components/VideoDownloader.js`:

```javascript
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { VideoDownloaderService } from '../services/videoDownloader';

export default function VideoDownloader() {
  const [url, setUrl] = useState('');
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');

  const handleFetchMetadata = async () => {
    if (!url.trim()) {
      Alert.alert('Error', 'Please enter a video URL');
      return;
    }

    setLoading(true);
    try {
      const data = await VideoDownloaderService.getMetadata(url);
      setMetadata(data);
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setProgress(0);

    try {
      const result = await VideoDownloaderService.downloadToDevice(
        url,
        (percent, status) => {
          setProgress(Math.round(percent));
          setStatusText(status);
        }
      );

      Alert.alert(
        'Success!',
        'Video downloaded and saved to your gallery!',
        [{ text: 'OK' }]
      );

      setStatusText('');
    } catch (error) {
      Alert.alert('Download Failed', error.message);
      setStatusText('');
    } finally {
      setDownloading(false);
      setProgress(0);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Social Media Downloader</Text>
      <Text style={styles.subtitle}>Download videos from Instagram, TikTok, YouTube & more</Text>

      <TextInput
        style={styles.input}
        placeholder="Paste video URL here..."
        value={url}
        onChangeText={setUrl}
        multiline
        autoCapitalize="none"
        autoCorrect={false}
      />

      <TouchableOpacity
        style={styles.button}
        onPress={handleFetchMetadata}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Get Video Info</Text>
        )}
      </TouchableOpacity>

      {metadata && (
        <View style={styles.videoCard}>
          <Image
            source={{ uri: VideoDownloaderService.getThumbnailUrl(metadata.thumbnail) }}
            style={styles.thumbnail}
            resizeMode="cover"
          />
          
          <Text style={styles.videoTitle}>{metadata.title}</Text>
          
          <View style={styles.metaRow}>
            <Text style={styles.metaText}>👤 {metadata.uploader}</Text>
            <Text style={styles.metaText}>📱 {metadata.platform}</Text>
          </View>

          {metadata.duration > 0 && (
            <Text style={styles.duration}>
              ⏱️ {Math.floor(metadata.duration / 60)}:{(metadata.duration % 60).toString().padStart(2, '0')}
            </Text>
          )}

          <TouchableOpacity
            style={[styles.downloadButton, downloading && styles.downloadButtonDisabled]}
            onPress={handleDownload}
            disabled={downloading}
          >
            {downloading ? (
              <View style={styles.downloadingContainer}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.buttonText}>{progress}%</Text>
              </View>
            ) : (
              <Text style={styles.buttonText}>📥 Download to Device</Text>
            )}
          </TouchableOpacity>

          {downloading && (
            <View style={styles.progressContainer}>
              <View style={styles.progressBarContainer}>
                <View style={[styles.progressBar, { width: `${progress}%` }]} />
              </View>
              <Text style={styles.statusText}>{statusText}</Text>
            </View>
          )}
        </View>
      )}

      <View style={styles.features}>
        <Text style={styles.featuresTitle}>✨ Features:</Text>
        <Text style={styles.featureItem}>• TikTok videos without watermark</Text>
        <Text style={styles.featureItem}>• Instagram videos in HD quality</Text>
        <Text style={styles.featureItem}>• Real-time download progress</Text>
        <Text style={styles.featureItem}>• Saves directly to your gallery</Text>
        <Text style={styles.featureItem}>• Supports 1000+ platforms</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 15,
    fontSize: 14,
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: 15,
  },
  button: {
    backgroundColor: '#6366f1',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  videoCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  thumbnail: {
    width: '100%',
    height: 200,
    borderRadius: 10,
    marginBottom: 15,
    backgroundColor: '#e0e0e0',
  },
  videoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  metaText: {
    fontSize: 14,
    color: '#666',
  },
  duration: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  downloadButton: {
    backgroundColor: '#10b981',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  downloadButtonDisabled: {
    backgroundColor: '#93c5fd',
  },
  downloadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  progressContainer: {
    marginTop: 15,
  },
  progressBarContainer: {
    height: 6,
    backgroundColor: '#e0e0e0',
    borderRadius: 3,
    marginBottom: 8,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#10b981',
    borderRadius: 3,
  },
  statusText: {
    textAlign: 'center',
    color: '#666',
    fontSize: 12,
  },
  features: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
  },
  featuresTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  featureItem: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
});
```

## 🚀 Usage in Your App

```javascript
import VideoDownloader from './components/VideoDownloader';

export default function App() {
  return <VideoDownloader />;
}
```

## ✅ Testing

1. **Install dependencies**:
   ```bash
   npx expo install expo-file-system expo-media-library axios
   ```

2. **Update API URL** in `videoDownloader.js`

3. **Run the app**:
   ```bash
   npx expo start
   ```

4. **Test download**:
   * Paste Instagram/TikTok URL
   * Click "Get Video Info"
   * Click "Download to Device"
   * **Watch real-time progress!** (0% → 100%)
   * Check your gallery

## 📝 Key Features

* ✅ **Real-time progress** - Shows 0%, 5%, 10%... 100%
* ✅ **Three-phase tracking**:
  * Server processing (0-50%)
  * Device download (50-90%)
  * Gallery save (90-100%)
* ✅ **Status messages** - "Processing...", "Downloading...", "Saving..."
* ✅ **Auto permissions** - Requests gallery access automatically
* ✅ **Error handling** - Clear error messages

## 🐛 Troubleshooting

**Progress stuck at 0%?**

* Check server is running
* Verify API\_URL is correct
* Check network connection

**"Permission denied" error?**

* Grant media library permissions
* Go to Settings → Your App → Permissions

**Video not in gallery?**

* Check "Downloads" album
* Restart gallery app
* Check storage space

***

**Status**: Ready for production! 📱✅\
**Progress**: Real-time tracking enabled\
**Platforms**: Instagram (HD), TikTok (no watermark), YouTube, and 1000+
