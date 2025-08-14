# Content Generation and Repurposing Pipeline

A comprehensive AI-powered content generation and repurposing system that transforms blog content into various social media formats while maintaining quality and brand consistency.

## 🚀 Features

- **AI-Powered Content Generation**: Generate high-quality content using advanced language models
- **Smart Content Repurposing**: Transform existing content into multiple formats (tweets, Facebook posts, LinkedIn updates, etc.)
- **Quality Assurance**: Automated quality checks for readability, SEO, and brand voice consistency
- **Version Control**: Track content changes and manage different versions with rollback capabilities
- **Analytics & Reporting**: Comprehensive performance tracking and insights
- **Command Line Interface**: Easy-to-use CLI for all operations
- **Extensible Architecture**: Modular design for easy customization and extension

## 🏗️ Architecture

The system is built with a modular architecture consisting of several key components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Content Types │    │   Content        │    │   Content       │
│   & Formats     │    │   Generation     │    │   Repurposing   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Quality        │
                    │   Checking       │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Versioning     │
                    │   System         │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Analytics &    │
                    │   Reporting      │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │   CLI Interface  │
                    └──────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.8+
- pip or poetry

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd autonomica-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## 🎯 Quick Start

### Using the CLI

The system provides a comprehensive command-line interface for all operations:

#### Generate Content
```bash
python app/ai/content_cli.py generate \
  --type blog_post \
  --prompt "Write about AI in marketing" \
  --format markdown \
  --brand-voice "Professional and engaging"
```

#### Repurpose Content
```bash
python app/ai/content_cli.py repurpose \
  --from blog_post \
  --to tweet \
  --content "path/to/blog.txt"
```

#### Check Content Quality
```bash
python app/ai/content_cli.py quality \
  --content "path/to/content.txt" \
  --type blog_post
```

#### Manage Versions
```bash
# Create new content
python app/ai/content_cli.py version --action create \
  --content "path/to/content.txt" \
  --type blog_post

# List versions
python app/ai/content_cli.py version --action list \
  --content-id "your-content-id"
```

#### View Available Options
```bash
# List content types and formats
python app/ai/content_cli.py types

# List repurposing strategies
python app/ai/content_cli.py strategies

# Get help
python app/ai/content_cli.py --help
```

### Using the Python API

#### Content Generation
```python
from app.ai.content_generation import ContentGenerator, ContentGenerationRequest
from app.ai.content_types_simple import ContentType, ContentFormat

generator = ContentGenerator()

request = ContentGenerationRequest(
    content_type=ContentType.BLOG_POST,
    target_format=ContentFormat.MARKDOWN,
    prompt="Write about the future of AI",
    brand_voice="Innovative and forward-thinking"
)

response = generator.generate_content_sync(request)
print(f"Generated content: {response.content}")
```

#### Content Repurposing
```python
from app.ai.content_generation import ContentRepurposingRequest

repurpose_request = ContentRepurposingRequest(
    source_content="Your blog content here...",
    source_type=ContentType.BLOG_POST,
    target_type=ContentType.TWEET,
    brand_voice="Professional and engaging"
)

repurpose_response = generator.repurpose_content_sync(repurpose_request)
print(f"Repurposed content: {repurpose_response.content}")
```

#### Quality Checking
```python
from app.ai.content_quality import get_quality_checker

checker = get_quality_checker()
report = checker.assess_content_quality(
    content="Your content here...",
    content_type=ContentType.BLOG_POST,
    target_format=ContentFormat.PLAIN_TEXT
)

print(f"Quality score: {report.overall_score}/100")
print(f"Recommendations: {report.recommendations}")
```

#### Version Management
```python
from app.ai.content_versioning import get_versioning_system

versioning = get_versioning_system()

# Create content
content_id = versioning.create_content(
    content="Initial content",
    content_type=ContentType.BLOG_POST,
    format=ContentFormat.PLAIN_TEXT,
    metadata={"title": "My Blog Post"},
    user_id="user123"
)

# Create new version
version_id = versioning.create_version(
    content_id=content_id,
    content="Updated content",
    user_id="user123",
    change_summary="Added more details"
)
```

