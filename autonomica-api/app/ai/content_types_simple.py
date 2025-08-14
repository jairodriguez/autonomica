"""
Content Types and Formats Definition Module (Simplified)

This module defines all content types and formats that will be generated
and repurposed in the content generation and repurposing pipeline.
Simplified version without external dependencies.
"""

from enum import Enum
from typing import Dict, List, Optional, Union


class ContentType(str, Enum):
    """Enumeration of all supported content types."""
    
    # Long-form content
    BLOG_POST = "blog_post"
    ARTICLE = "article"
    WHITEPAPER = "whitepaper"
    CASE_STUDY = "case_study"
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    
    # Social media content
    TWEET = "tweet"
    TWEET_THREAD = "tweet_thread"
    FACEBOOK_POST = "facebook_post"
    LINKEDIN_POST = "linkedin_post"
    INSTAGRAM_CAPTION = "instagram_caption"
    INSTAGRAM_STORY = "instagram_story"
    
    # Visual content
    CAROUSEL = "carousel"
    SLIDE_DECK = "slide_deck"
    INFOGRAPHIC = "infographic"
    MEME = "meme"
    
    # Video content
    VIDEO_SCRIPT = "video_script"
    SHORT_FORM_VIDEO = "short_form_video"
    LONG_FORM_VIDEO = "long_form_video"
    VIDEO_CAPTION = "video_caption"
    
    # Audio content
    PODCAST_SCRIPT = "podcast_script"
    AUDIO_AD = "audio_ad"
    
    # Email content
    EMAIL_NEWSLETTER = "email_newsletter"
    EMAIL_SEQUENCE = "email_sequence"
    TRANSACTIONAL_EMAIL = "transactional_email"
    
    # Marketing content
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"
    PRODUCT_DESCRIPTION = "product_description"
    PRESS_RELEASE = "press_release"


class ContentFormat(str, Enum):
    """Enumeration of all supported content formats."""
    
    # Text formats
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    
    # Structured formats
    OUTLINE = "outline"
    BULLET_POINTS = "bullet_points"
    Q_AND_A = "q_and_a"
    CHECKLIST = "checklist"
    
    # Media formats
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    
    # Social media specific
    HASHTAGS = "hashtags"
    EMOJIS = "emojis"
    MENTIONS = "mentions"


class ContentStructure:
    """Defines the structure for different content types."""
    
    def __init__(self, content_type: ContentType, sections: List[str], 
                 required_sections: List[str], optional_sections: List[str],
                 word_count_range: tuple[int, int], character_limit: Optional[int] = None):
        self.content_type = content_type
        self.sections = sections
        self.required_sections = required_sections
        self.optional_sections = optional_sections
        self.word_count_range = word_count_range
        self.character_limit = character_limit


class ContentTransformation:
    """Defines how content can be transformed between types."""
    
    def __init__(self, source_type: ContentType, target_type: ContentType,
                 transformation_method: str, complexity: str, estimated_time: int, quality_impact: str):
        self.source_type = source_type
        self.target_type = target_type
        self.transformation_method = transformation_method
        self.complexity = complexity
        self.estimated_time = estimated_time
        self.quality_impact = quality_impact


