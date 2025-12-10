# 📚 Deployment Documentation - Quick Start

Welcome! This folder contains everything you need to deploy StudySensei to production for **FREE**.

## 📖 Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** | Complete step-by-step deployment guide | Start here - read this first! |
| **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** | Track your deployment progress | Use while deploying |
| **[API_MIGRATION_GUIDE.md](./API_MIGRATION_GUIDE.md)** | Update hardcoded URLs for production | Before deploying frontend |
| **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** | Fix common deployment issues | When something goes wrong |
| **[render.yaml](./render.yaml)** | Render blueprint configuration | Optional: one-click deploy |
| **[frontend/env.template](./frontend/env.template)** | Environment variables template | Reference for Vercel setup |

---

## 🚀 Quick Start (5 Steps)

### 1️⃣ Read the Main Guide
Open **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** and read through it once.

### 2️⃣ Prepare Your Code
- [ ] Update API URLs using **[API_MIGRATION_GUIDE.md](./API_MIGRATION_GUIDE.md)**
- [ ] Push code to GitHub
- [ ] Get your Supabase credentials ready

### 3️⃣ Deploy Backend (Render)
- [ ] Create 2-3 web services on Render
- [ ] Set environment variables
- [ ] Wait for deployment
- [ ] Save the URLs

### 4️⃣ Deploy Frontend (Vercel)
- [ ] Import GitHub repo to Vercel
- [ ] Set environment variables (use backend URLs from step 3)
- [ ] Deploy
- [ ] Save the URL

### 5️⃣ Connect & Test
- [ ] Update CORS in backend
- [ ] Update Supabase redirect URLs
- [ ] Test all features
- [ ] 🎉 You're live!

Use **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** to track progress.

---

## 🎯 What You'll Deploy

```
┌─────────────────────────────────────────┐
│         Vercel (Frontend)               │
│  https://your-app.vercel.app            │
│  - Next.js application                  │
│  - User interface                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      Render (Backend Services)          │
│                                         │
│  1. Main API                            │
│     https://backend.onrender.com        │
│     - Chat, Quiz, Analytics             │
│                                         │
│  2. Code Runner                         │
│     https://code-runner.onrender.com    │
│     - Execute user code                 │
│                                         │
│  3. Worker (Optional)                   │
│     https://worker.onrender.com         │
│     - Process documents                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│       Supabase (Database)               │
│  - PostgreSQL database                  │
│  - Authentication                       │
│  - File storage                         │
└─────────────────────────────────────────┘
```

---

## 💰 Cost

**Total: $0/month** 🎉

All services use free tiers:
- ✅ Vercel: Free (100 GB bandwidth)
- ✅ Render: Free (750 hours/month)
- ✅ Supabase: Free (500 MB database)

---

## ⏱️ Time Required

- **First-time deployment**: 1-2 hours
- **Subsequent deployments**: 5-10 minutes (auto-deploy on git push)

---

## 🔑 What You Need

Before starting, gather:

1. **GitHub Account** (to host code)
2. **Render Account** (for backend)
3. **Vercel Account** (for frontend)
4. **Supabase Credentials**:
   - Supabase URL
   - Anon Key
   - Service Role Key
5. **Google Gemini API Key** (for AI features)

---

## 📋 Deployment Order

**Important**: Deploy in this order!

1. ✅ Push code to GitHub
2. ✅ Deploy backend to Render (get URLs)
3. ✅ Deploy frontend to Vercel (use backend URLs)
4. ✅ Update CORS in backend
5. ✅ Update Supabase settings
6. ✅ Test everything

---

## 🆘 Need Help?

1. **Something not working?** → Check **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**
2. **Forgot a step?** → Use **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)**
3. **API errors?** → See **[API_MIGRATION_GUIDE.md](./API_MIGRATION_GUIDE.md)**
4. **General questions?** → Re-read **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

---

## 🎓 Learning Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## ✨ After Deployment

Once deployed, consider:

1. **Custom Domain**: Add your own domain in Vercel
2. **Monitoring**: Set up UptimeRobot to prevent Render sleep
3. **Analytics**: Add Vercel Analytics
4. **Error Tracking**: Set up Sentry (free tier)
5. **Performance**: Optimize images and API calls

---

## 🔄 Updating Your App

After initial deployment, updates are automatic:

```bash
# Make changes to your code
git add .
git commit -m "Your changes"
git push

# Vercel and Render will auto-deploy!
```

---

## 📊 Monitoring

Keep an eye on:

- **Vercel Dashboard**: Deployment status, errors
- **Render Dashboard**: Service health, logs
- **Supabase Dashboard**: Database usage, storage

---

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ Frontend loads without errors
- ✅ Users can sign up and log in
- ✅ Can create skills and upload documents
- ✅ Chat, quiz, and coding features work
- ✅ Analytics displays correctly
- ✅ No errors in browser console
- ✅ No errors in server logs

---

## 🚀 Ready to Deploy?

1. Open **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**
2. Follow the steps carefully
3. Use the checklist to track progress
4. Refer to troubleshooting if needed

**Good luck! You've got this! 💪**

---

## 📝 Notes

- Keep your environment variables secure
- Never commit `.env` files to Git
- Test locally before deploying
- Read error messages carefully
- Check logs when debugging

---

**Made with ❤️ for StudySensei**
