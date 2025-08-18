"""
Content Repurposing Service

This service implements algorithms to repurpose existing content into different
types and formats while maintaining consistency and relevance.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass

from .content_types import (
    ContentType, ContentFormat, Platform, ContentStructure,
    get_content_structure, get_platform_requirements, get_repurposing_rules,
    validate_content_length, get_content_template
)

logger = logging.getLogger(__name__)


@dataclass
class RepurposingResult:
    """Result of content repurposing operation"""
    source_content: str
    source_type: ContentType
    target_type: ContentType
    repurposed_content: str
    target_platforms: List[Platform]
    brand_voice: str
    transformation_applied: List[str]
    quality_metrics: Dict[str, Any]
    metadata: Dict[str, Any]


class ContentRepurposingService:
    """Service for repurposing content between different types and formats."""
    
    def __init__(self):
        self.max_retries = 3
        self.quality_threshold = 0.8
        
    async def repurpose_content(
        self,
        source_content: str,
        source_type: ContentType,
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        **kwargs
    ) -> RepurposingResult:
        """
        Repurpose content from source type to target type.
        
        Args:
            source_content: Original content to repurpose
            source_type: Type of source content
            target_type: Target content type
            target_platforms: Target platforms for repurposed content
            brand_voice: Brand voice guidelines
            **kwargs: Additional parameters
            
        Returns:
            RepurposingResult containing repurposed content and metadata
        """
        try:
            # Get repurposing rules
            rules = get_repurposing_rules(source_type, target_type)
            if not rules:
                raise ValueError(f"No repurposing rules found for {source_type} to {target_type}")
            
            # Apply repurposing logic
            repurposed_content = await self._apply_repurposing_logic(
                source_content, source_type, target_type, target_platforms, 
                brand_voice, rules[0], **kwargs
            )
            
            # Apply quality checks and optimizations
            optimized_content = await self._optimize_content(
                repurposed_content, target_type, target_platforms, brand_voice
            )
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(
                source_content, optimized_content, source_type, target_type, target_platforms
            )
            
            # Track transformations applied
            transformation_applied = rules[0].transformation_rules + rules[0].content_adaptations
            
            return RepurposingResult(
                source_content=source_content,
                source_type=source_type,
                target_type=target_type,
                repurposed_content=optimized_content,
                target_platforms=target_platforms,
                brand_voice=brand_voice,
                transformation_applied=transformation_applied,
                quality_metrics=quality_metrics,
                metadata={
                    "repurposed_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(source_content),
                    "target_content_length": len(optimized_content),
                    "compression_ratio": len(optimized_content) / len(source_content) if source_content else 0,
                    "rules_applied": rules[0].transformation_rules,
                    "adaptations_applied": rules[0].content_adaptations
                }
            )
            
        except Exception as e:
            logger.error(f"Content repurposing failed: {e}")
            raise
    
    async def _apply_repurposing_logic(
        self,
        source_content: str,
        source_type: ContentType,
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str,
        rule: Any,
        **kwargs
    ) -> str:
        """Apply the core repurposing logic based on content types."""
        
        # Extract key insights and structure
        key_points = self._extract_key_points(source_content, source_type)
        
        # Apply type-specific transformations
        if target_type == ContentType.SOCIAL_MEDIA_POST:
            return await self._transform_to_social_media(
                key_points, target_platforms, brand_voice, **kwargs
            )
        elif target_type == ContentType.VIDEO_SCRIPT:
            return await self._transform_to_video_script(
                key_points, brand_voice, **kwargs
            )
        elif target_type == ContentType.EMAIL_NEWSLETTER:
            return await self._transform_to_email_newsletter(
                key_points, brand_voice, **kwargs
            )
        elif target_type == ContentType.BLOG_POST:
            return await self._transform_to_blog_post(
                key_points, brand_voice, **kwargs
            )
        else:
            # Generic transformation
            return self._apply_generic_transformation(
                key_points, target_type, target_platforms, brand_voice
            )
    
    def _extract_key_points(self, content: str, content_type: ContentType) -> List[Dict[str, Any]]:
        """Extract key points and insights from source content."""
        key_points = []
        
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            # Extract key information
            point = {
                "id": i + 1,
                "content": paragraph,
                "length": len(paragraph),
                "key_phrases": self._extract_key_phrases(paragraph),
                "sentiment": self._analyze_sentiment(paragraph),
                "has_numbers": bool(re.search(r'\d+', paragraph)),
                "has_quotes": '"' in paragraph or "'" in paragraph,
                "has_questions": '?' in paragraph,
                "has_calls_to_action": self._has_call_to_action(paragraph)
            }
            key_points.append(point)
        
        return key_points
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple key phrase extraction (could be enhanced with NLP)
        words = text.split()
        key_phrases = []
        
        # Look for capitalized phrases, numbers, and special terms
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 3:
                # Check if it's part of a phrase
                phrase = word
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    phrase += " " + words[i + 1]
                key_phrases.append(phrase)
            elif re.match(r'\d+', word):
                key_phrases.append(word)
        
        return key_phrases[:5]  # Limit to top 5
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'love', 'like']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'dislike', 'problem', 'issue']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _has_call_to_action(self, text: str) -> bool:
        """Check if text contains call-to-action phrases."""
        cta_phrases = [
            'click here', 'learn more', 'get started', 'sign up', 'download',
            'contact us', 'call now', 'visit', 'check out', 'try it'
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in cta_phrases)
    
    async def _transform_to_social_media(
        self,
        key_points: List[Dict[str, Any]],
        target_platforms: List[Platform],
        brand_voice: str,
        **kwargs
    ) -> str:
        """Transform content to social media format."""
        
        # Get platform requirements
        platform_req = get_platform_requirements(target_platforms[0]) if target_platforms else None
        char_limit = platform_req.character_limits.get("post", 280) if platform_req else 280
        
        # Select most engaging points
        engaging_points = self._select_engaging_points(key_points, char_limit)
        
        # Format for social media
        social_content = self._format_social_media_content(
            engaging_points, target_platforms[0], brand_voice, char_limit
        )
        
        return social_content
    
    async def _transform_to_video_script(
        self,
        key_points: List[Dict[str, Any]],
        brand_voice: str,
        **kwargs
    ) -> str:
        """Transform content to video script format."""
        
        # Structure for video script
        script_sections = {
            "hook": self._create_video_hook(key_points, brand_voice),
            "introduction": self._create_video_intro(key_points, brand_voice),
            "main_content": self._create_video_main_content(key_points, brand_voice),
            "conclusion": self._create_video_conclusion(key_points, brand_voice),
            "call_to_action": self._create_video_cta(key_points, brand_voice)
        }
        
        # Format as video script
        script = self._format_video_script(script_sections)
        
        return script
    
    async def _transform_to_email_newsletter(
        self,
        key_points: List[Dict[str, Any]],
        brand_voice: str,
        **kwargs
    ) -> str:
        """Transform content to email newsletter format."""
        
        # Create newsletter structure
        newsletter = {
            "subject_line": self._create_newsletter_subject(key_points, brand_voice),
            "greeting": self._create_newsletter_greeting(brand_voice),
            "main_content": self._create_newsletter_content(key_points, brand_voice),
            "signature": self._create_newsletter_signature(brand_voice)
        }
        
        # Format as newsletter
        formatted_newsletter = self._format_newsletter(newsletter)
        
        return formatted_newsletter
    
    async def _transform_to_blog_post(
        self,
        key_points: List[Dict[str, Any]],
        brand_voice: str,
        **kwargs
    ) -> str:
        """Transform content to blog post format."""
        
        # Create blog structure
        blog = {
            "title": self._create_blog_title(key_points, brand_voice),
            "introduction": self._create_blog_intro(key_points, brand_voice),
            "body": self._create_blog_body(key_points, brand_voice),
            "conclusion": self._create_blog_conclusion(key_points, brand_voice)
        }
        
        # Format as blog post
        formatted_blog = self._format_blog_post(blog)
        
        return formatted_blog
    
    def _select_engaging_points(self, key_points: List[Dict[str, Any]], char_limit: int) -> List[Dict[str, Any]]:
        """Select the most engaging points for social media."""
        # Score points based on engagement potential
        scored_points = []
        
        for point in key_points:
            score = 0
            
            # Higher score for shorter content (easier to read)
            if point["length"] <= 100:
                score += 3
            elif point["length"] <= 200:
                score += 2
            else:
                score += 1
            
            # Higher score for positive sentiment
            if point["sentiment"] == "positive":
                score += 2
            
            # Higher score for questions and calls to action
            if point["has_questions"]:
                score += 2
            if point["has_calls_to_action"]:
                score += 2
            
            # Higher score for numbers and statistics
            if point["has_numbers"]:
                score += 1
            
            scored_points.append((point, score))
        
        # Sort by score and select top points that fit within char limit
        scored_points.sort(key=lambda x: x[1], reverse=True)
        
        selected_points = []
        current_length = 0
        
        for point, score in scored_points:
            if current_length + point["length"] <= char_limit:
                selected_points.append(point)
                current_length += point["length"]
            else:
                break
        
        return selected_points
    
    def _format_social_media_content(
        self,
        points: List[Dict[str, Any]],
        platform: Platform,
        brand_voice: str,
        char_limit: int
    ) -> str:
        """Format content for social media."""
        
        if not points:
            return f"[{brand_voice} content about this topic]"
        
        # Combine points into engaging social media content
        content_parts = []
        
        for point in points:
            # Add emojis based on content
            emoji = self._get_relevant_emoji(point["content"])
            formatted_point = f"{emoji} {point['content']}"
            content_parts.append(formatted_point)
        
        # Join with line breaks
        content = "\n\n".join(content_parts)
        
        # Add hashtags if space allows
        hashtags = self._generate_relevant_hashtags(points, platform)
        if hashtags and len(content + " " + hashtags) <= char_limit:
            content += f"\n\n{hashtags}"
        
        return content
    
    def _get_relevant_emoji(self, text: str) -> str:
        """Get relevant emoji for text content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['ai', 'technology', 'future']):
            return "🤖"
        elif any(word in text_lower for word in ['success', 'growth', 'improvement']):
            return "🚀"
        elif any(word in text_lower for word in ['money', 'business', 'profit']):
            return "💰"
        elif any(word in text_lower for word in ['love', 'heart', 'care']):
            return "❤️"
        elif any(word in text_lower for word in ['lightbulb', 'idea', 'innovation']):
            return "💡"
        elif any(word in text_lower for word in ['star', 'excellent', 'amazing']):
            return "⭐"
        else:
            return "📝"
    
    def _generate_relevant_hashtags(self, points: List[Dict[str, Any]], platform: Platform) -> str:
        """Generate relevant hashtags for the content."""
        # Extract common themes from key points
        themes = set()
        
        for point in points:
            for phrase in point["key_phrases"]:
                if len(phrase) > 3:
                    # Convert to hashtag format
                    hashtag = "#" + phrase.replace(" ", "").replace("-", "")
                    themes.add(hashtag)
        
        # Add platform-specific hashtags
        if platform == Platform.TWITTER:
            themes.update(["#ContentMarketing", "#DigitalMarketing", "#AI"])
        elif platform == Platform.LINKEDIN:
            themes.update(["#ProfessionalDevelopment", "#IndustryInsights", "#Innovation"])
        elif platform == Platform.INSTAGRAM:
            themes.update(["#CreativeContent", "#VisualStorytelling", "#Engagement"])
        
        # Limit hashtags and return
        hashtag_list = list(themes)[:5]  # Max 5 hashtags
        return " ".join(hashtag_list)
    
    def _create_video_hook(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create an engaging video hook."""
        if not key_points:
            return f"Hey there! Let me share something amazing with you about {brand_voice} content."
        
        # Use the most engaging point for the hook
        best_point = max(key_points, key=lambda x: x.get("has_questions", False) + x.get("has_numbers", False))
        
        if best_point["has_questions"]:
            return f"Ever wondered {best_point['content'][:50]}...? Let me show you!"
        elif best_point["has_numbers"]:
            return f"Did you know that {best_point['content'][:50]}...? This will blow your mind!"
        else:
            return f"Here's the truth about {best_point['content'][:50]}... You won't believe what I discovered!"
    
    def _create_video_intro(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create video introduction."""
        return f"Welcome! I'm excited to share some incredible insights with you today. We're going to dive deep into {len(key_points)} key areas that will transform your understanding."
    
    def _create_video_main_content(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create main video content."""
        content_parts = []
        
        for i, point in enumerate(key_points, 1):
            content_parts.append(f"Point {i}: {point['content']}")
        
        return "\n\n".join(content_parts)
    
    def _create_video_conclusion(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create video conclusion."""
        return f"These {len(key_points)} insights are game-changers. Remember, success comes from consistent application of these principles."
    
    def _create_video_cta(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create video call-to-action."""
        return "If you found this valuable, hit that like button and subscribe for more amazing content. Drop a comment below with your biggest takeaway!"
    
    def _format_video_script(self, script_sections: Dict[str, str]) -> str:
        """Format video script sections."""
        script = []
        
        for section, content in script_sections.items():
            if content:
                script.append(f"{section.upper()}:")
                script.append(content)
                script.append("")  # Empty line for separation
        
        return "\n".join(script)
    
    def _create_newsletter_subject(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create newsletter subject line."""
        if not key_points:
            return f"Exciting {brand_voice} insights for you"
        
        # Use the most engaging point for subject
        best_point = max(key_points, key=lambda x: x.get("has_numbers", False) + x.get("sentiment") == "positive")
        
        if best_point["has_numbers"]:
            return f"{best_point['content'][:40]}... - You won't believe the numbers!"
        else:
            return f"{best_point['content'][:40]}... - This will change everything!"
    
    def _create_newsletter_greeting(self, brand_voice: str) -> str:
        """Create newsletter greeting."""
        return f"Hi there!\n\nI hope this email finds you well. I wanted to share some {brand_voice} insights that I think you'll find valuable."
    
    def _create_newsletter_content(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create newsletter main content."""
        content_parts = []
        
        for i, point in enumerate(key_points, 1):
            content_parts.append(f"🔑 Key Insight {i}: {point['content']}")
        
        return "\n\n".join(content_parts)
    
    def _create_newsletter_signature(self, brand_voice: str) -> str:
        """Create newsletter signature."""
        return f"Best regards,\n\nYour {brand_voice} content team\n\nP.S. If you have any questions or want to learn more, just reply to this email!"
    
    def _format_newsletter(self, newsletter: Dict[str, str]) -> str:
        """Format newsletter content."""
        return f"{newsletter['subject_line']}\n\n{newsletter['greeting']}\n\n{newsletter['main_content']}\n\n{newsletter['signature']}"
    
    def _create_blog_title(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create blog post title."""
        if not key_points:
            return f"The Ultimate Guide to {brand_voice} Content"
        
        # Use the most engaging point for title
        best_point = max(key_points, key=lambda x: (x.get("has_numbers", False), x.get("sentiment") == "positive"))
        
        if best_point["has_numbers"]:
            return f"{best_point['content'][:50]}...: A Complete Guide"
        else:
            return f"How to {best_point['content'][:40]}...: Expert Tips and Strategies"
    
    def _create_blog_intro(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create blog introduction."""
        return f"In today's fast-paced digital world, understanding {brand_voice} content is more important than ever. This comprehensive guide will walk you through {len(key_points)} essential insights that can transform your approach."
    
    def _create_blog_body(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create blog body content."""
        body_parts = []
        
        for i, point in enumerate(key_points, 1):
            body_parts.append(f"## Insight {i}: {point['content'][:50]}...\n\n{point['content']}\n")
        
        return "\n".join(body_parts)
    
    def _create_blog_conclusion(self, key_points: List[Dict[str, Any]], brand_voice: str) -> str:
        """Create blog conclusion."""
        return f"These {len(key_points)} insights represent the foundation of successful {brand_voice} content creation. By implementing these strategies consistently, you'll see remarkable improvements in your results."
    
    def _format_blog_post(self, blog: Dict[str, str]) -> str:
        """Format blog post content."""
        return f"# {blog['title']}\n\n{blog['introduction']}\n\n{blog['body']}\n\n## Conclusion\n\n{blog['conclusion']}"
    
    def _apply_generic_transformation(
        self,
        key_points: List[Dict[str, Any]],
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str
    ) -> str:
        """Apply generic transformation for unknown content types."""
        # Combine key points into a coherent narrative
        content_parts = []
        
        for i, point in enumerate(key_points, 1):
            content_parts.append(f"{i}. {point['content']}")
        
        content = "\n\n".join(content_parts)
        
        # Add brand voice context
        if brand_voice:
            content = f"[{brand_voice} content]\n\n{content}"
        
        return content
    
    async def _optimize_content(
        self,
        content: str,
        target_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str
    ) -> str:
        """Optimize repurposed content for quality and engagement."""
        
        # Apply content quality improvements
        optimized = content
        
        # Improve readability
        optimized = self._improve_readability(optimized)
        
        # Add brand voice consistency
        optimized = self._ensure_brand_voice_consistency(optimized, brand_voice)
        
        # Optimize for platforms
        if target_platforms:
            optimized = self._optimize_for_platforms(optimized, target_platforms[0])
        
        # Validate final content
        validation = validate_content_length(optimized, target_type)
        if not validation["valid"]:
            # Truncate or expand as needed
            optimized = self._adjust_content_length(optimized, target_type, validation)
        
        return optimized
    
    def _improve_readability(self, content: str) -> str:
        """Improve content readability."""
        # Break long sentences
        sentences = content.split('. ')
        improved_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 100:
                # Break into shorter sentences
                words = sentence.split()
                mid_point = len(words) // 2
                improved_sentences.append('. '.join(words[:mid_point]) + '.')
                improved_sentences.append('. '.join(words[mid_point:]) + '.')
            else:
                improved_sentences.append(sentence)
        
        return '. '.join(improved_sentences)
    
    def _ensure_brand_voice_consistency(self, content: str, brand_voice: str) -> str:
        """Ensure brand voice consistency throughout content."""
        # This is a simplified implementation
        # In a real system, you might use AI to analyze and adjust tone
        
        if "professional" in brand_voice.lower():
            # Remove casual language
            content = re.sub(r'\b(hey|hi there|awesome|cool)\b', 'Hello', content, flags=re.IGNORECASE)
        elif "casual" in brand_voice.lower():
            # Add casual language
            content = content.replace("Hello", "Hey there!")
        
        return content
    
    def _optimize_for_platforms(self, content: str, platform: Platform) -> str:
        """Optimize content for specific platform requirements."""
        platform_req = get_platform_requirements(platform)
        if not platform_req:
            return content
        
        # Apply platform-specific optimizations
        if platform == Platform.TWITTER:
            # Ensure hashtag optimization
            if '#' not in content:
                content += "\n\n#ContentMarketing #DigitalMarketing"
        elif platform == Platform.LINKEDIN:
            # Ensure professional tone
            content = content.replace("Hey there!", "Hello")
        
        return content
    
    def _adjust_content_length(self, content: str, target_type: ContentType, validation: Dict[str, Any]) -> str:
        """Adjust content length to meet requirements."""
        structure = get_content_structure(target_type)
        if not structure:
            return content
        
        if validation.get("warnings"):
            for warning in validation["warnings"]:
                if "too long" in warning.lower() and structure.max_length:
                    # Truncate content
                    content = content[:structure.max_length - 3] + "..."
                elif "too short" in warning.lower() and structure.min_length:
                    # Expand content
                    padding = " " * (structure.min_length - len(content))
                    content += padding
        
        return content
    
    def _calculate_quality_metrics(
        self,
        source_content: str,
        target_content: str,
        source_type: ContentType,
        target_type: ContentType,
        target_platforms: List[Platform]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for repurposed content."""
        
        # Content length metrics
        source_length = len(source_content)
        target_length = len(target_content)
        compression_ratio = target_length / source_length if source_length > 0 else 0
        
        # Readability metrics
        source_sentences = len(source_content.split('.'))
        target_sentences = len(target_content.split('.'))
        
        # Engagement metrics (simplified)
        engagement_score = 0
        if '?' in target_content:
            engagement_score += 0.2
        if '!' in target_content:
            engagement_score += 0.1
        if '#' in target_content:
            engagement_score += 0.1
        if any(word in target_content.lower() for word in ['you', 'your', 'we', 'us']):
            engagement_score += 0.2
        
        # Platform optimization score
        platform_score = 0
        if target_platforms:
            platform_req = get_platform_requirements(target_platforms[0])
            if platform_req:
                validation = validate_content_length(target_content, target_type)
                if validation["valid"]:
                    platform_score = 1.0
                else:
                    platform_score = 0.5
        
        # Overall quality score
        overall_score = min(1.0, (engagement_score + platform_score + (1 - abs(0.7 - compression_ratio))) / 3)
        
        return {
            "compression_ratio": compression_ratio,
            "readability": {
                "source_sentences": source_sentences,
                "target_sentences": target_sentences,
                "sentence_reduction": source_sentences - target_sentences
            },
            "engagement_score": engagement_score,
            "platform_optimization_score": platform_score,
            "overall_quality_score": overall_score,
            "meets_requirements": overall_score >= self.quality_threshold
        }
    
    async def health_check(self) -> bool:
        """Check if the content repurposing service is healthy."""
        try:
            # Test basic functionality
            test_content = "This is a test content for health check."
            test_result = await self.repurpose_content(
                test_content,
                ContentType.BLOG_POST,
                ContentType.SOCIAL_MEDIA_POST,
                [Platform.TWITTER],
                "Professional"
            )
            
            return (
                test_result is not None and
                test_result.repurposed_content is not None and
                len(test_result.repurposed_content) > 0
            )
            
        except Exception as e:
            logger.error(f"Content repurposing health check failed: {e}")
            return False


# Create a singleton instance
content_repurposing_service = ContentRepurposingService()
