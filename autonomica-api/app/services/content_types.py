"""
Content Types and Formats Definition Module

This module defines all content types, formats, and specifications for the
content generation and repurposing pipeline.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Primary content types that can be generated or repurposed"""
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    SOCIAL_MEDIA_POST = "social_media_post"
    VIDEO_SCRIPT = "video_script"
    EMAIL_NEWSLETTER = "email_newsletter"
    PODCAST_SCRIPT = "podcast_script"
    WHITEPAPER = "whitepaper"
    CASE_STUDY = "case_study"
    PRESS_RELEASE = "press_release"
    PRODUCT_DESCRIPTION = "product_description"
    LANDING_PAGE = "landing_page"
    FAQ = "faq"
    HOW_TO_GUIDE = "how_to_guide"
    REVIEW = "review"
    INTERVIEW = "interview"
    OPINION_PIECE = "opinion_piece"
    RESEARCH_PAPER = "research_paper"
    NEWS_UPDATE = "news_update"
    TUTORIAL = "tutorial"
    COMPARISON = "comparison"


class ContentFormat(str, Enum):
    """Content formats for different platforms and use cases"""
    # Text-based formats
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    RICH_TEXT = "rich_text"
    ARTICLE = "article"
    
    # Social media formats
    TWEET = "tweet"
    THREAD = "thread"
    LINKEDIN_POST = "linkedin_post"
    INSTAGRAM_CAPTION = "instagram_caption"
    FACEBOOK_POST = "facebook_post"
    TIKTOK_CAPTION = "tiktok_caption"
    
    # Video formats
    SHORT_FORM_VIDEO = "short_form_video"
    LONG_FORM_VIDEO = "long_form_video"
    LIVE_STREAM = "live_stream"
    STORY = "story"
    REEL = "reel"
    
    # Audio formats
    PODCAST_EPISODE = "podcast_episode"
    AUDIO_BLOG = "audio_blog"
    VOICE_NOTE = "voice_note"
    
    # Visual formats
    INFOGRAPHIC = "infographic"
    CAROUSEL = "carousel"
    SLIDE_DECK = "slide_deck"
    MEME = "meme"
    QUOTE_CARD = "quote_card"
    
    # Interactive formats
    POLL = "poll"
    QUIZ = "quiz"
    SURVEY = "survey"
    INTERACTIVE_STORY = "interactive_story"


class Platform(str, Enum):
    """Target platforms for content distribution"""
    # Social media platforms
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"
    
    # Content platforms
    MEDIUM = "medium"
    SUBSTACK = "substack"
    HASHNODE = "hashnode"
    DEV_TO = "dev_to"
    
    # Video platforms
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK_VIDEO = "tiktok_video"
    
    # Audio platforms
    SPOTIFY = "spotify"
    APPLE_PODCASTS = "apple_podcasts"
    GOOGLE_PODCASTS = "google_podcasts"
    
    # Owned platforms
    WEBSITE = "website"
    BLOG = "blog"
    EMAIL = "email"
    NEWSLETTER = "newsletter"


class ContentStructure(BaseModel):
    """Defines the structure for different content types"""
    content_type: ContentType
    required_sections: List[str] = Field(description="Required sections for this content type")
    optional_sections: List[str] = Field(description="Optional sections for this content type")
    max_length: Optional[int] = Field(description="Maximum character/word count")
    min_length: Optional[int] = Field(description="Minimum character/word count")
    recommended_length: Optional[int] = Field(description="Recommended character/word count")
    format_requirements: List[ContentFormat] = Field(description="Supported formats for this content type")


class PlatformRequirements(BaseModel):
    """Platform-specific requirements and constraints"""
    platform: Platform
    content_formats: List[ContentFormat]
    character_limits: Dict[str, int] = Field(description="Character limits for different elements")
    hashtag_limits: Optional[int] = Field(description="Maximum number of hashtags allowed")
    media_requirements: Dict[str, Any] = Field(description="Media requirements (dimensions, formats, etc.)")
    best_practices: List[str] = Field(description="Platform-specific best practices")
    engagement_tips: List[str] = Field(description="Tips for better engagement on this platform")


