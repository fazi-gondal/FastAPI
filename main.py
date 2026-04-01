from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import os
import json
import asyncio
import httpx
import time
import uuid
from downloader import get_video_metadata, download_video, get_downloads_folder, get_direct_url



# Store download progress globally
download_progress = {}


# Cleanup function to delete file after download
def cleanup_file(filepath: str):
    """Delete the downloaded file after it's been served"""
    try:
        # Small delay to ensure file is fully sent
        time.sleep(2)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up: {filepath}")
    except Exception as e:
        print(f"Cleanup error: {e}")


# Cleanup old files on startup (for files left from previous sessions)
def cleanup_old_files():
    """Remove files older than 1 hour from temp_downloads"""
    try:
        downloads_folder = get_downloads_folder()
        if not os.path.exists(downloads_folder):
            return
        
        current_time = time.time()
        for filename in os.listdir(downloads_folder):
            filepath = os.path.join(downloads_folder, filename)
            # Delete files older than 1 hour (3600 seconds)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > 3600:
                    os.remove(filepath)
                    print(f"Removed old file: {filename}")
    except Exception as e:
        print(f"Old files cleanup error: {e}")

# Lifespan event handler (modern FastAPI)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Cleanup old files
    cleanup_old_files()
    print("Cleaned up old temporary files")
    yield
    # Shutdown: Nothing to do
    pass

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request models
class URLRequest(BaseModel):
    url: str


class ProxyStreamRequest(BaseModel):
    direct_url: str
    filename: str = "video.mp4"
    headers: Optional[Dict[str, str]] = None


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/metadata")
async def fetch_metadata(request: URLRequest):
    """
    Fetch video metadata without downloading
    """
    try:
        metadata = get_video_metadata(request.url)
        return {"success": True, "data": metadata}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/get-direct-url")
