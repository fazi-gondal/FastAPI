# Render Deployment Notes

## 📁 Temporary Storage on Render

### How it Works:

1. **Ephemeral File System**:
   * Render uses ephemeral storage (temporary disk space)
   * Files in `temp_downloads/` are **automatically deleted** when:
     * Server restarts
     * App redeploys
     * Container restarts

2. **Automatic Cleanup**:
   * ✅ Files auto-delete **after download** (BackgroundTasks)
   * ✅ Old files (>1 hour) cleaned on **startup**
   * ✅ No manual cleanup needed!

3. **Storage Limits**:
   * Render Free Tier: ~512MB ephemeral storage
   * Paid Plans: More storage available
   * Files don't persist between deploys

### Current Implementation:

```python
# 1. After each download - file is deleted
background_tasks.add_task(cleanup_file, filepath)

# 2. On server startup - old files removed
@app.on_event("startup")
async def startup_event():
    cleanup_old_files()  # Removes files older than 1 hour
```

## 🚀 Deployment Best Practices

### For Render:

1. **Environment Variables** (Optional):
   * `MAX_FILE_AGE` - How long to keep files (default: 1 hour)
   * No sensitive data needed for basic setup

2. **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Health Check**:
   * Path: `/`
   * Should return 200 OK

### Storage Management:

#### Automatic (Current Setup):

✅ Files deleted after download
✅ Old files cleaned on startup
✅ No disk space buildup

#### Manual Cleanup (if needed):

You can add a cleanup endpoint for admin use:

```python
@app.post("/admin/cleanup")
async def manual_cleanup(secret: str):
    if secret != "your_secret_key":
        raise HTTPException(403)
    
    cleanup_old_files()
    return {"status": "cleaned"}
```

## 📊 Disk Space Monitoring

Render automatically monitors disk usage. If you need to check:

```bash
# In Render Shell
du -sh temp_downloads/
```

## ⚠️ Important Notes

1. **Don't Store Permanently**:
   * Never rely on `temp_downloads/` for long-term storage
   * Files will be lost on restart

2. **Large Files**:
   * Very large videos (>100MB) will take longer to download
   * But they're still deleted automatically after serving

3. **Concurrent Downloads**:
   * Multiple users can download simultaneously
   * Each gets their own file
   * All cleaned up after completion

## 🔧 Troubleshooting

### Disk Full Error:

```
Solution: Files are auto-cleaned, but if issue persists:
1. Check for failed deletions
2. Manually restart the Render service
3. Old files will be removed on startup
```

### Files Not Deleting:

```
Check logs for:
- "Cleaned up: [filename]" - successful deletion
- "Cleanup error: [error]" - deletion failed
```

## 💡 Alternative Approaches

If you want **zero local storage**:

### Option 1: Stream Directly (Advanced)

Instead of downloading to disk, stream from source to client:

```python
# Would require significant refactoring
# yt-dlp → stream → client (no disk storage)
```

### Option 2: Cloud Storage

Use external storage for temporary files:

* AWS S3 (with lifecycle policies)
* Cloudinary (auto-delete after X hours)
* Google Cloud Storage (temporary links)

**Current Setup is Best for Most Cases** ✅

* Simple
* Automatic cleanup
* No external dependencies
* Works great on Render

***

**Status**: ✅ Auto-cleanup enabled
**Disk Management**: Automatic
**No Manual Work**: Required
