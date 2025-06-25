# Autonomica Worker Pod 🐳

Docker-based background task processor for the Autonomica platform.

## Features

- ✅ **FastAPI Health Checks** - Monitoring and health endpoints
- ✅ **Redis Integration** - Task queue and caching support
- ✅ **Vercel KV Support** - Production-ready Redis alternative
- ✅ **Web Scraping Ready** - Playwright integration for browser automation
- ✅ **Background Tasks** - Celery integration for async processing
- ✅ **Railway Deployment** - Production deployment configuration
- ✅ **Docker Compose** - Local development environment

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd autonomica-worker
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access services**:
   - Worker Health Check: http://localhost:8080/health
   - Celery Flower: http://localhost:5555
   - Redis: localhost:6379

### Railway Deployment

1. **Connect to Railway**:
   ```bash
   railway login
   railway link
   ```

2. **Set environment variables** in Railway dashboard:
   ```
   REDIS_URL=redis://your-redis-url
   OPENAI_API_KEY=your-key
   CLERK_SECRET_KEY=your-key
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

## Architecture

```
┌─ Main API (Vercel) ─┐    ┌─ Worker Pod (Railway) ─┐
│  • FastAPI + venv   │ ←→ │  • Docker container    │
│  • Chat endpoints   │    │  • Background tasks    │
│  • Authentication   │    │  • Web scraping        │
│  • Redis client     │    │  • Heavy processing    │
└─────────────────────┘    └────────────────────────┘
```

## Environment Variables

See `.env.example` for all configuration options.

## Health Monitoring

The worker exposes a health check endpoint at `/health` that returns:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "worker_name": "autonomica-worker",
  "redis_connected": true
}
```

## Task Types

- **Web Scraping** - Playwright-based browser automation
- **AI Processing** - OpenAI/Anthropic API integration
- **Data Analysis** - Background data processing
- **Social Media** - Publishing to social platforms

## Development

```bash
# Build image
docker build -t autonomica-worker .

# Run standalone
docker run -p 8080:8080 autonomica-worker

# Run with environment
docker run --env-file .env -p 8080:8080 autonomica-worker
```
