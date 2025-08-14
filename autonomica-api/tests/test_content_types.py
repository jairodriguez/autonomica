"""
Test module for content types and formats functionality.
"""

import pytest
from app.ai.content_types import (
    ContentType,
    ContentFormat,
    ContentStructure,
    ContentTransformation,
    ContentTypeRegistry,
    get_content_registry,
    validate_content_structure,
    get_content_type_by_name,
    format_content_for_type
)


class TestContentTypes:
    """Test cases for ContentType enum."""
    
    def test_content_type_values(self):
        """Test that content types have correct string values."""
        assert ContentType.BLOG_POST == "blog_post"
        assert ContentType.TWEET == "tweet"
        assert ContentType.VIDEO_SCRIPT == "video_script"
    
    def test_content_type_count(self):
        """Test that we have the expected number of content types."""
        # We should have at least 20+ content types
        assert len(ContentType) >= 20


class TestContentFormats:
    """Test cases for ContentFormat enum."""
    
    def test_content_format_values(self):
        """Test that content formats have correct string values."""
        assert ContentFormat.PLAIN_TEXT == "plain_text"
        assert ContentFormat.MARKDOWN == "markdown"
        assert ContentFormat.HASHTAGS == "hashtags"
    
    def test_content_format_count(self):
        """Test that we have the expected number of content formats."""
        # We should have at least 15+ formats
        assert len(ContentFormat) >= 15


class TestContentStructure:
    """Test cases for ContentStructure model."""
    
    def test_blog_post_structure(self):
        """Test blog post structure definition."""
        structure = ContentStructure(
            content_type=ContentType.BLOG_POST,
            sections=["title", "introduction", "main_content", "conclusion"],
            required_sections=["title", "introduction", "main_content", "conclusion"],
            optional_sections=["meta_description", "call_to_action"],
            word_count_range=(800, 3000),
            character_limit=None
        )
        
        assert structure.content_type == ContentType.BLOG_POST
        assert len(structure.sections) == 4
        assert "title" in structure.required_sections
        assert structure.word_count_range == (800, 3000)
    
    def test_tweet_structure(self):
        """Test tweet structure definition."""
        structure = ContentStructure(
            content_type=ContentType.TWEET,
            sections=["content", "hashtags"],
            required_sections=["content"],
            optional_sections=["hashtags", "mentions"],
            word_count_range=(1, 50),
            character_limit=280
        )
        
        assert structure.content_type == ContentType.TWEET
        assert structure.character_limit == 280
        assert "content" in structure.required_sections


class TestContentTransformation:
    """Test cases for ContentTransformation model."""
    
    def test_transformation_creation(self):
        """Test creating a content transformation."""
        transformation = ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET,
            transformation_method="extract_key_points",
            complexity="Simple",
            estimated_time=30,
            quality_impact="Medium"
        )
        
        assert transformation.source_type == ContentType.BLOG_POST
        assert transformation.target_type == ContentType.TWEET
        assert transformation.complexity == "Simple"
        assert transformation.estimated_time == 30


class TestContentTypeRegistry:
    """Test cases for ContentTypeRegistry."""
    
    def test_registry_initialization(self):
        """Test that registry initializes with all content types."""
        registry = ContentTypeRegistry()
        
        # Should have structures for all content types
        assert len(registry.content_structures) >= 20
        
        # Should have transformation rules
        assert len(registry.transformations) >= 10
    
    def test_get_content_structure(self):
        """Test retrieving content structure from registry."""
        registry = ContentTypeRegistry()
        
        blog_structure = registry.get_content_structure(ContentType.BLOG_POST)
        assert blog_structure is not None
        assert blog_structure.content_type == ContentType.BLOG_POST
        assert "title" in blog_structure.required_sections
        
        tweet_structure = registry.get_content_structure(ContentType.TWEET)
        assert tweet_structure is not None
        assert tweet_structure.character_limit == 280
    
    def test_get_available_transformations(self):
        """Test getting available transformations from a source type."""
        registry = ContentTypeRegistry()
        
        blog_transformations = registry.get_available_transformations(ContentType.BLOG_POST)
        assert len(blog_transformations) >= 5  # Blog should have multiple transformation options
        
        # Check that all transformations are from blog post
        for transformation in blog_transformations:
            assert transformation.source_type == ContentType.BLOG_POST
    
    def test_get_transformation_path(self):
        """Test getting specific transformation path between two types."""
        registry = ContentTypeRegistry()
        
        # Test blog to tweet transformation
        transformation = registry.get_transformation_path(
            ContentType.BLOG_POST, 
            ContentType.TWEET
        )
        assert transformation is not None
        assert transformation.source_type == ContentType.BLOG_POST
        assert transformation.target_type == ContentType.TWEET
        
        # Test non-existent transformation
        transformation = registry.get_transformation_path(
            ContentType.TWEET, 
            ContentType.BLOG_POST
        )
        assert transformation is None
    
    def test_list_all_content_types(self):
        """Test listing all available content types."""
        registry = ContentTypeRegistry()
        
        content_types = registry.list_all_content_types()
        assert len(content_types) >= 20
        assert ContentType.BLOG_POST in content_types
        assert ContentType.TWEET in content_types
        assert ContentType.VIDEO_SCRIPT in content_types
    
    def test_list_all_formats(self):
        """Test listing all available content formats."""
        registry = ContentTypeRegistry()
        
        formats = registry.list_all_formats()
        assert len(formats) >= 15
        assert ContentFormat.PLAIN_TEXT in formats
        assert ContentFormat.MARKDOWN in formats
        assert ContentFormat.HASHTAGS in formats
    
    def test_get_content_type_metadata(self):
        """Test getting metadata for all content types."""
        registry = ContentTypeRegistry()
        
        metadata = registry.get_content_type_metadata()
        assert len(metadata) >= 20
        
        # Check blog post metadata
        blog_metadata = metadata.get("blog_post")
        assert blog_metadata is not None
        assert "sections" in blog_metadata
        assert "required_sections" in blog_metadata
        assert "word_count_range" in blog_metadata


