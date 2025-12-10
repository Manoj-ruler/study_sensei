# 🚀 StudySensei Deployment Guide
## Free Tier Deployment: Render (Backend) + Vercel (Frontend)

This guide will walk you through deploying your StudySensei application completely free using:
- **Vercel** for the Next.js frontend
- **Render** for the FastAPI backend services (main backend, code runner, and worker)
- **Supabase** for database and authentication (already set up)

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Structure Overview](#project-structure-overview)
3. [Part 1: Backend Deployment on Render](#part-1-backend-deployment-on-render)
4. [Part 2: Frontend Deployment on Vercel](#part-2-frontend-deployment-on-vercel)
5. [Part 3: Connecting Everything](#part-3-connecting-everything)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Prerequisites

Before starting, ensure you have:

- ✅ A GitHub account (for code repository)
- ✅ A Render account (sign up at [render.com](https://render.com))
- ✅ A Vercel account (sign up at [vercel.com](https://vercel.com))
- ✅ Your Supabase project credentials:
  - Supabase URL
  - Supabase Anon Key
  - Supabase Service Role Key
- ✅ Google Gemini API Key (for AI features)
- ✅ Git installed on your computer
- ✅ Your code pushed to a GitHub repository

---

## Project Structure Overview

Your project has 4 main components:

```
bluconn/
├── frontend/          → Next.js app (deploy to Vercel)
├── backend/           → Main FastAPI service (deploy to Render)
├── code_runner/       → Code execution service (deploy to Render)
└── worker/            → Background worker (deploy to Render)
```

---

## Part 1: Backend Deployment on Render

You'll deploy **3 separate services** on Render:
1. Main Backend API
2. Code Runner Service
3. Background Worker

### Step 1.1: Push Your Code to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   cd c:\Users\manoj\OneDrive\Desktop\bluconn
   git init
   git add .
   git commit -m "Initial commit for deployment"
   ```

2. **Create a new repository** on GitHub:
   - Go to [github.com/new](https://github.com/new)
   - Name it `studysensei` or `bluconn`
   - Make it **Public** (required for Render free tier)
   - Don't initialize with README

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

### Step 1.2: Deploy Main Backend API

1. **Go to Render Dashboard**:
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click **"New +"** → **"Web Service"**

2. **Connect GitHub Repository**:
   - Click **"Connect account"** to link GitHub
   - Select your `studysensei` repository
   - Click **"Connect"**

3. **Configure the Service**:
   - **Name**: `studysensei-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

4. **Add Environment Variables**:
   Click **"Advanced"** → **"Add Environment Variable"** and add these:

   | Key | Value | Notes |
   |-----|-------|-------|
   | `SUPABASE_URL` | `your-supabase-url` | From Supabase dashboard |
   | `SUPABASE_ANON_KEY` | `your-anon-key` | From Supabase dashboard |
   | `SUPABASE_SERVICE_ROLE_KEY` | `your-service-role-key` | From Supabase dashboard |
   | `GOOGLE_API_KEY` | `your-gemini-api-key` | Your Google AI API key |
   | `PYTHON_VERSION` | `3.11.0` | Specify Python version |

5. **Deploy**:
   - Click **"Create Web Service"**
   - Wait 5-10 minutes for deployment
   - Note the URL: `https://studysensei-backend.onrender.com`

### Step 1.3: Deploy Code Runner Service

1. **Create Another Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Connect the same GitHub repository

2. **Configure**:
   - **Name**: `studysensei-code-runner`
   - **Root Directory**: `code_runner`
   - **Build Command**: 
     ```bash
     pip install fastapi uvicorn pydantic
     ```
   - **Start Command**: 
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

3. **No Environment Variables Needed** (this service is stateless)

4. **Deploy** and note the URL: `https://studysensei-code-runner.onrender.com`

### Step 1.4: Deploy Background Worker

> **⚠️ Important**: Render's free tier **doesn't support background workers** that run continuously. You have two options:

#### Option A: Skip Worker (Recommended for Free Tier)
- The worker processes document uploads in the background
- Without it, document processing will be slower but still work
- Users might need to refresh to see processed documents

#### Option B: Deploy as Web Service (Workaround)
If you want to deploy the worker:

1. **Modify `worker/worker_main.py`** to add a health endpoint:
   ```python
   # Add at the top
   from fastapi import FastAPI
   import threading
   
   app = FastAPI()
   
   @app.get("/health")
   def health():
       return {"status": "ok"}
   
   # Start worker in background thread
   def start_worker():
       main()
   
   if __name__ == "__main__":
       import uvicorn
       worker_thread = threading.Thread(target=start_worker, daemon=True)
       worker_thread.start()
       uvicorn.run(app, host="0.0.0.0", port=8080)
   ```

2. **Create `worker/requirements.txt`**:
   ```
   fastapi
   uvicorn
   supabase
   python-dotenv
   pypdf
   sentence-transformers
   langchain
   langchain-text-splitters
   ```

3. **Deploy as Web Service**:
   - **Name**: `studysensei-worker`
   - **Root Directory**: `worker`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python worker_main.py`
   - Add same environment variables as backend

---

## Part 2: Frontend Deployment on Vercel

### Step 2.1: Prepare Frontend for Deployment

1. **Create `.env.local` template** in `frontend/` folder:
   ```bash
   # Create a file: frontend/.env.example
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   NEXT_PUBLIC_API_URL=your-backend-url
   NEXT_PUBLIC_CODE_RUNNER_URL=your-code-runner-url
   ```

2. **Update API URLs in your code**:
   
   Check where you're making API calls. You'll need to use environment variables:
   
   ```typescript
   // Instead of hardcoded localhost:
   const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
   const CODE_RUNNER_URL = process.env.NEXT_PUBLIC_CODE_RUNNER_URL || 'http://localhost:8001';
   ```

### Step 2.2: Deploy to Vercel

1. **Go to Vercel Dashboard**:
   - Visit [vercel.com/new](https://vercel.com/new)
   - Click **"Add New Project"**

2. **Import Git Repository**:
   - Click **"Import Git Repository"**
   - Select your GitHub repository
   - Click **"Import"**

3. **Configure Project**:
   - **Framework Preset**: `Next.js` (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

4. **Add Environment Variables**:
   Click **"Environment Variables"** and add:

   | Name | Value |
   |------|-------|
   | `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase Anon Key |
   | `NEXT_PUBLIC_API_URL` | `https://studysensei-backend.onrender.com` |
   | `NEXT_PUBLIC_CODE_RUNNER_URL` | `https://studysensei-code-runner.onrender.com` |

5. **Deploy**:
   - Click **"Deploy"**
   - Wait 2-5 minutes
   - Your app will be live at: `https://your-project.vercel.app`

---

## Part 3: Connecting Everything

### Step 3.1: Update CORS Settings

Your backend needs to allow requests from your Vercel domain.

1. **Update `backend/main.py`**:
   ```python
   # Update CORS middleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",  # Local development
           "https://your-project.vercel.app",  # Your Vercel domain
           "https://*.vercel.app",  # All Vercel preview deployments
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Commit and push**:
   ```bash
   git add backend/main.py
   git commit -m "Update CORS for production"
   git push
   ```

3. **Render will auto-redeploy** (takes 5-10 minutes)

### Step 3.2: Update Supabase Settings

1. **Add Vercel URL to Supabase**:
   - Go to Supabase Dashboard → Authentication → URL Configuration
   - Add your Vercel URL to **Site URL**: `https://your-project.vercel.app`
   - Add to **Redirect URLs**: `https://your-project.vercel.app/**`

### Step 3.3: Test the Connection

1. **Visit your Vercel URL**: `https://your-project.vercel.app`
2. **Try to sign up/login**
3. **Check browser console** for any errors
4. **Test creating a skill** and uploading documents

---

## Troubleshooting

### Issue: "Failed to fetch" errors

**Solution**: 
- Check that `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Verify CORS settings in `backend/main.py`
- Check Render logs: Dashboard → Your Service → Logs

### Issue: Backend service sleeping (Render free tier)

**Problem**: Free tier services sleep after 15 minutes of inactivity

**Solutions**:
1. **Use a ping service**: [UptimeRobot](https://uptimerobot.com) (free) to ping your backend every 5 minutes
2. **Add a warmup endpoint**: Create a lightweight endpoint that wakes up the service
3. **Upgrade to paid tier**: $7/month for always-on services

### Issue: Build fails on Vercel

**Solution**:
- Check build logs in Vercel dashboard
- Ensure all dependencies are in `package.json`
- Try building locally: `npm run build`
- Check for TypeScript errors

### Issue: Environment variables not working

**Solution**:
- Ensure variables start with `NEXT_PUBLIC_` for client-side access
- Redeploy after adding new variables
- Check spelling and case sensitivity

### Issue: Code runner timeout

**Solution**:
- Render free tier has 30-second timeout
- Optimize code execution
- Consider upgrading for longer timeouts

---

## Post-Deployment Checklist

- [ ] Frontend loads successfully
- [ ] User can sign up and log in
- [ ] Can create a new skill
- [ ] Can upload documents (may be slow without worker)
- [ ] Chat functionality works
- [ ] Quiz generation works
- [ ] Code execution works
- [ ] Analytics page displays data
- [ ] All API calls use production URLs
- [ ] CORS is configured correctly
- [ ] Supabase redirect URLs are set
- [ ] Custom domain configured (optional)

---

## 🎯 Quick Reference

### Your Deployed URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `https://your-project.vercel.app` | Main application |
| Backend API | `https://studysensei-backend.onrender.com` | API endpoints |
| Code Runner | `https://studysensei-code-runner.onrender.com` | Code execution |
| Worker | `https://studysensei-worker.onrender.com` | Background tasks |

### Important Commands

```bash
# Redeploy frontend
git push  # Vercel auto-deploys

# Redeploy backend
git push  # Render auto-deploys

# View logs
# Render: Dashboard → Service → Logs
# Vercel: Dashboard → Deployment → Function Logs

# Local testing
npm run dev  # Frontend
uvicorn main:app --reload  # Backend
```

---

## 🔒 Security Notes

1. **Never commit `.env` files** to Git
2. **Use environment variables** for all secrets
3. **Rotate API keys** regularly
4. **Enable Supabase RLS** (Row Level Security)
5. **Monitor usage** to avoid quota overruns

---

## 💰 Cost Breakdown (Free Tier Limits)

| Service | Free Tier Limits |
|---------|------------------|
| Vercel | 100 GB bandwidth/month, unlimited deployments |
| Render | 750 hours/month (enough for 1 service 24/7) |
| Supabase | 500 MB database, 1 GB file storage, 2 GB bandwidth |

**Total Monthly Cost**: $0 🎉

---

## 🚀 Next Steps

1. **Custom Domain**: Add your own domain in Vercel settings
2. **Analytics**: Add Vercel Analytics for usage insights
3. **Monitoring**: Set up error tracking (Sentry free tier)
4. **Performance**: Optimize images and API calls
5. **SEO**: Add meta tags and sitemap

---

## 📞 Need Help?

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)

---

**🎉 Congratulations!** Your StudySensei app is now live and accessible to the world!
