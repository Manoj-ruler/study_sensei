# 🔧 Fix: Render "Service Root Directory is missing" Error

## The Problem

You're getting this error:
```
Service Root Directory "/opt/render/project/src/backend" is missing.
```

This happens because Render is looking in the wrong path. Your GitHub repository structure doesn't match what Render expects.

## The Solution

You need to update the **Root Directory** setting in Render to match your actual repository structure.

---

## Step-by-Step Fix

### Option 1: Update Root Directory in Render Dashboard (Easiest)

1. **Go to your Render service**:
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click on your `studysensei-backend` service

2. **Update the Root Directory**:
   - Click **"Settings"** (left sidebar)
   - Scroll to **"Build & Deploy"** section
   - Find **"Root Directory"** field
   - Change it based on your repo structure:

   **If your GitHub repo looks like this:**
   ```
   StudySensei/
   ├── backend/
   ├── frontend/
   ├── code_runner/
   └── worker/
   ```
   **Set Root Directory to:** `backend`

   **If your GitHub repo has everything in root:**
   ```
   StudySensei/
   ├── main.py
   ├── requirements.txt
   ├── routers/
   └── ...
   ```
   **Set Root Directory to:** (leave blank or put `.`)

3. **Save and Redeploy**:
   - Click **"Save Changes"**
   - Render will automatically redeploy
   - Wait 5-10 minutes

---

### Option 2: Check Your GitHub Repository Structure

1. **Visit your GitHub repo**: https://github.com/Manoj-ruler/StudySensei

2. **Check the structure**:
   - Are the folders `backend`, `frontend`, etc. visible in the root?
   - Or are all the Python files directly in the root?

3. **Based on what you see**:

   **Scenario A: Folders are visible (backend, frontend, etc.)**
   - Root Directory should be: `backend`
   - This is the correct structure ✅

   **Scenario B: All files are in root (no backend folder)**
   - Root Directory should be: `.` or leave blank
   - Your repo structure needs fixing ❌

---

### Option 3: Fix Your Repository Structure (If Needed)

If you accidentally pushed everything to the root, here's how to fix it:

1. **Check your local folder structure**:
   ```bash
   cd c:\Users\manoj\OneDrive\Desktop\bluconn
   dir
   ```
   
   You should see:
   - `backend/` folder
   - `frontend/` folder
   - `code_runner/` folder
   - `worker/` folder

2. **If the structure is correct locally**, the issue is with how you pushed to GitHub.

3. **Re-push with correct structure**:
   ```bash
   # Make sure you're in the bluconn directory
   cd c:\Users\manoj\OneDrive\Desktop\bluconn
   
   # Check what's being tracked
   git status
   
   # If needed, remove and re-add
   git rm -r --cached .
   git add .
   git commit -m "Fix repository structure"
   git push -f origin main
   ```

---

## Quick Fix Commands

### For Render Settings:

1. **Backend Service**:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Code Runner Service**:
   - Root Directory: `code_runner`
   - Build Command: `pip install fastapi uvicorn pydantic`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Worker Service** (if deployed):
   - Root Directory: `worker`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python worker_main.py`

---

## Verify Your GitHub Structure

Visit: https://github.com/Manoj-ruler/StudySensei

You should see this structure:
```
StudySensei/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── routers/
├── frontend/
│   ├── package.json
│   ├── src/
│   └── ...
├── code_runner/
│   └── main.py
├── worker/
│   └── worker_main.py
├── DEPLOYMENT_GUIDE.md
└── README.md
```

---

## Still Not Working?

### Check Render Logs

1. Go to Render Dashboard
2. Click your service
3. Click "Logs" tab
4. Look for the exact error

### Common Issues:

**Error: "No such file or directory"**
- Root Directory is wrong
- Fix: Update in Render settings

**Error: "requirements.txt not found"**
- Root Directory doesn't contain requirements.txt
- Fix: Verify file exists in the correct folder

**Error: "main.py not found"**
- Root Directory doesn't contain main.py
- Fix: Check your repository structure

---

## What to Do Right Now

1. ✅ **Visit your GitHub repo**: https://github.com/Manoj-ruler/StudySensei
2. ✅ **Check if you see `backend/` folder** in the root
3. ✅ **Go to Render Dashboard** → Your Service → Settings
4. ✅ **Set Root Directory to `backend`**
5. ✅ **Save and wait for redeploy**

---

## Need More Help?

Share a screenshot of:
1. Your GitHub repository main page
2. The Render error logs

This will help diagnose the exact issue!

---

**Quick Answer**: Set **Root Directory** to `backend` in Render settings and save. That should fix it! 🚀
