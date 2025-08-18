"""
Tests for LangChain content generation module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.langchain_content_generation import (
    LangChainContentGenerator, 
    create_langchain_generator,
    LANGCHAIN_AVAILABLE
)
from app.services.content_types import ContentType, Platform


class TestLangChainContentGenerator:
    """Test LangChain content generation functionality"""
    
    @pytest.fixture
    def mock_langchain_components(self):
        """Mock LangChain components for testing"""
        with patch('app.services.langchain_content_generation.LANGCHAIN_AVAILABLE', True):
            with patch('app.services.langchain_content_generation.ChatOpenAI') as mock_chat:
                with patch('app.services.langchain_content_generation.RecursiveCharacterTextSplitter') as mock_splitter:
                    with patch('app.services.langchain_content_generation.load_summarize_chain') as mock_chain:
                        with patch('app.services.langchain_content_generation.PromptTemplate') as mock_prompt:
                            with patch('app.services.langchain_content_generation.Document') as mock_doc:
                                
                                # Mock ChatOpenAI
                                mock_chat_instance = Mock()
                                mock_chat.return_value = mock_chat_instance
                                
                                # Mock text splitter
                                mock_splitter_instance = Mock()
                                mock_splitter_instance.split_text.return_value = ["chunk1", "chunk2"]
                                mock_splitter.return_value = mock_splitter_instance
                                
                                # Mock chain
                                mock_chain_instance = AsyncMock()
                                mock_chain_instance.arun.return_value = "Mock generated content"
                                mock_chain.return_value = mock_chain_instance
                                
                                # Mock prompt template
                                mock_prompt_instance = Mock()
                                mock_prompt.return_value = mock_prompt_instance
                                
                                # Mock document
                                mock_doc_instance = Mock()
                                mock_doc_instance.page_content = "test content"
                                mock_doc.return_value = mock_doc_instance
                                
                                yield {
                                    'chat': mock_chat,
                                    'splitter': mock_splitter,
                                    'chain': mock_chain,
                                    'prompt': mock_prompt,
                                    'document': mock_doc,
                                    'chat_instance': mock_chat_instance,
                                    'splitter_instance': mock_splitter_instance,
                                    'chain_instance': mock_chain_instance,
                                    'prompt_instance': mock_prompt_instance,
                                    'doc_instance': mock_doc_instance
                                }
    
    @pytest.fixture
    def generator(self, mock_langchain_components):
        """Create a generator instance with mocked dependencies"""
        return LangChainContentGenerator(openai_api_key="test_key", model_name="gpt-4")
    
    def test_initialization(self, mock_langchain_components):
        """Test generator initialization"""
        generator = LangChainContentGenerator(openai_api_key="test_key", model_name="gpt-4")
        
        assert generator.model_name == "gpt-4"
        assert generator.openai_api_key == "test_key"
        assert generator.llm is not None
        assert generator.text_splitter is not None
    
    def test_initialization_langchain_not_available(self):
        """Test initialization when LangChain is not available"""
        with patch('app.services.langchain_content_generation.LANGCHAIN_AVAILABLE', False):
            with pytest.raises(ImportError, match="LangChain is required"):
                LangChainContentGenerator()
    
    @pytest.mark.asyncio
    async def test_repurpose_blog_to_tweets_success(self, generator, mock_langchain_components):
        """Test successful blog to tweet conversion"""
        # Mock the chain response
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.return_value = "1. First tweet content\n2. Second tweet content\n3. Third tweet content"
        
        # Test conversion
        result = await generator.repurpose_blog_to_tweets(
            "This is a test blog post about AI and machine learning.",
            "Professional and engaging",
            3
        )
        
        # Verify result structure
        assert "tweets" in result
        assert "raw_result" in result
        assert "brand_voice" in result
        assert "num_tweets" in result
        assert "validation" in result
        assert "metadata" in result
        
        # Verify tweets were parsed
        tweets = result["tweets"]
        assert len(tweets) == 3
        assert "First tweet content" in tweets[0]
        assert "Second tweet content" in tweets[1]
        assert "Third tweet content" in tweets[2]
        
        # Verify validation results
        assert len(result["validation"]) == 3
        assert all("valid" in validation for validation in result["validation"])
    
    @pytest.mark.asyncio
    async def test_generate_thread_from_content_success(self, generator, mock_langchain_components):
        """Test successful thread generation"""
        # Mock the chain response
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.return_value = "1. First thread post\n2. Second thread post\n3. Third thread post"
        
        # Test thread generation
        result = await generator.generate_thread_from_content(
            "This is long-form content for thread generation.",
            Platform.TWITTER,
            "Professional and engaging",
            3
        )
        
        # Verify result structure
        assert "thread_posts" in result
        assert "raw_result" in result
        assert "target_platform" in result
        assert "brand_voice" in result
        assert "num_posts" in result
        assert "metadata" in result
        
        # Verify thread posts were parsed
        posts = result["thread_posts"]
        assert len(posts) == 3
        assert all("content" in post for post in posts)
        assert all("platform" in post for post in posts)
        assert all("order" in post for post in posts)
    
    @pytest.mark.asyncio
    async def test_generate_carousel_content_success(self, generator, mock_langchain_components):
        """Test successful carousel generation"""
        # Mock the chain response
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.return_value = "Slide 1: First slide content\nSlide 2: Second slide content\nSlide 3: Third slide content"
        
        # Test carousel generation
        result = await generator.generate_carousel_content(
            "This is content for carousel generation.",
            3,
            "Professional and engaging"
        )
        
        # Verify result structure
        assert "slides" in result
        assert "raw_result" in result
        assert "num_slides" in result
        assert "brand_voice" in result
        assert "metadata" in result
        
        # Verify slides were parsed
        slides = result["slides"]
        assert len(slides) == 3
        assert all("slide_number" in slide for slide in slides)
        assert all("content" in slide for slide in slides)
        assert all("title" in slide for slide in slides)
    
    @pytest.mark.asyncio
    async def test_generate_video_script_success(self, generator, mock_langchain_components):
        """Test successful video script generation"""
        # Mock the chain response
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.return_value = "Hook: Attention grabber\nIntroduction: Welcome\nMain content: Key points\nConclusion: Summary"
        
        # Test video script generation
        result = await generator.generate_video_script(
            "This is content for video script generation.",
            "short-form",
            "Professional and engaging"
        )
        
        # Verify result structure
        assert "script" in result
        assert "raw_result" in result
        assert "video_length" in result
        assert "brand_voice" in result
        assert "metadata" in result
        
        # Verify script sections were parsed
        script = result["script"]
        assert "hook" in script
        assert "introduction" in script
        assert "main_content" in script
        assert "conclusion" in script
        assert "call_to_action" in script
        assert "visual_cues" in script
        assert "timing_markers" in script
    
    def test_parse_tweets_from_result(self, generator):
        """Test tweet parsing from LangChain result"""
        result = "1. First tweet here\n2. Second tweet here\n3. Third tweet here"
        tweets = generator._parse_tweets_from_result(result, 3)
        
        assert len(tweets) == 3
        assert "First tweet here" in tweets[0]
        assert "Second tweet here" in tweets[1]
        assert "Third tweet here" in tweets[2]
    
    def test_parse_tweets_fallback(self, generator):
        """Test tweet parsing fallback when numbered format fails"""
        result = "Tweet one content\n\nTweet two content\n\nTweet three content"
        tweets = generator._parse_tweets_from_result(result, 3)
        
        assert len(tweets) == 3
        assert "Tweet one content" in tweets[0]
        assert "Tweet two content" in tweets[1]
        assert "Tweet three content" in tweets[2]
    
    def test_parse_thread_posts(self, generator):
        """Test thread post parsing"""
        result = "1. First post\n2. Second post\n3. Third post"
        posts = generator._parse_thread_posts(result, 3, Platform.TWITTER)
        
        assert len(posts) == 3
        assert all(post["platform"] == Platform.TWITTER for post in posts)
        assert all("order" in post for post in posts)
        assert posts[0]["order"] == 1
        assert posts[1]["order"] == 2
        assert posts[2]["order"] == 3
    
    def test_parse_carousel_slides(self, generator):
        """Test carousel slide parsing"""
        result = "Slide 1: First slide\nSlide 2: Second slide\nSlide 3: Third slide"
        slides = generator._parse_carousel_slides(result, 3)
        
        assert len(slides) == 3
        assert all("slide_number" in slide for slide in slides)
        assert all("content" in slide for slide in slides)
        assert all("title" in slide for slide in slides)
        assert slides[0]["slide_number"] == 1
        assert slides[1]["slide_number"] == 2
        assert slides[2]["slide_number"] == 3
    
    def test_parse_video_script(self, generator):
        """Test video script parsing"""
        result = "Hook: Attention\nIntroduction: Welcome\nMain: Content\nConclusion: End"
        script = generator._parse_video_script(result)
        
        assert "hook" in script
        assert "introduction" in script
        assert "main_content" in script
        assert "conclusion" in script
        assert "call_to_action" in script
        assert "visual_cues" in script
        assert "timing_markers" in script
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, generator, mock_langchain_components):
        """Test successful health check"""
        # Mock successful health check
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.return_value = "Test summary"
        
        result = await generator.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, generator, mock_langchain_components):
        """Test failed health check"""
        # Mock failed health check
        mock_chain = mock_langchain_components['chain_instance']
        mock_chain.arun.side_effect = Exception("Health check failed")
        
        result = await generator.health_check()
        assert result is False


class TestFactoryFunction:
    """Test the factory function for creating generators"""
    
    def test_create_langchain_generator(self):
        """Test factory function creates generator correctly"""
        with patch('app.services.langchain_content_generation.LANGCHAIN_AVAILABLE', True):
            with patch('app.services.langchain_content_generation.LangChainContentGenerator') as mock_generator_class:
                mock_generator = Mock()
                mock_generator_class.return_value = mock_generator
                
                result = create_langchain_generator("test_key", "gpt-4")
                
                assert result == mock_generator
                mock_generator_class.assert_called_once_with("test_key", "gpt-4")


class TestLangChainAvailability:
    """Test behavior when LangChain is not available"""
    
    def test_langchain_not_available(self):
        """Test behavior when LangChain is not available"""
        with patch('app.services.langchain_content_generation.LANGCHAIN_AVAILABLE', False):
            with pytest.raises(ImportError, match="LangChain is required"):
                LangChainContentGenerator()


if __name__ == "__main__":
    pytest.main([__file__])
