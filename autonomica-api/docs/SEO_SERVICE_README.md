# SEO Service Documentation

## Overview

The SEO Service is a comprehensive module within the Autonomica API that provides advanced SEO research, keyword analysis, and competitor analysis capabilities. It integrates with multiple APIs and uses machine learning algorithms to deliver actionable SEO insights.

## Features

### 🔍 **Keyword Research & Analysis**
- **SEMrush API Integration**: Access to search volume, CPC, and keyword difficulty data
- **Keyword Clustering**: Advanced ML-based clustering using TF-IDF and cosine similarity
- **Opportunity Scoring**: Intelligent scoring system for identifying high-value keywords
- **Trend Analysis**: Historical data tracking and trend identification

### 🏆 **Competitor Analysis**
- **Content Structure Analysis**: Deep analysis of competitor content patterns
- **Technical SEO Audit**: Comprehensive technical SEO assessment
- **Engagement Element Detection**: Identification of user engagement features
- **Competitive Gap Analysis**: Strategic insights for competitive advantage

### 📊 **Data Processing & ML**
- **Natural Language Processing**: Advanced text preprocessing and feature extraction
- **Clustering Algorithms**: DBSCAN-based keyword clustering with similarity thresholds
- **Semantic Analysis**: TF-IDF vectorization and cosine similarity calculations
- **Fallback Mechanisms**: Robust error handling with alternative calculation methods

### 💡 **Keyword Suggestions**
- **Intelligent Suggestions**: AI-powered keyword generation based on seed keywords
- **Multiple Suggestion Types**: Related, long-tail, question-based, competitor, trending, and intent-based suggestions
- **Semantic Clustering**: Leverages keyword clustering for related term discovery
- **Competitor Analysis**: Generates suggestions based on competitor keyword usage
- **Trend Integration**: Incorporates trending keywords and seasonal patterns
- **Intent Targeting**: Generates keywords targeting specific search intents
- **Difficulty Filtering**: Suggests keywords based on target difficulty levels
- **Caching System**: Intelligent caching for improved performance and cost efficiency

## Architecture

```
SEO Service
├── Core Service (seo_service.py)
│   ├── SEMrush API Integration
│   ├── Rate Limiting & Caching
│   └── Response Parsing
├── Keyword Clustering (keyword_clustering.py)
│   ├── TF-IDF Vectorization
│   ├── DBSCAN Clustering
│   └── Opportunity Scoring
├── Competitor Analysis (competitor_analysis.py)
│   ├── Web Scraping
│   ├── Content Analysis
│   └── Technical SEO Audit
├── Keyword Suggestions (keyword_suggestion.py)
│   ├── Multi-Type Generation
│   ├── Semantic Clustering
│   ├── Competitor Analysis
│   └── Intelligent Caching
├── Data Pipeline (seo_data_pipeline.py)
│   ├── Multi-Stage Processing
│   ├── Orchestration Engine
│   └── Result Aggregation
└── Configuration (seo_config.py)
    ├── API Keys Management
    ├── Rate Limit Settings
    └── Service Configuration
```

## Installation

### Prerequisites
- Python 3.8+
- FastAPI
- Required dependencies (see `requirements-seo.txt`)

### Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements-seo.txt
   ```

2. **Install Playwright** (for advanced competitor analysis):
   ```bash
   playwright install
   ```

3. **Download NLTK Data**:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   nltk.download('wordnet')
   ```

### Environment Variables
Create a `.env` file with the following variables:

```env
# SEMrush API
SEMRUSH_API_KEY=your_semrush_api_key
SEMRUSH_BASE_URL=https://api.semrush.com
SEMRUSH_DATABASE=us

# Google APIs
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id

# Service Configuration
SCRAPING_DELAY=1.0
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
CACHE_TTL=3600
```

## Usage

### Basic Keyword Research

