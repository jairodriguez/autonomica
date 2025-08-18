# SEO Data Processing Pipeline

## Overview

The SEO Data Processing Pipeline is a comprehensive system that orchestrates all SEO components into a cohesive, automated workflow. It integrates keyword research, competitor analysis, keyword clustering, and opportunity analysis to provide actionable SEO insights.

## Architecture

### Core Components

The pipeline consists of several integrated components:

1. **SEO Service** - Handles SEMrush API integration and keyword research
2. **Keyword Clusterer** - Groups semantically similar keywords
3. **Competitor Analyzer** - Analyzes competitor domains and content
4. **Keyword Analyzer** - Provides detailed keyword metrics and insights
5. **Pipeline Orchestrator** - Coordinates all components and manages execution flow

### Pipeline Stages

The pipeline executes in the following sequence:

1. **Initialization** - Validates configuration and initializes services
2. **Keyword Research** - Researches primary keywords using SEMrush API
3. **Competitor Analysis** - Analyzes competitor domains and content structure
4. **Keyword Clustering** - Groups keywords by semantic similarity
5. **Keyword Analysis** - Calculates opportunity scores and generates insights
6. **Insights Generation** - Combines all analysis into actionable insights
7. **Report Generation** - Creates comprehensive SEO reports

## Features

### 🔄 **Automated Workflow**
- End-to-end SEO analysis in a single request
- Configurable analysis depth (basic, comprehensive, deep)
- Automatic rate limiting and error handling

### 📊 **Comprehensive Analysis**
- Keyword research with search volume, CPC, and difficulty
- Competitor analysis with content structure insights
- Semantic keyword clustering for content strategy
- Opportunity scoring and prioritization

### 🚀 **Performance & Scalability**
- Asynchronous execution for non-blocking operations
- Intelligent caching with configurable TTL
- Concurrent pipeline execution (configurable limits)
- Background task processing

### 📈 **Monitoring & Management**
- Real-time pipeline status tracking
- Progress percentage and time estimation
- Pipeline cancellation and cleanup
- Comprehensive execution statistics

## API Endpoints

### Execute Pipeline

**POST** `/api/seo/pipeline/execute`

Initiates a comprehensive SEO analysis pipeline.

**Request Body:**
```json
{
  "primary_keywords": ["python tutorial", "python guide"],
  "competitor_domains": ["example.com", "competitor.com"],
  "target_database": "us",
  "analysis_depth": "comprehensive",
  "include_competitors": true,
  "include_clustering": true,
  "include_opportunity_analysis": true,
  "max_keywords_per_analysis": 100,
  "max_competitors_per_domain": 20
}
```

**Response:**
```json
{
  "pipeline_id": "seo_pipeline_20241201_143022_a1b2c3d4",
  "status": "in_progress",
  "message": "Pipeline execution started successfully",
  "estimated_completion_time": "5-10 minutes depending on analysis depth",
  "stages_to_execute": [
    "keyword_research",
    "competitor_analysis",
    "keyword_clustering",
    "keyword_analysis",
    "insights_generation",
    "report_generation"
  ],
  "monitor_url": "/api/seo/pipeline/status/seo_pipeline_20241201_143022_a1b2c3d4"
}
```

### Check Pipeline Status

**GET** `/api/seo/pipeline/status/{pipeline_id}`

Returns the current status and progress of a pipeline execution.

**Response:**
```json
{
  "pipeline_id": "seo_pipeline_20241201_143022_a1b2c3d4",
  "status": "in_progress",
  "current_stage": "keyword_clustering",
  "stages_completed": ["initialization", "keyword_research", "competitor_analysis"],
  "start_time": "2024-12-01T14:30:22",
  "end_time": null,
  "progress_percentage": 50.0,
  "estimated_time_remaining": "0:02:30",
  "errors": []
}
```

### List Pipelines

**GET** `/api/seo/pipeline/list`

Lists all pipelines with optional status filtering.

**Query Parameters:**
- `status` - Filter by status (active, completed, failed)
- `limit` - Maximum number of pipelines to return (default: 20)

**Response:**
```json
{
  "active_pipelines": [
    {
      "pipeline_id": "seo_pipeline_20241201_143022_a1b2c3d4",
      "status": "in_progress",
      "current_stage": "keyword_clustering",
      "progress_percentage": 50.0
    }
  ],
  "completed_pipelines": [
    {
      "pipeline_id": "seo_pipeline_20241201_140000_x9y8z7w6",
      "status": "completed",
      "progress_percentage": 100.0
    }
  ],
  "total_count": 2
}
```

### Get Pipeline Insights

