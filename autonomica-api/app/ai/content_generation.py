"""
Content Generation Module

This module provides content generation and repurposing capabilities using
the integrated AI models and LangChain framework.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from content_types_simple import (
    ContentType, ContentFormat, ContentTypeRegistry, 
    get_content_registry, validate_content_structure
)
from content_templates import get_template_engine
# from .ai_manager import ai_manager  # Commented out for now to avoid import issues

logger = logging.getLogger(__name__)


@dataclass
class ContentGenerationRequest:
    """Request for content generation."""
    content_type: ContentType
    prompt: str
    target_format: ContentFormat = ContentFormat.PLAIN_TEXT
    brand_voice: Optional[str] = None
    tone: str = "professional"
    word_count: Optional[int] = None
    include_hashtags: bool = True
    include_mentions: bool = False
    custom_instructions: Optional[str] = None


@dataclass
class ContentGenerationResponse:
    """Response from content generation."""
    content: str
    content_type: ContentType
    format: ContentFormat
    word_count: int
    character_count: int
    generation_time: float
    model_used: str
    token_usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ContentRepurposingRequest:
    """Request for content repurposing."""
    source_content: str
    source_type: ContentType
    target_type: ContentType
    brand_voice: Optional[str] = None
    tone: str = "professional"
    preserve_key_points: bool = True
    add_hashtags: bool = True
    custom_instructions: Optional[str] = None


class ContentGenerator:
    """Main content generation class using AI models."""
    
    def __init__(self):
        self.content_registry = get_content_registry()
        self.default_model = "gpt-4"  # Default model for content generation
        
    async def generate_content(self, request: ContentGenerationRequest) -> ContentGenerationResponse:
        """Generate new content based on the request."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate content type
            if not self.content_registry.get_content_structure(request.content_type):
                raise ValueError(f"Unsupported content type: {request.content_type}")
            
            # Build the generation prompt
            prompt = self._build_generation_prompt(request)
            
            # Generate content using AI model (mocked for testing)
            # response = await ai_manager.execute(
            #     prompt=prompt,
            #     max_tokens=self._calculate_max_tokens(request),
            #     temperature=0.7,
            #     model_name=request.custom_instructions.get("model", self.default_model) if request.custom_instructions else self.custom_instructions
            # )
            
            # Mock response for testing
            response = {
                "choices": [{"message": {"content": f"Generated {request.content_type.value} content based on: {request.prompt}"}}],
                "model": self.default_model,
                "usage": {"total_tokens": 100}
            }
            
            # Extract and format the generated content
            generated_content = self._extract_generated_content(response, request)
            
            # Validate the generated content structure
            if not self._validate_generated_content(generated_content, request.content_type):
                logger.warning(f"Generated content validation failed for {request.content_type}")
            
            # Format content for the target type
            formatted_content = self._format_content_for_type(generated_content, request)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            return ContentGenerationResponse(
                content=formatted_content,
                content_type=request.content_type,
                format=request.target_format,
                word_count=len(formatted_content.split()),
                character_count=len(formatted_content),
                generation_time=generation_time,
                model_used=response.get("model", "unknown"),
                token_usage=response.get("usage"),
                metadata={
                    "brand_voice": request.brand_voice,
                    "tone": request.tone,
                    "original_prompt": request.prompt
                }
            )
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise
    
    async def repurpose_content(self, request: ContentRepurposingRequest) -> ContentGenerationResponse:
        """Repurpose existing content to a different format."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Get transformation information
            transformation = self.content_registry.get_transformation_path(
                request.source_type, request.target_type
            )
            
            if not transformation:
                raise ValueError(f"No transformation path from {request.source_type} to {request.target_type}")
            
            # Build repurposing prompt
            prompt = self._build_repurposing_prompt(request, transformation)
            
            # Generate repurposed content (mocked for testing)
            # response = await ai_manager.execute(
            #     prompt=prompt,
            #     max_tokens=self._calculate_max_tokens_for_repurposing(request),
            #     temperature=0.7
            # )
            
            # Mock response for testing
            response = {
                "choices": [{"message": {"content": f"Repurposed content from {request.source_type.value} to {request.target_type.value}"}}],
                "model": self.default_model,
                "usage": {"total_tokens": 80}
            }
            
            # Extract and format the repurposed content
            repurposed_content = self._extract_generated_content(response, 
                ContentGenerationRequest(content_type=request.target_type, prompt=""))
            
            # Format content for the target type
            formatted_content = self._format_content_for_type(repurposed_content, 
                ContentGenerationRequest(content_type=request.target_type, prompt=""))
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            return ContentGenerationResponse(
                content=formatted_content,
                content_type=request.target_type,
                format=ContentFormat.PLAIN_TEXT,  # Default format for repurposed content
                word_count=len(formatted_content.split()),
                character_count=len(formatted_content),
                generation_time=generation_time,
                model_used=response.get("model", "unknown"),
                token_usage=response.get("usage"),
                metadata={
                    "source_type": request.source_type,
                    "transformation_method": transformation.transformation_method,
                    "complexity": transformation.complexity,
                    "brand_voice": request.brand_voice,
                    "tone": request.tone
                }
            )
            
        except Exception as e:
            logger.error(f"Content repurposing failed: {str(e)}")
            raise
    
    def _build_generation_prompt(self, request: ContentGenerationRequest) -> str:
        """Build a comprehensive prompt for content generation using templates."""
        
        # Get template engine
        template_engine = get_template_engine()
        
        # Build base prompt
        base_prompt = f"""You are a professional content creator. Generate a {request.content_type.value} based on the following requirements:

