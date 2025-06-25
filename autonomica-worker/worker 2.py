#!/usr/bin/env python3
"""
Autonomica Worker Pod - Background Task Processor
Handles long-running tasks, web scraping, and AI agent operations
"""

import os
import sys
import asyncio
import signal
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import time

# Core imports
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from loguru import logger

# Background task processing
from celery import Celery
from celery.result import AsyncResult

# Web scraping
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup

# Environment and config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class WorkerConfig:
    """Worker configuration from environment variables"""
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    KV_REST_API_URL = os.getenv("KV_REST_API_URL")  # Vercel KV
    KV_REST_API_TOKEN = os.getenv("KV_REST_API_TOKEN")  # Vercel KV
    
    # Worker Configuration
    WORKER_NAME = os.getenv("WORKER_NAME", "autonomica-worker")
    WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
    
    # AI API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # External APIs
    SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")
    
    # Authentication
    CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Health check
    HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", "8080"))

config = WorkerConfig()

# Setup enhanced logging
logger.remove()
logger.add(
    sys.stdout,
    level=config.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Initialize Celery for background tasks
celery_app = Celery(
    config.WORKER_NAME,
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    include=['worker.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_routes={
        'worker.web_scraping': {'queue': 'web_scraping'},
        'worker.ai_processing': {'queue': 'ai_processing'},
        'worker.data_analysis': {'queue': 'data_analysis'},
        'worker.social_media': {'queue': 'social_media'},
    }
)

# Redis client setup
def get_redis_client():
    """Get Redis client with connection handling"""
    try:
        if config.KV_REST_API_URL and config.KV_REST_API_TOKEN:
            logger.info("Using Vercel KV for Redis operations")
            return VercelKVClient(config.KV_REST_API_URL, config.KV_REST_API_TOKEN)
        else:
            logger.info(f"Connecting to Redis at {config.REDIS_URL}")
            client = redis.from_url(config.REDIS_URL, decode_responses=True)
            client.ping()  # Test connection
            return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

class VercelKVClient:
    """Simple Vercel KV REST API client for basic operations"""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get(self, key: str):
        """Get value by key"""
        try:
            response = requests.get(f"{self.url}/get/{key}", headers=self.headers)
            return response.json().get('result') if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"KV get error: {e}")
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set key-value pair"""
        try:
            data = {'value': value}
            if ex:
                data['ex'] = ex
            response = requests.post(f"{self.url}/set/{key}", headers=self.headers, json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"KV set error: {e}")
            return False
    
    def ping(self):
        """Health check"""
        try:
            response = requests.get(f"{self.url}/get/health_check", headers=self.headers)
            return response.status_code in [200, 404]  # 404 is ok for missing key
        except:
            return False

# Initialize Redis client
redis_client = get_redis_client()

# FastAPI app for health checks and monitoring
app = FastAPI(
    title="Autonomica Worker Pod",
    description="Background task processor for Autonomica platform",
    version="1.0.0"
)

# Pydantic models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    worker_name: str
    redis_connected: bool
    active_tasks: int

class TaskRequest(BaseModel):
    """Background task request model"""
    task_type: str
    payload: Dict[str, Any]
    priority: str = "normal"
    user_id: Optional[str] = None

class TaskResponse(BaseModel):
    """Task submission response"""
    task_id: str
    task_type: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

# Background Task Queue Processing
class TaskQueueProcessor:
    """Process tasks from the Redis queue"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.running = True
    
    async def process_queue(self):
        """Main queue processing loop"""
        logger.info("🚀 Starting task queue processor")
        
        while self.running:
            try:
                # Process tasks from different user queues
                await self._process_user_tasks()
                await asyncio.sleep(1)  # Brief pause between cycles
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)  # Longer pause on error
    
    async def _process_user_tasks(self):
        """Process tasks from user-specific queues"""
        if not self.redis_client:
            return
            
        try:
            # Scan for user task queues (pattern: user:*:tasks)
            if hasattr(self.redis_client, 'scan_iter'):
                for key in self.redis_client.scan_iter(match="user:*:tasks"):
                    # Get next task from user queue
                    task_data = self.redis_client.lpop(key)
                    if task_data:
                        await self._handle_task(json.loads(task_data))
        except Exception as e:
            logger.error(f"Error processing user tasks: {e}")
    
    async def _handle_task(self, task_data: dict):
        """Handle individual task"""
        try:
            task_type = task_data.get('task_type')
            payload = task_data.get('payload', {})
            user_id = task_data.get('user_id')
            
            logger.info(f"Processing task: {task_type} for user: {user_id}")
            
            # Route task to appropriate Celery worker
            task_map = {
                "web_scraping": scrape_website_task,
                "ai_processing": process_ai_task,
                "data_analysis": analyze_data_task,
                "social_media": publish_social_media_task
            }
            
            task_func = task_map.get(task_type)
            if task_func:
                # Submit to Celery
                result = task_func.delay(payload, user_id)
                logger.info(f"Submitted {task_type} to Celery with ID: {result.id}")
            else:
                logger.warning(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Task handling error: {e}")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    redis_connected = False
    active_tasks = 0
    
    try:
        if redis_client:
            # Test Redis connection
            if hasattr(redis_client, 'ping'):
                redis_client.ping()
                redis_connected = True
            
            # Get active task count (approximate)
            try:
                inspect = celery_app.control.inspect()
                active = inspect.active() or {}
                active_tasks = sum(len(tasks) for tasks in active.values())
            except:
                pass
                
    except Exception as e:
        logger.warning(f"Health check Redis connection failed: {e}")
    
    return HealthResponse(
        status="healthy" if redis_connected else "degraded",
        timestamp=datetime.utcnow(),
        worker_name=config.WORKER_NAME,
        redis_connected=redis_connected,
        active_tasks=active_tasks
    )

@app.post("/tasks/submit", response_model=TaskResponse)
async def submit_task(task_request: TaskRequest):
    """Submit a background task for processing"""
    try:
        # Route task based on type
        task_map = {
            "web_scraping": scrape_website_task,
            "ai_processing": process_ai_task,
            "data_analysis": analyze_data_task,
            "social_media": publish_social_media_task
        }
        
        task_func = task_map.get(task_request.task_type)
        if not task_func:
            raise HTTPException(status_code=400, detail=f"Unknown task type: {task_request.task_type}")
        
        # Submit task to Celery
        result = task_func.delay(task_request.payload, task_request.user_id)
        
        logger.info(f"Submitted task {task_request.task_type} with ID {result.id}")
        
        return TaskResponse(
            task_id=result.id,
            task_type=task_request.task_type,
            status="submitted",
            message="Task submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a submitted task"""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=result.status.lower()
        )
        
        if result.ready():
            if result.successful():
                response.result = result.result
            else:
                response.error = str(result.info)
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# CELERY TASKS
# =============================================================================

@celery_app.task(bind=True, name='worker.scrape_website')
def scrape_website_task(self, payload: Dict[str, Any], user_id: Optional[str] = None):
    """Web scraping task using Playwright"""
    try:
        url = payload.get('url')
        if not url:
            raise ValueError("URL is required for web scraping")
        
        logger.info(f"Starting web scraping for URL: {url}")
        
        # Use asyncio to run the async scraping function
        result = asyncio.run(scrape_with_playwright(url, payload))
        
        logger.info(f"Web scraping completed for URL: {url}")
        return result
        
    except Exception as e:
        logger.error(f"Web scraping task failed: {e}")
        self.retry(countdown=60, max_retries=3)

async def scrape_with_playwright(url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Perform web scraping using Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to URL
            await page.goto(url, wait_until='networkidle')
            
            # Extract data based on options
            result = {
                'url': url,
                'title': await page.title(),
                'content': await page.content(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Custom selectors if provided
            if 'selectors' in options:
                for selector_name, selector in options['selectors'].items():
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            result[selector_name] = await element.text_content()
                    except Exception as e:
                        logger.warning(f"Selector {selector_name} failed: {e}")
            
            return result
            
        finally:
            await browser.close()

@celery_app.task(bind=True, name='worker.process_ai')
def process_ai_task(self, payload: Dict[str, Any], user_id: Optional[str] = None):
    """AI processing task"""
    try:
        task_type = payload.get('type', 'completion')
        
        logger.info(f"Starting AI processing task: {task_type}")
        
        # Route to appropriate AI processing function
        if task_type == 'completion':
            result = process_ai_completion(payload)
        elif task_type == 'analysis':
            result = process_ai_analysis(payload)
        else:
            raise ValueError(f"Unknown AI task type: {task_type}")
        
        logger.info(f"AI processing completed: {task_type}")
        return result
        
    except Exception as e:
        logger.error(f"AI processing task failed: {e}")
        self.retry(countdown=60, max_retries=3)

def process_ai_completion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process AI completion request"""
    # Implementation would depend on the specific AI provider and task
    return {
        'status': 'completed',
        'result': 'AI completion result placeholder',
        'timestamp': datetime.utcnow().isoformat()
    }

def process_ai_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process AI analysis request"""
    # Implementation would depend on the specific analysis type
    return {
        'status': 'completed',
        'result': 'AI analysis result placeholder',
        'timestamp': datetime.utcnow().isoformat()
    }

@celery_app.task(bind=True, name='worker.analyze_data')
def analyze_data_task(self, payload: Dict[str, Any], user_id: Optional[str] = None):
    """Data analysis task"""
    try:
        logger.info("Starting data analysis task")
        
        # Placeholder for data analysis logic
        result = {
            'status': 'completed',
            'analysis': 'Data analysis completed',
            'metrics': payload.get('metrics', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Data analysis completed")
        return result
        
    except Exception as e:
        logger.error(f"Data analysis task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name='worker.publish_social_media')
def publish_social_media_task(self, payload: Dict[str, Any], user_id: Optional[str] = None):
    """Social media publishing task"""
    try:
        platform = payload.get('platform')
        content = payload.get('content')
        
        logger.info(f"Publishing to {platform}")
        
        # Placeholder for social media publishing logic
        result = {
            'status': 'published',
            'platform': platform,
            'content_length': len(content) if content else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Published to {platform}")
        return result
        
    except Exception as e:
        logger.error(f"Social media publishing failed: {e}")
        self.retry(countdown=60, max_retries=3)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Graceful shutdown handler
class GracefulShutdown:
    """Handle graceful shutdown of the worker"""
    
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGINT, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown = True

# Main execution
async def main():
    """Main worker execution function"""
    logger.info(f"🚀 Starting {config.WORKER_NAME}")
    
    # Test Redis connection
    if redis_client:
        logger.info("✅ Redis connection established")
    else:
        logger.error("❌ Redis connection failed")
        # Don't exit - still provide health endpoint
    
    # Initialize graceful shutdown handler
    shutdown_handler = GracefulShutdown()
    
    # Initialize task queue processor
    if redis_client:
        task_processor = TaskQueueProcessor(redis_client)
        queue_task = asyncio.create_task(task_processor.process_queue())
    else:
        queue_task = None
    
    # Start FastAPI health check server
    health_config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config.HEALTH_CHECK_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
    health_server = uvicorn.Server(health_config)
    
    logger.info(f"🚀 Worker pod started successfully on port {config.HEALTH_CHECK_PORT}")
    logger.info(f"📋 Health check available at http://0.0.0.0:{config.HEALTH_CHECK_PORT}/health")
    logger.info(f"📋 Task submission available at http://0.0.0.0:{config.HEALTH_CHECK_PORT}/tasks/submit")
    
    try:
        # Run both the health server and queue processor
        tasks = [health_server.serve()]
        if queue_task:
            tasks.append(queue_task)
            
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if queue_task and not queue_task.done():
            queue_task.cancel()
        logger.info("Worker pod shutting down...")

if __name__ == "__main__":
    # Check if running as Celery worker
    if len(sys.argv) > 1 and sys.argv[1] == "celery":
        # Start Celery worker directly
        logger.info("Starting Celery worker mode")
        celery_app.start()
    else:
        # Start FastAPI health check server + queue processor
        asyncio.run(main())
