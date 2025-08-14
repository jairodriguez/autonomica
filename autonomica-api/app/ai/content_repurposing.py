"""
Content Repurposing Module

This module provides advanced algorithms for repurposing existing content
into different formats while maintaining quality and relevance.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from content_types_simple import (
    ContentType, ContentFormat, ContentTypeRegistry, 
    get_content_registry, validate_content_structure
)
from content_templates import get_template_engine

logger = logging.getLogger(__name__)


@dataclass
class RepurposingStrategy:
    """Defines a strategy for repurposing content."""
    name: str
    description: str
    complexity: str  # Simple, Medium, Complex
    estimated_time: int  # seconds
    quality_impact: str  # High, Medium, Low
    requirements: List[str]
    output_format: ContentFormat


class ContentRepurposingEngine:
    """Advanced engine for content repurposing operations."""
    
    def __init__(self):
        self.content_registry = get_content_registry()
        self.template_engine = get_template_engine()
        self.strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> Dict[str, RepurposingStrategy]:
        """Initialize repurposing strategies."""
        strategies = {}
        
        # Blog to Tweet strategies
        strategies["blog_to_tweet"] = RepurposingStrategy(
            name="blog_to_tweet",
            description="Extract key points and insights from blog post into engaging tweet",
            complexity="Simple",
            estimated_time=30,
            quality_impact="Medium",
            requirements=["blog_content", "target_tone"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        strategies["blog_to_tweet_thread"] = RepurposingStrategy(
            name="blog_to_tweet_thread",
            description="Summarize each section of blog post into tweet thread",
            complexity="Medium",
            estimated_time=60,
            quality_impact="High",
            requirements=["blog_content", "thread_length", "target_tone"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        # Blog to Social Media strategies
        strategies["blog_to_facebook"] = RepurposingStrategy(
            name="blog_to_facebook",
            description="Create engaging Facebook post with excerpt and call-to-action",
            complexity="Simple",
            estimated_time=45,
            quality_impact="High",
            requirements=["blog_content", "target_tone", "brand_voice"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        strategies["blog_to_linkedin"] = RepurposingStrategy(
            name="blog_to_linkedin",
            description="Extract professional insights and industry expertise",
            complexity="Medium",
            estimated_time=60,
            quality_impact="High",
            requirements=["blog_content", "professional_tone", "industry_context"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        # Blog to Visual strategies
        strategies["blog_to_carousel"] = RepurposingStrategy(
            name="blog_to_carousel",
            description="Convert key points into carousel slide format",
            complexity="Complex",
            estimated_time=120,
            quality_impact="High",
            requirements=["blog_content", "slide_count", "visual_descriptions"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        strategies["blog_to_video_script"] = RepurposingStrategy(
            name="blog_to_video_script",
            description="Convert blog content to spoken narrative format",
            complexity="Complex",
            estimated_time=180,
            quality_impact="High",
            requirements=["blog_content", "video_duration", "spoken_language"],
            output_format=ContentFormat.PLAIN_TEXT
        )
        
        # Social Media to Blog strategies
        strategies["thread_to_blog"] = RepurposingStrategy(
            name="thread_to_blog",
            description="Expand tweet thread into comprehensive blog post",
            complexity="Medium",
            estimated_time=300,
            quality_impact="Medium",
            requirements=["tweet_thread", "target_length", "additional_research"],
            output_format=ContentFormat.MARKDOWN
        )
        
        # Email strategies
        strategies["blog_to_newsletter"] = RepurposingStrategy(
            name="blog_to_newsletter",
            description="Convert blog post to email newsletter format",
            complexity="Medium",
            estimated_time=90,
            quality_impact="High",
            requirements=["blog_content", "email_structure", "personalization"],
            output_format=ContentFormat.HTML
        )
        
        return strategies
    
    def get_available_strategies(self, source_type: ContentType, target_type: ContentType) -> List[RepurposingStrategy]:
        """Get available repurposing strategies for the given transformation."""
        available_strategies = []
        
        # Map content type combinations to strategies
        strategy_mapping = {
            (ContentType.BLOG_POST, ContentType.TWEET): ["blog_to_tweet"],
            (ContentType.BLOG_POST, ContentType.TWEET_THREAD): ["blog_to_tweet_thread"],
            (ContentType.BLOG_POST, ContentType.FACEBOOK_POST): ["blog_to_facebook"],
            (ContentType.BLOG_POST, ContentType.LINKEDIN_POST): ["blog_to_linkedin"],
            (ContentType.BLOG_POST, ContentType.CAROUSEL): ["blog_to_carousel"],
            (ContentType.BLOG_POST, ContentType.VIDEO_SCRIPT): ["blog_to_video_script"],
            (ContentType.BLOG_POST, ContentType.EMAIL_NEWSLETTER): ["blog_to_newsletter"],
            (ContentType.TWEET_THREAD, ContentType.BLOG_POST): ["thread_to_blog"],
        }
        
        strategy_keys = strategy_mapping.get((source_type, target_type), [])
        for key in strategy_keys:
            if key in self.strategies:
                available_strategies.append(self.strategies[key])
        
        return available_strategies
    
    def get_optimal_strategy(self, source_type: ContentType, target_type: ContentType, 
                           requirements: Dict[str, Any]) -> Optional[RepurposingStrategy]:
        """Get the optimal repurposing strategy based on requirements."""
        available_strategies = self.get_available_strategies(source_type, target_type)
        
        if not available_strategies:
            return None
        
        # Score strategies based on requirements
        scored_strategies = []
        for strategy in available_strategies:
            score = self._score_strategy(strategy, requirements)
            scored_strategies.append((strategy, score))
        
        # Sort by score (higher is better) and return the best
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        return scored_strategies[0][0] if scored_strategies else None
    
    def _score_strategy(self, strategy: RepurposingStrategy, requirements: Dict[str, Any]) -> float:
        """Score a strategy based on how well it meets requirements."""
        score = 0.0
        
        # Base score from quality impact
        quality_scores = {"High": 3.0, "Medium": 2.0, "Low": 1.0}
        score += quality_scores.get(strategy.quality_impact, 1.0)
        
        # Time efficiency score (faster is better, but not at expense of quality)
        if strategy.estimated_time <= 60:
            score += 1.0
        elif strategy.estimated_time <= 120:
            score += 0.5
        
        # Complexity score (simpler is better for basic needs)
        complexity_scores = {"Simple": 1.0, "Medium": 0.8, "Complex": 0.6}
        score += complexity_scores.get(strategy.complexity, 0.5)
        
        # Requirements match score
        requirements_met = sum(1 for req in strategy.requirements if req in requirements)
        requirements_ratio = requirements_met / len(strategy.requirements) if strategy.requirements else 0
        score += requirements_ratio * 2.0
        
        return score
    
    def repurpose_content(self, source_content: str, source_type: ContentType, 
                         target_type: ContentType, strategy_name: Optional[str] = None,
                         **kwargs) -> Dict[str, Any]:
        """Repurpose content using the specified or optimal strategy."""
        
        # Get available strategies
        available_strategies = self.get_available_strategies(source_type, target_type)
        
        if not available_strategies:
            raise ValueError(f"No repurposing strategies available from {source_type} to {target_type}")
        
        # Select strategy
        if strategy_name:
            strategy = next((s for s in available_strategies if s.name == strategy_name), None)
            if not strategy:
                raise ValueError(f"Strategy '{strategy_name}' not available for this transformation")
        else:
            # Use optimal strategy
            strategy = self.get_optimal_strategy(source_type, target_type, kwargs)
            if not strategy:
                raise ValueError(f"Could not determine optimal strategy for this transformation")
        
        # Execute repurposing
        try:
            result = self._execute_strategy(strategy, source_content, source_type, target_type, **kwargs)
            return {
                "success": True,
                "strategy_used": strategy.name,
                "repurposed_content": result,
                "metadata": {
                    "source_type": source_type.value,
                    "target_type": target_type.value,
                    "strategy_complexity": strategy.complexity,
                    "estimated_time": strategy.estimated_time,
                    "quality_impact": strategy.quality_impact
                }
            }
        except Exception as e:
            logger.error(f"Repurposing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "strategy_used": strategy.name
            }
    
    def _execute_strategy(self, strategy: RepurposingStrategy, source_content: str,
                         source_type: ContentType, target_type: ContentType, **kwargs) -> str:
        """Execute a specific repurposing strategy."""
        
        if strategy.name == "blog_to_tweet":
            return self._blog_to_tweet(source_content, **kwargs)
        elif strategy.name == "blog_to_tweet_thread":
            return self._blog_to_tweet_thread(source_content, **kwargs)
        elif strategy.name == "blog_to_facebook":
            return self._blog_to_facebook(source_content, **kwargs)
        elif strategy.name == "blog_to_linkedin":
            return self._blog_to_linkedin(source_content, **kwargs)
        elif strategy.name == "blog_to_carousel":
            return self._blog_to_carousel(source_content, **kwargs)
        elif strategy.name == "blog_to_video_script":
            return self._blog_to_video_script(source_content, **kwargs)
        elif strategy.name == "thread_to_blog":
            return self._thread_to_blog(source_content, **kwargs)
        elif strategy.name == "blog_to_newsletter":
            return self._blog_to_newsletter(source_content, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {strategy.name}")
    
    def _blog_to_tweet(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to tweet using key points extraction."""
        # Extract key sentences (simple approach)
        sentences = re.split(r'[.!?]+', blog_content)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 100]
        
        if not key_sentences:
            # Fallback: use first sentence
            key_sentences = [blog_content[:100]]
        
        # Select the most engaging sentence
        tweet_content = key_sentences[0]
        
        # Truncate to fit Twitter limit
        if len(tweet_content) > 250:  # Leave room for hashtags
            tweet_content = tweet_content[:247] + "..."
        
        # Add hashtags
        hashtags = self._extract_hashtags(blog_content)
        if hashtags:
            tweet_content += f"\n\n{hashtags}"
        
        return tweet_content
    
    def _blog_to_tweet_thread(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to tweet thread."""
        thread_length = kwargs.get('thread_length', 5)
        
        # Split content into sections
        sections = self._extract_blog_sections(blog_content)
        
        # Create thread
        thread_parts = []
        
        # Thread intro
        if sections.get('introduction'):
            intro = sections['introduction'][:200] + "..." if len(sections['introduction']) > 200 else sections['introduction']
            thread_parts.append(f"1/ {intro}")
        
        # Main content parts
        if sections.get('main_content'):
            main_content = sections['main_content']
            # Split main content into chunks
            chunks = self._split_content_into_chunks(main_content, thread_length - 2)  # -2 for intro and conclusion
            
            for i, chunk in enumerate(chunks[:thread_length - 2]):
                thread_parts.append(f"{i + 2}/ {chunk[:200]}...")
        
        # Thread conclusion
        if sections.get('conclusion'):
            conclusion = sections['conclusion'][:200] + "..." if len(sections['conclusion']) > 200 else sections['conclusion']
            thread_parts.append(f"{thread_length}/ {conclusion}")
        
        # Add hashtags to the last tweet
        hashtags = self._extract_hashtags(blog_content)
        if hashtags and thread_parts:
            thread_parts[-1] += f"\n\n{hashtags}"
        
        return "\n\n".join(thread_parts)
    
    def _blog_to_facebook(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to Facebook post."""
        # Extract engaging excerpt
        excerpt = self._extract_engaging_excerpt(blog_content)
        
        # Add call-to-action
        cta = kwargs.get('call_to_action', 'What do you think about this? Share your thoughts below!')
        
        # Add hashtags
        hashtags = self._extract_hashtags(blog_content)
        
        facebook_post = f"{excerpt}\n\n{cta}"
        if hashtags:
            facebook_post += f"\n\n{hashtags}"
        
        return facebook_post
    
    def _blog_to_linkedin(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to LinkedIn post."""
        # Extract professional insights
        insights = self._extract_professional_insights(blog_content)
        
        # Create hook
        hook = kwargs.get('hook', 'Here are some key insights from my latest research:')
        
        # Add call-to-action
        cta = kwargs.get('call_to_action', 'What are your thoughts on this? I\'d love to hear your perspective.')
        
        # Add hashtags
        hashtags = self._extract_hashtags(blog_content)
        
        linkedin_post = f"{hook}\n\n{insights}\n\n{cta}"
        if hashtags:
            linkedin_post += f"\n\n{hashtags}"
        
        return linkedin_post
    
    def _blog_to_carousel(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to carousel format."""
        slide_count = kwargs.get('slide_count', 5)
        
        # Extract key points
        key_points = self._extract_key_points(blog_content, slide_count)
        
        # Create carousel content
        carousel_content = []
        for i, point in enumerate(key_points, 1):
            slide_title = f"Key Point {i}"
            slide_content = point[:150] + "..." if len(point) > 150 else point
            carousel_content.append(f"Slide {i}: {slide_title}\n{slide_content}")
        
        # Add conclusion
        conclusion = kwargs.get('conclusion', 'These insights can help transform your approach.')
        carousel_content.append(f"CONCLUSION:\n{conclusion}")
        
        # Add hashtags
        hashtags = self._extract_hashtags(blog_content)
        if hashtags:
            carousel_content.append(hashtags)
        
        return "\n\n".join(carousel_content)
    
    def _blog_to_video_script(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to video script."""
        video_duration = kwargs.get('video_duration', '2-3 minutes')
        
        # Extract sections
        sections = self._extract_blog_sections(blog_content)
        
        # Create video script structure
        script_parts = []
        
        # Hook
        if sections.get('introduction'):
            hook = sections['introduction'][:100] + "..." if len(sections['introduction']) > 100 else sections['introduction']
            script_parts.append(f"HOOK (0-15 seconds):\n{hook}")
        
        # Introduction
        if sections.get('introduction'):
            intro = sections['introduction'][:150] + "..." if len(sections['introduction']) > 150 else sections['introduction']
            script_parts.append(f"INTRODUCTION (15-30 seconds):\n{intro}")
        
        # Main points
        if sections.get('main_content'):
            main_points = self._extract_key_points(sections['main_content'], 3)
            script_parts.append("MAIN POINTS:\n" + "\n".join(main_points))
        
        # Conclusion
        if sections.get('conclusion'):
            conclusion = sections['conclusion'][:100] + "..." if len(sections['conclusion']) > 100 else sections['conclusion']
            script_parts.append(f"CONCLUSION (30 seconds):\n{conclusion}")
        
        # Call to action
        cta = kwargs.get('call_to_action', 'Subscribe for more insights!')
        script_parts.append(f"CALL TO ACTION (15 seconds):\n{cta}")
        
        # Add metadata
        script_parts.append(f"---\nTotal Duration: {video_duration}\nTarget Audience: Business professionals")
        
        return "\n\n".join(script_parts)
    
    def _thread_to_blog(self, thread_content: str, **kwargs) -> str:
        """Convert tweet thread to blog post."""
        # Split thread into parts
        thread_parts = thread_content.split('\n\n')
        
        # Extract content from each part
        blog_sections = []
        
        # Introduction from first tweet
        if thread_parts:
            first_tweet = thread_parts[0].replace('1/ ', '').replace('Thread: ', '')
            blog_sections.append(f"## Introduction\n\n{first_tweet}")
        
        # Main content from middle tweets
        for part in thread_parts[1:-1]:
            if part.startswith(('2/', '3/', '4/', '5/')):
                content = part.split(' ', 1)[1] if ' ' in part else part
                blog_sections.append(f"## Main Point\n\n{content}")
        
        # Conclusion from last tweet
        if len(thread_parts) > 1:
            last_tweet = thread_parts[-1].split(' ', 1)[1] if ' ' in thread_parts[-1] else thread_parts[-1]
            # Remove hashtags from conclusion
            last_tweet = re.sub(r'#\w+', '', last_tweet).strip()
            blog_sections.append(f"## Conclusion\n\n{last_tweet}")
        
        # Combine into blog post
        blog_post = "\n\n".join(blog_sections)
        
        return blog_post
    
    def _blog_to_newsletter(self, blog_content: str, **kwargs) -> str:
        """Convert blog post to email newsletter."""
        # Extract sections
        sections = self._extract_blog_sections(blog_content)
        
        # Create newsletter structure
        newsletter_parts = []
        
        # Subject line
        subject = kwargs.get('subject_line', 'Your Weekly Insights')
        newsletter_parts.append(f"Subject: {subject}")
        
        # Preheader
        if sections.get('introduction'):
            preheader = sections['introduction'][:100] + "..." if len(sections['introduction']) > 100 else sections['introduction']
            newsletter_parts.append(f"Preheader: {preheader}")
        
        # Greeting
        greeting = kwargs.get('greeting', 'Hello there,')
        newsletter_parts.append(f"Dear {greeting}")
        
        # Main content
        if sections.get('main_content'):
            main_content = sections['main_content'][:500] + "..." if len(sections['main_content']) > 500 else sections['main_content']
            newsletter_parts.append(f"{main_content}")
        
        # Footer
        footer = kwargs.get('footer', 'Thanks for reading!')
        newsletter_parts.append(f"{footer}")
        
        # Company info
        company_name = kwargs.get('company_name', 'Autonomica')
        unsubscribe_link = kwargs.get('unsubscribe_link', 'Unsubscribe')
        newsletter_parts.append(f"---\n{company_name}\n{unsubscribe_link}")
        
        return "\n\n".join(newsletter_parts)
    
    def _extract_blog_sections(self, blog_content: str) -> Dict[str, str]:
        """Extract sections from blog content."""
        sections = {}
        
        # Simple section extraction
        lines = blog_content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if line.lower().startswith(('introduction', 'intro', 'main', 'conclusion', 'summary')):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.lower().replace(':', '').replace(' ', '_')
                current_content = []
            elif current_section:
                current_content.append(line)
            else:
                # Default to main content if no section identified
                if 'main_content' not in sections:
                    sections['main_content'] = ''
                sections['main_content'] += line + '\n'
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Clean up main content
        if 'main_content' in sections:
            sections['main_content'] = sections['main_content'].strip()
        
        return sections
    
    def _extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extract key points from content."""
        # Simple approach: split by sentences and select key ones
        sentences = re.split(r'[.!?]+', content)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.strip()) < 200]
        
        # Return top sentences up to max_points
        return key_sentences[:max_points]
    
    def _extract_engaging_excerpt(self, content: str, max_length: int = 200) -> str:
        """Extract an engaging excerpt from content."""
        # Find the most engaging sentence (simple heuristic: longer sentences with action words)
        sentences = re.split(r'[.!?]+', content)
        engaging_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not engaging_sentences:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # Select the most engaging sentence
        excerpt = engaging_sentences[0]
        
        # Truncate if needed
        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length-3] + "..."
        
        return excerpt
    
    def _extract_professional_insights(self, content: str, max_length: int = 300) -> str:
        """Extract professional insights from content."""
        # Extract insights (sentences with professional keywords)
        professional_keywords = ['strategy', 'business', 'industry', 'market', 'growth', 'efficiency', 'innovation']
        
        sentences = re.split(r'[.!?]+', content)
        insight_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in professional_keywords):
                insight_sentences.append(sentence)
        
        if not insight_sentences:
            return self._extract_engaging_excerpt(content, max_length)
        
        # Combine insights
        insights = ' '.join(insight_sentences[:3])  # Take first 3 insights
        
        # Truncate if needed
        if len(insights) > max_length:
            insights = insights[:max_length-3] + "..."
        
        return insights
    
    def _extract_hashtags(self, content: str, max_hashtags: int = 5) -> str:
        """Extract or generate relevant hashtags from content."""
        # Extract existing hashtags
        existing_hashtags = re.findall(r'#\w+', content)
        
        if existing_hashtags:
            return ' '.join(existing_hashtags[:max_hashtags])
        
        # Generate hashtags from key words
        words = re.findall(r'\b\w+\b', content.lower())
        # Filter out common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        key_words = [word for word in words if word not in common_words and len(word) > 3]
        
        # Take top words and convert to hashtags
        hashtags = [f"#{word.capitalize()}" for word in key_words[:max_hashtags]]
        
        return ' '.join(hashtags) if hashtags else "#ContentCreation #DigitalMarketing"
    
    def _split_content_into_chunks(self, content: str, num_chunks: int) -> List[str]:
        """Split content into roughly equal chunks."""
        if num_chunks <= 1:
            return [content]
        
        # Simple chunking by character count
        chunk_size = len(content) // num_chunks
        chunks = []
        
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size if i < num_chunks - 1 else len(content)
            chunk = content[start:end]
            
            # Try to break at sentence boundary
            if i < num_chunks - 1 and end < len(content):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.7:  # If we can break at 70% or later
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
            
            chunks.append(chunk.strip())
        
        return chunks


# Global repurposing engine instance
repurposing_engine = ContentRepurposingEngine()


def get_repurposing_engine() -> ContentRepurposingEngine:
    """Get the global repurposing engine instance."""
    return repurposing_engine