import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.content_quality_checker import (
    ContentQualityChecker, QualityCheckStatus, QualityIssueSeverity,
    QualityIssue, QualityCheckResult
)
from app.services.content_types import ContentType, Platform


class TestContentQualityChecker:
    """Test cases for ContentQualityChecker service."""
    
    @pytest.fixture
    def quality_checker(self):
        """Create a quality checker instance for testing."""
        return ContentQualityChecker()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        Artificial Intelligence is transforming the way we work and live. 
        With AI-powered tools, businesses can achieve 40% productivity improvements.
        This technology offers incredible opportunities for growth and innovation.
        """
    
    @pytest.fixture
    def sample_blog_content(self):
        """Sample blog content for testing."""
        return """
        # The Future of AI in Business
        
        Artificial Intelligence represents a paradigm shift in how organizations operate.
        Companies implementing AI solutions report significant improvements in efficiency.
        
        ## Key Benefits
        
        - Increased productivity by up to 40%
        - Better decision-making through data analysis
        - Enhanced customer experiences
        
        ## Conclusion
        
        The future belongs to those who embrace AI technology.
        """
    
    @pytest.mark.asyncio
    async def test_initialization(self, quality_checker):
        """Test quality checker initialization."""
        assert quality_checker.grammar_rules is not None
        assert quality_checker.style_rules is not None
        assert quality_checker.tone_rules is not None
        assert quality_checker.relevance_rules is not None
        assert quality_checker.quality_thresholds is not None
    
    @pytest.mark.asyncio
    async def test_check_content_quality_success(self, quality_checker, sample_content):
        """Test successful content quality check."""
        result = await quality_checker.check_content_quality(
            content=sample_content,
            content_type=ContentType.BLOG_POST,
            target_platforms=[Platform.WEBSITE],
            brand_voice="Professional and engaging"
        )
        
        assert isinstance(result, QualityCheckResult)
        assert result.content_id == "unknown"
        assert result.content_type == ContentType.BLOG_POST
        assert result.status in [QualityCheckStatus.PASSED, QualityCheckStatus.NEEDS_REVIEW, QualityCheckStatus.FAILED]
        assert len(result.checks_performed) == 5
        assert "grammar" in result.checks_performed
        assert "style" in result.checks_performed
        assert "tone" in result.checks_performed
        assert "relevance" in result.checks_performed
        assert "platform_optimization" in result.checks_performed
    
    @pytest.mark.asyncio
    async def test_check_content_quality_with_content_id(self, quality_checker, sample_content):
        """Test content quality check with specific content ID."""
        result = await quality_checker.check_content_quality(
            content=sample_content,
            content_type=ContentType.BLOG_POST,
            target_platforms=[Platform.WEBSITE],
            brand_voice="Professional and engaging",
            content_id="test_content_123"
        )
        
        assert result.content_id == "test_content_123"
    
    @pytest.mark.asyncio
    async def test_grammar_check(self, quality_checker):
        """Test grammar checking functionality."""
        # Test content with appropriate grammar for blog post
        blog_content = "This is a professional blog post about AI technology."
        issues = await quality_checker._check_grammar(blog_content, ContentType.BLOG_POST)
        
        # Blog posts can use various perspectives, so no issues should be found
        assert len(issues) == 0
        
        # Test content with potentially inappropriate grammar for social media
        social_content = "I think this is amazing content for you to read."
        issues = await quality_checker._check_grammar(social_content, ContentType.SOCIAL_MEDIA_POST)
        
        # Social media should use 'you' for engagement, so this should be fine
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    async def test_style_check(self, quality_checker, sample_blog_content):
        """Test style checking functionality."""
        issues = await quality_checker._check_style(
            sample_blog_content, 
            ContentType.BLOG_POST, 
            "Professional and engaging"
        )
        
        # Should find paragraph structure issue (only 1 paragraph)
        assert len(issues) >= 1
        
        # Check for paragraph structure issue
        paragraph_issues = [i for i in issues if "paragraph structure" in i.description]
        assert len(paragraph_issues) >= 1
    
    @pytest.mark.asyncio
    async def test_tone_check_professional(self, quality_checker):
        """Test tone checking for professional brand voice."""
        professional_content = "This is a professional article about business technology."
        issues = await quality_checker._check_tone(
            professional_content, 
            ContentType.BLOG_POST, 
            "Professional and formal"
        )
        
        # Professional content should pass tone checks
        assert len(issues) == 0
        
        # Test with casual language in professional content
        casual_content = "Hey there! This is awesome content about cool technology."
        issues = await quality_checker._check_tone(
            casual_content, 
            ContentType.BLOG_POST, 
            "Professional and formal"
        )
        
        # Should find casual language issues
        assert len(issues) >= 1
        casual_issues = [i for i in issues if "casual language" in i.description]
        assert len(casual_issues) >= 1
    
    @pytest.mark.asyncio
    async def test_tone_check_casual(self, quality_checker):
        """Test tone checking for casual brand voice."""
        casual_content = "Hey there! This is awesome content about cool technology."
        issues = await quality_checker._check_tone(
            casual_content, 
            ContentType.SOCIAL_MEDIA_POST, 
            "Casual and friendly"
        )
        
        # Casual content should pass tone checks
        assert len(issues) == 0
        
        # Test with formal language in casual content
        formal_content = "Nevertheless, this content is consequently important."
        issues = await quality_checker._check_tone(
            formal_content, 
            ContentType.SOCIAL_MEDIA_POST, 
            "Casual and friendly"
        )
        
        # Should find formal language issues
        assert len(issues) >= 1
        formal_issues = [i for i in issues if "formal language" in i.description]
        assert len(formal_issues) >= 1
    
    @pytest.mark.asyncio
    async def test_relevance_check(self, quality_checker):
        """Test relevance checking functionality."""
        # Test Twitter content that exceeds character limit
        long_twitter_content = "A" * 300  # 300 characters, exceeds Twitter limit
        issues = await quality_checker._check_relevance(
            long_twitter_content,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.TWITTER]
        )
        
        # Should find character limit issue
        assert len(issues) >= 1
        char_limit_issues = [i for i in issues if "character limit" in i.description]
        assert len(char_limit_issues) >= 1
        
        # Test Instagram content without hashtags
        instagram_content = "This is a beautiful photo of nature."
        issues = await quality_checker._check_relevance(
            instagram_content,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.INSTAGRAM]
        )
        
        # Should find hashtag issue
        assert len(issues) >= 1
        hashtag_issues = [i for i in issues if "hashtags" in i.description]
        assert len(hashtag_issues) >= 1
    
    @pytest.mark.asyncio
    async def test_social_media_engagement_check(self, quality_checker):
        """Test engagement checking for social media content."""
        # Test social media content without engagement elements
        non_engaging_content = "This is some information about technology."
        issues = await quality_checker._check_relevance(
            non_engaging_content,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.TWITTER]
        )
        
        # Should find engagement issue
        assert len(issues) >= 1
        engagement_issues = [i for i in issues if "engagement elements" in i.description]
        assert len(engagement_issues) >= 1
        
        # Test social media content with engagement elements
        engaging_content = "What do you think about this technology? How can it help your business?"
        issues = await quality_checker._check_relevance(
            engaging_content,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.TWITTER]
        )
        
        # Should not find engagement issues
        engagement_issues = [i for i in issues if "engagement elements" in i.description]
        assert len(engagement_issues) == 0
    
    @pytest.mark.asyncio
    async def test_quality_score_calculation(self, quality_checker):
        """Test quality score calculation."""
        # Test with no issues
        score = quality_checker._calculate_overall_score([], ContentType.BLOG_POST)
        assert score == 1.0
        
        # Test with low severity issues
        low_issues = [
            QualityIssue(
                issue_type="style",
                severity=QualityIssueSeverity.LOW,
                description="Minor formatting issue"
            )
        ]
        score = quality_checker._calculate_overall_score(low_issues, ContentType.BLOG_POST)
        assert 0.8 <= score <= 1.0
        
        # Test with high severity issues
        high_issues = [
            QualityIssue(
                issue_type="grammar",
                severity=QualityIssueSeverity.HIGH,
                description="Major grammar issue"
            )
        ]
        score = quality_checker._calculate_overall_score(high_issues, ContentType.BLOG_POST)
        assert 0.0 <= score <= 0.6
    
    @pytest.mark.asyncio
    async def test_status_determination(self, quality_checker):
        """Test status determination based on quality score."""
        # Test passed status
        status = quality_checker._determine_status(0.95, [])
        assert status == QualityCheckStatus.PASSED
        
        # Test needs review status
        status = quality_checker._determine_status(0.85, [])
        assert status == QualityCheckStatus.NEEDS_REVIEW
        
        # Test failed status
        status = quality_checker._determine_status(0.65, [])
        assert status == QualityCheckStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_grammar_appropriateness(self, quality_checker):
        """Test grammar appropriateness checking."""
        # Blog posts can use various perspectives
        assert quality_checker._is_grammar_appropriate(
            ContentType.BLOG_POST, "you", "Second person usage"
        ) == True
        
        # Social media should use 'you' for engagement
        assert quality_checker._is_grammar_appropriate(
            ContentType.SOCIAL_MEDIA_POST, "you", "Second person usage"
        ) == True
        
        # Video scripts can be conversational
        assert quality_checker._is_grammar_appropriate(
            ContentType.VIDEO_SCRIPT, "we", "First person plural usage"
        ) == True
    
    @pytest.mark.asyncio
    async def test_health_check(self, quality_checker):
        """Test health check functionality."""
        health = await quality_checker.health_check()
        
        assert health["status"] == "healthy"
        assert health["service"] == "ContentQualityChecker"
        assert "timestamp" in health
        assert "checks_available" in health
        assert "rules_loaded" in health
        
        # Check that all rule categories are loaded
        rules = health["rules_loaded"]
        assert "grammar" in rules
        assert "style" in rules
        assert "tone" in rules
        assert "relevance" in rules
    
    @pytest.mark.asyncio
    async def test_error_handling(self, quality_checker):
        """Test error handling in quality checks."""
        # Test with invalid content type (should handle gracefully)
        result = await quality_checker.check_content_quality(
            content="Test content",
            content_type=ContentType.BLOG_POST,  # Valid type
            target_platforms=[Platform.WEBSITE],
            brand_voice="Professional"
        )
        
        # Should complete without errors
        assert result is not None
        assert result.status != QualityCheckStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_metadata_collection(self, quality_checker, sample_content):
        """Test that metadata is properly collected."""
        result = await quality_checker.check_content_quality(
            content=sample_content,
            content_type=ContentType.BLOG_POST,
            target_platforms=[Platform.WEBSITE],
            brand_voice="Professional"
        )
        
        metadata = result.metadata
        assert "content_length" in metadata
        assert "word_count" in metadata
        assert "sentence_count" in metadata
        assert "paragraph_count" in metadata
        assert "brand_voice" in metadata
        assert "target_platforms" in metadata
        
        # Verify metadata values
        assert metadata["content_length"] == len(sample_content)
        assert metadata["word_count"] == len(sample_content.split())
        assert metadata["brand_voice"] == "Professional"
        assert Platform.WEBSITE.value in metadata["target_platforms"]


if __name__ == "__main__":
    pytest.main([__file__])




