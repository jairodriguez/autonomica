"""
Tests for content types and formats module
"""

import pytest
from app.services.content_types import (
    ContentType,
    ContentFormat,
    Platform,
    ContentStructure,
    PlatformRequirements,
    ContentTemplate,
    RepurposingRule,
    get_content_structure,
    get_platform_requirements,
    get_content_template,
    get_repurposing_rules,
    get_supported_formats,
    get_platform_formats,
    validate_content_length,
    CONTENT_STRUCTURES,
    PLATFORM_REQUIREMENTS,
    CONTENT_TEMPLATES,
    REPURPOSING_RULES
)


class TestContentTypes:
    """Test content type enums and basic functionality"""
    
    def test_content_type_enum_values(self):
        """Test that content type enum values are correct"""
        assert ContentType.BLOG_POST == "blog_post"
        assert ContentType.SOCIAL_MEDIA_POST == "social_media_post"
        assert ContentType.VIDEO_SCRIPT == "video_script"
        assert ContentType.EMAIL_NEWSLETTER == "email_newsletter"
    
    def test_content_format_enum_values(self):
        """Test that content format enum values are correct"""
        assert ContentFormat.PLAIN_TEXT == "plain_text"
        assert ContentFormat.MARKDOWN == "markdown"
        assert ContentFormat.TWEET == "tweet"
        assert ContentFormat.LINKEDIN_POST == "linkedin_post"
    
    def test_platform_enum_values(self):
        """Test that platform enum values are correct"""
        assert Platform.TWITTER == "twitter"
        assert Platform.LINKEDIN == "linkedin"
        assert Platform.INSTAGRAM == "instagram"
        assert Platform.WEBSITE == "website"


class TestContentStructures:
    """Test content structure definitions"""
    
    def test_blog_post_structure(self):
        """Test blog post content structure"""
        structure = CONTENT_STRUCTURES[ContentType.BLOG_POST]
        assert structure.content_type == ContentType.BLOG_POST
        assert "title" in structure.required_sections
        assert "introduction" in structure.required_sections
        assert "body" in structure.required_sections
        assert "conclusion" in structure.required_sections
        assert structure.max_length == 5000
        assert structure.min_length == 300
        assert structure.recommended_length == 1500
        assert ContentFormat.MARKDOWN in structure.format_requirements
    
    def test_social_media_post_structure(self):
        """Test social media post content structure"""
        structure = CONTENT_STRUCTURES[ContentType.SOCIAL_MEDIA_POST]
        assert structure.content_type == ContentType.SOCIAL_MEDIA_POST
        assert "main_content" in structure.required_sections
        assert structure.max_length == 280
        assert structure.min_length == 10
        assert structure.recommended_length == 200
    
    def test_video_script_structure(self):
        """Test video script content structure"""
        structure = CONTENT_STRUCTURES[ContentType.VIDEO_SCRIPT]
        assert structure.content_type == ContentType.VIDEO_SCRIPT
        assert "hook" in structure.required_sections
        assert "introduction" in structure.required_sections
        assert "main_content" in structure.required_sections
        assert "conclusion" in structure.required_sections