**GET** `/api/seo/pipeline/insights/{pipeline_id}`

Retrieves insights and analysis results from a completed pipeline.

**Response:**
```json
{
  "pipeline_id": "seo_pipeline_20241201_140000_x9y8z7w6",
  "summary": {
    "total_keywords_analyzed": 25,
    "total_competitors_analyzed": 5,
    "total_clusters_identified": 8,
    "high_opportunity_keywords": 12
  },
  "key_findings": [
    {
      "type": "opportunity",
      "description": "Found 12 high-opportunity keywords",
      "details": "Top keyword: 'python tutorial' with score 85.0"
    }
  ],
  "recommendations": [
    "Create comprehensive, educational content",
    "Include step-by-step guides and examples",
    "Focus on long-tail variations with lower difficulty"
  ],
  "opportunities": [
    {
      "keyword": "python tutorial",
      "opportunity_score": 85.0,
      "search_volume": 10000,
      "difficulty": 45
    }
  ],
  "risks": [
    "Very high difficulty - may take significant time and resources"
  ]
}
```

### Get Pipeline Report

**GET** `/api/seo/pipeline/report/{pipeline_id}`

Retrieves the complete report from a completed pipeline.

**Query Parameters:**
- `format` - Report format: json, html, or pdf (default: json)

**Response (JSON format):**
```json
{
  "executive_summary": {
    "pipeline_id": "seo_pipeline_20241201_140000_x9y8z7w6",
    "execution_date": "2024-12-01T14:00:00",
    "total_execution_time": "0:05:30",
    "status": "completed",
    "stages_completed": 6
  },
  "request_summary": {
    "primary_keywords": ["python tutorial", "python guide"],
    "competitor_domains": ["example.com", "competitor.com"],
    "analysis_depth": "comprehensive",
    "target_database": "us"
  },
  "results_summary": {
    "keyword_research": {
      "status": "completed",
      "items_processed": 25
    },
    "competitor_analysis": {
      "status": "completed",
      "items_processed": 5
    }
  },
  "detailed_results": { ... },
  "insights": { ... }
}
```

### Cancel Pipeline

**DELETE** `/api/seo/pipeline/cancel/{pipeline_id}`

Cancels a running pipeline.

**Response:**
```json
{
  "message": "Pipeline seo_pipeline_20241201_143022_a1b2c3d4 cancelled successfully",
  "pipeline_id": "seo_pipeline_20241201_143022_a1b2c3d4"
}
```

### Cleanup Expired Pipelines

**POST** `/api/seo/pipeline/cleanup`

Cleans up expired pipeline cache entries.

**Response:**
```json
{
  "message": "Pipeline cache cleanup completed successfully",
  "timestamp": "2024-12-01T15:00:00"
}
```

### Get Pipeline Statistics

**GET** `/api/seo/pipeline/statistics`

Returns pipeline execution statistics.

**Response:**
```json
{
  "statistics": {
    "active_pipelines": 1,
    "cached_results": 15,
    "total_pipelines_executed": 25,
    "cache_hit_rate": 0.0,
    "average_execution_time": 0.0
  },
  "timestamp": "2024-12-01T15:00:00"
}
```

## Usage Examples

### Basic Pipeline Execution

```python
import requests

# Execute a basic SEO analysis pipeline
response = requests.post(
    "http://localhost:8000/api/seo/pipeline/execute",
    json={
        "primary_keywords": ["python tutorial", "python guide"],
        "competitor_domains": ["example.com", "competitor.com"],
        "analysis_depth": "basic"
    }
)

pipeline_id = response.json()["pipeline_id"]
print(f"Pipeline started: {pipeline_id}")
```

### Monitor Pipeline Progress

```python
import time
import requests

def monitor_pipeline(pipeline_id):
    while True:
        response = requests.get(
            f"http://localhost:8000/api/seo/pipeline/status/{pipeline_id}"
        )
        status = response.json()
        
        print(f"Status: {status['status']}")
        print(f"Progress: {status['progress_percentage']}%")
        print(f"Current Stage: {status['current_stage']}")
        
        if status['status'] in ['completed', 'failed']:
            break
            
        time.sleep(30)  # Check every 30 seconds

# Monitor the pipeline
monitor_pipeline(pipeline_id)
```

### Retrieve Results

```python
# Get insights
insights_response = requests.get(
    f"http://localhost:8000/api/seo/pipeline/insights/{pipeline_id}"
)
insights = insights_response.json()

print("Key Findings:")
for finding in insights['key_findings']:
    print(f"- {finding['description']}")

print("\nRecommendations:")
for rec in insights['recommendations']:
    print(f"- {rec}")

# Get full report
report_response = requests.get(
    f"http://localhost:8000/api/seo/pipeline/report/{pipeline_id}"
)
report = report_response.json()

print(f"\nAnalysis completed in: {report['executive_summary']['total_execution_time']}")
```

