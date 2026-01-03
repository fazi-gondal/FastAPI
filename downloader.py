import yt_dlp
import os
from pathlib import Path
import re
import time


def get_downloads_folder():
    """Get appropriate downloads folder based on environment (serverless vs local)"""
    # Check if running on serverless platform (Vercel, AWS Lambda, etc.)
    is_serverless = (
        os.getenv('VERCEL') or 
        os.getenv('AWS_LAMBDA_FUNCTION_NAME') or
        os.getenv('NETLIFY') or
        # Additional check: /tmp exists but typical home directories don't
        (os.path.exists('/tmp') and not os.path.exists('/home') and os.name != 'nt')
    )
    
    if is_serverless:
        # Use /tmp on serverless platforms (Vercel, AWS Lambda, etc.)
        temp_dir = '/tmp/temp_downloads'
        print(f"Serverless environment detected, using {temp_dir}")
    else:
        # Use project directory for local development
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp_downloads')
    
    # Create directory if it doesn't exist
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            print(f"Created temp directory: {temp_dir}")
    except Exception as e:
        print(f"Warning: Could not create temp directory {temp_dir}: {e}")
        # Fallback to /tmp if creation fails
        if not is_serverless:
            temp_dir = '/tmp'
            print(f"Falling back to {temp_dir}")
    
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
    Get direct download URL without downloading the video
    Perfect for mobile apps to save server bandwidth
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'no_check_certificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Add cookie support if available
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
    
    # Platform-specific format selection
    if 'tiktok.com' in url or 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
        ydl_opts['format'] = 'best/bestvideo+bestaudio/best'
    elif 'instagram.com' in url:
        ydl_opts['format'] = 'best[height>=720]/best'
    elif 'youtube.com' in url or 'youtu.be' in url:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get the direct URL
            if 'url' in info:
                direct_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Get the best format's URL
                direct_url = info['formats'][-1]['url']
            else:
                raise Exception("Could not extract direct URL")
            
            # Get file info
            title = info.get('title', 'video')
            filename = sanitize_filename(title) + '.mp4'
            filesize = info.get('filesize', 0) or info.get('filesize_approx', 0)
            
            return {
                'direct_url': direct_url,
                'filename': filename,
                'filesize': filesize,
                'expires_in': 21600,  # URLs typically expire in 6 hours
            }
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