class TestPlatformRequirements:
    """Test platform-specific requirements"""
    
    def test_twitter_requirements(self):
        """Test Twitter platform requirements"""
        requirements = PLATFORM_REQUIREMENTS[Platform.TWITTER]
        assert requirements.platform == Platform.TWITTER
        assert ContentFormat.TWEET in requirements.content_formats
        assert ContentFormat.THREAD in requirements.content_formats
        assert requirements.character_limits["tweet"] == 280
        assert requirements.hashtag_limits == 30
        assert "image" in requirements.media_requirements
        assert "video" in requirements.media_requirements
        assert len(requirements.best_practices) > 0
        assert len(requirements.engagement_tips) > 0
    
    def test_linkedin_requirements(self):
        """Test LinkedIn platform requirements"""
        requirements = PLATFORM_REQUIREMENTS[Platform.LINKEDIN]
        assert requirements.platform == Platform.LINKEDIN
        assert ContentFormat.LINKEDIN_POST in requirements.content_formats
        assert ContentFormat.ARTICLE in requirements.content_formats
        assert requirements.character_limits["post"] == 3000
        assert requirements.character_limits["article"] == 100000
        assert len(requirements.best_practices) > 0
        assert len(requirements.engagement_tips) > 0
    
    def test_instagram_requirements(self):
        """Test Instagram platform requirements"""
        requirements = PLATFORM_REQUIREMENTS[Platform.INSTAGRAM]
        assert requirements.platform == Platform.INSTAGRAM
        assert ContentFormat.INSTAGRAM_CAPTION in requirements.content_formats
        assert ContentFormat.STORY in requirements.content_formats
        assert ContentFormat.REEL in requirements.content_formats
        assert requirements.character_limits["caption"] == 2200
        assert requirements.hashtag_limits == 30


class TestContentTemplates:
    """Test content templates"""
    
    def test_blog_to_tweet_template(self):
        """Test blog to tweet conversion template"""
        template = CONTENT_TEMPLATES["blog_to_tweet"]
        assert template.name == "Blog to Tweet Conversion"
        assert template.content_type == ContentType.SOCIAL_MEDIA_POST
        assert Platform.TWITTER in template.target_platforms
        assert "blog_content" in template.variables
        assert "num_tweets" in template.variables
        assert "brand_voice" in template.variables
        assert len(template.examples) > 0
    
    def test_blog_to_linkedin_template(self):
        """Test blog to LinkedIn conversion template"""
        template = CONTENT_TEMPLATES["blog_to_linkedin"]
        assert template.name == "Blog to LinkedIn Post"
        assert template.content_type == ContentType.SOCIAL_MEDIA_POST
        assert Platform.LINKEDIN in template.target_platforms
        assert "blog_content" in template.variables
        assert len(template.examples) > 0


