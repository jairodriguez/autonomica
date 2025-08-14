# User Training Guide

## Content Generation and Repurposing Pipeline

Welcome to the comprehensive training guide for the AI-powered content generation and repurposing system. This guide will help you master all aspects of the platform, from basic operations to advanced workflows.

---

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Content Generation](#content-generation)
4. [Content Repurposing](#content-repurposing)
5. [Quality Management](#quality-management)
6. [Version Control](#version-control)
7. [Analytics & Reporting](#analytics--reporting)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## 🚀 Getting Started

### First Steps

1. **Access the System**: Use the command-line interface (CLI) to interact with the system
2. **Verify Installation**: Run `python app/ai/content_cli.py --help` to confirm everything is working
3. **Explore Available Options**: Use `python app/ai/content_cli.py types` to see supported content types

### Understanding the Interface

The system provides a command-line interface with intuitive commands:
- `generate` - Create new content
- `repurpose` - Transform existing content
- `quality` - Check content quality
- `version` - Manage content versions
- `types` - View content types
- `strategies` - View repurposing strategies

---

## 🔧 Basic Operations

### Command Structure

All commands follow this pattern:
```bash
python app/ai/content_cli.py [command] [options]
```

### Getting Help

```bash
# General help
python app/ai/content_cli.py --help

# Command-specific help
python app/ai/content_cli.py generate --help
python app/ai/content_cli.py repurpose --help
```

### Viewing System Information

```bash
# List all content types and formats
python app/ai/content_cli.py types

# List all repurposing strategies
python app/ai/content_cli.py strategies
```

---

## ✍️ Content Generation

### Basic Content Generation

Generate a simple blog post:
```bash
python app/ai/content_cli.py generate \
  --type blog_post \
  --prompt "Write about the benefits of remote work" \
  --format plain_text
```

### Advanced Content Generation

Generate content with specific requirements:
```bash
python app/ai/content_cli.py generate \
  --type blog_post \
  --prompt "Create a comprehensive guide to digital marketing" \
  --format markdown \
  --brand-voice "Professional and authoritative" \
  --custom-instructions "Include case studies and actionable tips"
```

### Content Types Available

- **Blog Posts**: Long-form articles (800-3000 words)
- **Tweets**: Short social media posts (1-50 words, 280 characters)
- **Facebook Posts**: Social media content (50-500 words)
- **LinkedIn Posts**: Professional content (100-1000 words)
- **Email Newsletters**: Email marketing content (200-1000 words)
- **Video Scripts**: Video content scripts (100-1000 words)

### Output Formats

- **Plain Text**: Simple text format
- **Markdown**: Rich text with formatting
- **HTML**: Web-ready content
- **JSON**: Structured data format
- **Outline**: Hierarchical structure
- **Bullet Points**: Key point format

---

## 🔄 Content Repurposing

### Basic Repurposing

Transform a blog post into a tweet:
```bash
python app/ai/content_cli.py repurpose \
  --from blog_post \
  --to tweet \
  --content "path/to/your/blog.txt"
```

### Advanced Repurposing

Repurpose with specific strategy:
```bash
python app/ai/content_cli.py repurpose \
  --from blog_post \
  --to tweet_thread \
  --content "path/to/your/blog.txt" \
  --strategy "blog_to_tweet_thread"
```

### Repurposing Strategies

#### Blog to Social Media
- **blog_to_tweet**: Extract key insights for Twitter
- **blog_to_tweet_thread**: Create engaging thread series
- **blog_to_facebook**: Generate Facebook posts with excerpts
- **blog_to_linkedin**: Extract professional insights

#### Blog to Visual Content
- **blog_to_carousel**: Convert to slide format
- **blog_to_video_script**: Transform to video narrative

#### Social Media to Blog
- **thread_to_blog**: Expand tweet threads into full posts

### Content Transformation Examples

**Original Blog Post:**
```
AI in Marketing: A Complete Guide

Artificial Intelligence is revolutionizing marketing...
[Full blog content]
```

**Repurposed to Tweet:**
```
🚀 AI is revolutionizing marketing! 

Key benefits:
✅ Increased productivity
✅ Better targeting
✅ Personalized content

What's your experience with AI in marketing?
#AIMarketing #DigitalMarketing
```

---

## ✅ Quality Management

### Running Quality Checks

Check content quality:
```bash
python app/ai/content_cli.py quality \
  --content "path/to/content.txt" \
  --type blog_post
```

### Understanding Quality Scores

The system evaluates content across multiple dimensions:

#### Readability (0-100)
- **90-100**: Excellent - Easy to read and understand
- **80-89**: Good - Generally clear and accessible
- **70-79**: Fair - Some complexity but manageable
- **60-69**: Poor - Difficult to read
- **0-59**: Unacceptable - Very difficult to understand

#### SEO Optimization (0-100)
- **90-100**: Excellent - Fully optimized
- **80-89**: Good - Well optimized
- **70-79**: Fair - Some optimization needed
- **60-69**: Poor - Significant optimization required
- **0-59**: Unacceptable - Major SEO issues

#### Brand Voice Consistency (0-100)
- **90-100**: Excellent - Perfect brand alignment
- **80-89**: Good - Strong brand consistency
- **70-79**: Fair - Some brand alignment
- **60-69**: Poor - Weak brand consistency
- **0-59**: Unacceptable - No brand alignment

### Quality Recommendations

The system provides actionable recommendations:

1. **Readability Improvements**
   - Break long sentences
   - Use simpler vocabulary
   - Improve paragraph structure

2. **SEO Enhancements**
   - Add internal links
   - Include relevant keywords
   - Optimize headings

3. **Brand Voice Alignment**
   - Adjust tone consistency
   - Use brand-specific vocabulary
   - Maintain style guidelines

---

## 📚 Version Control

### Creating Content Versions

Create new content:
```bash
python app/ai/content_cli.py version --action create \
  --content "path/to/content.txt" \
  --type blog_post
```

### Managing Versions

List all versions:
```bash
python app/ai/content_cli.py version --action list \
  --content-id "your-content-id"
```

Create new version:
```bash
python app/ai/content_cli.py version --action create \
  --content "path/to/updated-content.txt" \
  --content-id "your-content-id" \
  --change-summary "Updated introduction and added new section"
```

### Version Statuses

- **Draft**: Initial version, work in progress
- **In Review**: Ready for review and approval
- **Approved**: Content approved for publication
- **Published**: Content live and public
- **Archived**: Content no longer active
- **Rejected**: Content not approved

### Rollback Operations

Rollback to previous version:
```bash
python app/ai/content_cli.py version --action rollback \
  --content-id "your-content-id" \
  --version-id "target-version-id" \
  --change-summary "Reverting to previous version due to issues"
```

---

## 📊 Analytics & Reporting

### Tracking Performance

The system automatically tracks various metrics:

#### Engagement Metrics
- **Views**: Number of content views
- **Likes**: Social media likes
- **Shares**: Content shares
- **Comments**: User comments
- **Clicks**: Link clicks
- **Conversions**: Goal completions

#### Performance Metrics
- **Bounce Rate**: Percentage of single-page visits
- **Time on Page**: Average time spent
- **Engagement Rate**: Overall engagement percentage
- **Conversion Rate**: Goal completion percentage

### Generating Reports

#### Content Performance Report
```python
from app.ai.content_analytics import get_analytics

analytics = get_analytics()
report = analytics.generate_content_report("your-content-id")

print(f"Overall Score: {report.overall_score}")
print(f"Insights: {report.insights}")
print(f"Recommendations: {report.recommendations}")
```

#### System Analytics Report
```python
# Generate system-wide report
system_report = analytics.generate_system_report("30d")
print(f"System Performance: {system_report.summary}")
```

### Key Performance Indicators

- **Content Engagement Rate**: Target > 5%
- **Quality Score**: Target > 80
- **SEO Score**: Target > 75
- **Conversion Rate**: Target > 2%

---

## 🚀 Advanced Features

### Custom Content Types

Create custom content structures:
```python
from app.ai.content_types_simple import ContentType, ContentStructure

# Define custom content type
custom_structure = ContentStructure(
    content_type="custom_type",
    sections=["intro", "main", "conclusion"],
    required_sections=["intro", "main"],
    word_count_range=(500, 1500),
    character_limit=None
)
```

### Custom Quality Metrics

Implement custom quality assessments:
```python
from app.ai.content_quality import QualityMetric, ContentQualityChecker

class CustomQualityChecker(ContentQualityChecker):
    def _assess_custom_metric(self, content: str) -> QualityScore:
        # Your custom assessment logic
        score = self._calculate_custom_score(content)
        return QualityScore(
            score=score,
            level=self._score_to_level(score),
            details="Custom metric assessment"
        )
```

### Batch Processing

Process multiple content pieces:
```python
import asyncio
from app.ai.content_generation import ContentGenerator

async def batch_generate_content(requests):
    generator = ContentGenerator()
    tasks = [generator.generate_content_async(req) for req in requests]
    return await asyncio.gather(*tasks)
```

---

## 💡 Best Practices

### Content Generation

1. **Clear Prompts**: Be specific about what you want
   - ❌ "Write about marketing"
   - ✅ "Write a 1000-word blog post about digital marketing trends in 2025, targeting small business owners"

2. **Brand Voice Consistency**: Maintain consistent tone across all content
3. **Quality First**: Always run quality checks before publishing
4. **Iterative Improvement**: Use feedback to refine content

### Content Repurposing

1. **Choose the Right Strategy**: Match strategy to target format
2. **Maintain Key Messages**: Ensure core points are preserved
3. **Format Appropriately**: Adapt content to platform requirements
4. **Test and Optimize**: Monitor performance and adjust

### Quality Management

1. **Regular Checks**: Run quality assessments on all content
2. **Address Issues**: Fix problems identified by quality checks
3. **Set Standards**: Establish minimum quality thresholds
4. **Continuous Improvement**: Use insights to enhance content

### Version Control

1. **Meaningful Changes**: Document significant modifications
2. **Regular Backups**: Create versions before major changes
3. **Clear Documentation**: Use descriptive change summaries
4. **Approval Workflow**: Follow established review processes

### Analytics

1. **Track Everything**: Monitor all relevant metrics
2. **Set Goals**: Establish performance targets
3. **Regular Reviews**: Analyze reports regularly
4. **Actionable Insights**: Use data to improve content

---

## 🆘 Troubleshooting

### Common Issues

#### Content Generation Fails

**Problem**: Content generation returns errors
**Solutions**:
- Check API key configuration
- Verify content type and format validity
- Ensure prompt meets minimum requirements
- Check system logs for detailed error messages

#### Quality Check Errors

**Problem**: Quality assessment fails
**Solutions**:
- Validate content structure
- Check content type compatibility
- Verify brand voice configuration
- Ensure content meets minimum length requirements

#### Versioning Issues

**Problem**: Version management problems
**Solutions**:
- Ensure content ID exists
- Check user permissions
- Validate version history integrity
- Verify metadata format

#### Analytics Problems

**Problem**: Analytics data issues
**Solutions**:
- Verify metric data format
- Check timestamp validity
- Ensure content ID references are correct
- Validate data integrity

### Debug Mode

Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. **Check Documentation**: Review this guide and README
2. **Review Logs**: Check system logs for error details
3. **Test Components**: Run individual component tests
4. **Contact Support**: Reach out to the development team

---

## 📋 Quick Reference

### Essential Commands

```bash
# Generate content
python app/ai/content_cli.py generate --type blog_post --prompt "Your prompt"

# Repurpose content
python app/ai/content_cli.py repurpose --from blog_post --to tweet --content file.txt

# Check quality
python app/ai/content_cli.py quality --content file.txt --type blog_post

# Manage versions
python app/ai/content_cli.py version --action create --content file.txt --type blog_post

# View options
python app/ai/content_cli.py types
python app/ai/content_cli.py strategies
```

### Quality Thresholds

- **Readability**: Minimum 70
- **SEO**: Minimum 75
- **Brand Voice**: Minimum 80
- **Overall**: Minimum 75

### Content Guidelines

- **Blog Posts**: 800-3000 words
- **Tweets**: 1-50 words, 280 characters max
- **Facebook Posts**: 50-500 words
- **LinkedIn Posts**: 100-1000 words
- **Email Newsletters**: 200-1000 words

---

## 🎯 Next Steps

### Training Completion

After completing this training, you should be able to:

1. ✅ Generate high-quality content using AI
2. ✅ Repurpose content across multiple formats
3. ✅ Assess and improve content quality
4. ✅ Manage content versions effectively
5. ✅ Track performance and generate reports
6. ✅ Troubleshoot common issues
7. ✅ Apply best practices consistently

### Advanced Training

Consider these next-level topics:

1. **Custom Development**: Extending the system with custom features
2. **Integration**: Connecting with other marketing tools
3. **Automation**: Setting up automated workflows
4. **Team Management**: Managing multiple users and permissions
5. **Performance Optimization**: Scaling for high-volume usage

### Resources

- **Documentation**: README.md for technical details
- **API Reference**: Code documentation for developers
- **Examples**: Sample content and workflows
- **Support**: Team contact information and issue tracking

---

## 📞 Support & Contact

### Getting Help

- **Documentation**: Check this guide and README first
- **Team Support**: Contact the development team
- **Issue Tracking**: Report bugs and request features
- **Community**: Connect with other users

### Feedback

We value your feedback! Please share:
- Training experience
- Feature requests
- Bug reports
- Improvement suggestions

---

**Training Guide Version**: 1.0.0  
**Last Updated**: August 2025  
**For**: Content Generation and Repurposing Pipeline Users  
**Maintainer**: Autonomica Team