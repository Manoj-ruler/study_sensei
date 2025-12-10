# 🔧 API URL Migration Guide

This guide helps you update hardcoded localhost URLs to use the centralized API configuration.

## What Changed?

We created a centralized API configuration file at `frontend/src/config/api.ts` that:
- Uses environment variables for production URLs
- Falls back to localhost for development
- Provides type-safe API endpoint constants

## Files That Need Updates

The following files have hardcoded `http://localhost:8000` URLs:

1. ✅ `frontend/src/app/skills/[id]/roadmap/page.tsx`
2. ✅ `frontend/src/app/skills/[id]/quiz/page.tsx`
3. ✅ `frontend/src/app/skills/[id]/page.tsx`
4. ✅ `frontend/src/app/skills/[id]/coding/page.tsx`
5. ✅ `frontend/src/components/AnalyticsDashboard.tsx`
6. ✅ `frontend/src/app/dashboard/page.tsx`

## How to Update

### Step 1: Import the API configuration

At the top of each file, add:

```typescript
import { API_ENDPOINTS } from '@/config/api';
```

### Step 2: Replace hardcoded URLs

**Before:**
```typescript
const response = await fetch('http://localhost:8000/mentor/message', {
  method: 'POST',
  // ...
});
```

**After:**
```typescript
const response = await fetch(API_ENDPOINTS.MENTOR_MESSAGE, {
  method: 'POST',
  // ...
});
```

## Quick Reference

### Common Replacements

| Old URL | New Constant |
|---------|--------------|
| `'http://localhost:8000/mentor/message'` | `API_ENDPOINTS.MENTOR_MESSAGE` |
| `'http://localhost:8000/documents/upload'` | `API_ENDPOINTS.DOCUMENTS_UPLOAD` |
| `` `http://localhost:8000/documents/${docId}` `` | `API_ENDPOINTS.DOCUMENTS_DELETE(docId)` |
| `'http://localhost:8000/roadmap/generate'` | `API_ENDPOINTS.ROADMAP_GENERATE` |
| `'http://localhost:8000/quiz/generate'` | `API_ENDPOINTS.QUIZ_GENERATE` |
| `'http://localhost:8000/quiz/save'` | `API_ENDPOINTS.QUIZ_SAVE` |
| `` `http://localhost:8000/quiz/history/${id}` `` | `API_ENDPOINTS.QUIZ_HISTORY(id)` |
| `'http://localhost:8000/solver/generate-question'` | `API_ENDPOINTS.SOLVER_GENERATE` |
| `'http://localhost:8000/solver/submit'` | `API_ENDPOINTS.SOLVER_SUBMIT` |
| `` `http://localhost:8000/analytics/skill/${skillId}?user_id=${userId}` `` | `API_ENDPOINTS.ANALYTICS_SKILL(skillId, userId)` |
| `` `http://localhost:8000/skills/${skillId}` `` | `API_ENDPOINTS.SKILLS_DELETE(skillId)` |

## Example: Full File Update

**Before (`dashboard/page.tsx`):**
```typescript
const response = await fetch('http://localhost:8000/documents/upload', {
  method: 'POST',
  body: formData,
});
```

**After:**
```typescript
import { API_ENDPOINTS } from '@/config/api';

// ... later in the code
const response = await fetch(API_ENDPOINTS.DOCUMENTS_UPLOAD, {
  method: 'POST',
  body: formData,
});
```

## Benefits

✅ **Easy Deployment**: Just set environment variables in Vercel
✅ **Type Safety**: TypeScript will catch typos
✅ **Single Source of Truth**: Update URLs in one place
✅ **Development Friendly**: Still works with localhost
✅ **No Code Changes**: Same code works in dev and production

## Testing

After making changes:

1. **Test locally**: Run `npm run dev` and verify everything works
2. **Check console**: No 404 or connection errors
3. **Test all features**: Chat, quiz, coding, analytics, etc.

## Deployment

Once updated, deployment is simple:

1. Push code to GitHub
2. Set environment variables in Vercel:
   - `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`
   - `NEXT_PUBLIC_CODE_RUNNER_URL=https://your-code-runner.onrender.com`
3. Deploy!

---

**Note**: I've created the configuration file for you. You can either:
1. Update the files manually using this guide
2. Ask me to update them for you
3. Update them gradually as you work on each feature
