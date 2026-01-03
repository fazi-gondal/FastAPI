from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
import httpx
import time
import uuid
from downloader import get_video_metadata, download_video, get_downloads_folder, get_direct_url, stream_video_download


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
async def get_video_direct_url(request: URLRequest):
    """
    Get direct download URL without using server bandwidth
    Perfect for mobile apps - downloads directly from source
    """
    try:
        url_info = get_direct_url(request.url)
        return {"success": True, "data": url_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@app.post("/api/stream")
async def stream_download(request: URLRequest):
    """
    Stream video download without saving to disk (ZERO storage usage!)
    Perfect for Vercel - no temp_downloads needed at all
    Returns redirect to direct video URL
    """
    try:
        # Get direct URL and filename without downloading
        direct_url, filename = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: stream_video_download(request.url)
        )
        
        # Redirect to direct URL (client downloads from source)
        # This is the BEST option for Vercel - zero storage, zero bandwidth!
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=direct_url,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
