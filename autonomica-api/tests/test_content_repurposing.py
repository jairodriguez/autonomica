"""
Tests for the Content Repurposing Service

This module tests the content repurposing functionality, including
content transformation, quality metrics, and optimization.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from app.services.content_repurposing import (
    ContentRepurposingService,
    RepurposingResult,
    content_repurposing_service
)
from app.services.content_types import ContentType, Platform


class TestRepurposingResult:
    """Test the RepurposingResult dataclass."""
    
    def test_repurposing_result_creation(self):
        """Test creating a RepurposingResult instance."""
        result = RepurposingResult(
            source_content="Original content",
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.SOCIAL_MEDIA_POST,
            repurposed_content="New content",
            target_platforms=[Platform.TWITTER],
            brand_voice="Professional",
            transformation_applied=["rule1", "rule2"],
            quality_metrics={"score": 0.9},
            metadata={"key": "value"}
        )
        
        assert result.source_content == "Original content"
        assert result.source_type == ContentType.BLOG_POST
        assert result.target_type == ContentType.SOCIAL_MEDIA_POST
        assert result.repurposed_content == "New content"
        assert result.target_platforms == [Platform.TWITTER]
        assert result.brand_voice == "Professional"
        assert result.transformation_applied == ["rule1", "rule2"]
        assert result.quality_metrics == {"score": 0.9}
        assert result.metadata == {"key": "value"}


class TestContentRepurposingService:
    """Test the ContentRepurposingService class."""
    
    @pytest.fixture
    def service(self):
        """Create a ContentRepurposingService instance for testing."""
        return ContentRepurposingService()
    
    @pytest.fixture
    def sample_blog_content(self):
        """Sample blog content for testing."""
        return """
        Artificial Intelligence is transforming the way we work and live. 
        Companies that embrace AI see 40% increase in productivity.
        
        The future of work is here, and it's powered by machine learning algorithms.
        Organizations must adapt or risk being left behind in this digital revolution.
        
        What does this mean for your business? It means opportunity for growth and innovation.
        The time to act is now, before your competitors gain the advantage.
        """
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.max_retries == 3
        assert service.quality_threshold == 0.8
    
    @pytest.mark.asyncio
    async def test_repurpose_content_success(self, service, sample_blog_content):
        """Test successful content repurposing."""
        with patch('app.services.content_repurposing.get_repurposing_rules') as mock_rules:
            # Mock the repurposing rules
            mock_rule = Mock()
            mock_rule.transformation_rules = ["extract_key_points", "format_for_platform"]
            mock_rule.content_adaptations = ["optimize_length", "add_hashtags"]
            mock_rules.return_value = [mock_rule]
            
            # Mock the repurposing logic
            with patch.object(service, '_apply_repurposing_logic', return_value="Repurposed content"):
                with patch.object(service, '_optimize_content', return_value="Optimized content"):
                    result = await service.repurpose_content(
                        source_content=sample_blog_content,
                        source_type=ContentType.BLOG_POST,
                        target_type=ContentType.SOCIAL_MEDIA_POST,
                        target_platforms=[Platform.TWITTER],
                        brand_voice="Professional"
                    )
            
            assert isinstance(result, RepurposingResult)
            assert result.source_content == sample_blog_content
            assert result.source_type == ContentType.BLOG_POST
            assert result.target_type == ContentType.SOCIAL_MEDIA_POST
            assert result.repurposed_content == "Optimized content"
            assert result.target_platforms == [Platform.TWITTER]
            assert result.brand_voice == "Professional"
            assert "extract_key_points" in result.transformation_applied
            assert "add_hashtags" in result.transformation_applied
    
    @pytest.mark.asyncio
    async def test_repurpose_content_no_rules(self, service, sample_blog_content):
        """Test repurposing when no rules are found."""
        with patch('app.services.content_repurposing.get_repurposing_rules', return_value=[]):
            with pytest.raises(ValueError, match="No repurposing rules found"):
                await service.repurpose_content(
                    source_content=sample_blog_content,
                    source_type=ContentType.BLOG_POST,
                    target_type=ContentType.SOCIAL_MEDIA_POST,
                    target_platforms=[Platform.TWITTER],
                    brand_voice="Professional"
                )
    
    def test_extract_key_points(self, service, sample_blog_content):
        """Test key point extraction from content."""
        key_points = service._extract_key_points(sample_blog_content, ContentType.BLOG_POST)
        
        assert len(key_points) == 3  # 3 paragraphs
        assert key_points[0]["id"] == 1
        assert key_points[0]["length"] > 0
        assert "key_phrases" in key_points[0]
        assert "sentiment" in key_points[0]
        assert "has_numbers" in key_points[0]
        assert "has_questions" in key_points[0]
        assert "has_calls_to_action" in key_points[0]
    
    def test_extract_key_phrases(self, service):
        """Test key phrase extraction."""
        text = "Artificial Intelligence is transforming the way we work. AI companies see 40% growth."
        phrases = service._extract_key_phrases(text)
        
        # Should extract capitalized phrases and numbers
        assert "Artificial Intelligence" in phrases
        assert "40" in phrases
    
    def test_analyze_sentiment(self, service):
        """Test sentiment analysis."""
        # Test positive sentiment
        positive_text = "This is amazing and wonderful content that we love."
        assert service._analyze_sentiment(positive_text) == "positive"
        
        # Test negative sentiment
        negative_text = "This is terrible and awful content with many problems."
        assert service._analyze_sentiment(negative_text) == "negative"
        
        # Test neutral sentiment
        neutral_text = "This is content about technology and business."
        assert service._analyze_sentiment(neutral_text) == "neutral"
    
    def test_has_call_to_action(self, service):
        """Test call-to-action detection."""
        # Test with CTA phrases
        cta_text = "Click here to learn more about our services."
        assert service._has_call_to_action(cta_text) is True
        
        # Test without CTA phrases
        no_cta_text = "This is regular content without any action items."
        assert service._has_call_to_action(no_cta_text) is False
    
    @pytest.mark.asyncio
    async def test_transform_to_social_media(self, service):
        """Test transformation to social media format."""
        key_points = [
            {
                "id": 1,
                "content": "AI is transforming business with 40% productivity gains.",
                "length": 50,
                "key_phrases": ["AI", "business"],
                "sentiment": "positive",
                "has_numbers": True,
                "has_questions": False,
                "has_calls_to_action": False
            }
        ]
        
        with patch('app.services.content_repurposing.get_platform_requirements') as mock_platform:
            mock_platform.return_value = Mock()
            mock_platform.return_value.character_limits = {"post": 280}
            
            result = await service._transform_to_social_media(
                key_points, [Platform.TWITTER], "Professional"
            )
            
            assert result is not None
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_transform_to_video_script(self, service):
        """Test transformation to video script format."""
        key_points = [
            {
                "id": 1,
                "content": "AI is transforming business with 40% productivity gains.",
                "length": 50,
                "key_phrases": ["AI", "business"],
                "sentiment": "positive",
                "has_numbers": True,
                "has_questions": False,
                "has_calls_to_action": False
            }
        ]
        
        result = await service._transform_to_video_script(key_points, "Professional")
        
        assert result is not None
        assert "HOOK:" in result
        assert "INTRODUCTION:" in result
        assert "MAIN_CONTENT:" in result
        assert "CONCLUSION:" in result
        assert "CALL_TO_ACTION:" in result
    
    @pytest.mark.asyncio
    async def test_transform_to_email_newsletter(self, service):
        """Test transformation to email newsletter format."""
        key_points = [
            {
                "id": 1,
                "content": "AI is transforming business with 40% productivity gains.",
                "length": 50,
                "key_phrases": ["AI", "business"],
                "sentiment": "positive",
                "has_numbers": True,
                "has_questions": False,
                "has_calls_to_action": False
            }
        ]
        
        result = await service._transform_to_email_newsletter(key_points, "Professional")
        
        assert result is not None
        assert "subject_line" in result
        assert "greeting" in result
        assert "main_content" in result
        assert "signature" in result
    
    @pytest.mark.asyncio
    async def test_transform_to_blog_post(self, service):
        """Test transformation to blog post format."""
        key_points = [
            {
                "id": 1,
                "content": "AI is transforming business with 40% productivity gains.",
                "length": 50,
                "key_phrases": ["AI", "business"],
                "sentiment": "positive",
                "has_numbers": True,
                "has_questions": False,
                "has_calls_to_action": False
            }
        ]
        
        result = await service._transform_to_blog_post(key_points, "Professional")
        
        assert result is not None
        assert "title" in result
        assert "introduction" in result
        assert "body" in result
        assert "conclusion" in result
    
    def test_select_engaging_points(self, service):
        """Test selection of engaging points for social media."""
        key_points = [
            {
                "id": 1,
                "content": "Short content",
                "length": 50,
                "sentiment": "positive",
                "has_questions": True,
                "has_calls_to_action": True,
                "has_numbers": True
            },
            {
                "id": 2,
                "content": "Longer content that might not be as engaging",
                "length": 200,
                "sentiment": "neutral",
                "has_questions": False,
                "has_calls_to_action": False,
                "has_numbers": False
            }
        ]
        
        selected = service._select_engaging_points(key_points, 100)
        
        # Should select the first point as it's more engaging
        assert len(selected) == 1
        assert selected[0]["id"] == 1
    
    def test_format_social_media_content(self, service):
        """Test social media content formatting."""
        points = [
            {
                "content": "AI is transforming business",
                "key_phrases": ["AI", "business"]
            }
        ]
        
        result = service._format_social_media_content(
            points, Platform.TWITTER, "Professional", 280
        )
        
        assert result is not None
        assert "🤖" in result  # Should add relevant emoji
        assert "#" in result  # Should add hashtags
    
    def test_get_relevant_emoji(self, service):
        """Test emoji selection based on content."""
        # Test AI/technology content
        assert service._get_relevant_emoji("AI technology future") == "🤖"
        
        # Test success/growth content
        assert service._get_relevant_emoji("success growth improvement") == "🚀"
        
        # Test business/money content
        assert service._get_relevant_emoji("money business profit") == "💰"
        
        # Test default case
        assert service._get_relevant_emoji("random content") == "📝"
    
    def test_generate_relevant_hashtags(self, service):
        """Test hashtag generation."""
        points = [
            {
                "key_phrases": ["Artificial Intelligence", "Business Growth"]
            }
        ]
        
        # Test Twitter hashtags
        twitter_hashtags = service._generate_relevant_hashtags(points, Platform.TWITTER)
        assert "#ContentMarketing" in twitter_hashtags
        assert "#AI" in twitter_hashtags
        
        # Test LinkedIn hashtags
        linkedin_hashtags = service._generate_relevant_hashtags(points, Platform.LINKEDIN)
        assert "#ProfessionalDevelopment" in linkedin_hashtags
        assert "#Innovation" in linkedin_hashtags
    
    def test_improve_readability(self, service):
        """Test readability improvement."""
        long_sentence = "This is a very long sentence that contains many words and should be broken down into smaller more manageable pieces for better readability and comprehension by the reader."
        
        improved = service._improve_readability(long_sentence)
        
        # Should break long sentences
        sentences = improved.split('. ')
        assert len(sentences) > 1
        assert all(len(sentence) <= 100 for sentence in sentences if sentence)
    
    def test_ensure_brand_voice_consistency(self, service):
        """Test brand voice consistency."""
        # Test professional voice
        content = "Hey there! This is awesome content."
        professional = service._ensure_brand_voice_consistency(content, "Professional")
        assert "Hey there!" not in professional
        assert "Hello" in professional
        
        # Test casual voice
        content = "Hello, this is content."
        casual = service._ensure_brand_voice_consistency(content, "Casual")
        assert "Hey there!" in casual
    
    def test_optimize_for_platforms(self, service):
        """Test platform-specific optimization."""
        # Test Twitter optimization
        content = "This is content without hashtags."
        twitter_optimized = service._optimize_for_platforms(content, Platform.TWITTER)
        assert "#ContentMarketing" in twitter_optimized
        
        # Test LinkedIn optimization
        content = "Hey there! This is content."
        linkedin_optimized = service._optimize_for_platforms(content, Platform.LINKEDIN)
        assert "Hello" in linkedin_optimized
    
    def test_calculate_quality_metrics(self, service):
        """Test quality metrics calculation."""
        source_content = "This is source content with multiple sentences. It has some content."
        target_content = "This is target content with questions? And exclamations! And hashtags #content"
        
        metrics = service._calculate_quality_metrics(
            source_content, target_content, ContentType.BLOG_POST, 
            ContentType.SOCIAL_MEDIA_POST, [Platform.TWITTER]
        )
        
        assert "compression_ratio" in metrics
        assert "readability" in metrics
        assert "engagement_score" in metrics
        assert "platform_optimization_score" in metrics
        assert "overall_quality_score" in metrics
        assert "meets_requirements" in metrics
        
        # Test engagement score calculation
        assert metrics["engagement_score"] > 0  # Should have questions, exclamations, hashtags
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test successful health check."""
        with patch.object(service, 'repurpose_content') as mock_repurpose:
            mock_result = Mock()
            mock_result.repurposed_content = "Test content"
            mock_repurpose.return_value = mock_result
            
            result = await service.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """Test failed health check."""
        with patch.object(service, 'repurpose_content', side_effect=Exception("Test error")):
            result = await service.health_check()
            assert result is False


