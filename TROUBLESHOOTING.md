# 🔍 Deployment Troubleshooting Guide

Common issues and their solutions when deploying StudySensei.

---

## 🚨 Common Issues

### 1. "Failed to fetch" or CORS Errors

**Symptoms:**
- Browser console shows: `Failed to fetch`
- Or: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solutions:**

#### A. Update Backend CORS Settings
Edit `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # ← Add your Vercel URL
        "https://*.vercel.app",  # ← Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### B. Check Environment Variables
In Vercel dashboard:
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Should be: `https://your-backend.onrender.com` (no trailing slash)

#### C. Wait for Render Redeploy
After updating CORS:
- Render auto-deploys when you push to GitHub
- Wait 5-10 minutes
- Check Render logs to confirm deployment

---

### 2. Render Service is Sleeping

**Symptoms:**
- First request takes 30+ seconds
- Subsequent requests are fast
- Service shows "Sleeping" in Render dashboard

**Why This Happens:**
- Render free tier sleeps after 15 minutes of inactivity
- First request "wakes up" the service

**Solutions:**

#### A. Use UptimeRobot (Recommended)
1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. Create a new monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://your-backend.onrender.com/health`
   - **Interval**: 5 minutes
3. This pings your service every 5 minutes to keep it awake

#### B. Add Health Endpoint
Ensure your backend has a health endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

#### C. Upgrade to Paid Plan
- $7/month for always-on service
- No sleep time
- Better for production apps

---

### 3. Environment Variables Not Working

**Symptoms:**
- `undefined` in API calls
- Features not working in production but work locally

**Solutions:**

#### A. Check Variable Names
Frontend variables MUST start with `NEXT_PUBLIC_`:
- ✅ `NEXT_PUBLIC_API_URL`
- ❌ `API_URL` (won't work in browser)

#### B. Redeploy After Adding Variables
1. Add/update variables in Vercel dashboard
2. Go to Deployments tab
3. Click "..." on latest deployment
4. Click "Redeploy"

#### C. Check for Typos
Common mistakes:
- Extra spaces in values
- Missing `https://`
- Trailing slashes

---

### 4. Build Fails on Vercel

**Symptoms:**
- Deployment fails with build errors
- TypeScript errors in build logs

**Solutions:**

#### A. Test Build Locally
```bash
cd frontend
npm run build
```

Fix any errors that appear.

#### B. Check Dependencies
Ensure all packages are in `package.json`:
```bash
npm install
```

#### C. TypeScript Errors
If TypeScript is too strict, you can temporarily relax it in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": false,  // ← Add this
    // ... other options
  }
}
```

**Better solution**: Fix the TypeScript errors properly.

---

### 5. Supabase Authentication Not Working

**Symptoms:**
- Can't log in or sign up
- Redirect loops
- "Invalid redirect URL" error

**Solutions:**

#### A. Update Supabase URLs
In Supabase Dashboard → Authentication → URL Configuration:

1. **Site URL**: `https://your-app.vercel.app`
2. **Redirect URLs**: Add:
   - `https://your-app.vercel.app/**`
   - `https://your-app.vercel.app/auth/callback`

#### B. Check Environment Variables
In Vercel, verify:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

#### C. Email Confirmation
If using email auth:
- Check Supabase → Authentication → Email Templates
- Ensure confirmation emails are being sent
- Check spam folder

---

### 6. Code Execution Timeout

**Symptoms:**
- Code runner returns timeout error
- Takes longer than 30 seconds

**Solutions:**

#### A. Optimize Code Execution
In `code_runner/main.py`, the timeout is set to 5 seconds:
```python
stdout, stderr = process.communicate(input=input_data, timeout=5)
```

You can increase it, but Render has a 30-second overall timeout.

#### B. Use Async Execution
For longer-running code, consider:
1. Queue the job
2. Return immediately
3. Poll for results

---

### 7. Document Upload Not Working

**Symptoms:**
- Files upload but never process
- Status stays "pending"

**Solutions:**

#### A. Check Worker Status
If you deployed the worker:
- Check Render logs for the worker service
- Ensure environment variables are set

#### B. Worker Not Deployed
If you skipped the worker:
- Documents will stay in "pending" state
- Consider deploying the worker
- Or implement client-side processing

#### C. Check Supabase Storage
- Verify files are actually uploaded to Supabase
- Check storage bucket permissions
- Ensure service role key has access

---

### 8. Slow Performance

**Symptoms:**
- Pages load slowly
- API calls take a long time

**Solutions:**

#### A. Render Cold Starts
- Free tier services sleep
- Use UptimeRobot to keep them awake

#### B. Optimize Images
In Next.js, use the Image component:
```typescript
import Image from 'next/image';

<Image src="/path" alt="..." width={500} height={300} />
```

#### C. Enable Caching
Add caching headers in `next.config.ts`:
```typescript
async headers() {
  return [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=60' },
      ],
    },
  ];
}
```

---

### 9. Database Connection Errors

**Symptoms:**
- "Connection refused" errors
- "Too many connections"

**Solutions:**

#### A. Check Supabase Limits
Free tier limits:
- 500 MB database
- 2 GB bandwidth/month
- Check usage in Supabase dashboard

#### B. Connection Pooling
Ensure you're not creating too many connections:
```python
# Create client once, reuse it
supabase: Client = create_client(url, key)
```

#### C. Upgrade Supabase Plan
If you hit limits, consider upgrading.

---

### 10. API Rate Limiting

**Symptoms:**
- "Too many requests" errors
- 429 status codes

**Solutions:**

#### A. Google Gemini API
Free tier limits:
- 60 requests per minute
- Implement rate limiting in your code

#### B. Supabase API
Free tier limits:
- Check Supabase dashboard for limits
- Implement caching to reduce calls

---

## 🔧 Debugging Tools

### Check Render Logs
```
Dashboard → Your Service → Logs
```

Look for:
- Startup errors
- Runtime errors
- Request logs

### Check Vercel Logs
```
Dashboard → Deployment → Function Logs
```

Look for:
- Build errors
- Runtime errors
- API call failures

### Browser DevTools
Press F12 and check:
- **Console**: JavaScript errors
- **Network**: Failed requests, status codes
- **Application**: Cookies, local storage

### Test API Directly
Use curl or Postman:
```bash
curl https://your-backend.onrender.com/health
```

Should return: `{"status":"ok"}`

---

## 📞 Getting Help

If you're still stuck:

1. **Check Logs**: Render + Vercel logs usually show the issue
2. **Search Error**: Google the exact error message
3. **Check Status Pages**:
   - [Render Status](https://status.render.com)
   - [Vercel Status](https://vercel-status.com)
   - [Supabase Status](https://status.supabase.com)

---

## ✅ Health Check Checklist

Use this to verify everything is working:

- [ ] Backend health endpoint responds: `https://your-backend.onrender.com/health`
- [ ] Code runner responds: `https://your-code-runner.onrender.com/`
- [ ] Frontend loads: `https://your-app.vercel.app`
- [ ] Can sign up new user
- [ ] Can log in
- [ ] Can create skill
- [ ] Can upload document
- [ ] Chat works
- [ ] Quiz generation works
- [ ] Code execution works
- [ ] No errors in browser console
- [ ] No errors in Render logs
- [ ] No errors in Vercel logs

---

**💡 Pro Tip**: Keep this guide handy during deployment. Most issues are quick fixes once you know what to look for!
