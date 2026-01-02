// DOM Elements
const urlInput = document.getElementById('urlInput');
const loadingState = document.getElementById('loadingState');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const videoCard = document.getElementById('videoCard');
const downloadBtn = document.getElementById('downloadBtn');
const downloadBtnText = document.getElementById('downloadBtnText');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const successMessage = document.getElementById('successMessage');

// Video metadata storage
let currentVideoUrl = '';
let isDownloading = false;
let currentDownloadId = null;

// Format duration from seconds to MM:SS
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Show/Hide elements
function showElement(element) {
    element.classList.remove('hidden');
}

function hideElement(element) {
    element.classList.add('hidden');
}

// Show error message
function showError(message) {
    errorText.textContent = message;
    showElement(errorMessage);
    hideElement(loadingState);
    hideElement(videoCard);
}

// Hide error message
function hideError() {
    hideElement(errorMessage);
}

// Reset UI
function resetUI() {
    hideElement(loadingState);
    hideElement(errorMessage);
    hideElement(videoCard);
    hideElement(progressContainer);
    hideElement(successMessage);
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    isDownloading = false;
    downloadBtn.disabled = false;
    downloadBtnText.textContent = 'Download Video';
}

// Fetch video metadata
async function fetchMetadata(url) {
    hideError();
    hideElement(videoCard);
    showElement(loadingState);

    try {
        const response = await fetch('/api/metadata', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to fetch video metadata');
        }

        if (data.success) {
            displayVideoCard(data.data);
            currentVideoUrl = url;
        }
    } catch (error) {
        showError(error.message);
    } finally {
        hideElement(loadingState);
    }
}

// Display video card with metadata
function displayVideoCard(metadata) {
    // Use thumbnail proxy for platforms with CORS issues
    let thumbnailUrl = metadata.thumbnail;
    const platform = metadata.platform.toLowerCase();

    // Proxy thumbnail for Instagram, TikTok, and other platforms that block CORS
    if (platform.includes('instagram') || platform.includes('tiktok') || platform.includes('facebook')) {
        thumbnailUrl = `/api/thumbnail?url=${encodeURIComponent(metadata.thumbnail)}`;
    }

    document.getElementById('thumbnail').src = thumbnailUrl;
    document.getElementById('videoTitle').textContent = metadata.title;
    document.getElementById('videoUploader').textContent = metadata.uploader;
    document.getElementById('videoPlatform').textContent = metadata.platform;
    document.getElementById('durationBadge').textContent = formatDuration(metadata.duration);

    showElement(videoCard);
    hideElement(successMessage);
}

// Update progress bar
function updateProgress(percent) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
}

// Download video with real-time progress
async function downloadVideo() {
    if (isDownloading || !currentVideoUrl) return;

    isDownloading = true;
    downloadBtn.disabled = true;
    downloadBtnText.textContent = 'Preparing...';
    hideElement(successMessage);
    showElement(progressContainer);
    updateProgress(0);

    try {
        // Step 1: Start download
        const startResponse = await fetch('/api/download/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: currentVideoUrl })
        });

        if (!startResponse.ok) {
            const errorData = await startResponse.json();
            throw new Error(errorData.detail || 'Failed to start download');
        }

        const { download_id } = await startResponse.json();
        currentDownloadId = download_id;

        downloadBtnText.textContent = 'Downloading...';

        // Step 2: Track progress using EventSource
        await trackProgress(download_id);

    } catch (error) {
        showError(error.message);
        downloadBtn.disabled = false;
        downloadBtnText.textContent = 'Download Video';
        isDownloading = false;
        hideElement(progressContainer);
    }
}

// Track download progress with Server-Sent Events
async function trackProgress(downloadId) {
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(`/api/download/progress/${downloadId}`);

        eventSource.onmessage = async (event) => {
            const data = JSON.parse(event.data);

            if (data.status === 'downloading' || data.status === 'starting') {
                updateProgress(data.progress || 0);
            } else if (data.status === 'completed') {
                updateProgress(100);
                eventSource.close();

                // Step 3: Download the file
                downloadBtnText.textContent = 'Getting file...';

                try {
                    // Trigger file download
                    const downloadUrl = `/api/download/file/${downloadId}`;
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = data.filename || 'video.mp4';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);

                    // Show success
                    downloadBtnText.textContent = 'Downloaded!';
                    showElement(successMessage);

                    // Reset after 3 seconds
                    setTimeout(() => {
                        downloadBtn.disabled = false;
                        downloadBtnText.textContent = 'Download Video';
                        isDownloading = false;
                        hideElement(progressContainer);
                    }, 3000);

                    resolve();
                } catch (error) {
                    reject(error);
                }
            } else if (data.status === 'error') {
                eventSource.close();
                reject(new Error(data.error || 'Download failed'));
            }
        };

        eventSource.onerror = (error) => {
            eventSource.close();
            reject(new Error('Connection to server lost'));
        };
    });
}

// Auto-fetch on paste
urlInput.addEventListener('paste', (e) => {
    // Small delay to ensure paste completes
    setTimeout(() => {
        const url = urlInput.value.trim();
        if (url) {
            fetchMetadata(url);
        }
    }, 100);
});

// Also fetch on Enter key
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const url = urlInput.value.trim();
        if (url) {
            fetchMetadata(url);
        }
    }
});

// Download button click
downloadBtn.addEventListener('click', downloadVideo);

// Clear input button (optional)
urlInput.addEventListener('input', () => {
    if (urlInput.value.trim() === '') {
        resetUI();
        currentVideoUrl = '';
    }
});