```python
from app.services.seo_service import create_seo_service

# Create SEO service instance
seo_service = await create_seo_service()

# Research a keyword
result = await seo_service.research_keyword("python tutorial")
print(f"Search Volume: {result['search_volume']}")
print(f"Keyword Difficulty: {result['keyword_difficulty']}")
```

### Keyword Clustering

```python
from app.services.keyword_clustering import KeywordClusterer

# Initialize clusterer
clusterer = KeywordClusterer(similarity_threshold=0.7)

# Cluster keywords
keywords = ["python tutorial", "python guide", "javascript tutorial", "js guide"]
clusters = clusterer.cluster_keywords(keywords)

# Find opportunities
opportunities = clusterer.find_keyword_opportunities(
    clusters, 
    min_volume=1000, 
    max_difficulty=70
)
```

### Competitor Analysis

```python
from app.services.competitor_analysis import CompetitorAnalyzer

# Analyze competitors
async with CompetitorAnalyzer() as analyzer:
    result = await analyzer.analyze_competitors(
        domain="example.com",
        competitor_domains=["competitor1.com", "competitor2.com"],
        analysis_depth="basic"
    )
    
    print(f"Competitors analyzed: {result['competitors_analyzed']}")
    print(f"Landscape metrics: {result['landscape_metrics']}")
```

### Keyword Suggestions

```python
from app.services.keyword_suggestion import create_keyword_suggestion_service

# Create suggestion service
suggestion_service = await create_keyword_suggestion_service()

# Generate suggestions
request = SuggestionRequest(
    seed_keywords=["python tutorial", "web development"],
    suggestion_types=[
        SuggestionType.RELATED,
        SuggestionType.LONG_TAIL,
        SuggestionType.QUESTION_BASED
    ],
    max_suggestions=50,
    min_relevance_score=0.5,
    target_difficulty="medium",
    target_intent=KeywordIntent.INFORMATIONAL
)

response = await suggestion_service.generate_suggestions(request)

print(f"Generated {response.total_suggestions} suggestions")
for suggestion in response.suggestions[:5]:
    print(f"- {suggestion.keyword} ({suggestion.suggestion_type.value})")
    print(f"  Relevance: {suggestion.relevance_score:.2f}")
    if suggestion.explanation:
        print(f"  Reason: {suggestion.explanation}")
```

### Advanced Suggestion Types

The service supports multiple suggestion types:

- **Related Keywords**: Based on semantic similarity and clustering
- **Long-tail Variations**: Extended keyword phrases with modifiers
- **Question-based**: Keywords starting with question words
- **Competitor-based**: Keywords used by competitor domains
- **Trending**: Currently popular and growing keywords
- **Intent-based**: Keywords targeting specific search intents
- **Difficulty-based**: Keywords matching target difficulty levels

## API Endpoints

### SEO Routes

The service exposes the following API endpoints:

- `POST /api/seo/keyword-analysis` - Analyze keywords with clustering
- `POST /api/seo/domain-analysis` - Analyze domain SEO metrics
- `POST /api/seo/competitor-analysis` - Analyze competitor domains
- `GET /api/seo/opportunities` - Get keyword opportunities
- `GET /api/seo/config-status` - Check configuration status

### Keyword Suggestion Routes

- `POST /api/seo/suggestions/generate` - Generate keyword suggestions
- `POST /api/seo/suggestions/batch-generate` - Generate suggestions for multiple requests
- `GET /api/seo/suggestions/types` - Get available suggestion types and sources
- `GET /api/seo/suggestions/statistics` - Get suggestion service statistics
- `POST /api/seo/suggestions/clear-cache` - Clear suggestion cache
- `GET /api/seo/suggestions/health` - Health check for suggestion service
- `GET /api/seo/suggestions/suggestions/{request_id}` - Get cached suggestions by ID

### Example API Request

```bash
curl -X POST "http://localhost:8000/api/seo/keyword-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "python tutorial",
    "database": "us",
    "include_competitors": true,
    "clustering": true
  }'
```

### Keyword Suggestion API Request

