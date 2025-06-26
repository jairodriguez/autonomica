# 🚀 Autonomica Deployment Guide

## Overview

This guide covers deploying your **Autonomica OWL Multi-Agent System** to production with real AI integration.

## 🎯 Current vs Production Setup

### **Current Setup (Development/Mock)**
- ✅ **Simple Mock AI**: Fast responses from predefined arrays
- ✅ **Local URLs**: `localhost:8000` and `localhost:3001`
- ✅ **No API Keys Required**: Works immediately for testing

### **Production Setup (Real AI)**
- 🤖 **Real AI Integration**: OpenAI GPT or Anthropic Claude
- 🌐 **Environment URLs**: Automatic detection of deployment platform
- 🔐 **API Keys Required**: Real AI provider credentials

---

## 🏗️ Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │     │                     │
│  Frontend (Next.js) │────▶│  Backend (FastAPI)  │────▶│   AI Provider      │
│                     │     │                     │     │                     │
│  - Chat Interface   │     │  - OWL Framework    │     │  - OpenAI GPT      │
│  - Dashboard        │     │  - Multi-Agent      │     │  - Anthropic Claude │
│  - Real-time UI     │     │  - Streaming API    │     │  - Custom Models    │
│                     │     │                     │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
       Vercel                      Railway/Heroku              External API
```

---

## 📋 Prerequisites

### **1. AI Provider Account**
Choose one:
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/

### **2. Deployment Platforms**
- **Frontend**: Vercel (recommended) or Netlify
- **Backend**: Railway, Heroku, or AWS

---

## 🔧 Step 1: Backend Deployment

### **Option A: Railway (Recommended)**

1. **Create Railway Account**: https://railway.app
2. **Connect GitHub Repository**
3. **Deploy Backend**:
   ```bash
   cd autonomica-api
   railway login
   railway init
   railway add
   ```

4. **Set Environment Variables** in Railway Dashboard:
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   AI_MODEL=gpt-3.5-turbo
   FRONTEND_URL=https://your-frontend.vercel.app
   RESPONSE_DELAY=0.15
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

### **Option B: Heroku**

1. **Create Heroku App**:
   ```bash
   cd autonomica-api
   heroku create your-autonomica-api
   ```

2. **Set Environment Variables**:
   ```bash
   heroku config:set AI_PROVIDER=openai
   heroku config:set OPENAI_API_KEY=sk-your-key-here
   heroku config:set AI_MODEL=gpt-3.5-turbo
   heroku config:set FRONTEND_URL=https://your-frontend.vercel.app
   ```

3. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy production API"
   git push heroku main
   ```

---

## 🌐 Step 2: Frontend Deployment

### **Vercel (Recommended)**

1. **Connect GitHub to Vercel**: https://vercel.com
2. **Import Project**: Select `autonomica-frontend` folder
3. **Set Environment Variables** in Vercel Dashboard:
   ```env
   NEXT_PUBLIC_API_URL=https://your-api.railway.app
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_key
   CLERK_SECRET_KEY=sk_test_your_clerk_secret
   ```

4. **Deploy**: Vercel auto-deploys on git push

### **Manual Deployment**

1. **Build Frontend**:
   ```bash
   cd autonomica-frontend
   npm run build
   npm start
   ```

---

## 🔐 Step 3: API Keys Setup

### **OpenAI Setup**
1. **Get API Key**: https://platform.openai.com/api-keys
2. **Add Billing**: Add payment method for usage
3. **Set Usage Limits**: Recommended $50/month limit

### **Anthropic Setup**
1. **Get API Key**: https://console.anthropic.com/
2. **Add Credits**: Purchase Claude API credits
3. **Update Environment**:
   ```env
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

---

## 🧪 Step 4: Test Production System

### **Health Check**
```bash
curl https://your-api.railway.app/api/health
```

### **AI Chat Test**
```bash
curl -X POST https://your-api.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "id": "1",
        "role": "user", 
        "content": "Create a marketing strategy for a new SaaS product",
        "timestamp": "2024-01-01T00:00:00Z"
      }
    ],
    "agentContext": {}
  }'
```

### **Frontend Test**
1. **Visit**: https://your-frontend.vercel.app
2. **Sign In**: Test Clerk authentication
3. **Chat**: Send message and verify real AI response
4. **Dashboard**: Check all tabs load correctly

---

## 🔄 Step 5: Switch to Production API

### **Update Current Backend**

If you want to test real AI locally first:

1. **Install Dependencies**:
   ```bash
   cd autonomica-api
   pip install httpx  # For AI API calls
   ```

2. **Create `.env` File**:
   ```bash
   cp env.production.example .env
   # Edit .env with your API keys
   ```

3. **Run Production API**:
   ```bash
   python production_owl_api.py
   ```

4. **Test Locally**:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3001

---

## 🐛 Troubleshooting

### **Common Issues**

**❌ "AI Provider not configured"**
```bash
# Check environment variables
echo $OPENAI_API_KEY
# Verify in deployment dashboard
```

**❌ "CORS Error"**
```bash
# Update FRONTEND_URL in backend environment
FRONTEND_URL=https://your-actual-frontend-url.vercel.app
```

**❌ "500 Internal Server Error"**
```bash
# Check backend logs
railway logs
# or
heroku logs --tail
```

**❌ "Chat not working"**
```bash
# Test API directly
curl -X POST your-api-url/api/chat -H "Content-Type: application/json" -d '{"messages":[{"id":"1","role":"user","content":"test","timestamp":"2024-01-01T00:00:00Z"}],"agentContext":{}}'
```

---

## 💰 Cost Estimates

### **OpenAI Costs**
- **GPT-3.5-turbo**: ~$0.002 per 1K tokens
- **GPT-4**: ~$0.03 per 1K tokens
- **Estimated**: $10-50/month for moderate usage

### **Deployment Costs**
- **Vercel**: Free tier (sufficient for most apps)
- **Railway**: $5/month (includes database)
- **Heroku**: $7/month (basic dyno)

### **Total Monthly Cost**
- **Development**: $0 (mock AI)
- **Production**: $15-60/month (AI + hosting)

---

## 🚀 Go Live Checklist

- [ ] ✅ **Backend deployed** with real AI integration
- [ ] ✅ **Frontend deployed** with environment configuration
- [ ] ✅ **API keys configured** and working
- [ ] ✅ **CORS configured** for your domain
- [ ] ✅ **Health checks passing**
- [ ] ✅ **Chat functionality tested**
- [ ] ✅ **Authentication working**
- [ ] ✅ **Dashboard loading**
- [ ] ✅ **Real AI responses confirmed**

---

## 🔧 Environment Variables Reference

### **Backend (.env)**
```env
# Required
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
FRONTEND_URL=https://your-frontend.vercel.app

# Optional
AI_MODEL=gpt-3.5-turbo
RESPONSE_DELAY=0.1
MAX_TOKENS=1000
API_HOST=0.0.0.0
API_PORT=8000
```

### **Frontend (.env.local)**
```env
# Required
NEXT_PUBLIC_API_URL=https://your-api.railway.app
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key

# Optional
CLERK_SECRET_KEY=sk_test_your_secret
```

---

## 🎉 Success!

Once deployed, you'll have a **production-ready Autonomica system** with:

- 🤖 **Real AI**: OpenAI GPT or Anthropic Claude
- ⚡ **Fast Responses**: Optimized streaming
- 🔐 **Secure Auth**: Clerk authentication
- 📊 **Analytics**: Real-time metrics
- 🌐 **Global Access**: Available worldwide
- 📱 **Mobile Ready**: Responsive design

**Your Autonomica app is now live and ready for users!** 🚀 