class TestRepurposingRules:
    """Test content repurposing rules"""
    
    def test_blog_to_tweet_rules(self):
        """Test blog to tweet repurposing rules"""
        rules = [r for r in REPURPOSING_RULES 
                if r.source_type == ContentType.BLOG_POST and r.target_type == ContentType.SOCIAL_MEDIA_POST]
        assert len(rules) > 0
        
        rule = rules[0]
        assert rule.source_format == ContentFormat.MARKDOWN
        assert rule.target_format == ContentFormat.TWEET
        assert len(rule.transformation_rules) > 0
        assert len(rule.content_adaptations) > 0
        assert len(rule.quality_checks) > 0
    
    def test_blog_to_video_script_rules(self):
        """Test blog to video script repurposing rules"""
        rules = [r for r in REPURPOSING_RULES 
                if r.source_type == ContentType.BLOG_POST and r.target_type == ContentType.VIDEO_SCRIPT]
        assert len(rules) > 0
        
        rule = rules[0]
        assert rule.source_format == ContentFormat.MARKDOWN
        assert rule.target_format == ContentFormat.PLAIN_TEXT
        assert len(rule.transformation_rules) > 0
        assert len(rule.content_adaptations) > 0
        assert len(rule.quality_checks) > 0


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_content_structure(self):
        """Test get_content_structure function"""
        structure = get_content_structure(ContentType.BLOG_POST)
        assert structure is not None
        assert structure.content_type == ContentType.BLOG_POST
        
        # Test unknown content type
        structure = get_content_structure("unknown_type")
        assert structure is None
    
    def test_get_platform_requirements(self):
        """Test get_platform_requirements function"""
        requirements = get_platform_requirements(Platform.TWITTER)
        assert requirements is not None
        assert requirements.platform == Platform.TWITTER
        
        # Test unknown platform
        requirements = get_platform_requirements("unknown_platform")
        assert requirements is None
    
    def test_get_content_template(self):
        """Test get_content_template function"""
        template = get_content_template("blog_to_tweet")
        assert template is not None
        assert template.name == "Blog to Tweet Conversion"
        
        # Test unknown template
        template = get_content_template("unknown_template")
        assert template is None
    
    def test_get_repurposing_rules(self):
        """Test get_repurposing_rules function"""
        rules = get_repurposing_rules(ContentType.BLOG_POST, ContentType.SOCIAL_MEDIA_POST)
        assert len(rules) > 0
        assert all(r.source_type == ContentType.BLOG_POST for r in rules)
        assert all(r.target_type == ContentType.SOCIAL_MEDIA_POST for r in rules)
    
    def test_get_supported_formats(self):
        """Test get_supported_formats function"""
        formats = get_supported_formats(ContentType.BLOG_POST)
        assert len(formats) > 0
        assert ContentFormat.MARKDOWN in formats
        assert ContentFormat.HTML in formats
    
    def test_get_platform_formats(self):
        """Test get_platform_formats function"""
        formats = get_platform_formats(Platform.TWITTER)
        assert len(formats) > 0
        assert ContentFormat.TWEET in formats
        assert ContentFormat.THREAD in formats
    
    def test_validate_content_length_valid(self):
        """Test content length validation with valid content"""
        content = "This is a valid blog post content that meets the minimum length requirements."
        result = validate_content_length(content, ContentType.BLOG_POST)
        assert result["valid"] is True
        assert result["content_length"] == len(content)
        assert "min_length" in result["requirements"]
        assert "max_length" in result["requirements"]
    
    def test_validate_content_length_too_short(self):
        """Test content length validation with content that's too short"""
        content = "Too short"
        result = validate_content_length(content, ContentType.BLOG_POST)
        assert result["valid"] is False
        assert len(result["warnings"]) > 0
        assert any("too short" in warning.lower() for warning in result["warnings"])
    
    def test_validate_content_length_too_long(self):
        """Test content length validation with content that's too long"""
        content = "x" * 6000  # Exceeds max length of 5000
        result = validate_content_length(content, ContentType.BLOG_POST)
        assert result["valid"] is False
        assert len(result["warnings"]) > 0
        assert any("too long" in warning.lower() for warning in result["warnings"])
    
    def test_validate_content_length_unknown_type(self):
        """Test content length validation with unknown content type"""
        content = "Some content"
        result = validate_content_length(content, "unknown_type")
        assert result["valid"] is False
        assert "error" in result
        assert "Unknown content type" in result["error"]


class TestIntegration:
    """Test integration between different components"""
    
    def test_content_type_format_consistency(self):
        """Test that content types and formats are consistent"""
        for content_type in ContentType:
            structure = get_content_structure(content_type)
            if structure:
                # All formats in structure should be valid ContentFormat values
                for format_type in structure.format_requirements:
                    assert format_type in ContentFormat
    
    def test_platform_format_consistency(self):
        """Test that platforms and formats are consistent"""
        for platform in Platform:
            requirements = get_platform_requirements(platform)
            if requirements:
                # All formats in requirements should be valid ContentFormat values
                for format_type in requirements.content_formats:
                    assert format_type in ContentFormat
    
    def test_template_structure_consistency(self):
        """Test that templates reference valid structures"""
        for template in CONTENT_TEMPLATES.values():
            # Template should reference a valid content structure
            assert template.structure in CONTENT_STRUCTURES.values()
            
            # Template should reference valid platforms
            for platform in template.target_platforms:
                assert platform in Platform
    
    def test_repurposing_rules_consistency(self):
        """Test that repurposing rules reference valid types and formats"""
        for rule in REPURPOSING_RULES:
            # Source and target types should be valid ContentType values
            assert rule.source_type in ContentType
            assert rule.target_type in ContentType
            
            # Source and target formats should be valid ContentFormat values
            assert rule.source_format in ContentFormat
            assert rule.target_format in ContentFormat


if __name__ == "__main__":
    pytest.main([__file__])
