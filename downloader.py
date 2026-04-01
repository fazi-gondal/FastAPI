import yt_dlp
import os
from pathlib import Path
import re
import time


def get_downloads_folder():
    """Get a temporary downloads folder in the project directory"""
    # Use project directory's temp folder instead of system Downloads
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp_downloads')
    # Create directory if it doesn't exist
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir


def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove any leading/trailing dots or spaces
    filename = filename.strip('. ')
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def get_video_metadata(url: str):
    """
    Extract video metadata using yt-dlp with improved error handling
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': False,
        'no_check_certificate': True,
        # Add user agent to avoid blocking
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Add cookie support for YouTube (optional)
    # If cookies.txt exists in the project directory, use it
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
        print(f"Using cookies from: {cookies_file}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant metadata
            metadata = {
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'url': url,
                'platform': info.get('extractor', 'Unknown'),
            }
            
            return metadata
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        # Provide helpful message for YouTube bot detection
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
            raise Exception(
                "YouTube bot detection. Please add cookies.txt file. "
                "See YOUTUBE_COOKIES.md for instructions."
            )
        raise Exception(f"Failed to fetch metadata: {error_msg}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def get_direct_url(url: str):
    """
    Get direct download URL without downloading the video.
    Returns the CDN URL + any required HTTP headers so the client
    can download straight from the source (no server bandwidth used).
    """
    is_tiktok    = 'tiktok.com' in url or 'vm.tiktok.com' in url or 'vt.tiktok.com' in url
    is_instagram = 'instagram.com' in url
    is_youtube   = 'youtube.com' in url or 'youtu.be' in url

    # Build base yt-dlp options exactly as the original repo did
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'no_check_certificate': True,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
    }

    # Cookies support
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file

    # ── Platform overrides (Original Repo logic + TikTok patch) ────────────
    if is_tiktok:
        ydl_opts.update({
            'format': 'download_addr_2/download_addr/play_addr/best/bestvideo+bestaudio',
            'http_headers': {
                'User-Agent': ydl_opts['user_agent'],
                'Referer': 'https://www.tiktok.com/',
            },
            'extractor_args': {
                'tiktok': {
                    'api_hostname': ['api22-normal-c-useast2a.tiktokv.com'],
                    'app_version': ['300904'],
                }
            },
        })

    elif is_instagram:
        ydl_opts.update({
            # The exact original format from this repo that perfectly gets IG media with audio
            'format': 'best[height>=720]/best',
            'http_headers': {
                'User-Agent': ydl_opts['user_agent'],
            },
        })

    elif is_youtube:
        ydl_opts.update({
            'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Get the direct URL just like the original repo:
            if 'url' in info:
                direct_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                direct_url = info['formats'][-1]['url']
            else:
                raise Exception("Could not extract direct URL")

            # Collect headers the client must send to the CDN
            cdn_headers = {}
            for src in (ydl_opts.get('http_headers', {}), info.get('http_headers', {})):
                if src:
                    cdn_headers.update(src)

            # Always include User-Agent for mobile proxy calls
            if 'User-Agent' not in cdn_headers:
                cdn_headers['User-Agent'] = ydl_opts['user_agent']

            title    = info.get('title', 'video')
            filename = sanitize_filename(title) + '.mp4'
            filesize = info.get('filesize') or info.get('filesize_approx') or 0

            return {
                'direct_url':  direct_url,
                'filename':    filename,
                'filesize':    filesize,
                'http_headers': cdn_headers,
                # Route cross-origin links through our Fast proxy so the web browser 
                # auto-saves instead of opening a new tab. Mobile app ignores this flag.
                'needs_proxy':  is_tiktok or is_instagram,
                'use_server_download': False, # We disabled the slow fallback!
                'expires_in':  21600,
            }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg.lower():
            raise Exception("Bot detection triggered. Add a cookies.txt file.")
        raise Exception(f"Failed to get direct URL: {error_msg}")
    except Exception as e:
        raise Exception(f"Failed to get direct URL: {str(e)}")




def download_video(url: str, progress_callback=None, max_retries=3):
    """
    Download video with platform-specific quality settings and retry logic
    Returns the filepath of the downloaded video
    """
    downloads_folder = get_downloads_folder()
    
    # Base options with improved settings
    ydl_opts = {
        'outtmpl': os.path.join(downloads_folder, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'no_check_certificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Retry settings
        'retries': 10,
        'fragment_retries': 10,
        # Buffer size for better download performance
        'buffersize': 1024 * 16,
    }
    
    # Add cookie support if cookies.txt exists
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
        print(f"Using cookies from: {cookies_file}")
    
    # Platform-specific configurations
    if 'tiktok.com' in url or 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
        # TikTok: Download without watermark (try multiple formats)
        ydl_opts.update({
            'format': 'best/bestvideo+bestaudio/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            },
            # Try to get version without watermark
            'extractor_args': {
                'tiktok': {
                    'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
                }
            }
        })
    elif 'instagram.com' in url:
        # Instagram: Download in HD quality
        ydl_opts.update({
            'format': 'best[height>=720]/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        })
    elif 'youtube.com' in url or 'youtu.be' in url:
        # YouTube: Best quality with audio
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })
    else:
        # Other platforms: Best quality available
        ydl_opts.update({
            'format': 'best[ext=mp4]/best',
        })
    
    # Add progress hook if callback provided
    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]
    
    # Retry logic
    last_error = None
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get the filename that was actually created
                filename = ydl.prepare_filename(info)
                
                # Sanitize the filename
                base_name = os.path.basename(filename)
                sanitized_name = sanitize_filename(base_name)
                
                # If filename was sanitized, rename the file
                if sanitized_name != base_name:
                    new_path = os.path.join(downloads_folder, sanitized_name)
                    if os.path.exists(filename):
                        os.rename(filename, new_path)
                        filename = new_path
                
                # Return just the filename (not full path) for serving
                return os.path.basename(filename), filename
                
        except yt_dlp.utils.DownloadError as e:
            last_error = e
            if attempt < max_retries - 1:
                # Wait before retrying (exponential backoff)
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"Failed to download video after {max_retries} attempts: {str(e)}")
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise Exception(f"Unexpected error: {str(e)}")
    
    # If we get here, all retries failed
    raise Exception(f"Failed to download video: {str(last_error)}")

