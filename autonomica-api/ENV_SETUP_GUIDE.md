# Environment Setup Guide

## Overview

The Autonomica API supports multiple environment file configurations with a clear priority order. This allows you to keep sensitive API keys and local development settings separate from your main configuration.

## Environment File Priority

The application loads environment variables in this order (highest to lowest priority):

1. **`.env.local`** - Local development overrides (highest priority)
2. **`.env`** - Default environment configuration
3. **System environment variables** - OS-level variables (lowest priority)

## Why Use `.env.local`?

✅ **Perfect for API keys** - Keep sensitive keys out of version control  
✅ **Local development** - Override settings for your development environment  
✅ **Team collaboration** - Each developer can have their own local config  
✅ **Automatic gitignore** - `.env*` is already excluded from version control  

## Quick Setup

### 1. Copy the example file
```bash
cp env.example .env
```

### 2. Create your local overrides
```bash
# Create .env.local for your personal API keys and settings
touch .env.local
```

### 3. Add your API keys to .env.local
```bash
# .env.local - Local development overrides
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
CLERK_SECRET_KEY=sk_test_your-actual-clerk-key-here

# Local development settings
DEBUG=true
LOG_LEVEL=debug
ENVIRONMENT=development
```

## Required API Keys for LangChain NLP Features

### OpenAI (Required)
- **Purpose**: Core LangChain NLP capabilities (summarization, sentiment analysis, Q&A)
- **Get your key**: https://platform.openai.com/api-keys
- **Variable**: `OPENAI_API_KEY=sk-your-key-here`

### Anthropic (Optional)
- **Purpose**: Alternative LLM provider for enhanced capabilities
- **Get your key**: https://console.anthropic.com/
- **Variable**: `ANTHROPIC_API_KEY=sk-ant-your-key-here`

### Clerk (Required for API endpoints)
- **Purpose**: User authentication for API endpoints
- **Get your key**: https://clerk.com/
- **Variable**: `CLERK_SECRET_KEY=sk_test_your-key-here`

## File Structure

```
autonomica-api/
├── .env.local          # Your personal API keys (gitignored)
├── .env               # Default configuration (committed)
├── env.example        # Template file (committed)
└── app/
    └── main.py        # Loads environment variables
```

## Example Configurations

### .env.local (Personal - Not Committed)
```bash
# API Keys
OPENAI_API_KEY=sk-proj-abc123...
ANTHROPIC_API_KEY=sk-ant-xyz789...
CLERK_SECRET_KEY=sk_test_def456...

# Development Settings
DEBUG=true
LOG_LEVEL=debug
ENVIRONMENT=development
RATE_LIMIT_PER_MINUTE=1000

# Local Database
DATABASE_URL=sqlite:///./autonomica_local.db
```

### .env (Shared - Committed)
```bash
# Server Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Placeholder values (real values go in .env.local)
OPENAI_API_KEY=your_openai_api_key_here
CLERK_SECRET_KEY=your_clerk_secret_key_here

# Shared configuration
MAX_AGENTS=10
AGENT_TIMEOUT_SECONDS=300
```

## Testing Your Setup

### 1. Check environment loading
```bash
cd autonomica-api
python -c "
import os
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
print('DEBUG:', os.getenv('DEBUG', 'NOT SET'))
"
```

### 2. Test LangChain integration
```bash
# Run the API server
python -m uvicorn app.main:app --reload

# Check the health endpoint
curl http://localhost:8000/api/health
```

### 3. Verify NLP capabilities
```bash
# Check available NLP capabilities
curl http://localhost:8000/api/nlp/capabilities
```

## Security Best Practices

### ✅ DO
- Use `.env.local` for all API keys and secrets
- Keep `.env.local` out of version control (already configured)
- Use different API keys for development vs production
- Regularly rotate your API keys

### ❌ DON'T
- Commit real API keys to version control
- Share your `.env.local` file
- Use production API keys in development
- Hard-code API keys in source code

## Troubleshooting

### API Keys Not Working
1. Check if `.env.local` exists and contains your keys
2. Verify key format (starts with `sk-` for OpenAI)
3. Ensure no extra spaces around the `=` sign
4. Restart the server after changing environment files

### Environment Variables Not Loading
1. Verify file is named exactly `.env.local` (not `.env.local.txt`)
2. Check file is in the `autonomica-api` directory (same as `app/`)
3. Ensure proper format: `KEY=value` (no spaces around `=`)

### LangChain Features Not Working
1. Verify `OPENAI_API_KEY` is set in `.env.local`
2. Check API key has sufficient credits
3. Test with a simple API call outside the application

## Production Deployment

For production environments:

1. **Use system environment variables** or secure secret management
2. **Don't use `.env.local`** in production
3. **Set environment variables** through your deployment platform
4. **Use production API keys** with appropriate rate limits

```bash
# Example production environment variables
export OPENAI_API_KEY="sk-prod-key-here"
export CLERK_SECRET_KEY="sk_live_key_here"
export ENVIRONMENT="production"
export DEBUG="false"
```

## Summary

The `.env.local` approach gives you:
- 🔒 **Security**: API keys never committed to version control
- 🛠️ **Flexibility**: Easy local development configuration
- 👥 **Team-friendly**: Each developer has their own settings
- 🚀 **Production-ready**: Clear separation of environments

Your LangChain NLP capabilities are now ready to use with proper environment configuration! 