Topic/Prompt: {request.prompt}
Content Type: {request.content_type.value}
Target Format: {request.target_format.value}
Tone: {request.tone}"""

        if request.brand_voice:
            base_prompt += f"\nBrand Voice: {request.brand_voice}"
        
        if request.custom_instructions:
            base_prompt += f"\nCustom Instructions: {request.custom_instructions}"
        
        # Get enhanced prompt with template and formatting instructions
        enhanced_prompt = template_engine.get_enhanced_prompt(
            base_prompt, 
            request.content_type, 
            request.target_format
        )
        
        return enhanced_prompt
    
    def _build_repurposing_prompt(self, request: ContentRepurposingRequest, 
                                 transformation: Any) -> str:
        """Build a prompt for content repurposing."""
        
        target_structure = self.content_registry.get_content_structure(request.target_type)
        
        prompt_parts = [
            f"You are a content repurposing expert. Transform the following {request.source_type.value} into a {request.target_type.value}:",
            f"\nSource Content:",
            f"{request.source_content}",
            f"\nTransformation Method: {transformation.transformation_method}",
            f"Target Format: {request.target_type.value}",
            f"Tone: {request.tone}"
        ]
        
        if request.brand_voice:
            prompt_parts.append(f"Brand Voice: {request.brand_voice}")
        
        if target_structure:
            prompt_parts.append(f"\nRequired Sections: {', '.join(target_structure.required_sections)}")
            if target_structure.word_count_range:
                prompt_parts.append(f"Word Count: {target_structure.word_count_range[0]}-{target_structure.word_count_range[1]} words")
            if target_structure.character_limit:
                prompt_parts.append(f"Character Limit: {target_structure.character_limit} characters")
        
        if request.preserve_key_points:
            prompt_parts.append("\nImportant: Preserve all key points and main ideas from the source content.")
        
        if request.custom_instructions:
            prompt_parts.append(f"\nCustom Instructions: {request.custom_instructions}")
        
        prompt_parts.append("\nPlease generate the repurposed content following these requirements exactly.")
        
        return "\n".join(prompt_parts)
    
    def _calculate_max_tokens(self, request: ContentGenerationRequest) -> int:
        """Calculate appropriate max tokens based on content type and word count."""
        structure = self.content_registry.get_content_structure(request.content_type)
        
        if request.word_count:
            # Estimate tokens: roughly 1.3 tokens per word
            estimated_tokens = int(request.word_count * 1.3)
        elif structure and structure.word_count_range:
            # Use average of word count range
            avg_words = sum(structure.word_count_range) / 2
            estimated_tokens = int(avg_words * 1.3)
        else:
            # Default token limit
            estimated_tokens = 2000
        
        # Add buffer for prompt and formatting
        return estimated_tokens + 500
    
    def _calculate_max_tokens_for_repurposing(self, request: ContentRepurposingRequest) -> int:
        """Calculate max tokens for content repurposing."""
        target_structure = self.content_registry.get_content_structure(request.target_type)
        
        if target_structure and target_structure.word_count_range:
            avg_words = sum(target_structure.word_count_range) / 2
            estimated_tokens = int(avg_words * 1.3)
        else:
            estimated_tokens = 1500
        
        return estimated_tokens + 500
    
    def _extract_generated_content(self, response: Dict[str, Any], 
                                 request: ContentGenerationRequest) -> str:
        """Extract the generated content from the AI response."""
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0].get("message", {}).get("content", "")
        elif "content" in response:
            content = response["content"]
        elif "text" in response:
            content = response["text"]
        else:
            # Fallback: try to find content in the response
            content = str(response)
            logger.warning(f"Unexpected response format: {response}")
        
        return content.strip()
    
    def _validate_generated_content(self, content: str, content_type: ContentType) -> bool:
        """Validate that generated content meets the requirements for its type."""
        # Basic validation - check if content is not empty
        if not content or len(content.strip()) < 10:
            return False
        
        # Get structure requirements
        structure = self.content_registry.get_content_structure(content_type)
        if not structure:
            return True  # Can't validate without structure
        
        # Check word count if specified
        if structure.word_count_range:
            word_count = len(content.split())
            if not (structure.word_count_range[0] <= word_count <= structure.word_count_range[1]):
                logger.warning(f"Word count {word_count} outside range {structure.word_count_range}")
                return False
        
        # Check character limit if specified
        if structure.character_limit and len(content) > structure.character_limit:
            logger.warning(f"Content exceeds character limit: {len(content)} > {structure.character_limit}")
            return False
        
        return True
    
    def _format_content_for_type(self, content: str, request: ContentGenerationRequest) -> str:
        """Format content according to the target content type requirements."""
        structure = self.content_registry.get_content_structure(request.content_type)
        if not structure:
            return content
        
        # Apply character limits
        if structure.character_limit:
            content = content[:structure.character_limit]
        
        # Add hashtags for social media if requested
        if (request.include_hashtags and 
            request.content_type in [ContentType.TWEET, ContentType.INSTAGRAM_CAPTION, 
                                   ContentType.FACEBOOK_POST, ContentType.LINKEDIN_POST]):
            if '#' not in content:
                # Add relevant hashtags based on content type
                hashtags = self._generate_relevant_hashtags(request.content_type, request.prompt)
                content += f"\n\n{hashtags}"
        
        return content
    
    def _generate_relevant_hashtags(self, content_type: ContentType, prompt: str) -> str:
        """Generate relevant hashtags for social media content."""
        base_hashtags = {
            ContentType.TWEET: "#ContentCreation #DigitalMarketing",
            ContentType.INSTAGRAM_CAPTION: "#ContentCreation #Instagram #SocialMedia",
            ContentType.FACEBOOK_POST: "#ContentCreation #Facebook #SocialMedia",
            ContentType.LINKEDIN_POST: "#ContentCreation #LinkedIn #Professional"
        }
        
        # Extract potential hashtags from the prompt
        prompt_words = prompt.lower().split()
        potential_hashtags = [f"#{word}" for word in prompt_words 
                            if len(word) > 3 and word.isalpha()][:3]
        
        # Combine base hashtags with prompt-based hashtags
        all_hashtags = base_hashtags.get(content_type, "#ContentCreation") + " " + " ".join(potential_hashtags)
        
        return all_hashtags


class ContentGenerationService:
    """Service layer for content generation operations."""
    
    def __init__(self):
        self.generator = ContentGenerator()
    
    async def create_blog_post(self, topic: str, brand_voice: Optional[str] = None, 
                              tone: str = "professional", word_count: int = 1500) -> ContentGenerationResponse:
        """Create a blog post on the given topic."""
        request = ContentGenerationRequest(
            content_type=ContentType.BLOG_POST,
            prompt=topic,
            brand_voice=brand_voice,
            tone=tone,
            word_count=word_count,
            target_format=ContentFormat.MARKDOWN
        )
        return await self.generator.generate_content(request)
    
    async def create_tweet(self, topic: str, brand_voice: Optional[str] = None, 
                          include_hashtags: bool = True) -> ContentGenerationResponse:
        """Create a tweet on the given topic."""
        request = ContentGenerationRequest(
            content_type=ContentType.TWEET,
            prompt=topic,
            brand_voice=brand_voice,
            tone="conversational",
            include_hashtags=include_hashtags,
            target_format=ContentFormat.PLAIN_TEXT
        )
        return await self.generator.generate_content(request)
    
    async def create_tweet_thread(self, topic: str, brand_voice: Optional[str] = None, 
                                thread_length: int = 5) -> ContentGenerationResponse:
        """Create a tweet thread on the given topic."""
        request = ContentGenerationRequest(
            content_type=ContentType.TWEET_THREAD,
            prompt=f"{topic} (Create a {thread_length}-tweet thread)",
            brand_voice=brand_voice,
            tone="conversational",
            include_hashtags=True,
            target_format=ContentFormat.PLAIN_TEXT
        )
        return await self.generator.generate_content(request)
    
    async def repurpose_blog_to_tweets(self, blog_content: str, brand_voice: Optional[str] = None) -> ContentGenerationResponse:
        """Repurpose a blog post into engaging tweets."""
        request = ContentRepurposingRequest(
            source_content=blog_content,
            source_type=ContentType.BLOG_POST,
            target_type=ContentType.TWEET_THREAD,
            brand_voice=brand_voice,
            preserve_key_points=True,
            add_hashtags=True
        )
        return await self.generator.repurpose_content(request)
    
    async def repurpose_blog_to_social_media(self, blog_content: str, target_type: ContentType,
                                           brand_voice: Optional[str] = None) -> ContentGenerationResponse:
        """Repurpose a blog post to various social media formats."""
        request = ContentRepurposingRequest(
            source_content=blog_content,
            source_type=ContentType.BLOG_POST,
            target_type=target_type,
            brand_voice=brand_voice,
            preserve_key_points=True,
            add_hashtags=True
        )
        return await self.generator.repurpose_content(request)
    
    async def create_video_script(self, topic: str, video_length: str = "2-3 minutes",
                                brand_voice: Optional[str] = None) -> ContentGenerationResponse:
        """Create a video script for the given topic."""
        request = ContentGenerationRequest(
            content_type=ContentType.VIDEO_SCRIPT,
            prompt=f"{topic} (Create a {video_length} video script)",
            brand_voice=brand_voice,
            tone="conversational",
            target_format=ContentFormat.PLAIN_TEXT
        )
        return await self.generator.generate_content(request)
    
    async def create_email_newsletter(self, topic: str, brand_voice: Optional[str] = None,
                                    tone: str = "professional") -> ContentGenerationResponse:
        """Create an email newsletter on the given topic."""
        request = ContentGenerationRequest(
            content_type=ContentType.EMAIL_NEWSLETTER,
            prompt=topic,
            brand_voice=brand_voice,
            tone=tone,
            target_format=ContentFormat.HTML
        )
        return await self.generator.generate_content(request)


# Global service instance
content_service = ContentGenerationService()


def get_content_service() -> ContentGenerationService:
    """Get the global content generation service instance."""
    return content_service