#### Analytics
```python
from app.ai.content_analytics import get_analytics, MetricType, EngagementMetric

analytics = get_analytics()

# Track metrics
analytics.track_metric(
    content_id="your-content-id",
    version_id="your-version-id",
    metric_type=MetricType.ENGAGEMENT,
    metric_name=EngagementMetric.VIEWS.value,
    value=150,
    unit="views"
)

# Generate reports
report = analytics.generate_content_report("your-content-id")
print(f"Report: {report.summary}")
```

## 📋 Content Types and Formats

### Supported Content Types

- **Long-form Content**: Blog posts, articles, whitepapers, case studies, guides, tutorials
- **Social Media**: Tweets, tweet threads, Facebook posts, LinkedIn posts, Instagram captions
- **Visual Content**: Carousels, slide decks, infographics, memes
- **Video Content**: Video scripts, short-form videos, long-form videos, video captions
- **Audio Content**: Podcast scripts, audio ads
- **Email Content**: Newsletters, email sequences, transactional emails
- **Marketing Content**: Landing pages, ad copy, product descriptions, press releases

### Supported Formats

- **Text Formats**: Plain text, Markdown, HTML, JSON
- **Structured Formats**: Outlines, bullet points, Q&A, checklists
- **Media Formats**: Image, video, audio, PDF
- **Social Media**: Hashtags, emojis, mentions

## 🔄 Repurposing Strategies

The system includes sophisticated algorithms for transforming content between different formats:

### Blog to Social Media
- **Blog → Tweet**: Extract key points and insights
- **Blog → Tweet Thread**: Summarize each section
- **Blog → Facebook Post**: Create engaging excerpts with call-to-action
- **Blog → LinkedIn Post**: Extract professional insights and industry expertise

### Blog to Visual Content
- **Blog → Carousel**: Convert key points into slides
- **Blog → Video Script**: Transform into spoken narrative format

### Social Media to Blog
- **Tweet Thread → Blog**: Expand thread into comprehensive blog post

### Email Marketing
- **Blog → Newsletter**: Convert to email newsletter format

## 📊 Quality Metrics

The quality checking system evaluates content across multiple dimensions:

### Readability
- Sentence length analysis
- Word complexity assessment
- Flesch Reading Ease approximation
- Content length validation

### Grammar & Style
- Passive voice detection
- Wordy phrase identification
- Repetitive word detection
- Long sentence identification

### SEO Optimization
- Title and meta description length
- Heading structure analysis
- Keyword density assessment
- Internal link verification
- Image alt text checking

### Brand Voice Consistency
- Tone analysis
- Vocabulary assessment
- Style consistency checking

### Content Structure
- Required section validation
- Word count compliance
- Character limit adherence

### Engagement Potential
- Call-to-action detection
- Personal pronoun usage
- Interactive element identification

## 🔧 Configuration

### Environment Variables

```bash
# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key
DEFAULT_MODEL=gpt-4

# Content Generation Settings
MAX_TOKENS=2000
TEMPERATURE=0.7

# Quality Check Thresholds
MIN_READABILITY_SCORE=60
MIN_SEO_SCORE=70
MIN_ENGAGEMENT_SCORE=50

# Analytics Settings
METRICS_RETENTION_DAYS=90
REPORT_GENERATION_INTERVAL=24h
```

### Customization

#### Adding New Content Types
```python
from app.ai.content_types_simple import ContentType, ContentStructure

# Add new content type
ContentType.NEW_TYPE = "new_type"

# Define structure
new_structure = ContentStructure(
    content_type=ContentType.NEW_TYPE,
    sections=["intro", "main", "conclusion"],
    required_sections=["intro", "main"],
    optional_sections=["conclusion"],
    word_count_range=(500, 1500),
    character_limit=None
)
```

#### Custom Quality Metrics
```python
from app.ai.content_quality import QualityMetric, ContentQualityChecker

# Add custom metric
QualityMetric.CUSTOM_METRIC = "custom_metric"

class CustomQualityChecker(ContentQualityChecker):
    def _assess_custom_metric(self, content: str) -> QualityScore:
        # Your custom assessment logic
        pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python test_content_generation.py
python test_content_repurposing.py
python test_content_quality.py
python test_content_versioning.py
python test_content_analytics.py
python test_cli.py

# Run system integration tests
python test_system_integration.py
```

