# Deployment Guide

This guide covers deployment to various platforms including Vercel and Koyeb.

***

## 🔵 Vercel Deployment

### Overview

Vercel is a serverless platform that makes deployment easy with automatic Git integration. This API is fully compatible with Vercel.

### Important: File Storage on Vercel

Vercel serverless functions have a **read-only filesystem** except for `/tmp` directory:

* ✅ **Automatic Detection**: The app automatically detects Vercel environment and uses `/tmp/temp_downloads`
* 📦 **Storage Limit**: `/tmp` has 512MB limit
* ⏱️ **Ephemeral**: Files are deleted after the function execution completes
* 🔄 **Perfect for**: Temporary downloads that are immediately served to users

### Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **GitHub Account**: Your code should be in a GitHub repository
3. **Git Installed**: To push your code

### Deployment Steps

#### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push to GitHub**:
   ```bash
   cd d:\Python\FastAPI
   git add .
   git commit -m "Add Vercel support"
   git push origin main
   ```

2. **Import Project on Vercel**:
   * Go to https://vercel.com/new
   * Import your GitHub repository
   * Vercel will auto-detect it as a Python project

3. **Configure Project**:
   * **Framework Preset**: Other
   * **Build Command**: (leave empty)
   * **Output Directory**: (leave empty)
   * **Install Command**: `pip install -r requirements.txt`

4. **Deploy**:
   * Click "Deploy"
   * Wait for deployment (2-5 minutes)
   * Your API will be live at `https://your-project.vercel.app`

#### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   cd d:\Python\FastAPI
   vercel --prod
   ```

### Configuration File

The project includes `vercel.json` with optimized settings:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "functions": {
    "main.py": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

**Key Settings**:

* **memory**: 3008MB (maximum for better performance)
* **maxDuration**: 60 seconds (Hobby plan limit)
* **maxLambdaSize**: 50MB (includes yt-dlp and dependencies)

### Environment Variables

The app automatically detects Vercel via the `VERCEL` environment variable (set automatically by Vercel).

**Optional**: Add custom environment variables in Vercel Dashboard → Settings → Environment Variables

### Testing Your Deployed API

1. **Get your Vercel URL** from the deployment output
2. **Test endpoints**:
   ```bash
   # Test homepage
   curl https://your-project.vercel.app/

   # Test metadata endpoint
   curl -X POST https://your-project.vercel.app/api/metadata \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.instagram.com/reel/xxxxx/"}'
   ```

### Vercel-Specific Limitations

1. **Execution Time**: 60 seconds max on Hobby plan (10 seconds on free)
2. **File Size**: Downloads work, but very large files (>100MB) may timeout
3. **/tmp Storage**: 512MB maximum
4. **Concurrent Executions**: Limited by plan

**Solutions for Large Files**:

* Use the `/api/get-direct-url` endpoint for large files (mobile apps download directly)
* Upgrade to Pro plan for longer timeouts (5 minutes)
* Consider alternative platforms for very large video downloads

### Automatic Redeployment

Vercel automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update features"
git push origin main
# Vercel automatically redeploys
```

### Monitoring

View logs and analytics:

1. Go to Vercel Dashboard
2. Select your project
3. Check **Deployments** tab for logs
4. Check **Analytics** for usage metrics

***

# Koyeb Deployment Guide

Step-by-step guide to deploy your Social Media Downloader API to Koyeb.

## 📋 Prerequisites

1. **Koyeb Account**: Sign up at https://www.koyeb.com/
2. **GitHub Account**: Your code should be in a GitHub repository
3. **Git Installed**: To push your code

***

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Create a Git repository** (if not already done):
   ```bash
   cd d:\Python\FastAPI
   git init
   git add .
   git commit -m "Initial commit - Social Media Downloader API"
   ```

2. **Push to GitHub**:
   ```bash
   # Create a new repository on GitHub first, then:
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Koyeb

1. **Log in to Koyeb**: Go to https://app.koyeb.com/

2. **Create New App**:
   * Click **"Create App"**
   * Choose **"GitHub"** as deployment method

3. **Connect GitHub**:
   * Authorize Koyeb to access your GitHub repositories
   * Select your repository

4. **Configure Build**:
   * **Builder**: Buildpack (auto-detected)
   * **Branch**: `main`
   * **Build command**: Leave empty (auto-detected)
   * **Run command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Configure Instance**:
   * **Instance type**: Free tier (or choose based on needs)
   * **Regions**: Choose closest to your users
   * **Scaling**: 1 instance (can scale later)

6. **Environment Variables** (Optional):
   * No environment variables required for basic setup
   * Add `PYTHONUNBUFFERED=1` for better logging (optional)

7. **Health Check**:
   * **Path**: `/` (returns status 200)
   * **Port**: Same as application port

8. **Deploy**:
   * Click **"Deploy"**
   * Wait for deployment to complete (5-10 minutes)

### Step 3: Get Your API URL

After deployment completes:

1. Your app will be available at: `https://your-app-name.koyeb.app`
2. Test the API:
   ```bash
   curl https://your-app-name.koyeb.app/
   ```

***

## ⚙️ Configuration Files

The following files are already set up for deployment:

### `Procfile`

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### `runtime.txt`

```
python-3.11
```

### `requirements.txt`

```
fastapi>=0.109.1
uvicorn>=0.27.0
yt-dlp==2024.12.23
python-multipart>=0.0.18
aiofiles>=23.2.1
httpx>=0.25.0
```

***

## 🔧 Koyeb-Specific Configuration

### Using Koyeb CLI (Alternative Method)