class ContentTypeRegistry:
    """Registry containing all content type definitions and transformation rules."""
    
    def __init__(self):
        self.content_structures: Dict[ContentType, ContentStructure] = {}
        self.transformations: List[ContentTransformation] = []
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the registry with all content type definitions."""
        
        # Blog Post Structure
        self.content_structures[ContentType.BLOG_POST] = ContentStructure(
            content_type=ContentType.BLOG_POST,
            sections=["title", "meta_description", "introduction", "main_content", "conclusion", "call_to_action"],
            required_sections=["title", "introduction", "main_content", "conclusion"],
            optional_sections=["meta_description", "call_to_action"],
            word_count_range=(800, 3000),
            character_limit=None
        )
        
        # Tweet Structure
        self.content_structures[ContentType.TWEET] = ContentStructure(
            content_type=ContentType.TWEET,
            sections=["content", "hashtags", "mentions"],
            required_sections=["content"],
            optional_sections=["hashtags", "mentions"],
            word_count_range=(1, 50),
            character_limit=280
        )
        
        # Tweet Thread Structure
        self.content_structures[ContentType.TWEET_THREAD] = ContentStructure(
            content_type=ContentType.TWEET_THREAD,
            sections=["thread_intro", "thread_parts", "thread_conclusion"],
            required_sections=["thread_intro", "thread_parts"],
            optional_sections=["thread_conclusion"],
            word_count_range=(100, 1000),
            character_limit=None
        )
        
        # Facebook Post Structure
        self.content_structures[ContentType.FACEBOOK_POST] = ContentStructure(
            content_type=ContentType.FACEBOOK_POST,
            sections=["content", "hashtags", "call_to_action"],
            required_sections=["content"],
            optional_sections=["hashtags", "call_to_action"],
            word_count_range=(50, 500),
            character_limit=None
        )
        
        # LinkedIn Post Structure
        self.content_structures[ContentType.LINKEDIN_POST] = ContentStructure(
            content_type=ContentType.LINKEDIN_POST,
            sections=["hook", "content", "insights", "call_to_action"],
            required_sections=["hook", "content"],
            optional_sections=["insights", "call_to_action"],
            word_count_range=(100, 1000),
            character_limit=None
        )
        
        # Instagram Caption Structure
        self.content_structures[ContentType.INSTAGRAM_CAPTION] = ContentStructure(
            content_type=ContentType.INSTAGRAM_CAPTION,
            sections=["caption", "hashtags", "call_to_action"],
            required_sections=["caption"],
            optional_sections=["hashtags", "call_to_action"],
            word_count_range=(20, 300),
            character_limit=2200
        )
        
        # Video Script Structure
        self.content_structures[ContentType.VIDEO_SCRIPT] = ContentStructure(
            content_type=ContentType.VIDEO_SCRIPT,
            sections=["hook", "introduction", "main_points", "conclusion", "call_to_action"],
            required_sections=["hook", "main_points", "conclusion"],
            optional_sections=["introduction", "call_to_action"],
            word_count_range=(100, 1000),
            character_limit=None
        )
        
        # Carousel Structure
        self.content_structures[ContentType.CAROUSEL] = ContentStructure(
            content_type=ContentType.CAROUSEL,
            sections=["title", "slides", "conclusion"],
            required_sections=["title", "slides"],
            optional_sections=["conclusion"],
            word_count_range=(50, 500),
            character_limit=None
        )
        
        # Email Newsletter Structure
        self.content_structures[ContentType.EMAIL_NEWSLETTER] = ContentStructure(
            content_type=ContentType.EMAIL_NEWSLETTER,
            sections=["subject_line", "preheader", "greeting", "main_content", "footer"],
            required_sections=["subject_line", "main_content"],
            optional_sections=["preheader", "greeting", "footer"],
            word_count_range=(200, 1000),
            character_limit=None
        )
        
        # Initialize transformation rules
        self._initialize_transformations()
    
    def _initialize_transformations(self):
        """Initialize transformation rules between content types."""
        
        # Blog to Tweet transformations
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET,
            transformation_method="extract_key_points",
            complexity="Simple",
            estimated_time=30,
            quality_impact="Medium"
        ))
        
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET_THREAD,
            transformation_method="summarize_sections",
            complexity="Medium",
            estimated_time=60,
            quality_impact="High"
        ))
        
        # Blog to Social Media transformations
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.FACEBOOK_POST,
            transformation_method="extract_engaging_excerpt",
            complexity="Simple",
            estimated_time=45,
            quality_impact="High"
        ))
        
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.LINKEDIN_POST,
            transformation_method="extract_professional_insights",
            complexity="Medium",
            estimated_time=60,
            quality_impact="High"
        ))
        
        # Blog to Visual transformations
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.CAROUSEL,
            transformation_method="extract_key_points_for_slides",
            complexity="Complex",
            estimated_time=120,
            quality_impact="High"
        ))
        
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.VIDEO_SCRIPT,
            transformation_method="convert_to_narrative_script",
            complexity="Complex",
            estimated_time=180,
            quality_impact="High"
        ))
        
        # Social Media to Blog transformations
        self.transformations.append(ContentTransformation(
            source_type=ContentType.TWEET_THREAD,
            target_type=ContentType.BLOG_POST,
            transformation_method="expand_thread_into_article",
            complexity="Medium",
            estimated_time=300,
            quality_impact="Medium"
        ))
        
        # Email transformations
        self.transformations.append(ContentTransformation(
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.EMAIL_NEWSLETTER,
            transformation_method="convert_to_email_format",
            complexity="Medium",
            estimated_time=90,
            quality_impact="High"
        ))
    
    def get_content_structure(self, content_type: ContentType) -> Optional[ContentStructure]:
        """Get the structure definition for a specific content type."""
        return self.content_structures.get(content_type)
    
    def get_available_transformations(self, source_type: ContentType) -> List[ContentTransformation]:
        """Get all available transformations from a source content type."""
        return [t for t in self.transformations if t.source_type == source_type]
    
    def get_transformation_path(self, source_type: ContentType, target_type: ContentType) -> Optional[ContentTransformation]:
        """Get the transformation path between two content types."""
        for transformation in self.transformations:
            if transformation.source_type == source_type and transformation.target_type == target_type:
                return transformation
        return None
    
    def list_all_content_types(self) -> List[ContentType]:
        """List all available content types."""
        return list(self.content_structures.keys())
    
    def list_all_formats(self) -> List[ContentFormat]:
        """List all available content formats."""
        return list(ContentFormat)
    
    def get_content_type_metadata(self) -> Dict[str, Dict]:
        """Get metadata for all content types."""
        metadata = {}
        for content_type, structure in self.content_structures.items():
            metadata[content_type.value] = {
                "sections": structure.sections,
                "required_sections": structure.required_sections,
                "optional_sections": structure.optional_sections,
                "word_count_range": structure.word_count_range,
                "character_limit": structure.character_limit
            }
        return metadata


# Global registry instance
content_registry = ContentTypeRegistry()


def get_content_registry() -> ContentTypeRegistry:
    """Get the global content registry instance."""
    return content_registry


def validate_content_structure(content_type: ContentType, content: Dict) -> bool:
    """Validate that content follows the required structure for its type."""
    structure = content_registry.get_content_structure(content_type)
    if not structure:
        return False
    
    # Check required sections
    for required_section in structure.required_sections:
        if required_section not in content:
            return False
    
    # Check word count if applicable
    if 'content' in content:
        word_count = len(content['content'].split())
        if not (structure.word_count_range[0] <= word_count <= structure.word_count_range[1]):
            return False
    
    # Check character limit if applicable
    if structure.character_limit and 'content' in content:
        if len(content['content']) > structure.character_limit:
            return False
    
    return True


def get_content_type_by_name(name: str) -> Optional[ContentType]:
    """Get content type by name string."""
    try:
        return ContentType(name.lower())
    except ValueError:
        return None


def format_content_for_type(content: str, target_type: ContentType, **kwargs) -> str:
    """Format content according to the target content type requirements."""
    structure = content_registry.get_content_structure(target_type)
    if not structure:
        return content
    
    # Apply character limits
    if structure.character_limit:
        content = content[:structure.character_limit]
    
    # Add hashtags for social media if not present
    if target_type in [ContentType.TWEET, ContentType.INSTAGRAM_CAPTION, ContentType.FACEBOOK_POST]:
        if '#' not in content and kwargs.get('add_hashtags', True):
            # Add some default hashtags (this would be enhanced with AI-generated relevant hashtags)
            content += "\n\n#ContentCreation #DigitalMarketing #AI"
    
    return content