```bash
curl -X POST "http://localhost:8000/api/seo/suggestions/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{
    "seed_keywords": ["python tutorial", "web development"],
    "suggestion_types": ["related", "long_tail", "question_based"],
    "max_suggestions": 50,
    "min_relevance_score": 0.5,
    "target_difficulty": "medium",
    "target_intent": "informational",
    "include_metrics": true,
    "include_explanations": true
  }'
```

## Configuration

### Rate Limiting
- **SEMrush**: 100 requests per minute
- **Google APIs**: 100 queries per day
- **Web Scraping**: 1 second delay between requests

### Caching
- **TTL**: 1 hour (3600 seconds)
- **Max Size**: 1000 cached items
- **Strategy**: LRU (Least Recently Used)

### Analysis Limits
- **Max Keywords**: 100 per analysis
- **Max Competitors**: 20 per domain
- **Clustering Threshold**: 0.7 similarity

## Testing

### Run Tests
```bash
# Run all tests
pytest tests/test_seo_service.py -v

# Run specific test class
pytest tests/test_seo_service.py::TestSEOService -v

# Run with coverage
pytest tests/test_seo_service.py --cov=app.services --cov-report=html
```

### Test Coverage
The test suite covers:
- ✅ Service initialization and configuration
- ✅ API integration and error handling
- ✅ Keyword clustering algorithms
- ✅ Competitor analysis functionality
- ✅ Configuration validation
- ✅ Integration workflows

## Performance Considerations

### Optimization Strategies
1. **Async Processing**: All API calls use async/await for better performance
2. **Connection Pooling**: HTTP session reuse for multiple requests
3. **Intelligent Caching**: Cache frequently requested data
4. **Rate Limit Management**: Automatic throttling to respect API limits

### Memory Management
- **Lazy Loading**: Load data only when needed
- **Streaming Responses**: Handle large datasets efficiently
- **Resource Cleanup**: Proper cleanup of async resources

## Error Handling

### Graceful Degradation
- **API Failures**: Fallback to alternative data sources
- **Network Issues**: Retry mechanisms with exponential backoff
- **Data Parsing Errors**: Robust error handling with detailed logging

### Logging
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Error Tracking**: Detailed error context for debugging
- **Performance Monitoring**: Request timing and success rate tracking

## Security

### API Key Management
- **Environment Variables**: Secure storage of sensitive credentials
- **Key Rotation**: Support for multiple API keys
- **Access Control**: Role-based access to different service levels

### Data Privacy
- **No Data Storage**: Raw API responses are not persisted
- **Secure Transmission**: HTTPS for all external API calls
- **Input Validation**: Strict validation of all user inputs

## Monitoring & Maintenance

### Health Checks
- **API Status**: Monitor external API availability
- **Rate Limit Status**: Track API quota usage
- **Performance Metrics**: Response time and success rate monitoring

### Maintenance Tasks
- **Cache Cleanup**: Regular cache invalidation
- **API Key Validation**: Periodic validation of API credentials
- **Dependency Updates**: Regular updates of external libraries

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Check current usage in configuration
   - Implement request queuing if needed
   - Consider upgrading API plans

2. **Playwright Installation Issues**
   - Ensure system dependencies are installed
   - Run `playwright install` with proper permissions
   - Check browser compatibility

3. **NLTK Data Issues**
   - Verify NLTK data is downloaded
   - Check internet connectivity for downloads
   - Use offline NLTK data if available

### Debug Mode
Enable debug logging by setting:
```python
import logging
logging.getLogger('app.services').setLevel(logging.DEBUG)
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit a pull request

### Code Standards
- **Type Hints**: Use Python type hints throughout
- **Docstrings**: Comprehensive docstrings for all functions
- **Error Handling**: Proper exception handling and logging
- **Testing**: Maintain high test coverage

## License

This SEO service is part of the Autonomica project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test cases for examples
3. Check the API documentation
4. Open an issue in the repository

---

*Last updated: December 2024*
*Version: 1.0.0*