class ContentTemplate(BaseModel):
    """Template structure for content generation"""
    name: str
    content_type: ContentType
    target_platforms: List[Platform]
    structure: ContentStructure
    prompt_template: str
    variables: List[str] = Field(description="Template variables that need to be filled")
    examples: List[Dict[str, Any]] = Field(description="Example outputs for this template")


class RepurposingRule(BaseModel):
    """Rules for repurposing content between different formats"""
    source_type: ContentType
    target_type: ContentType
    source_format: ContentFormat
    target_format: ContentFormat
    transformation_rules: List[str] = Field(description="Rules for transforming content")
    content_adaptations: List[str] = Field(description="Required content adaptations")
    quality_checks: List[str] = Field(description="Quality checks for the transformed content")


# Content structure definitions
CONTENT_STRUCTURES = {
    ContentType.BLOG_POST: ContentStructure(
        content_type=ContentType.BLOG_POST,
        required_sections=["title", "introduction", "body", "conclusion"],
        optional_sections=["subtitle", "summary", "key_takeaways", "call_to_action", "related_links"],
        max_length=5000,
        min_length=300,
        recommended_length=1500,
        format_requirements=[ContentFormat.MARKDOWN, ContentFormat.HTML, ContentFormat.RICH_TEXT]
    ),
    
    ContentType.SOCIAL_MEDIA_POST: ContentStructure(
        content_type=ContentType.SOCIAL_MEDIA_POST,
        required_sections=["main_content"],
        optional_sections=["hashtags", "call_to_action", "mention"],
        max_length=280,  # Twitter limit as baseline
        min_length=10,
        recommended_length=200,
        format_requirements=[ContentFormat.PLAIN_TEXT, ContentFormat.TWEET, ContentFormat.LINKEDIN_POST]
    ),
    
    ContentType.VIDEO_SCRIPT: ContentStructure(
        content_type=ContentType.VIDEO_SCRIPT,
        required_sections=["hook", "introduction", "main_content", "conclusion"],
        optional_sections=["call_to_action", "visual_cues", "sound_effects"],
        max_length=2000,
        min_length=100,
        recommended_length=800,
        format_requirements=[ContentFormat.PLAIN_TEXT, ContentFormat.MARKDOWN]
    ),
    
    ContentType.EMAIL_NEWSLETTER: ContentStructure(
        content_type=ContentType.EMAIL_NEWSLETTER,
        required_sections=["subject_line", "greeting", "main_content", "signature"],
        optional_sections=["header_image", "footer", "unsubscribe_link"],
        max_length=1000,
        min_length=200,
        recommended_length=500,
        format_requirements=[ContentFormat.HTML, ContentFormat.RICH_TEXT]
    )
}

