/**
 * DOM Elements
 */
const urlInput = document.getElementById('urlInput');
const getVideoBtn = document.getElementById('getVideoBtn');
const getVideoBtnText = document.getElementById('getVideoBtnText');
const featuresSection = document.getElementById('featuresSection');

// Status Contains
const statusContainer = document.getElementById('statusContainer');
const loadingState = document.getElementById('loadingState');
const loadingMsgText = document.getElementById('loadingMsgText');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const successMessage = document.getElementById('successMessage');

// Video Card
const videoCard = document.getElementById('videoCard');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');

// Storage
let isDownloading = false;
let currentVideoUrl = '';

/**
 * Utility functions
 */
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function show(element) { element.classList.remove('hidden'); }
function hide(element) { element.classList.add('hidden'); }

/**
 * UI State Management
 */
function resetUI() {
    hide(loadingState);
    hide(errorMessage);
    hide(successMessage);
    hide(videoCard);
    
    // reset input
    urlInput.value = '';
    currentVideoUrl = '';
    
    // reset button
    getVideoBtn.disabled = false;
    getVideoBtnText.textContent = 'Get Video';
    
    // progress
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
    progressText.textContent = 'Preparing download...';
    
    isDownloading = false;
}

function showError(message) {
    errorText.textContent = message;
    hide(loadingState);
    show(errorMessage);
    hide(videoCard);
    
    getVideoBtn.disabled = false;
    getVideoBtnText.textContent = 'Try Again';
    isDownloading = false;
}

function updateProgress(percent, textMsg) {
    // ensure within 0 - 100
    const val = Math.max(0, Math.min(100, percent));
    progressFill.style.width = `${val}%`;
    progressPercent.textContent = `${Math.round(val)}%`;
    if (textMsg) progressText.textContent = textMsg;
}

/**
 * Core Flow: Click "Get Video" -> Fetch Metadata -> Start Download
 */
async function handleGetVideoFlow() {
    const url = urlInput.value.trim();
    if (!url || isDownloading) return;
    
    currentVideoUrl = url;
    isDownloading = true;
    
    // Prepare UI for flow
    getVideoBtn.disabled = true;
    getVideoBtnText.textContent = 'Processing...';
    
    hide(errorMessage);
    hide(successMessage);
    hide(featuresSection);
    hide(videoCard);
    show(loadingState);
    loadingMsgText.textContent = "Fetching video details...";
    
    try {
        // Step 1: Fetch Metadata
        const metadataResponse = await fetch('/api/metadata', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentVideoUrl })
        });
        
        const metadataJson = await metadataResponse.json();
        
        if (!metadataResponse.ok) {
            throw new Error(metadataJson.detail || 'Failed to fetch video details.');
        }
        
        if (!metadataJson.success) {
            throw new Error('Could not resolve video metadata.');
        }
        
        // Hide loader, show the gorgeous tailwind card we built
        hide(loadingState);
        displayVideoCard(metadataJson.data);
        
        // Step 2: Transition seamlessly to downloading sequence
        getVideoBtnText.textContent = 'Downloading...';
        await executeDownloadSequence();
        
    } catch (error) {
        showError(error.message);
    }
}

/**
 * Populate video card details using Tailwind structure
 */
function displayVideoCard(metadata) {
    let thumbnailUrl = metadata.thumbnail;
    const platform = metadata.platform.toLowerCase();

    // Use proxy for protected CDN images
    if (platform.includes('instagram') || platform.includes('tiktok') || platform.includes('facebook')) {
        thumbnailUrl = `/api/thumbnail?url=${encodeURIComponent(metadata.thumbnail)}`;
    }

    // Replace outer image source dynamically
    const imgWrapper = videoCard.querySelector('.relative.w-full.aspect-video');
    imgWrapper.innerHTML = `
        <img src="${thumbnailUrl}" alt="Video thumbnail" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105">
        <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent opacity-80"></div>
        <div class="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur-sm text-xs font-bold px-2 py-1 rounded text-slate-200">
            ${formatDuration(metadata.duration)}
        </div>
    `;

    document.getElementById('videoTitle').textContent = metadata.title;
    document.getElementById('videoUploader').textContent = metadata.uploader || 'Unknown User';
    document.getElementById('videoPlatform').textContent = metadata.platform;
    
    show(videoCard);
    
    // reset progress UI inside card
    updateProgress(0, 'Resolving direct download link...');
}

/**
 * Handle direct download or proxy stream logic
 */
