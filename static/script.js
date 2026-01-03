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

// Download video directly (no progress tracking, no server storage!)
async function downloadVideo() {
    if (isDownloading || !currentVideoUrl) return;

    isDownloading = true;
    downloadBtn.disabled = true;
    downloadBtnText.textContent = 'Getting download link...';
    hideElement(successMessage);

    try {
        // Get the direct download URL (zero storage!)
        const response = await fetch('/api/get-direct-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: currentVideoUrl })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get download link');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error('Failed to get download URL');
        }

        const { direct_url, filename } = data.data;

        downloadBtnText.textContent = 'Starting download...';

        // Trigger download by opening the direct URL in a new window
        // This works better than trying to fetch and create a blob
        const link = document.createElement('a');
        link.href = direct_url;
        link.download = filename || 'video.mp4';
        link.target = '_blank';  // Open in new tab as backup
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Show success
        downloadBtnText.textContent = 'Download started!';
        showElement(successMessage);

        // Reset after 3 seconds
        setTimeout(() => {
            downloadBtn.disabled = false;
            downloadBtnText.textContent = 'Download Video';
            isDownloading = false;
        }, 3000);

    } catch (error) {
        showError(error.message);
        downloadBtn.disabled = false;
        downloadBtnText.textContent = 'Download Video';
        isDownloading = false;
    }
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