1. **Install Koyeb CLI**:
   ```bash
   # Windows (PowerShell)
   iwr https://cli.koyeb.com/install.ps1 -useb | iex

   # Or download from https://github.com/koyeb/koyeb-cli/releases
   ```

2. **Login**:
   ```bash
   koyeb login
   ```

3. **Deploy**:
   ```bash
   koyeb app init social-media-downloader \
     --git github.com/yourusername/your-repo-name \
     --git-branch main \
     --ports 8000:http \
     --routes /:8000 \
     --env PYTHONUNBUFFERED=1
   ```

***

## 🌐 Custom Domain (Optional)

1. **Add Domain in Koyeb**:
   * Go to your app settings
   * Click **"Domains"**
   * Add your custom domain

2. **Configure DNS**:
   * Add CNAME record pointing to `your-app-name.koyeb.app`
   * Wait for DNS propagation (can take up to 48 hours)

***

## 📊 Monitoring & Logs

### View Logs

1. Go to your app in Koyeb dashboard
2. Click **"Logs"** tab
3. View real-time logs

### Metrics

* **CPU Usage**
* **Memory Usage**
* **Request Count**
* **Response Times**

All available in the Koyeb dashboard.

***

## 🔄 Updates & Redeployment

### Automatic Deployments

Koyeb automatically redeploys when you push to your GitHub repository:

```bash
# Make changes to your code
git add .
git commit -m "Update: Added new feature"
git push origin main

# Koyeb will automatically detect and redeploy
```

### Manual Redeployment

1. Go to Koyeb dashboard
2. Click **"Redeploy"** button
3. Wait for deployment

***

## ⚠️ Important Production Considerations

### 1. File Storage

Koyeb uses **ephemeral storage**. Downloaded videos are temporary.

**Solutions**:

* Use cloud storage (AWS S3, Google Cloud Storage)
* Return direct download URLs instead of saving files
* Implement streaming responses

### 2. Rate Limiting

Consider adding rate limiting for production:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/metadata")
@limiter.limit("10/minute")
async def fetch_metadata(request: Request, data: URLRequest):
    # ...
```

### 3. CORS Configuration

For production, restrict CORS to your app's domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.com"],  # Your React Native app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Error Tracking

Add error tracking service (Sentry, etc.):

```bash
pip install sentry-sdk
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

***

## 🐛 Troubleshooting

### Build Fails

**Problem**: Build fails during deployment

**Solutions**:

1. Check `requirements.txt` for correct versions
2. Verify `Procfile` command is correct
3. Check build logs in Koyeb dashboard
4. Ensure Python version is compatible (3.11 recommended)

### App Crashes

**Problem**: App starts but crashes immediately

**Solutions**:

1. Check application logs in Koyeb dashboard
2. Verify port binding uses `$PORT` environment variable
3. Test locally with same command:
   ```bash
   PORT=8000 uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Slow Performance

**Problem**: API responses are slow

**Solutions**:

1. Upgrade to a higher tier instance
2. Enable caching for metadata
3. Optimize yt-dlp settings
4. Use CDN for static assets

### Out of Memory

**Problem**: App crashes with memory errors

**Solutions**:

1. Upgrade instance to higher memory tier
2. Reduce concurrent downloads
3. Implement streaming instead of full file downloads
4. Clean up temporary files

***

## 💰 Pricing Tiers

### Free Tier

* **Price**: $0/month
* **Instances**: 1
* **RAM**: 512 MB
* **vCPU**: Shared
* **Good for**: Testing, small projects

### Starter Tier

* **Price**: ~$5-10/month
* **Instances**: 1-2
* **RAM**: 1-2 GB
* **vCPU**: Shared
* **Good for**: Small to medium apps

### Production Tier

* **Price**: Custom
* **Instances**: Multiple
* **RAM**: 4+ GB
* **vCPU**: Dedicated
* **Good for**: High-traffic production apps

***

## 📱 Testing Your Deployed API

### From React Native

```javascript
const API_URL = 'https://your-app-name.koyeb.app';

// Test metadata endpoint
const testAPI = async () => {
  const response = await fetch(`${API_URL}/api/metadata`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      url: 'https://www.instagram.com/reel/xxxxx/' 
    }),
  });
  
  const data = await response.json();
  console.log('API Response:', data);
};
```

### From Browser

Navigate to: `https://your-app-name.koyeb.app`

You should see the web interface.

***

## 🔐 Security Best Practices

1. **Enable HTTPS**: Koyeb provides SSL certificates automatically
2. **Restrict CORS**: Limit to your app's domains
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Validate all URLs
5. **Error Messages**: Don't expose internal errors
6. **Logging**: Log all requests for monitoring
7. **Updates**: Keep dependencies updated

***

## 📚 Additional Resources

* **Koyeb Documentation**: https://www.koyeb.com/docs
* **Koyeb Status**: https://status.koyeb.com/
* **Koyeb Community**: https://community.koyeb.com/
* **yt-dlp Docs**: https://github.com/yt-dlp/yt-dlp

***

## ✅ Deployment Checklist

* \[ ] Code pushed to GitHub
* \[ ] Repository connected to Koyeb
* \[ ] Build configuration set
* \[ ] App deployed successfully
* \[ ] Health check passing
* \[ ] API endpoints tested
* \[ ] CORS configured
* \[ ] Error handling verified
* \[ ] Monitoring enabled
* \[ ] Documentation updated with live URL

***

**Deployment Status**: Ready for production 🚀

After deployment, update your React Native app with the Koyeb URL and you're ready to go!