async function executeDownloadSequence() {
    try {
        updateProgress(10, 'Getting download link...');
        
        // Request the direct url info
        const res = await fetch('/api/get-direct-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentVideoUrl })
        });

        const json = await res.json();

        if (!res.ok) {
            throw new Error(json.detail || 'Failed to resolve download URL');
        }

        const { direct_url, filename, http_headers, needs_proxy, use_server_download } = json.data;
        updateProgress(40, 'Starting download...');

        if (use_server_download) {
            // Instagram & DASH platforms: yt-dlp downloads + merges on server,
            // then streams the merged file back to the browser. Guaranteed audio+video.
            await downloadViaServerStream(filename);
        } else if (needs_proxy) {
            // TikTok: single combined CDN file, just proxy the bytes through.
            await downloadViaProxy(direct_url, filename, http_headers);
        } else {
            // Other platforms (Twitter/X, Vimeo, etc): direct CDN link works.
            await downloadDirectFromCDN(direct_url, filename);
        }

    } catch (error) {
        console.warn('Direct URL/Proxy failed, falling back to server download:', error.message);
        await downloadViaServerFallback();
    }
}

/**
 * Proxy stream — server fetches from CDN with required headers and streams bytes
 */
async function downloadViaProxy(directUrl, filename, headers) {
    updateProgress(50, 'Streaming via secure proxy...');

    // Fetch the stream as Blob
    const res = await fetch('/api/proxy-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            direct_url: directUrl,
            filename: filename || 'video.mp4',
            headers: headers || {}
        })
    });

    if (!res.ok) {
        throw new Error('Proxy stream disconnected or failed.');
    }

    updateProgress(80, 'Receiving high-speed bytes...');

    // Generate blob url and invoke download
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);

    updateProgress(95, 'Saving file to device...');

    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'video.mp4';
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
    }, 5000);

    completeDownloadSequence();
}

/**
 * Server stream — server downloads via yt-dlp (merging DASH streams) and streams bytes
 */
async function downloadViaServerStream(filename) {
    updateProgress(50, 'Downloading & merging on server...');

    // Fetch the stream as Blob
    const res = await fetch('/api/server-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: currentVideoUrl })
    });

    if (!res.ok) {
        throw new Error('Server stream disconnected or failed.');
    }

    updateProgress(80, 'Receiving high-speed bytes...');

    // Generate blob url and invoke download
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);

    updateProgress(95, 'Saving file to device...');

    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'video.mp4';
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);
    }, 5000);

    completeDownloadSequence();
}


/**
 * Direct CDN download (best for YouTube, IG)
 */
async function downloadDirectFromCDN(directUrl, filename) {
    return new Promise((resolve, reject) => {
        updateProgress(70, 'Downloading from source...');

        try {
            const a = document.createElement('a');
            a.href = directUrl;
            a.download = filename || 'video.mp4';
            // NOTE: do NOT set target='_blank' — that overrides the download
            // attribute and opens a new tab for cross-origin URLs instead of saving.
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            completeDownloadSequence();
            resolve();
        } catch (err) {
            reject(err);
        }
    });
}

/**
 * Server-download fallback for unsupported direct cases
 */
async function downloadViaServerFallback() {
    updateProgress(0, 'Server downloading...');

    try {
        const startResponse = await fetch('/api/download/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: currentVideoUrl })
        });

        if (!startResponse.ok) {
            const errorData = await startResponse.json();
            throw new Error(errorData.detail || 'Failed to start download on server');
        }

        const { download_id } = await startResponse.json();
        
        // Track using SSE
        await trackProgressFromServer(download_id);
    } catch (error) {
        showError(error.message);
    }
}

/**
 * SSE Tracking for Fallback
 */
function trackProgressFromServer(downloadId) {
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(`/api/download/progress/${downloadId}`);

        eventSource.onmessage = async (event) => {
            const data = JSON.parse(event.data);

            if (data.status === 'downloading' || data.status === 'starting') {
                updateProgress(data.progress || 0, `Downloading: ${data.progress || 0}%`);
            } else if (data.status === 'completed') {
                updateProgress(100, 'Finishing up...');
                eventSource.close();

                try {
                    const downloadUrl = `/api/download/file/${downloadId}`;
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = data.filename || 'video.mp4';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);

                    completeDownloadSequence();
                    resolve();
                } catch (error) {
                    reject(error);
                }
            } else if (data.status === 'error') {
                eventSource.close();
                reject(new Error(data.error || 'Download failed on server.'));
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            reject(new Error('Connection to server timeout or lost.'));
        };
    });
}

/**
 * Handle successful completion of flow
 */
function completeDownloadSequence() {
    updateProgress(100, 'Done!');
    getVideoBtnText.textContent = 'Get Another';
    getVideoBtn.disabled = false;
    isDownloading = false;
    
    show(successMessage);
    
    // hide progress indicator visually after 3 seconds so the card is fully clean
    setTimeout(() => {
        hide(successMessage);
    }, 4000);
}


/**
 * Event Listeners
 */
getVideoBtn.addEventListener('click', handleGetVideoFlow);

urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        handleGetVideoFlow();
    }
});

// Clear state when user starts typing a new URL
urlInput.addEventListener('input', () => {
    if (isDownloading) return;
    hide(successMessage);
    hide(errorMessage);
    if (!urlInput.value.trim()) {
        resetUI();
        show(featuresSection);
    }
});
