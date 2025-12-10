# 🚀 Quick Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment

- [ ] Code is working locally (frontend + backend)
- [ ] All environment variables documented
- [ ] Supabase project is set up and working
- [ ] Google Gemini API key obtained
- [ ] GitHub account created
- [ ] Render account created (render.com)
- [ ] Vercel account created (vercel.com)

## Step 1: Push to GitHub

- [ ] Git repository initialized
- [ ] Created GitHub repository (public)
- [ ] Pushed code to GitHub
- [ ] Verified all files are uploaded

## Step 2: Deploy Backend to Render

### Main Backend API
- [ ] Created web service on Render
- [ ] Connected GitHub repository
- [ ] Set root directory to `backend`
- [ ] Set build command: `pip install -r requirements.txt`
- [ ] Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Added environment variables:
  - [ ] SUPABASE_URL
  - [ ] SUPABASE_ANON_KEY
  - [ ] SUPABASE_SERVICE_ROLE_KEY
  - [ ] GOOGLE_API_KEY
  - [ ] PYTHON_VERSION (3.11.0)
- [ ] Deployment successful
- [ ] Copied backend URL: `_______________________________`

### Code Runner Service
- [ ] Created second web service on Render
- [ ] Set root directory to `code_runner`
- [ ] Set build command: `pip install fastapi uvicorn pydantic`
- [ ] Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Deployment successful
- [ ] Copied code runner URL: `_______________________________`

### Worker Service (Optional)
- [ ] Decided to deploy worker (yes/no)
- [ ] If yes, created third web service
- [ ] Deployment successful
- [ ] Copied worker URL: `_______________________________`

## Step 3: Update Backend CORS

- [ ] Updated `backend/main.py` with Vercel domain
- [ ] Committed and pushed changes
- [ ] Render auto-redeployed

## Step 4: Deploy Frontend to Vercel

- [ ] Opened Vercel dashboard
- [ ] Imported GitHub repository
- [ ] Set root directory to `frontend`
- [ ] Added environment variables:
  - [ ] NEXT_PUBLIC_SUPABASE_URL
  - [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY
  - [ ] NEXT_PUBLIC_API_URL (Render backend URL)
  - [ ] NEXT_PUBLIC_CODE_RUNNER_URL (Render code runner URL)
- [ ] Deployment successful
- [ ] Copied Vercel URL: `_______________________________`

## Step 5: Configure Supabase

- [ ] Added Vercel URL to Supabase Site URL
- [ ] Added Vercel URL to Redirect URLs
- [ ] Tested authentication

## Step 6: Testing

- [ ] Frontend loads without errors
- [ ] Can sign up new user
- [ ] Can log in
- [ ] Can create a skill
- [ ] Can upload documents
- [ ] Chat works
- [ ] Quiz generation works
- [ ] Code execution works
- [ ] Analytics displays

## Step 7: Post-Deployment

- [ ] Set up UptimeRobot to prevent Render sleep
- [ ] Added custom domain (optional)
- [ ] Configured analytics (optional)
- [ ] Shared app with friends/testers

## Troubleshooting

If something doesn't work:

1. **Check Render Logs**: Dashboard → Service → Logs
2. **Check Vercel Logs**: Dashboard → Deployment → Function Logs
3. **Check Browser Console**: F12 → Console tab
4. **Verify Environment Variables**: Make sure all are set correctly
5. **Check CORS**: Ensure backend allows your Vercel domain

## Important URLs

| Service | URL |
|---------|-----|
| GitHub Repo | https://github.com/____________/____________ |
| Backend API | https://__________________________________ |
| Code Runner | https://__________________________________ |
| Worker | https://__________________________________ |
| Frontend | https://__________________________________ |
| Supabase | https://__________________________________ |

## Notes

Add any deployment notes or issues you encountered:

_______________________________________________________________

_______________________________________________________________

_______________________________________________________________

---

**🎉 Deployment Complete!** Share your app: `https://your-app.vercel.app`
