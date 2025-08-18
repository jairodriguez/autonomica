"""
LangChain Content Generation Module

This module implements the content generation and repurposing pipeline using LangChain
as specified in the task requirements. It provides the core functionality for
transforming blog content into various social media formats.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

try:
    from langchain.chains.summarize import load_summarize_chain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain langchain-openai")

from .content_types import (
    ContentType, ContentFormat, Platform, ContentStructure,
    get_content_structure, get_platform_requirements, get_content_template,
    get_repurposing_rules, validate_content_length
)

logger = logging.getLogger(__name__)


class LangChainContentGenerator:
    """LangChain-based content generation and repurposing service."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model_name: str = "gpt-4"):
        """
        Initialize the LangChain content generator.
        
        Args:
            openai_api_key: OpenAI API key for content generation
            model_name: OpenAI model to use (default: gpt-4)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required but not available. Install with: pip install langchain langchain-openai")
        
        self.model_name = model_name
        self.openai_api_key = openai_api_key
        
        # Initialize LangChain components
        self._initialize_langchain()
    
    def _initialize_langchain(self):
        """Initialize LangChain components."""
        try:
            # Initialize OpenAI Chat model
            self.llm = ChatOpenAI(
                temperature=0.7,
                model=self.model_name,
                openai_api_key=self.openai_api_key
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            
            logger.info(f"LangChain initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
            raise
    
    async def repurpose_blog_to_tweets(
        self, 
        blog_content: str, 
        brand_voice: str = "Professional and engaging",
        num_tweets: int = 3
    ) -> Dict[str, Any]:
        """
        Convert blog content to tweets using LangChain's Stuff → Summarize pipeline.
        
        This implements the example from the task requirements.
        
        Args:
            blog_content: Original blog content to convert
            brand_voice: Brand voice guidelines
            num_tweets: Number of tweets to generate
            
        Returns:
            Dictionary containing generated tweets and metadata
        """
        try:
            # Split text into chunks
            docs = [Document(page_content=t) for t in self.text_splitter.split_text(blog_content)]
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["text", "brand_voice", "num_tweets"],
                template=f"""Convert the following blog section into {{num_tweets}} engaging tweets.
                Use the brand voice: {{brand_voice}}
                Include relevant hashtags and emojis.
                Make each tweet engaging and shareable.
                
                Blog section: {{text}}
                
                Generate exactly {{num_tweets}} tweets, numbered 1, 2, 3, etc.
                Each tweet should be under 280 characters.
                Tweets:"""
            )
            
            # Create chain
            chain = load_summarize_chain(
                self.llm,
                chain_type="stuff",
                prompt=prompt_template
            )
            
            # Run chain
            result = await chain.arun({
                "input_documents": docs,
                "brand_voice": brand_voice,
                "num_tweets": num_tweets
            })
            
            # Parse tweets from result
            tweets = self._parse_tweets_from_result(result, num_tweets)
            
            # Validate each tweet
            validation_results = []
            for tweet in tweets:
                validation = validate_content_length(tweet, ContentType.SOCIAL_MEDIA_POST)
                validation_results.append(validation)
            
            return {
                "tweets": tweets,
                "raw_result": result,
                "brand_voice": brand_voice,
                "num_tweets": num_tweets,
                "validation": validation_results,
                "metadata": {
                    "model_used": self.model_name,
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(blog_content),
                    "method": "LangChain Stuff → Summarize pipeline"
                }
            }
            
        except Exception as e:
            logger.error(f"Blog to tweet conversion failed: {e}")
            raise
    
    async def generate_thread_from_content(
        self, 
        content: str, 
        target_platform: Platform,
        brand_voice: str = "Professional and engaging",
        num_posts: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a social media thread from long-form content.
        
        Args:
            content: Long-form content to convert to thread
            target_platform: Target social media platform
            brand_voice: Brand voice guidelines
            num_posts: Number of posts in the thread
            
        Returns:
            Dictionary containing generated thread posts and metadata
        """
        try:
            # Get platform requirements
            platform_req = get_platform_requirements(target_platform)
            if not platform_req:
                raise ValueError(f"Unknown platform: {target_platform}")
            
            # Split content into chunks
            docs = [Document(page_content=t) for t in self.text_splitter.split_text(content)]
            
            # Create thread generation prompt
            prompt_template = PromptTemplate(
                input_variables=["text", "brand_voice", "num_posts", "platform"],
                template=f"""Convert the following content into a {{num_posts}}-post social media thread for {{platform}}.
                Use the brand voice: {{brand_voice}}
                
                Content: {{text}}
                
                Requirements:
                - Generate exactly {{num_posts}} posts
                - Each post should be optimized for {{platform}}
                - Posts should flow logically from one to the next
                - Include relevant hashtags and emojis
                - Make each post engaging and shareable
                - Number posts as 1, 2, 3, etc.
                
                Thread:"""
            )
            
            # Create chain
            chain = load_summarize_chain(
                self.llm,
                chain_type="stuff",
                prompt=prompt_template
            )
            
            # Run chain
            result = await chain.arun({
                "input_documents": docs,
                "brand_voice": brand_voice,
                "num_posts": num_posts,
                "platform": target_platform.value
            })
            
            # Parse thread posts
            thread_posts = self._parse_thread_posts(result, num_posts, target_platform)
            
            return {
                "thread_posts": thread_posts,
                "raw_result": result,
                "target_platform": target_platform,
                "brand_voice": brand_voice,
                "num_posts": num_posts,
                "metadata": {
                    "model_used": self.model_name,
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(content),
                    "method": "LangChain thread generation"
                }
            }
            
        except Exception as e:
            logger.error(f"Thread generation failed: {e}")
            raise
    
    async def generate_carousel_content(
        self, 
        content: str, 
        num_slides: int = 5,
        brand_voice: str = "Professional and engaging"
    ) -> Dict[str, Any]:
        """
        Generate carousel/slide deck content from long-form content.
        
        Args:
            content: Content to convert to carousel format
            num_slides: Number of slides to generate
            brand_voice: Brand voice guidelines
            
        Returns:
            Dictionary containing carousel slides and metadata
        """
        try:
            # Split content into chunks
            docs = [Document(page_content=t) for t in self.text_splitter.split_text(content)]
            
            # Create carousel generation prompt
            prompt_template = PromptTemplate(
                input_variables=["text", "brand_voice", "num_slides"],
                template=f"""Convert the following content into {{num_slides}} carousel slides.
                Use the brand voice: {{brand_voice}}
                
                Content: {{text}}
                
                Requirements:
                - Generate exactly {{num_slides}} slides
                - Each slide should have a clear title and key points
                - Include visual suggestions (icons, colors, layout)
                - Make each slide engaging and informative
                - Number slides as Slide 1, Slide 2, etc.
                
                Carousel Slides:"""
            )
            
            # Create chain
            chain = load_summarize_chain(
                self.llm,
                chain_type="stuff",
                prompt=prompt_template
            )
            
            # Run chain
            result = await chain.arun({
                "input_documents": docs,
                "brand_voice": brand_voice,
                "num_slides": num_slides
            })
            
            # Parse carousel slides
            slides = self._parse_carousel_slides(result, num_slides)
            
            return {
                "slides": slides,
                "raw_result": result,
                "num_slides": num_slides,
                "brand_voice": brand_voice,
                "metadata": {
                    "model_used": self.model_name,
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(content),
                    "method": "LangChain carousel generation"
                }
            }
            
        except Exception as e:
            logger.error(f"Carousel generation failed: {e}")
            raise
    
    async def generate_video_script(
        self, 
        content: str, 
        video_length: str = "short-form",
        brand_voice: str = "Professional and engaging"
    ) -> Dict[str, Any]:
        """
        Generate video script from content.
        
        Args:
            content: Content to convert to video script
            video_length: Target video length (short-form, medium, long-form)
            brand_voice: Brand voice guidelines
            
        Returns:
            Dictionary containing video script and metadata
        """
        try:
            # Split content into chunks
            docs = [Document(page_content=t) for t in self.text_splitter.split_text(content)]
            
            # Create video script generation prompt
            prompt_template = PromptTemplate(
                input_variables=["text", "brand_voice", "video_length"],
                template=f"""Convert the following content into a {{video_length}} video script.
                Use the brand voice: {{brand_voice}}
                
                Content: {{text}}
                
                Requirements:
                - Structure as a video script with timing markers
                - Include visual cues and suggestions
                - Add engaging hooks and transitions
                - Include call-to-action
                - Optimize for {{video_length}} video format
                
                Video Script:"""
            )
            
            # Create chain
            chain = load_summarize_chain(
                self.llm,
                chain_type="stuff",
                prompt=prompt_template
            )
            
            # Run chain
            result = await chain.arun({
                "input_documents": docs,
                "brand_voice": brand_voice,
                "video_length": video_length
            })
            
            # Parse video script
            script = self._parse_video_script(result)
            
            return {
                "script": script,
                "raw_result": result,
                "video_length": video_length,
                "brand_voice": brand_voice,
                "metadata": {
                    "model_used": self.model_name,
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_content_length": len(content),
                    "method": "LangChain video script generation"
                }
            }
            
        except Exception as e:
            logger.error(f"Video script generation failed: {e}")
            raise
    
    def _parse_tweets_from_result(self, result: str, num_tweets: int) -> List[str]:
        """Parse individual tweets from the LangChain result."""
        lines = result.strip().split('\n')
        tweets = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) and len(tweets) < num_tweets:
                # Remove the number prefix and clean up
                tweet_content = line.split('.', 1)[1].strip()
                if tweet_content:
                    tweets.append(tweet_content)
        
        # If we didn't get enough tweets, split the result differently
        if len(tweets) < num_tweets:
            # Fallback: split by double newlines or other separators
            parts = result.split('\n\n')
            for part in parts:
                if len(tweets) >= num_tweets:
                    break
                part = part.strip()
                if part and not part.startswith('Tweets:'):
                    tweets.append(part)
        
        # Ensure we have the right number of tweets
        while len(tweets) < num_tweets:
            tweets.append(f"Additional tweet {len(tweets) + 1}")
        
        return tweets[:num_tweets]
    
    def _parse_thread_posts(self, result: str, num_posts: int, platform: Platform) -> List[Dict[str, Any]]:
        """Parse thread posts from the LangChain result."""
        lines = result.strip().split('\n')
        posts = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) and len(posts) < num_posts:
                # Remove the number prefix and clean up
                post_content = line.split('.', 1)[1].strip()
                if post_content:
                    posts.append({
                        "content": post_content,
                        "platform": platform,
                        "order": len(posts) + 1
                    })
        
        # Ensure we have the right number of posts
        while len(posts) < num_posts:
            posts.append({
                "content": f"Additional post {len(posts) + 1}",
                "platform": platform,
                "order": len(posts) + 1
            })
        
        return posts[:num_posts]
    
    def _parse_carousel_slides(self, result: str, num_slides: int) -> List[Dict[str, Any]]:
        """Parse carousel slides from the LangChain result."""
        lines = result.strip().split('\n')
        slides = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('Slide 1', 'Slide 2', 'Slide 3', 'Slide 4', 'Slide 5')) and len(slides) < num_slides:
                # Extract slide number and content
                if ':' in line:
                    slide_num, content = line.split(':', 1)
                    slide_num = slide_num.replace('Slide ', '').strip()
                    slides.append({
                        "slide_number": int(slide_num),
                        "content": content.strip(),
                        "title": f"Slide {slide_num}"
                    })
        
        # Ensure we have the right number of slides
        while len(slides) < num_slides:
            slides.append({
                "slide_number": len(slides) + 1,
                "content": f"Content for slide {len(slides) + 1}",
                "title": f"Slide {len(slides) + 1}"
            })
        
        return slides[:num_slides]
    
    def _parse_video_script(self, result: str) -> Dict[str, Any]:
        """Parse video script from the LangChain result."""
        lines = result.strip().split('\n')
        script_sections = {
            "hook": "",
            "introduction": "",
            "main_content": "",
            "conclusion": "",
            "call_to_action": "",
            "visual_cues": [],
            "timing_markers": []
        }
        
        current_section = "main_content"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if "hook" in line.lower() or "attention" in line.lower():
                current_section = "hook"
            elif "intro" in line.lower() or "begin" in line.lower():
                current_section = "introduction"
            elif "conclusion" in line.lower() or "wrap" in line.lower():
                current_section = "conclusion"
            elif "call" in line.lower() or "action" in line.lower():
                current_section = "call_to_action"
            elif "visual" in line.lower() or "cue" in line.lower():
                script_sections["visual_cues"].append(line)
                continue
            elif any(marker in line.lower() for marker in ["0:", "5:", "10:", "15:", "20:", "30:"]):
                script_sections["timing_markers"].append(line)
                continue
            
            # Add content to current section
            if script_sections[current_section]:
                script_sections[current_section] += "\n" + line
            else:
                script_sections[current_section] = line
        
        return script_sections
    
    async def health_check(self) -> bool:
        """Check if the LangChain service is healthy."""
        try:
            # Test with a simple prompt
            test_docs = [Document(page_content="Test content")]
            test_chain = load_summarize_chain(
                self.llm,
                chain_type="stuff",
                prompt=PromptTemplate(
                    input_variables=["text"],
                    template="Summarize: {text}"
                )
            )
            
            result = await test_chain.arun({"input_documents": test_docs})
            return bool(result and len(result.strip()) > 0)
            
        except Exception as e:
            logger.error(f"LangChain health check failed: {e}")
            return False


# Factory function to create LangChain content generator
def create_langchain_generator(
    openai_api_key: Optional[str] = None, 
    model_name: str = "gpt-4"
) -> LangChainContentGenerator:
    """
    Create a LangChain content generator instance.
    
    Args:
        openai_api_key: OpenAI API key
        model_name: OpenAI model to use
        
    Returns:
        LangChainContentGenerator instance
    """
    return LangChainContentGenerator(openai_api_key, model_name)