## Configuration

### Environment Variables

The pipeline uses the same configuration as the SEO service:

```bash
# SEMrush API Configuration
SEMRUSH_API_KEY=your_semrush_api_key
SEMRUSH_BASE_URL=https://api.semrush.com
SEMRUSH_DATABASE=us

# Google APIs Configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id

# Rate Limiting
SEMRUSH_RATE_LIMIT=100
SCRAPING_DELAY=1.0
MAX_CONCURRENT_REQUESTS=5

# Caching
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

### Pipeline Settings

```python
# Pipeline configuration
MAX_CONCURRENT_PIPELINES = 3
PIPELINE_TIMEOUT = 300  # 5 minutes
ENABLE_CACHING = True
CACHE_TTL = 3600  # 1 hour
```

## Error Handling

### Common Error Scenarios

1. **API Key Missing**
   ```json
   {
     "detail": "Missing required API keys: SEMRUSH_API_KEY"
   }
   ```

2. **Pipeline Already Running**
   ```json
   {
     "detail": "Pipeline seo_pipeline_123 is already running"
   }
   ```

3. **Pipeline Not Found**
   ```json
   {
     "detail": "Pipeline non_existent not found"
   }
   ```

4. **Pipeline Not Completed**
   ```json
   {
     "detail": "Pipeline seo_pipeline_123 is not completed. Current status: in_progress"
   }
   ```

### Error Recovery

- **Automatic Retry**: Failed stages are logged but don't stop the pipeline
- **Partial Results**: Pipeline continues with available data
- **Error Logging**: All errors are captured and included in the final report
- **Graceful Degradation**: Pipeline can complete with reduced functionality

## Performance Considerations

### Execution Time Estimates

- **Basic Analysis**: 2-3 minutes
- **Comprehensive Analysis**: 5-10 minutes
- **Deep Analysis**: 10-15 minutes

### Rate Limiting

- SEMrush API: 100 requests per minute
- Web scraping: 1 second delay between requests
- Concurrent requests: Maximum 5 simultaneous

### Caching Strategy

- **Pipeline Results**: Cached for 1 hour
- **API Responses**: Cached based on SEMrush TTL
- **Competitor Analysis**: Cached for 24 hours
- **Keyword Clustering**: Results cached for 1 hour

## Security

### Authentication

All pipeline endpoints require authentication via Clerk middleware.

### Rate Limiting

- Per-user rate limiting
- Pipeline execution limits
- API call throttling

### Data Privacy

- User data isolation
- Secure API key storage
- Encrypted data transmission

## Monitoring and Logging

### Pipeline Metrics

- Execution time per stage
- Success/failure rates
- Cache hit rates
- Resource utilization

### Logging

- Structured logging with correlation IDs
- Stage-by-stage progress tracking
- Error context and stack traces
- Performance metrics

## Troubleshooting

### Common Issues

1. **Pipeline Stuck in Progress**
   - Check for API rate limit issues
   - Verify competitor domain accessibility
   - Review error logs for specific failures

2. **Slow Execution**
   - Reduce analysis depth
   - Limit number of keywords/competitors
   - Check network connectivity

3. **Cache Issues**
   - Clear expired cache entries
   - Verify cache TTL settings
   - Check memory usage

### Debug Mode

Enable debug logging for detailed pipeline execution information:

```python
import logging
logging.getLogger('app.services.seo_data_pipeline').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Real-time Notifications**
   - WebSocket updates for pipeline progress
   - Email/SMS notifications on completion
   - Slack/Teams integration

2. **Advanced Analytics**
   - Historical trend analysis
   - Performance benchmarking
   - ROI calculations

3. **Batch Processing**
   - Multiple pipeline execution
   - Scheduled pipeline runs
   - Bulk keyword analysis

4. **Export Formats**
   - PDF report generation
   - Excel/CSV data export
   - Custom report templates

### Integration Opportunities

1. **Content Management Systems**
   - WordPress plugin
   - Drupal module
   - Custom CMS integration

2. **Marketing Tools**
   - HubSpot integration
   - Mailchimp campaigns
   - Google Analytics correlation

3. **Project Management**
   - Jira ticket creation
   - Trello board updates
   - Asana task management

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.

---

*This documentation covers the SEO Data Processing Pipeline v1.0. For updates and additional information, refer to the project repository.*
