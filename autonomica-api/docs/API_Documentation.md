# Autonomica Content Management System - API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL and Endpoints](#base-url-and-endpoints)
4. [Content Generation APIs](#content-generation-apis)
5. [Content Repurposing APIs](#content-repurposing-apis)
6. [Content Management APIs](#content-management-apis)
7. [Quality Management APIs](#quality-management-apis)
8. [Review Workflow APIs](#review-workflow-apis)
9. [Analytics APIs](#analytics-apis)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)
12. [SDKs and Examples](#sdks-and-examples)

## Overview

The Autonomica Content Management System provides a comprehensive REST API for integrating content generation, repurposing, and management capabilities into your applications. The API is built on FastAPI and follows RESTful principles with JSON request/response formats.

### API Version
- **Current Version**: v1.0
- **Base URL**: `/api/content`
- **Content Type**: `application/json`

### Features
- **Content Generation**: AI-powered content creation for multiple formats
- **Content Repurposing**: Transform content between different types and platforms
- **Quality Management**: Automated content quality checking and scoring
- **Review Workflow**: Human review and approval processes
- **Version Control**: Content versioning and change tracking
- **Analytics**: Performance metrics and reporting

## Authentication

### API Key Authentication
All API requests require an API key to be included in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key
1. Contact your system administrator
2. Provide your organization details and use case
3. Receive your unique API key
4. Keep your API key secure and never expose it in client-side code

### Security Best Practices
- Store API keys securely (environment variables, secure vaults)
- Rotate keys regularly
- Use HTTPS for all API calls
- Monitor API usage for suspicious activity

## Base URL and Endpoints

### Base URL
```
https://your-domain.com/api/content
```

### Endpoint Structure
```
/api/content/{resource}/{action}
```

### Common HTTP Methods
- `GET`: Retrieve data
- `POST`: Create new resources
- `PUT`: Update existing resources
- `DELETE`: Remove resources

## Content Generation APIs

### Generate Content

**Endpoint**: `POST /generate`

**Description**: Generate new content using AI based on prompts and parameters.

**Request Body**:
```json
{
  "content_type": "blog_post",
  "prompt": "Write about AI in content marketing",
  "target_platforms": ["website", "linkedin"],
  "brand_voice": "professional",
  "length": "medium",
  "tone": "informative",
  "keywords": ["AI", "content marketing", "automation"],
  "target_audience": "marketing professionals"
}
```

**Response**:
```json
{
  "success": true,
  "content_id": "gen_12345",
  "content": {
    "raw": "AI is revolutionizing content marketing...",
    "formatted": "<h1>AI in Content Marketing</h1><p>AI is revolutionizing...</p>",
    "summary": "Comprehensive overview of AI applications in content marketing",
    "metadata": {
      "word_count": 850,
      "read_time": "3-4 minutes",
      "seo_score": 85
    }
  },
  "quality_score": 87,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Generate Video Script

**Endpoint**: `POST /generate/video-script`

**Description**: Generate video scripts from existing content or prompts.

**Request Body**:
```json
{
  "blog_content": "AI is revolutionizing content marketing...",
  "target_duration": 60,
  "style": "casual",
  "include_visual_cues": true,
  "target_platform": "youtube",
  "brand_voice": "conversational"
}
```

**Response**:
```json
{
  "success": true,
  "script_id": "vs_67890",
  "script": {
    "opening": "Hey there! Today we're talking about...",
    "main_points": ["Point 1: AI basics", "Point 2: Marketing applications"],
    "closing": "Thanks for watching! Don't forget to...",
    "visual_cues": ["Show AI logo", "Display marketing dashboard"],
    "estimated_duration": 58
  },
  "quality_score": 92,
  "generated_at": "2024-01-15T10:35:00Z"
}
```

## Content Repurposing APIs

### Repurpose Content

**Endpoint**: `POST /repurpose`

**Description**: Transform existing content into different formats and platforms.

**Request Body**:
```json
{
  "source_content": "AI is revolutionizing content marketing...",
  "source_type": "blog_post",
  "target_type": "social_media_post",
  "target_platforms": ["twitter", "linkedin"],
  "brand_voice": "professional",
  "content_length": "short",
  "include_hashtags": true,
  "platform_optimization": true
}
```

**Response**:
```json
{
  "success": true,
  "repurposed_content": [
    {
      "platform": "twitter",
      "content": "🚀 AI is revolutionizing content marketing! Here's how...",
      "hashtags": ["#AI", "#ContentMarketing", "#Innovation"],
      "character_count": 280,
      "quality_score": 89
    },
    {
      "platform": "linkedin",
      "content": "The future of content marketing is here...",
      "hashtags": ["#ContentMarketing", "#AI", "#DigitalTransformation"],
      "character_count": 1300,
      "quality_score": 91
    }
  ],
  "repurposed_at": "2024-01-15T10:40:00Z"
}
```

### LangChain Repurposing

**Endpoint**: `POST /{content_id}/langchain-repurpose`

**Description**: Use advanced LangChain pipeline for content repurposing.

**Request Body**:
```json
{
  "target_type": "email_newsletter",
  "target_platforms": ["email"],
  "brand_voice": "professional",
  "custom_prompt": "Transform this into a weekly newsletter format",
  "include_summary": true,
  "call_to_action": "Read more on our blog"
}
```

**Response**:
```json
{
  "success": true,
  "repurposed_content": {
    "subject_line": "Weekly Update: AI in Content Marketing",
    "body": "Dear subscribers,\n\nThis week we explore...",
    "summary": "Key insights about AI applications in marketing",
    "call_to_action": "Read more on our blog",
    "quality_score": 94
  },
  "processing_time": "2.3s",
  "repurposed_at": "2024-01-15T10:45:00Z"
}
```

## Content Management APIs

### Get Content

**Endpoint**: `GET /{content_id}`

**Description**: Retrieve content details and metadata.

**Response**:
```json
{
  "success": true,
  "content": {
    "content_id": "cont_12345",
    "title": "AI in Content Marketing",
    "content_type": "blog_post",
    "content_format": "article",
    "raw_content": "AI is revolutionizing content marketing...",
    "formatted_content": "<h1>AI in Content Marketing</h1>...",
    "metadata": {
      "author": "AI Assistant",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "word_count": 850,
      "read_time": "3-4 minutes"
    },
    "platforms": ["website", "linkedin"],
    "brand_voice": "professional",
    "quality_score": 87,
    "status": "draft"
  }
}
```

### Update Content

**Endpoint**: `PUT /{content_id}/update`

**Description**: Update existing content with new information.

**Request Body**:
```json
{
  "title": "Updated: AI in Content Marketing 2024",
  "raw_content": "Updated content with latest trends...",
  "brand_voice": "casual",
  "platforms": ["website", "linkedin", "medium"],
  "metadata": {
    "keywords": ["AI", "content marketing", "2024 trends"],
    "target_audience": "marketing professionals and beginners"
  }
}
```

**Response**:
```json
{
  "success": true,
  "content_id": "cont_12345",
  "version": "2.0.0",
  "updated_at": "2024-01-15T11:00:00Z",
  "quality_score": 89,
  "message": "Content updated successfully"
}
```

### Search Content

**Endpoint**: `POST /search`

**Description**: Search for content using various criteria.

**Request Body**:
```json
{
  "query": "AI marketing",
  "content_type": "blog_post",
  "platforms": ["website"],
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "quality_score_min": 80,
  "limit": 20,
  "offset": 0
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "content_id": "cont_12345",
      "title": "AI in Content Marketing",
      "content_type": "blog_post",
      "quality_score": 87,
      "created_at": "2024-01-15T10:30:00Z",
      "relevance_score": 0.95
    }
  ],
  "total_count": 15,
  "has_more": false
}
```

## Quality Management APIs

### Check Content Quality

**Endpoint**: `POST /quality/check`

**Description**: Perform comprehensive quality checks on content.

**Request Body**:
```json
{
  "content": "AI is revolutionizing content marketing...",
  "content_type": "blog_post",
  "target_platforms": ["website"],
  "brand_voice": "professional",
  "quality_checks": ["grammar", "style", "brand_voice", "relevance"]
}
```

**Response**:
```json
{
  "success": true,
  "quality_result": {
    "overall_score": 87,
    "checks": {
      "grammar": {
        "score": 95,
        "issues": [],
        "status": "excellent"
      },
      "style": {
        "score": 88,
        "issues": ["Consider shorter sentences for better readability"],
        "status": "good"
      },
      "brand_voice": {
        "score": 92,
        "issues": [],
        "status": "excellent"
      },
      "relevance": {
        "score": 78,
        "issues": ["Content could be more specific to target audience"],
        "status": "fair"
      }
    },
    "recommendations": [
      "Break down long sentences for better readability",
      "Add more specific examples for target audience"
    ],
    "auto_approval": false
  }
}
```

### Get Quality Metrics

**Endpoint**: `GET /quality/metrics/{content_id}`

**Description**: Retrieve quality metrics for specific content.

**Response**:
```json
{
  "success": true,
  "metrics": {
    "content_id": "cont_12345",
    "quality_history": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "score": 87,
        "checks_performed": ["grammar", "style", "brand_voice", "relevance"]
      }
    ],
    "trends": {
      "score_improvement": "+5",
      "issues_resolved": 3,
      "quality_stability": "stable"
    }
  }
}
```

## Review Workflow APIs

### Submit for Review

**Endpoint**: `POST /{content_id}/submit-review`

**Description**: Submit content for human review and approval.

**Request Body**:
```json
{
  "priority": "medium",
  "reviewer_notes": "Please review for brand voice consistency",
  "requested_by": "user@company.com",
  "deadline": "2024-01-20T18:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "review_request": {
    "request_id": "rev_98765",
    "content_id": "cont_12345",
    "status": "pending_review",
    "assigned_reviewer": "reviewer@company.com",
    "priority": "medium",
    "submitted_at": "2024-01-15T11:00:00Z",
    "estimated_completion": "2024-01-16T11:00:00Z"
  }
}
```

### Review Content

**Endpoint**: `POST /{content_id}/review`

**Description**: Submit review decision and feedback.

**Request Body**:
```json
{
  "reviewer_id": "rev_001",
  "decision": "approve",
  "feedback": "Content meets quality standards and brand guidelines",
  "revision_notes": "",
  "quality_score": 89
}
```

**Response**:
```json
{
  "success": true,
  "review_result": {
    "review_id": "rev_98765",
    "content_id": "cont_12345",
    "decision": "approved",
    "reviewer": "reviewer@company.com",
    "reviewed_at": "2024-01-15T14:00:00Z",
    "next_steps": "Content ready for publishing"
  }
}
```

### Get Review Status

**Endpoint**: `GET /{content_id}/review-status`

**Description**: Check the current review status of content.

**Response**:
```json
{
  "success": true,
  "review_status": {
    "content_id": "cont_12345",
    "status": "under_review",
    "current_reviewer": "reviewer@company.com",
    "review_started": "2024-01-15T12:00:00Z",
    "estimated_completion": "2024-01-16T12:00:00Z",
    "priority": "medium",
    "review_history": [
      {
        "reviewer": "reviewer@company.com",
        "action": "started_review",
        "timestamp": "2024-01-15T12:00:00Z"
      }
    ]
  }
}
```

## Analytics APIs

### Get Dashboard Stats

**Endpoint**: `GET /dashboard/stats`

**Description**: Retrieve dashboard statistics and key metrics.

**Query Parameters**:
- `date_from`: Start date for statistics (YYYY-MM-DD)
- `date_to`: End date for statistics (YYYY-MM-DD)
- `content_type`: Filter by content type
- `platform`: Filter by platform

**Response**:
```json
{
  "success": true,
  "stats": {
    "period": "2024-01-01 to 2024-01-31",
    "content_metrics": {
      "total_content": 45,
      "published_content": 38,
      "draft_content": 7,
      "average_quality_score": 85.2
    },
    "performance_metrics": {
      "total_views": 12500,
      "average_engagement_rate": 4.2,
      "top_performing_content": "cont_12345"
    },
    "workflow_metrics": {
      "content_in_review": 3,
      "average_review_time": "4.5 hours",
      "approval_rate": 92.1
    }
  }
}
```

### Get Content Performance

**Endpoint**: `GET /analytics/performance/{content_id}`

**Description**: Retrieve performance metrics for specific content.

**Response**:
```json
{
  "success": true,
  "performance": {
    "content_id": "cont_12345",
    "metrics": {
      "views": 1250,
      "likes": 89,
      "shares": 23,
      "comments": 15,
      "click_through_rate": 3.2,
      "engagement_rate": 4.1
    },
    "platform_breakdown": {
      "website": {
        "views": 800,
        "engagement": 4.5
      },
      "linkedin": {
        "views": 450,
        "engagement": 3.7
      }
    },
    "trends": {
      "daily_growth": "+12%",
      "weekly_growth": "+8%",
      "monthly_growth": "+15%"
    }
  }
}
```

### Generate Report

**Endpoint**: `POST /analytics/reports`

**Description**: Generate custom analytics reports.

**Request Body**:
```json
{
  "report_type": "weekly",
  "start_date": "2024-01-08",
  "end_date": "2024-01-14",
  "include_recommendations": true,
  "format": "json",
  "metrics": ["engagement", "conversion", "quality"]
}
```

**Response**:
```json
{
  "success": true,
  "report": {
    "report_id": "rep_45678",
    "report_type": "weekly",
    "period": "2024-01-08 to 2024-01-14",
    "generated_at": "2024-01-15T16:00:00Z",
    "data": {
      "summary": "Strong performance with 15% growth in engagement",
      "metrics": {...},
      "recommendations": [
        "Focus on video content for higher engagement",
        "Optimize posting times for better reach"
      ]
    },
    "download_url": "/api/content/analytics/reports/rep_45678/download"
  }
}
```

## Error Handling

### Error Response Format
All API errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid content type specified",
    "details": {
      "field": "content_type",
      "value": "invalid_type",
      "allowed_values": ["blog_post", "social_media_post", "video_script"]
    }
  },
  "timestamp": "2024-01-15T16:00:00Z"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request parameters
- `AUTHENTICATION_ERROR`: Invalid or missing API key
- `NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server-side error
- `CONTENT_TOO_LONG`: Content exceeds platform limits
- `QUALITY_CHECK_FAILED`: Content quality below threshold

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

### Rate Limits
- **Standard Plan**: 100 requests per minute
- **Professional Plan**: 500 requests per minute
- **Enterprise Plan**: 2000 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1642248000
```

### Handling Rate Limits
When rate limited, the API returns a 429 status with retry information:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": 60
  }
}
```

## SDKs and Examples

### Python SDK
```python
import requests

class AutonomicaAPI:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_content(self, prompt, content_type, platforms):
        url = f"{self.base_url}/generate"
        data = {
            "prompt": prompt,
            "content_type": content_type,
            "target_platforms": platforms,
            "brand_voice": "professional"
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
    
    def repurpose_content(self, content_id, target_type, platforms):
        url = f"{self.base_url}/{content_id}/langchain-repurpose"
        data = {
            "target_type": target_type,
            "target_platforms": platforms,
            "brand_voice": "professional"
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

# Usage
api = AutonomicaAPI("your_api_key", "https://api.autonomica.com/api/content")
content = api.generate_content("AI in marketing", "blog_post", ["website"])
```

### JavaScript/Node.js Example
```javascript
class AutonomicaAPI {
    constructor(apiKey, baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async generateContent(prompt, contentType, platforms) {
        const url = `${this.baseUrl}/generate`;
        const data = {
            prompt,
            content_type: contentType,
            target_platforms: platforms,
            brand_voice: 'professional'
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }
    
    async repurposeContent(contentId, targetType, platforms) {
        const url = `${this.baseUrl}/${contentId}/langchain-repurpose`;
        const data = {
            target_type: targetType,
            target_platforms: platforms,
            brand_voice: 'professional'
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }
}

// Usage
const api = new AutonomicaAPI('your_api_key', 'https://api.autonomica.com/api/content');
const content = await api.generateContent('AI in marketing', 'blog_post', ['website']);
```

### cURL Examples

#### Generate Content
```bash
curl -X POST "https://api.autonomica.com/api/content/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "blog_post",
    "prompt": "AI in content marketing",
    "target_platforms": ["website"],
    "brand_voice": "professional"
  }'
```

#### Repurpose Content
```bash
curl -X POST "https://api.autonomica.com/api/content/cont_12345/langchain-repurpose" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "social_media_post",
    "target_platforms": ["twitter"],
    "brand_voice": "casual"
  }'
```

#### Get Content Details
```bash
curl -X GET "https://api.autonomica.com/api/content/cont_12345" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Support and Contact

### Technical Support
- **Email**: api-support@autonomica.com
- **Documentation**: https://docs.autonomica.com
- **Status Page**: https://status.autonomica.com

### API Status
- **Production**: https://api.autonomica.com
- **Staging**: https://staging-api.autonomica.com
- **Development**: https://dev-api.autonomica.com

### SDK Downloads
- **Python**: https://github.com/autonomica/python-sdk
- **JavaScript**: https://github.com/autonomica/js-sdk
- **PHP**: https://github.com/autonomica/php-sdk

---

*For additional API support or questions, please contact our developer relations team.*