class TestGlobalFunctions:
    """Test cases for global utility functions."""
    
    def test_get_content_registry(self):
        """Test getting the global content registry."""
        registry = get_content_registry()
        assert isinstance(registry, ContentTypeRegistry)
        assert len(registry.content_structures) >= 20
    
    def test_validate_content_structure(self):
        """Test content structure validation."""
        # Valid blog post content
        valid_blog_content = {
            "title": "Test Blog Post",
            "introduction": "This is an introduction",
            "main_content": "This is the main content of the blog post with enough words to meet the minimum requirement",
            "conclusion": "This is the conclusion"
        }
        
        assert validate_content_structure(ContentType.BLOG_POST, valid_blog_content) is True
        
        # Invalid blog post content (missing required section)
        invalid_blog_content = {
            "title": "Test Blog Post",
            "introduction": "This is an introduction"
            # Missing main_content and conclusion
        }
        
        assert validate_content_structure(ContentType.BLOG_POST, invalid_blog_content) is False
    
    def test_get_content_type_by_name(self):
        """Test getting content type by name string."""
        assert get_content_type_by_name("blog_post") == ContentType.BLOG_POST
        assert get_content_type_by_name("tweet") == ContentType.TWEET
        assert get_content_type_by_name("invalid_type") is None
        assert get_content_type_by_name("BLOG_POST") == ContentType.BLOG_POST  # Case insensitive
    
    def test_format_content_for_type(self):
        """Test formatting content for specific content types."""
        # Test tweet formatting with character limit
        long_content = "This is a very long tweet that exceeds the character limit for Twitter"
        formatted_tweet = format_content_for_type(long_content, ContentType.TWEET)
        assert len(formatted_tweet) <= 280
        
        # Test adding hashtags for social media
        content = "This is a social media post"
        formatted_social = format_content_for_type(content, ContentType.FACEBOOK_POST)
        assert "#" in formatted_social
        
        # Test no hashtags when disabled
        formatted_no_hashtags = format_content_for_type(
            content, 
            ContentType.FACEBOOK_POST, 
            add_hashtags=False
        )
        assert "#" not in formatted_no_hashtags


class TestIntegration:
    """Integration tests for the content types system."""
    
    def test_complete_workflow(self):
        """Test a complete content transformation workflow."""
        registry = get_content_registry()
        
        # 1. Get source content structure
        blog_structure = registry.get_content_structure(ContentType.BLOG_POST)
        assert blog_structure is not None
        
        # 2. Get available transformations
        transformations = registry.get_available_transformations(ContentType.BLOG_POST)
        assert len(transformations) > 0
        
        # 3. Find specific transformation path
        tweet_transformation = registry.get_transformation_path(
            ContentType.BLOG_POST, 
            ContentType.TWEET
        )
        assert tweet_transformation is not None
        assert tweet_transformation.complexity == "Simple"
        
        # 4. Validate content structure
        sample_blog = {
            "title": "Sample Blog",
            "introduction": "Introduction text",
            "main_content": "Main content with sufficient words to meet requirements",
            "conclusion": "Conclusion text"
        }
        assert validate_content_structure(ContentType.BLOG_POST, sample_blog) is True
        
        # 5. Format content for target type
        formatted_tweet = format_content_for_type(
            "Sample content for tweet", 
            ContentType.TWEET
        )
        assert len(formatted_tweet) <= 280


if __name__ == "__main__":
    pytest.main([__file__])