# Platform requirements definitions
PLATFORM_REQUIREMENTS = {
    Platform.TWITTER: PlatformRequirements(
        platform=Platform.TWITTER,
        content_formats=[ContentFormat.TWEET, ContentFormat.THREAD],
        character_limits={
            "tweet": 280,
            "thread_tweet": 280,
            "username": 15,
            "display_name": 50
        },
        hashtag_limits=30,
        media_requirements={
            "image": {"max_size": "5MB", "formats": ["JPG", "PNG", "GIF"], "dimensions": "1200x675"},
            "video": {"max_size": "512MB", "formats": ["MP4"], "duration": "2m20s"}
        },
        best_practices=[
            "Use relevant hashtags (1-3 per tweet)",
            "Include engaging visuals",
            "Ask questions to encourage replies",
            "Use conversational tone"
        ],
        engagement_tips=[
            "Reply to mentions quickly",
            "Retweet relevant content",
            "Use Twitter polls for engagement",
            "Post at optimal times (9 AM, 12 PM, 3 PM)"
        ]
    ),
    
    Platform.LINKEDIN: PlatformRequirements(
        platform=Platform.LINKEDIN,
        content_formats=[ContentFormat.LINKEDIN_POST, ContentFormat.ARTICLE],
        character_limits={
            "post": 3000,
            "article": 100000,
            "headline": 220
        },
        hashtag_limits=30,
        media_requirements={
            "image": {"max_size": "5MB", "formats": ["JPG", "PNG"], "dimensions": "1200x627"},
            "video": {"max_size": "200MB", "formats": ["MP4"], "duration": "10m"}
        },
        best_practices=[
            "Use professional tone",
            "Include industry-specific hashtags",
            "Share insights and thought leadership",
            "Engage with comments professionally"
        ],
        engagement_tips=[
            "Post during business hours",
            "Use LinkedIn polls",
            "Tag relevant people and companies",
            "Share industry news and insights"
        ]
    ),
    
    Platform.INSTAGRAM: PlatformRequirements(
        platform=Platform.INSTAGRAM,
        content_formats=[ContentFormat.INSTAGRAM_CAPTION, ContentFormat.STORY, ContentFormat.REEL],
        character_limits={
            "caption": 2200,
            "bio": 150,
            "username": 30
        },
        hashtag_limits=30,
        media_requirements={
            "image": {"formats": ["JPG", "PNG"], "dimensions": "1080x1080"},
            "story": {"dimensions": "1080x1920"},
            "reel": {"dimensions": "1080x1920", "duration": "15s-90s"}
        },
        best_practices=[
            "Use high-quality visuals",
            "Include relevant hashtags in first comment",
            "Use Instagram Stories for behind-the-scenes",
            "Post consistently"
        ],
        engagement_tips=[
            "Use Instagram Stories daily",
            "Engage with followers' content",
            "Use Instagram Reels for trending content",
            "Post during peak hours (7-9 PM)"
        ]
    )
}

# Content templates for different use cases
CONTENT_TEMPLATES = {
    "blog_to_tweet": ContentTemplate(
        name="Blog to Tweet Conversion",
        content_type=ContentType.SOCIAL_MEDIA_POST,
        target_platforms=[Platform.TWITTER],
        structure=CONTENT_STRUCTURES[ContentType.SOCIAL_MEDIA_POST],
        prompt_template="Convert the following blog post into {num_tweets} engaging tweets:\n\n{blog_content}\n\nRequirements:\n- Use brand voice: {brand_voice}\n- Include relevant hashtags\n- Make it conversational and engaging\n- Each tweet should be under 280 characters",
        variables=["blog_content", "num_tweets", "brand_voice"],
        examples=[
            {
                "blog_content": "How to implement effective SEO strategies for your business",
                "num_tweets": 3,
                "brand_voice": "Professional yet friendly",
                "output": [
                    "🚀 Want to boost your business visibility? Here are 3 game-changing SEO strategies that actually work! #SEO #DigitalMarketing",
                    "2️⃣ Content is king, but distribution is queen! Learn how to create content that ranks AND gets shared. #ContentMarketing",
                    "3️⃣ Technical SEO isn't boring - it's your secret weapon! From page speed to mobile optimization, here's what matters most. #TechSEO"
                ]
            }
        ]
    ),
    
    "blog_to_linkedin": ContentTemplate(
        name="Blog to LinkedIn Post",
        content_type=ContentType.SOCIAL_MEDIA_POST,
        target_platforms=[Platform.LINKEDIN],
        structure=CONTENT_STRUCTURES[ContentType.SOCIAL_MEDIA_POST],
        prompt_template="Transform this blog post into a professional LinkedIn post:\n\n{blog_content}\n\nRequirements:\n- Professional tone\n- Include key insights\n- Add relevant hashtags\n- End with a thought-provoking question\n- Keep under 1300 characters for optimal engagement",
        variables=["blog_content"],
        examples=[
            {
                "blog_content": "The future of AI in content marketing",
                "output": "🤖 AI is revolutionizing content marketing, but are we ready for what's coming?\n\nKey insights from our latest research:\n• 73% of marketers plan to increase AI investment\n• Content personalization is now table stakes\n• The human touch remains irreplaceable\n\nWhat's your take? Are you embracing AI in your content strategy, or do you have concerns about maintaining authenticity?\n\n#AIMarketing #ContentMarketing #DigitalTransformation #FutureOfWork"
            }
        ]
    )
}

