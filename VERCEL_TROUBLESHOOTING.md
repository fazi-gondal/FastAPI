# Vercel Build Troubleshooting

## Current Setup

I've created two files for Vercel deployment:

1. **Simplified `vercel.json`** - Uses modern configuration format
2. **`api/index.py`** - Entry point for Vercel serverless functions

## Common Vercel Build Errors & Solutions

### Error 1: "No Python Project detected"

**Solution**: Create a `requirements.txt` file (✅ already have this)

### Error 2: "Build exceeded maximum duration"

**Cause**: yt-dlp is a large package (~50MB)

**Solutions**:

* Vercel should cache dependencies after first build
* Or use Vercel Pro plan (longer build timeout)
* Or simplify dependencies

### Error 3: "Lambda size exceeds limit"

**Cause**: Package size with yt-dlp is large

**Solution**: Already set `maxLambdaSize: "50mb"` but Vercel has hard limits

### Error 4: "Module 'app' has no attribute 'app'"

**Cause**: Vercel can't find the FastAPI app instance

**Solution**: Created `api/index.py` that imports from main.py

### Error 5: Static files not working

**Cause**: Vercel treats static files differently in serverless

**Solution**: Static files need special handling in Vercel

## What I've Changed

### Option A: Modern Vercel Structure (RECOMMENDED)

```
FastAPI/
├── api/
│   └── index.py          # ← NEW: Vercel entry point
├── main.py               # Your FastAPI app
├── downloader.py
├── vercel.json           # ← UPDATED: Simplified config
├── requirements.txt
└── static/
    └── index.html
```

The `api/index.py` tells Vercel your serverless function is at `/api`

### Option B: Root-level deployment (ALTERNATIVE)

If Option A doesn't work, we can try deploying at root level.

## Next Steps

**Please share the EXACT error message from Vercel**, then I can provide a targeted fix.

Common places to find the error:

1. Vercel Dashboard → Your deployment → Click on failed deployment
2. Look for "Build Logs" section
3. Copy the error message (usually in red)

## Quick Fixes to Try

### Fix 1: Ensure Python version is specified

Create `runtime.txt`:

```
python-3.11
```

(✅ Already exists)

### Fix 2: Try minimal vercel.json

If build still fails, try this minimal config:

```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 60
    }
  }
}
```

### Fix 3: Revert to no vercel.json

Sometimes Vercel's auto-detection works better. Try deleting `vercel.json` entirely.

## What Error Are You Seeing?

Please share:

1. The error message from Vercel build logs
2. At what stage it fails (Install, Build, or Deploy)
3. Screenshot if possible

Then I can provide the exact fix!
