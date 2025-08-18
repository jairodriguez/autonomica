"""
Content Generation Service

This service handles content generation using the AI manager and integrates
with the content types and formats system.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..ai.ai_manager import ai_manager
from ..ai.model_interface import ModelConfig, ModelProvider
from .content_types import (
    ContentType, ContentFormat, Platform, ContentStructure,
    get_content_structure, get_platform_requirements, get_content_template,
    get_repurposing_rules, validate_content_length
)

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Service for generating and repurposing content using AI models."""
    
    def __init__(self):
        self.ai_manager = ai_manager
        self.default_model = "gpt-4"  # Default model for content generation
        self.fallback_model = "gpt-3.5-turbo"  # Fallback model
        
    async def generate_content(
        self,
        content_type: ContentType,
        prompt: str,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate content of a specific type for target platforms.
        
        Args:
            content_type: Type of content to generate
            prompt: User prompt for content generation
            target_platforms: List of platforms to target
            brand_voice: Brand voice guidelines
            max_tokens: Maximum tokens for generation
            temperature: Creativity level (0.0-1.0)
            **kwargs: Additional parameters for content generation
            
        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            # Get content structure for validation
            structure = get_content_structure(content_type)
            if not structure:
                raise ValueError(f"Unknown content type: {content_type}")
            
            # Build enhanced prompt with structure and platform requirements
            enhanced_prompt = self._build_enhanced_prompt(
                content_type, prompt, target_platforms, brand_voice, structure
            )
            
            # Generate content using AI manager
            result = await self.ai_manager.execute(
                enhanced_prompt,
                max_tokens=max_tokens or self._get_default_max_tokens(content_type),
                temperature=temperature,
                **kwargs
            )
            
            # Extract and validate generated content
            generated_content = result.get("content", "")
            
            # Validate content length
            validation_result = validate_content_length(generated_content, content_type)
            
            # Parse structured content if possible
            parsed_content = self._parse_structured_content(generated_content, content_type)
            
            return {
                "content": parsed_content,
                "raw_content": generated_content,
                "content_type": content_type,
                "target_platforms": target_platforms,
                "brand_voice": brand_voice,
                "validation": validation_result,
                "metadata": {
                    "model_used": result.get("model", self.default_model),
                    "tokens_used": result.get("usage", {}),
                    "generated_at": datetime.utcnow().isoformat(),
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def repurpose_content(
        self,
        source_content: str,
        source_type: ContentType,
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Repurpose existing content from one type to another.
        
        Args:
            source_content: Original content to repurpose
            source_type: Type of source content
            target_type: Target content type
            target_platforms: Target platforms for repurposed content
            brand_voice: Brand voice for repurposed content
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing repurposed content and metadata
        """
        try:
            # Get repurposing rules
            rules = get_repurposing_rules(source_type, target_type)
            if not rules:
                raise ValueError(f"No repurposing rules found for {source_type} to {target_type}")
            
            # Build repurposing prompt
            repurposing_prompt = self._build_repurposing_prompt(
                source_content, source_type, target_type, target_platforms, 
                brand_voice, rules[0]  # Use first matching rule
            )
            
            # Generate repurposed content
            result = await self.ai_manager.execute(
                repurposing_prompt,
                max_tokens=self._get_default_max_tokens(target_type),
                temperature=0.7,
                **kwargs
            )
            
            generated_content = result.get("content", "")
            
            # Validate repurposed content
            validation_result = validate_content_length(generated_content, target_type)
            
            # Parse structured content
            parsed_content = self._parse_structured_content(generated_content, target_type)
            
            return {
                "content": parsed_content,
                "raw_content": generated_content,
                "source_type": source_type,
                "target_type": target_type,
                "target_platforms": target_platforms,
                "brand_voice": brand_voice,
                "validation": validation_result,
                "repurposing_rules_applied": rules[0].transformation_rules,
                "metadata": {
                    "model_used": result.get("model", self.default_model),
                    "tokens_used": result.get("usage", {}),
                    "repurposed_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(source_content)
                }
            }
            
        except Exception as e:
            logger.error(f"Content repurposing failed: {e}")
            raise
    
    async def generate_social_media_content(
        self,
        blog_content: str,
        target_platforms: List[Platform],
        num_posts: int = 3,
        brand_voice: str = "Professional and engaging",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate social media content from blog content.
        
        Args:
            blog_content: Blog content to convert
            target_platforms: Target social media platforms
            num_posts: Number of social media posts to generate
            brand_voice: Brand voice guidelines
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing generated social media content
        """
        try:
            # Build social media generation prompt
            prompt = self._build_social_media_prompt(
                blog_content, target_platforms, num_posts, brand_voice
            )
            
            # Generate content
            result = await self.ai_manager.execute(
                prompt,
                max_tokens=1000,  # Social media posts are typically shorter
                temperature=0.8,  # Slightly more creative for social media
                **kwargs
            )
            
            generated_content = result.get("content", "")
            
            # Parse multiple social media posts
            social_posts = self._parse_social_media_posts(generated_content, target_platforms)
            
            return {
                "social_posts": social_posts,
                "raw_content": generated_content,
                "source_content_length": len(blog_content),
                "target_platforms": target_platforms,
                "num_posts": num_posts,
                "brand_voice": brand_voice,
                "metadata": {
                    "model_used": result.get("model", self.default_model),
                    "tokens_used": result.get("usage", {}),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Social media content generation failed: {e}")
            raise
    
    def _build_enhanced_prompt(
        self,
        content_type: ContentType,
        prompt: str,
        target_platforms: List[Platform],
        brand_voice: str,
        structure: ContentStructure
    ) -> str:
        """Build an enhanced prompt with structure and platform requirements."""
        
        platform_requirements = []
        for platform in target_platforms:
            req = get_platform_requirements(platform)
            if req:
                platform_requirements.append(f"- {platform.value}: {', '.join(req.content_formats)}")
        
        enhanced_prompt = f"""
Generate {content_type.value} content based on the following requirements:

USER PROMPT: {prompt}

CONTENT TYPE: {content_type.value}
REQUIRED SECTIONS: {', '.join(structure.required_sections)}
OPTIONAL SECTIONS: {', '.join(structure.optional_sections)}
TARGET PLATFORMS: {', '.join(target_platforms)}
PLATFORM FORMATS: {'; '.join(platform_requirements)}

BRAND VOICE: {brand_voice}

LENGTH REQUIREMENTS:
- Minimum: {structure.min_length} characters
- Maximum: {structure.max_length} characters
- Recommended: {structure.recommended_length} characters

FORMAT REQUIREMENTS: {', '.join(structure.format_requirements)}

Please generate high-quality, engaging content that follows these requirements exactly.
Structure the content according to the required sections and ensure it meets all length and format constraints.
"""
        return enhanced_prompt.strip()
    
    def _build_repurposing_prompt(
        self,
        source_content: str,
        source_type: ContentType,
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str,
        rule: Any
    ) -> str:
        """Build a prompt for content repurposing."""
        
        prompt = f"""
Repurpose the following {source_type.value} content into {target_type.value} content:

SOURCE CONTENT:
{source_content}

TARGET REQUIREMENTS:
- Content Type: {target_type.value}
- Target Platforms: {', '.join(target_platforms)}
- Brand Voice: {brand_voice}

TRANSFORMATION RULES:
{chr(10).join(f"- {rule}" for rule in rule.transformation_rules)}

CONTENT ADAPTATIONS:
{chr(10).join(f"- {adaptation}" for adaptation in rule.content_adaptations)}

QUALITY CHECKS:
{chr(10).join(f"- {check}" for check in rule.quality_checks)}

Please transform the content following these rules exactly. Ensure the output maintains the key message and insights while adapting to the new format and platform requirements.
"""
        return prompt.strip()
    
    def _build_social_media_prompt(
        self,
        blog_content: str,
        target_platforms: List[Platform],
        num_posts: int,
        brand_voice: str
    ) -> str:
        """Build a prompt for social media content generation."""
        
        platform_info = []
        for platform in target_platforms:
            req = get_platform_requirements(platform)
            if req:
                char_limit = req.character_limits.get("post", req.character_limits.get("tweet", 280))
                platform_info.append(f"- {platform.value}: {char_limit} character limit")
        
        prompt = f"""
Convert the following blog content into {num_posts} engaging social media posts:

BLOG CONTENT:
{blog_content}

TARGET PLATFORMS:
{chr(10).join(platform_info)}

REQUIREMENTS:
- Generate exactly {num_posts} posts
- Each post should be optimized for its target platform
- Use brand voice: {brand_voice}
- Include relevant hashtags and emojis
- Make each post engaging and shareable
- Ensure posts work together as a series but can stand alone

Please format the output as numbered posts (1, 2, 3, etc.) with clear separation between each post.
"""
        return prompt.strip()
    
    def _get_default_max_tokens(self, content_type: ContentType) -> int:
        """Get default max tokens for a content type."""
        structure = get_content_structure(content_type)
        if structure and structure.recommended_length:
            # Estimate tokens as roughly 4 characters per token
            return int(structure.recommended_length / 4) + 100  # Add buffer
        return 1000  # Default fallback
    
    def _parse_structured_content(
        self, 
        content: str, 
        content_type: ContentType
    ) -> Dict[str, Any]:
        """Parse generated content into structured format."""
        
        structure = get_content_structure(content_type)
        if not structure:
            return {"raw": content}
        
        # For now, return a simple structure
        # In a more advanced implementation, this could use AI to parse sections
        return {
            "raw": content,
            "sections": {
                "all": content,
                "required": structure.required_sections,
                "optional": structure.optional_sections
            },
            "length": len(content),
            "word_count": len(content.split())
        }
    
    def _parse_social_media_posts(
        self, 
        content: str, 
        target_platforms: List[Platform]
    ) -> List[Dict[str, Any]]:
        """Parse generated social media content into individual posts."""
        
        # Simple parsing - split by numbered posts
        posts = []
        lines = content.split('\n')
        current_post = {"content": "", "platform": target_platforms[0] if target_platforms else "unknown"}
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) and current_post["content"]:
                # Save previous post and start new one
                posts.append(current_post.copy())
                current_post = {"content": line, "platform": target_platforms[0] if target_platforms else "unknown"}
            elif line:
                if current_post["content"]:
                    current_post["content"] += "\n" + line
                else:
                    current_post["content"] = line
        
        # Add the last post
        if current_post["content"]:
            posts.append(current_post)
        
        # Assign platforms if multiple posts and platforms
        if len(posts) > 1 and len(target_platforms) > 1:
            for i, post in enumerate(posts):
                post["platform"] = target_platforms[i % len(target_platforms)]
        
        return posts
    
    async def health_check(self) -> bool:
        """Check if the content generation service is healthy."""
        try:
            # Test with a simple prompt
            test_result = await self.generate_content(
                ContentType.SOCIAL_MEDIA_POST,
                "Test content generation",
                [Platform.TWITTER],
                max_tokens=50
            )
            return "content" in test_result
        except Exception as e:
            logger.error(f"Content generation health check failed: {e}")
            return False

    def _get_content_structure(self, content_type: ContentType):
        """Helper method to get content structure (for testing)"""
        return get_content_structure(content_type)
    
    def _get_platform_requirements(self, platform: Platform):
        """Helper method to get platform requirements (for testing)"""
        from .content_types import get_platform_requirements
        return get_platform_requirements(platform)


# Create a singleton instance
content_generation_service = ContentGenerationService()