async def get_video_direct_url(body: URLRequest, request: Request):
    """
    Get direct download URL (or server proxy stream if CDN is strictly protected).
    Works for both mobile (React Native) and web frontend.
    Returns:
      - direct_url    : CDN URL to download from (or our protected GET stream proxy)
      - http_headers  : headers the client must attach
      - needs_proxy   : True if browser should use /api/proxy-stream instead of direct fetch
    """
    import urllib.parse
    try:
        url_info = get_direct_url(body.url)
        # If the platform aggressively blocks mobile direct fetching (like TikTok no-watermark), 
        # instantly route them to our seamless backend GET stream proxy instead of outputting a 403 CDN
        if url_info.get("force_backend_stream"):
            base_url = str(request.base_url)
            safe_url = urllib.parse.quote(body.url)
            url_info["direct_url"] = f"{base_url}api/stream?url={safe_url}"
        return {"success": True, "data": url_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/stream")
async def stream_video_get(url: str):
    """
    Server-side GET proxy stream for aggressive CDNs that block mobile fetching.
    Runs yt-dlp to safely merge/download the media into the Render server, then 
    streams those stable bytes natively to the React Native app avoiding 403 crashes.
    """
    from urllib.parse import quote
    import re
    import asyncio
    import os

    try:
        loop = asyncio.get_event_loop()
        filename, filepath = await loop.run_in_executor(
            None,
            lambda: download_video(url)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail="Downloaded file not found on server")

    ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    encoded_filename = quote(filename)
    content_disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    file_size = os.path.getsize(filepath)

    async def stream_and_cleanup():
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        finally:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Cleaned up GET stream temp file: {filename}")
                except Exception as e:
                    print(f"Cleanup error: {e}")

    return StreamingResponse(
        stream_and_cleanup(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": content_disposition,
            "Content-Length": str(file_size),
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/proxy-stream")
async def proxy_stream_video(request: ProxyStreamRequest):
    """
    Lightweight streaming proxy — streams the CDN video directly to the client
    in 64 KB chunks WITHOUT saving anything to disk.

    Use this when the CDN requires headers (Referer, User-Agent) that browsers
    cannot set freely (e.g. TikTok). The server acts as a thin pass-through.
    """
    cdn_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    if request.headers:
        cdn_headers.update(request.headers)

    from urllib.parse import quote
    import re
    ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', request.filename)
    encoded_filename = quote(request.filename)
    content_disposition = (
        f'attachment; filename="{ascii_filename}"; '
        f"filename*=UTF-8''{encoded_filename}"
    )

    async def stream_chunks():
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", request.direct_url, headers=cdn_headers) as response:
                if response.status_code not in (200, 206):
                    raise HTTPException(
                        status_code=502,
                        detail=f"CDN returned {response.status_code}"
                    )
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_chunks(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/server-stream")
async def server_stream_video(request: URLRequest):
    """
    Server-side download + stream: yt-dlp downloads the video (auto-merging
    DASH video+audio streams), then we stream the merged file to the client
    in 64 KB chunks and delete the temp file immediately after.

    Used for Instagram and any platform whose CDN uses DASH (separate streams).
    This guarantees the downloaded file has full audio+video.
    """
    from urllib.parse import quote
    import re

    try:
        # Run yt-dlp download in a thread (blocking call)
        loop = asyncio.get_event_loop()
        filename, filepath = await loop.run_in_executor(
            None,
            lambda: download_video(request.url)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail="Downloaded file not found on server")

    # Build Content-Disposition header
    ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    encoded_filename = quote(filename)
    content_disposition = (
        f'attachment; filename="{ascii_filename}"; '
        f"filename*=UTF-8''{encoded_filename}"
    )

    # Get file size for Content-Length header
    file_size = os.path.getsize(filepath)

    async def stream_and_cleanup():
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        finally:
            # Always clean up the temp file after streaming
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Cleaned up server-stream temp file: {filename}")
            except Exception as e:
                print(f"Cleanup error: {e}")

    return StreamingResponse(
        stream_and_cleanup(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": content_disposition,
            "Content-Length": str(file_size),
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )




@app.post("/api/download/start")
async def start_download(request: URLRequest):
    """
    Start video download and return download ID for progress tracking
    """
    try:
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        download_progress[download_id] = {
            "status": "starting",
            "progress": 0,
            "filename": None,
            "filepath": None
        }
        
        # Start download in background
        asyncio.create_task(download_in_background(download_id, request.url))
        
        return {"download_id": download_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def download_in_background(download_id: str, url: str):
    """Background task to download video and track progress"""
    try:
        download_progress[download_id]["status"] = "downloading"
        
        # Progress callback
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    download_progress[download_id]["progress"] = round(percent, 1)
                elif '_percent_str' in d:
                    try:
                        percent_str = d['_percent_str'].strip().replace('%', '')
                        download_progress[download_id]["progress"] = round(float(percent_str), 1)
                    except:
                        pass
        
        # Download with progress tracking
        filename, filepath = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: download_video(url, progress_hook)
        )
        
        download_progress[download_id].update({
            "status": "completed",
            "progress": 100,
            "filename": filename,
            "filepath": filepath
        })
    except Exception as e:
        download_progress[download_id].update({
            "status": "error",
            "error": str(e)
        })


@app.get("/api/download/progress/{download_id}")
async def get_download_progress(download_id: str):
    """
    Get current download progress (Server-Sent Events)
    """
    async def event_generator():
        while True:
            if download_id not in download_progress:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Invalid download ID'})}\n\n"
                break
            
            progress_data = download_progress[download_id]
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            if progress_data["status"] in ["completed", "error"]:
                break
            
            await asyncio.sleep(0.5)  # Update every 500ms
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/download/file/{download_id}")
async def get_download_file(download_id: str, background_tasks: BackgroundTasks):
    """
    Get the downloaded file
    """
    try:
        if download_id not in download_progress:
            raise HTTPException(status_code=404, detail="Download not found")
        
        progress_data = download_progress[download_id]
        
        if progress_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="Download not completed yet")
        
        filename = progress_data["filename"]
        filepath = progress_data["filepath"]
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Downloaded file not found")
        
        # Encode filename for Content-Disposition header
        from urllib.parse import quote
        import re
        
        ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
        encoded_filename = quote(filename)
        content_disposition = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file, filepath)
        background_tasks.add_task(cleanup_progress, download_id)
        
        return FileResponse(
            filepath,
            media_type="video/mp4",
            headers={
                "Content-Disposition": content_disposition,
                "Cache-Control": "no-cache",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_progress(download_id: str):
    """Remove progress data after file is served"""
    try:
        time.sleep(5)  # Wait a bit before cleanup
        if download_id in download_progress:
            del download_progress[download_id]
    except Exception as e:
        print(f"Progress cleanup error: {e}")


@app.get("/api/thumbnail")
async def proxy_thumbnail(url: str):
    """
    Proxy thumbnail images to bypass CORS restrictions
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Thumbnail not found")
            
            content_type = response.headers.get("content-type", "image/jpeg")
            
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                }
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thumbnail: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("Starting Social Media Downloader...")
    print("Server running at: http://localhost:8000")
    print("Press CTRL+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000)
