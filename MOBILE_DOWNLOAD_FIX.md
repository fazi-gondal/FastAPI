# Mobile Video Download Fix

## Problem
Videos download on the server but don't appear on mobile devices.

## Solution: Download to Mobile Device

### 1. Install Required Libraries

```bash
npx expo install expo-file-system expo-media-library
```

### 2. Update API Integration

Create or update `api/downloader.js`:

```javascript
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';

const API_BASE_URL = 'https://your-app.onrender.com'; // Your Render URL

export const VideoDownloaderAPI = {
  /**
   * Fetch video metadata
   */
  async getMetadata(videoUrl) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/metadata`, {
        url: videoUrl
      });
      return response.data.data;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to fetch metadata';
      throw new Error(errorMsg);
    }
  },

  /**
   * Download video to device with progress tracking
   */
  async downloadVideoToDevice(videoUrl, onProgress = () => {}) {
    try {
      // Step 1: Start server-side download
      const response = await fetch(`${API_BASE_URL}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: videoUrl }),
      });

      if (!response.ok) {
        throw new Error('Failed to initiate download');
      }

      // Step 2: Parse SSE stream for progress
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let serverFilename = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));

            if (data.status === 'downloading') {
              onProgress(data.progress * 0.5); // Server download is 50% of total
            } else if (data.status === 'completed') {
              serverFilename = data.filename;
            } else if (data.status === 'error') {
              throw new Error(data.message);
            }
          }
        }
      }

      if (!serverFilename) {
        throw new Error('Download completed but filename not received');
      }

      // Step 3: Download file from server to device
      onProgress(50); // Server download complete, starting device download

      const fileUri = `${API_BASE_URL}/downloads/${encodeURIComponent(serverFilename)}`;
      const downloadPath = `${FileSystem.documentDirectory}${serverFilename}`;

      const downloadResumable = FileSystem.createDownloadResumable(
        fileUri,
        downloadPath,
        {},
        (downloadProgress) => {
          const progress = downloadProgress.totalBytesWritten / downloadProgress.totalBytesExpectedToWrite;
          onProgress(50 + (progress * 40)); // 50-90% for device download
        }
      );

      const result = await downloadResumable.downloadAsync();

      if (!result || !result.uri) {
        throw new Error('Failed to download to device');
      }

      onProgress(90); // Download complete, saving to media library

      // Step 4: Request media library permissions
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        throw new Error('Media library permission denied');
      }

      // Step 5: Save to device media library
      const asset = await MediaLibrary.createAssetAsync(result.uri);
      await MediaLibrary.createAlbumAsync('Downloads', asset, false);

      onProgress(100);

      return {
        success: true,
        filename: serverFilename,
        localUri: result.uri,
        asset: asset,
      };
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  /**
   * Get proxied thumbnail URL
   */
  getThumbnailUrl(originalUrl) {
    return `${API_BASE_URL}/api/thumbnail?url=${encodeURIComponent(originalUrl)}`;
  },
};
```

### 3. Update Your React Native Component

```javascript
import React, { useState } from 'react';
import { View, TextInput, Button, Image, Text, Alert, StyleSheet } from 'react-native';
import { VideoDownloaderAPI } from './api/downloader';

export default function VideoDownloader() {
  const [url, setUrl] = useState('');
  const [metadata, setMetadata] = useState(null);
  const [progress, setProgress] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [statusText, setStatusText] = useState('');

  const handleFetchMetadata = async () => {
    try {
      setStatusText('Fetching metadata...');
      const data = await VideoDownloaderAPI.getMetadata(url);
      setMetadata(data);
      setStatusText('');
    } catch (error) {
      Alert.alert('Error', error.message);
      setStatusText('');
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setProgress(0);

    try {
      const result = await VideoDownloaderAPI.downloadVideoToDevice(
        url,
        (percent) => {
          setProgress(Math.round(percent));
          
          if (percent < 50) {
            setStatusText('Processing video...');
          } else if (percent < 90) {
            setStatusText('Downloading to device...');
          } else {
            setStatusText('Saving to gallery...');
          }
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
    <View style={styles.container}>
      <TextInput
        placeholder="Paste video URL (Instagram, TikTok, etc.)"
        value={url}
        onChangeText={setUrl}
        style={styles.input}
        multiline
      />
      
      <Button title="Fetch Video Info" onPress={handleFetchMetadata} />

      {metadata && (
        <View style={styles.videoCard}>
          <Image
            source={{ uri: VideoDownloaderAPI.getThumbnailUrl(metadata.thumbnail) }}
            style={styles.thumbnail}
          />
          <Text style={styles.title}>{metadata.title}</Text>
          <Text style={styles.meta}>
            {metadata.uploader} • {metadata.platform}
          </Text>
          
          <Button
            title={downloading ? `Downloading... ${progress}%` : 'Download to Device'}
            onPress={handleDownload}
            disabled={downloading}
          />

          {downloading && (
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, { width: `${progress}%` }]} />
              </View>
              <Text style={styles.statusText}>{statusText}</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    flex: 1,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    marginBottom: 10,
    borderRadius: 5,
    minHeight: 60,
  },
  videoCard: {
    marginTop: 20,
  },
  thumbnail: {
    width: '100%',
    height: 200,
    borderRadius: 10,
    marginBottom: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  meta: {
    color: '#666',
    marginBottom: 15,
  },
  progressContainer: {
    marginTop: 15,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 5,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
  },
  statusText: {
    textAlign: 'center',
    color: '#666',
    fontSize: 12,
  },
});
```

### 4. Add Permissions to app.json

```json
{
  "expo": {
    "plugins": [
      [
        "expo-media-library",
        {
          "photosPermission": "Allow $(PRODUCT_NAME) to save videos to your photo library.",
          "savePhotosPermission": "Allow $(PRODUCT_NAME) to save videos to your photo library."
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

## How It Works Now

1. ✅ **Server Processing** (0-50%): Video downloads on server
2. ✅ **Device Download** (50-90%): File transfers to your phone
3. ✅ **Gallery Save** (90-100%): Video saved to media library
4. ✅ **Result**: Video appears in your phone's gallery!

## Testing

1. Install dependencies:
   ```bash
   npx expo install expo-file-system expo-media-library
   ```

2. Update your Render URL in the API file

3. Test with an Instagram or TikTok URL

4. Check your phone's gallery - the video should appear!

## Important Notes

- **Permissions**: App will ask for media library permissions
- **Storage**: Videos saved to device gallery/photos app
- **Progress**: Shows real-time download progress
- **Platform**: Works on both iOS and Android

## Troubleshooting

**Video still not appearing?**
- Check that permissions were granted
- Look in "Downloads" album in your gallery
- Verify the Render URL is correct in the API
- Check device storage space

**Error downloading to device?**
- Ensure expo-file-system is installed
- Check that the video exists on server
- Verify network connection

---

**Status**: Videos will now download to your device and appear in your gallery! 📱✅