### Test Coverage

The system includes comprehensive test coverage for:
- Unit tests for individual components
- Integration tests for component interactions
- System tests for end-to-end workflows
- Error handling and edge cases
- Performance and scalability

## 📈 Performance

### Benchmarks

- **Content Generation**: < 5 seconds for typical blog posts
- **Content Repurposing**: < 3 seconds for social media formats
- **Quality Checking**: < 2 seconds for comprehensive analysis
- **Version Management**: < 1 second for operations
- **Analytics Processing**: < 2 seconds for report generation

### Scalability

- Supports concurrent processing of multiple content pieces
- Efficient memory usage with lazy loading
- Optimized database queries for large datasets
- Horizontal scaling capabilities

## 🔒 Security

### Authentication
- User-based access control
- API key management
- Session management
- Audit logging

### Data Protection
- Content encryption at rest
- Secure transmission protocols
- GDPR compliance features
- Data retention policies

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app/main.py"]
```

### Production Considerations

- Use production-grade AI model endpoints
- Implement proper logging and monitoring
- Set up health checks and alerting
- Configure backup and disaster recovery
- Implement rate limiting and throttling

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Add comprehensive docstrings
- Maintain test coverage above 90%

## 📚 API Reference

### Core Classes

#### ContentGenerator
Main class for content generation operations.

**Methods:**
- `generate_content_sync(request)`: Generate content synchronously
- `generate_content_async(request)`: Generate content asynchronously
- `repurpose_content_sync(request)`: Repurpose content synchronously
- `repurpose_content_async(request)`: Repurpose content asynchronously

#### ContentQualityChecker
Handles content quality assessment.

**Methods:**
- `assess_content_quality(content, content_type, target_format)`: Assess content quality
- `get_quality_score(content, metric)`: Get specific quality metric score

#### ContentVersioningSystem
Manages content versions and history.

**Methods:**
- `create_content(content, content_type, format, metadata, user_id)`: Create new content
- `create_version(content_id, content, user_id, change_summary)`: Create new version
- `rollback_to_version(content_id, target_version_id, user_id, reason)`: Rollback to previous version

#### ContentAnalytics
Tracks content performance and generates reports.

**Methods:**
- `track_metric(content_id, version_id, metric_type, metric_name, value)`: Track metric
- `generate_content_report(content_id)`: Generate content performance report
- `generate_system_report(time_period)`: Generate system-wide analytics report

### Data Models

#### ContentGenerationRequest
```python
@dataclass
class ContentGenerationRequest:
    content_type: ContentType
    prompt: str
    target_format: ContentFormat = ContentFormat.PLAIN_TEXT
    brand_voice: Optional[str] = None
    tone: str = "professional"
    word_count: Optional[int] = None
    custom_instructions: Optional[str] = None
```

#### ContentQualityReport
```python
@dataclass
class ContentQualityReport:
    overall_score: float
    overall_level: QualityLevel
    metric_scores: Dict[QualityMetric, QualityScore]
    summary: str
    recommendations: List[str]
    word_count: int
    character_count: int
    estimated_reading_time: float
```

## 🆘 Troubleshooting

### Common Issues

#### Content Generation Fails
- Check API key configuration
- Verify content type and format validity
- Ensure prompt meets minimum requirements

#### Quality Check Errors
- Validate content structure
- Check content type compatibility
- Verify brand voice configuration

#### Versioning Issues
- Ensure content ID exists
- Check user permissions
- Validate version history integrity

#### Analytics Problems
- Verify metric data format
- Check timestamp validity
- Ensure content ID references are correct

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For additional support:
- Check the issue tracker
- Review the documentation
- Contact the development team

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for language model capabilities
- The open-source community for inspiration and tools
- Contributors and maintainers of this project

---

**Version**: 1.0.0  
**Last Updated**: August 2025  
**Maintainer**: Autonomica Team