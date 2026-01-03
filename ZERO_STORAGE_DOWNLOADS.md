# Zero-Storage Download Methods

## Problem with Vercel

Vercel has `/tmp` storage limits (512MB) and files are ephemeral. For maximum efficiency, you should avoid using disk storage entirely!

## ✅ RECOMMENDED: Use These No-Storage Options

### Option 1: `/api/stream` - NEW! (Best for Vercel)

**Zero storage, zero bandwidth usage!**

This endpoint redirects the client directly to the video source URL.

```javascript
// Frontend usage
const response = await fetch(`${API_URL}/api/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: videoUrl })
});

// Browser automatically starts download from source
// No server storage or bandwidth used!
```

**Benefits:**

* ✅ **Zero disk storage** - No temp\_downloads needed
* ✅ **Zero bandwidth** - Download comes directly from source
* ✅ **Fast** - No server processing delay
* ✅ **Perfect for Vercel** - No filesystem issues ever!

### Option 2: `/api/get-direct-url` (Best for Mobile Apps)

Returns the direct download URL for the client to use.

```javascript
const response = await fetch(`${API_URL}/api/get-direct-url`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: videoUrl })
});

const data = await response.json();
const { direct_url, filename, filesize, expires_in } = data.data;

// Mobile app downloads directly from source
// e.g., using FileSystem.downloadAsync() in React Native
```

**Benefits:**

* ✅ **Zero server resources** - Client does everything
* ✅ **Progress tracking** - Client can show download progress
* ✅ **Perfect for mobile** - Works great with FileSystem API
* ✅ **URL expires in ~6 hours** - Need to fetch fresh URL after expiry

## ⚠️ Old Method (Uses Storage): `/api/download/start`

This downloads to `/tmp` first (on Vercel) then serves the file. Only use if you need progress tracking on web.

```javascript
// Start download
const startResp = await fetch(`${API_URL}/api/download/start`, {
  method: 'POST',
  body: JSON.stringify({ url: videoUrl })
});
const { download_id } = await startResp.json();

// Track progress (Server-Sent Events)
const events = new EventSource(`${API_URL}/api/download/progress/${download_id}`);
events.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log(`Progress: ${data.progress}%`);
  if (data.status === 'completed') {
    events.close();
    // Download file
    window.location.href = `${API_URL}/api/download/file/${download_id}`;
  }
};
```

**Downsides:**

* ❌ Uses `/tmp` storage (512MB limit on Vercel)
* ❌ Uses server bandwidth
* ❌ Slower (must download to server first)

## Recommendation for Each Use Case

| Use Case | Recommended Method | Reason |
|----------|-------------------|--------|
| **Vercel deployment** | `/api/stream` | No storage, no bandwidth |
| **Mobile app** | `/api/get-direct-url` | Client handles download |
| **Web with progress** | `/api/download/start` | Need progress tracking |
| **Large files (>100MB)** | `/api/get-direct-url` | Avoid timeouts |

## Example: Converting Your Current Code

### Before (uses storage):

```javascript
const startResp = await fetch(`${API_URL}/api/download/start`, {
  method: 'POST',
  body: JSON.stringify({ url: videoUrl })
});
// ... track progress ...
```

### After (no storage):

```javascript
// Just change the endpoint!
const response = await fetch(`${API_URL}/api/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: videoUrl })
});

// Browser automatically downloads - that's it!
```

## Summary

✅ **For Vercel**: Use `/api/stream` - Zero storage, zero problems!\
✅ **For Mobile**: Use `/api/get-direct-url` - Full control, direct download\
⚠️ **Legacy Support**: `/api/download/start` still works but uses `/tmp` storage