class TestSingletonInstance:
    """Test the singleton instance of the service."""
    
    def test_singleton_instance(self):
        """Test that the singleton instance is created correctly."""
        assert content_repurposing_service is not None
        assert isinstance(content_repurposing_service, ContentRepurposingService)
    
    def test_singleton_consistency(self):
        """Test that the singleton instance is consistent."""
        instance1 = content_repurposing_service
        instance2 = content_repurposing_service
        assert instance1 is instance2


class TestIntegration:
    """Integration tests for the content repurposing service."""
    
    @pytest.mark.asyncio
    async def test_full_repurposing_workflow(self):
        """Test the complete repurposing workflow."""
        service = ContentRepurposingService()
        sample_content = """
        Artificial Intelligence is revolutionizing content creation. 
        Companies using AI see 40% increase in engagement rates.
        
        The key is to understand your audience and create personalized content.
        What questions do they have? What problems do they need solved?
        
        Start implementing AI-powered content strategies today to stay ahead of the competition.
        """
        
        with patch('app.services.content_repurposing.get_repurposing_rules') as mock_rules:
            mock_rule = Mock()
            mock_rule.transformation_rules = ["extract_key_points", "format_for_platform"]
            mock_rule.content_adaptations = ["optimize_length", "add_hashtags"]
            mock_rules.return_value = [mock_rule]
            
            with patch.object(service, '_apply_repurposing_logic', return_value="Repurposed content"):
                with patch.object(service, '_optimize_content', return_value="Optimized content"):
                    result = await service.repurpose_content(
                        source_content=sample_content,
                        source_type=ContentType.BLOG_POST,
                        target_type=ContentType.SOCIAL_MEDIA_POST,
                        target_platforms=[Platform.TWITTER],
                        brand_voice="Professional and engaging"
                    )
            
            # Verify the complete result structure
            assert result.source_content == sample_content
            assert result.repurposed_content == "Optimized content"
            assert result.quality_metrics["meets_requirements"] is True
            assert len(result.metadata) > 0
            assert "repurposed_at" in result.metadata
    
    @pytest.mark.asyncio
    async def test_multiple_platform_repurposing(self):
        """Test repurposing for multiple platforms."""
        service = ContentRepurposingService()
        sample_content = "AI is transforming content creation with amazing results."
        
        with patch('app.services.content_repurposing.get_repurposing_rules') as mock_rules:
            mock_rule = Mock()
            mock_rule.transformation_rules = ["extract_key_points"]
            mock_rule.content_adaptations = ["optimize_length"]
            mock_rules.return_value = [mock_rule]
            
            with patch.object(service, '_apply_repurposing_logic', return_value="Repurposed content"):
                with patch.object(service, '_optimize_content', return_value="Optimized content"):
                    result = await service.repurpose_content(
                        source_content=sample_content,
                        source_type=ContentType.BLOG_POST,
                        target_type=ContentType.SOCIAL_MEDIA_POST,
                        target_platforms=[Platform.TWITTER, Platform.LINKEDIN],
                        brand_voice="Professional"
                    )
            
            assert len(result.target_platforms) == 2
            assert Platform.TWITTER in result.target_platforms
            assert Platform.LINKEDIN in result.target_platforms


if __name__ == "__main__":
    pytest.main([__file__])
