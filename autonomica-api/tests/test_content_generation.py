"""
Tests for content generation service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.services.content_generation import ContentGenerationService
from app.services.content_types import ContentType, ContentFormat, Platform


class TestContentGenerationService:
    """Test content generation service functionality"""
    
    @pytest.fixture
    def mock_ai_manager(self):
        """Create a mock AI manager for testing"""
        mock_manager = Mock()
        mock_manager.execute = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def service(self, mock_ai_manager):
        """Create a service instance with mocked dependencies"""
        with patch('app.services.content_generation.ai_manager', mock_ai_manager):
            service = ContentGenerationService()
            service.ai_manager = mock_ai_manager
            return service
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.default_model == "gpt-4"
        assert service.fallback_model == "gpt-3.5-turbo"
        assert service.ai_manager is not None
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, service, mock_ai_manager):
        """Test successful content generation"""
        # Mock AI manager response
        mock_response = {
            "content": "This is a test blog post about AI and machine learning.",
            "model": "gpt-4",
            "usage": {"total_tokens": 50}
        }
        mock_ai_manager.execute.return_value = mock_response
        
        # Test content generation
        result = await service.generate_content(
            ContentType.BLOG_POST,
            "Write a blog post about AI",
            [Platform.WEBSITE],
            "Professional and engaging"
        )
        
        # Verify result structure
        assert "content" in result
        assert "raw_content" in result
        assert result["content_type"] == ContentType.BLOG_POST
        assert result["target_platforms"] == [Platform.WEBSITE]
        assert result["brand_voice"] == "Professional and engaging"
        assert "validation" in result
        assert "metadata" in result
        
        # Verify AI manager was called
        mock_ai_manager.execute.assert_called_once()
        call_args = mock_ai_manager.execute.call_args
        assert "Write a blog post about AI" in call_args[0][0]  # Check prompt contains user input
    
    @pytest.mark.asyncio
    async def test_generate_content_unknown_type(self, service):
        """Test content generation with unknown content type"""
        with pytest.raises(ValueError, match="Unknown content type"):
            await service.generate_content(
                "unknown_type",  # Invalid content type
                "Test prompt",
                [Platform.WEBSITE]
            )
    
    @pytest.mark.asyncio
    async def test_repurpose_content_success(self, service, mock_ai_manager):
        """Test successful content repurposing"""
        # Mock AI manager response
        mock_response = {
            "content": "🚀 AI is revolutionizing content marketing! #AI #Marketing",
            "model": "gpt-4",
            "usage": {"total_tokens": 30}
        }
        mock_ai_manager.execute.return_value = mock_response
        
        # Test content repurposing
        source_content = "AI is revolutionizing content marketing by providing new tools and capabilities."
        result = await service.repurpose_content(
            source_content,
            ContentType.BLOG_POST,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.TWITTER],
            "Professional and engaging"
        )
        
        # Verify result structure
        assert "content" in result
        assert "raw_content" in result
        assert result["source_type"] == ContentType.BLOG_POST
        assert result["target_type"] == ContentType.SOCIAL_MEDIA_POST
        assert result["target_platforms"] == [Platform.TWITTER]
        assert "repurposing_rules_applied" in result
        assert "metadata" in result
        
        # Verify AI manager was called
        mock_ai_manager.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_repurpose_content_no_rules(self, service):
        """Test content repurposing with no available rules"""
        with pytest.raises(ValueError, match="No repurposing rules found"):
            await service.repurpose_content(
                "Test content",
                ContentType.VIDEO_SCRIPT,  # No rules for this combination
                ContentType.BLOG_POST,
                [Platform.WEBSITE]
            )
    
    @pytest.mark.asyncio
    async def test_generate_social_media_content_success(self, service, mock_ai_manager):
        """Test successful social media content generation"""
        # Mock AI manager response
        mock_response = {
            "content": "1. 🚀 AI is transforming marketing! #AI #Marketing\n\n2. Learn how AI tools boost productivity #Productivity #AI\n\n3. The future of content creation is here #FutureOfWork",
            "model": "gpt-4",
            "usage": {"total_tokens": 80}
        }
        mock_ai_manager.execute.return_value = mock_response
        
        # Test social media generation
        blog_content = "AI is transforming marketing by providing new tools and capabilities that boost productivity and creativity."
        result = await service.generate_social_media_content(
            blog_content,
            [Platform.TWITTER, Platform.LINKEDIN],
            num_posts=3,
            brand_voice="Professional and engaging"
        )
        
        # Verify result structure
        assert "social_posts" in result
        assert "raw_content" in result
        assert result["source_content_length"] == len(blog_content)
        assert result["target_platforms"] == [Platform.TWITTER, Platform.LINKEDIN]
        assert result["num_posts"] == 3
        assert result["brand_voice"] == "Professional and engaging"
        assert "metadata" in result
        
        # Verify social posts were parsed correctly
        social_posts = result["social_posts"]
        assert len(social_posts) == 3
        assert all("content" in post for post in social_posts)
        assert all("platform" in post for post in social_posts)
    
    def test_build_enhanced_prompt(self, service):
        """Test enhanced prompt building"""
        prompt = service._build_enhanced_prompt(
            ContentType.BLOG_POST,
            "Write about AI",
            [Platform.WEBSITE],
            "Professional",
            service._get_content_structure(ContentType.BLOG_POST)
        )
        
        assert "Write about AI" in prompt
        assert "blog_post" in prompt
        assert "title" in prompt  # Required section
        assert "introduction" in prompt  # Required section
        assert "body" in prompt  # Required section
        assert "conclusion" in prompt  # Required section
        assert "Professional" in prompt
    
    def test_build_repurposing_prompt(self, service):
        """Test repurposing prompt building"""
        # Mock repurposing rule
        mock_rule = Mock()
        mock_rule.transformation_rules = ["Extract key points", "Condense content"]
        mock_rule.content_adaptations = ["Add hashtags", "Use emojis"]
        mock_rule.quality_checks = ["Check length", "Verify tone"]
        
        prompt = service._build_repurposing_prompt(
            "Source content here",
            ContentType.BLOG_POST,
            ContentType.SOCIAL_MEDIA_POST,
            [Platform.TWITTER],
            "Professional",
            mock_rule
        )
        
        assert "Source content here" in prompt
        assert "blog_post" in prompt
        assert "social_media_post" in prompt
        assert "Extract key points" in prompt
        assert "Add hashtags" in prompt
        assert "Check length" in prompt
    
    def test_build_social_media_prompt(self, service):
        """Test social media prompt building"""
        prompt = service._build_social_media_prompt(
            "Blog content about AI",
            [Platform.TWITTER, Platform.LINKEDIN],
            3,
            "Professional"
        )
        
        assert "Blog content about AI" in prompt
        assert "3" in prompt
        assert "Professional" in prompt
        assert "twitter" in prompt.lower()
        assert "linkedin" in prompt.lower()
    
    def test_get_default_max_tokens(self, service):
        """Test default max tokens calculation"""
        # Test with blog post (has recommended length)
        tokens = service._get_default_max_tokens(ContentType.BLOG_POST)
        assert tokens > 0
        
        # Test with unknown type (should return default)
        tokens = service._get_default_max_tokens("unknown_type")
        assert tokens == 1000
    
    def test_parse_structured_content(self, service):
        """Test structured content parsing"""
        content = "This is test content for parsing."
        result = service._parse_structured_content(content, ContentType.BLOG_POST)
        
        assert "raw" in result
        assert "sections" in result
        assert "length" in result
        assert "word_count" in result
        assert result["length"] == len(content)
        assert result["word_count"] == 7
    
    def test_parse_social_media_posts(self, service):
        """Test social media posts parsing"""
        content = "1. First post content\n\n2. Second post content\n\n3. Third post content"
        platforms = [Platform.TWITTER, Platform.LINKEDIN]
        
        posts = service._parse_social_media_posts(content, platforms)
        
        assert len(posts) == 3
        assert posts[0]["content"].startswith("1. First post content")
        assert posts[1]["content"].startswith("2. Second post content")
        assert posts[2]["content"].startswith("3. Third post content")
        
        # Check platform assignment
        assert posts[0]["platform"] == Platform.TWITTER
        assert posts[1]["platform"] == Platform.LINKEDIN
        assert posts[2]["platform"] == Platform.TWITTER
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service, mock_ai_manager):
        """Test successful health check"""
        # Mock successful generation
        mock_response = {"content": "Test content"}
        mock_ai_manager.execute.return_value = mock_response
        
        result = await service.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, service, mock_ai_manager):
        """Test failed health check"""
        # Mock failed generation
        mock_ai_manager.execute.side_effect = Exception("AI service unavailable")
        
        result = await service.health_check()
        assert result is False


class TestContentGenerationIntegration:
    """Test integration between content generation and content types"""
    
    def test_content_type_integration(self):
        """Test that content generation service works with content types"""
        from app.services.content_generation import ContentGenerationService
        
        service = ContentGenerationService()
        
        # Verify service can handle all content types
        for content_type in ContentType:
            # This should not raise an error
            structure = service._get_content_structure(content_type)
            # Some content types might not have structures defined yet
            if structure:
                assert structure.content_type == content_type
    
    def test_platform_integration(self):
        """Test that content generation service works with platforms"""
        from app.services.content_generation import ContentGenerationService
        
        service = ContentGenerationService()
        
        # Verify service can handle all platforms
        for platform in Platform:
            # This should not raise an error
            requirements = service._get_platform_requirements(platform)
            # Some platforms might not have requirements defined yet
            if requirements:
                assert requirements.platform == platform


if __name__ == "__main__":
    pytest.main([__file__])