# Repurposing rules for content transformation
REPURPOSING_RULES = [
    RepurposingRule(
        source_type=ContentType.BLOG_POST,
        target_type=ContentType.SOCIAL_MEDIA_POST,
        source_format=ContentFormat.MARKDOWN,
        target_format=ContentFormat.TWEET,
        transformation_rules=[
            "Extract key points and insights",
            "Condense to platform character limits",
            "Maintain brand voice and tone",
            "Add relevant hashtags and mentions"
        ],
        content_adaptations=[
            "Convert paragraphs to bullet points",
            "Add emojis for visual appeal",
            "Include call-to-action",
            "Optimize for mobile reading"
        ],
        quality_checks=[
            "Verify character count compliance",
            "Check hashtag relevance",
            "Ensure brand voice consistency",
            "Validate engagement potential"
        ]
    ),
    
    RepurposingRule(
        source_type=ContentType.BLOG_POST,
        target_type=ContentType.VIDEO_SCRIPT,
        source_format=ContentFormat.MARKDOWN,
        target_format=ContentFormat.PLAIN_TEXT,
        transformation_rules=[
            "Convert text to spoken language",
            "Add visual and audio cues",
            "Structure for video pacing",
            "Include hook and call-to-action"
        ],
        content_adaptations=[
            "Rewrite for oral delivery",
            "Add timing markers",
            "Include visual transition notes",
            "Optimize for video platform algorithms"
        ],
        quality_checks=[
            "Verify script readability",
            "Check timing estimates",
            "Ensure visual cue clarity",
            "Validate platform compliance"
        ]
    )
]


def get_content_structure(content_type: ContentType) -> Optional[ContentStructure]:
    """Get the content structure for a specific content type"""
    return CONTENT_STRUCTURES.get(content_type)


def get_platform_requirements(platform: Platform) -> Optional[PlatformRequirements]:
    """Get the requirements for a specific platform"""
    return PLATFORM_REQUIREMENTS.get(platform)


def get_content_template(template_name: str) -> Optional[ContentTemplate]:
    """Get a specific content template by name"""
    return CONTENT_TEMPLATES.get(template_name)


def get_repurposing_rules(source_type: ContentType, target_type: ContentType) -> List[RepurposingRule]:
    """Get repurposing rules for transforming content from source to target type"""
    return [
        rule for rule in REPURPOSING_RULES
        if rule.source_type == source_type and rule.target_type == target_type
    ]


def get_supported_formats(content_type: ContentType) -> List[ContentFormat]:
    """Get all supported formats for a content type"""
    structure = get_content_structure(content_type)
    return structure.format_requirements if structure else []


def get_platform_formats(platform: Platform) -> List[ContentFormat]:
    """Get all supported formats for a platform"""
    requirements = get_platform_requirements(platform)
    return requirements.content_formats if requirements else []


def validate_content_length(content: str, content_type: ContentType) -> Dict[str, Any]:
    """Validate content length against type requirements"""
    structure = get_content_structure(content_type)
    if not structure:
        return {"valid": False, "error": "Unknown content type"}
    
    content_length = len(content)
    
    validation_result = {
        "valid": True,
        "content_length": content_length,
        "requirements": {
            "min_length": structure.min_length,
            "max_length": structure.max_length,
            "recommended_length": structure.recommended_length
        },
        "warnings": []
    }
    
    if structure.min_length and content_length < structure.min_length:
        validation_result["valid"] = False
        validation_result["warnings"].append(f"Content too short. Minimum: {structure.min_length} characters")
    
    if structure.max_length and content_length > structure.max_length:
        validation_result["valid"] = False
        validation_result["warnings"].append(f"Content too long. Maximum: {structure.max_length} characters")
    
    if structure.recommended_length:
        if content_length < structure.recommended_length * 0.8:
            validation_result["warnings"].append("Content significantly shorter than recommended")
        elif content_length > structure.recommended_length * 1.2:
            validation_result["warnings"].append("Content significantly longer than recommended")
    
    return validation_result
