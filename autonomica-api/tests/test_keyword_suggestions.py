"""
Tests for Keyword Suggestion Service Module
Tests the intelligent keyword suggestion functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.services.keyword_suggestion import (
    KeywordSuggestionService,
    create_keyword_suggestion_service,
    SuggestionRequest,
    SuggestionResponse,
    KeywordSuggestion,
    SuggestionType,
    SuggestionSource
)
from app.services.keyword_analysis import KeywordIntent, KeywordType


class TestSuggestionType:
    """Test SuggestionType enum"""
    
    def test_suggestion_type_values(self):
        """Test that all suggestion types have valid values"""
        assert SuggestionType.RELATED.value == "related"
        assert SuggestionType.LONG_TAIL.value == "long_tail"
        assert SuggestionType.QUESTION_BASED.value == "question_based"
        assert SuggestionType.COMPETITOR.value == "competitor"
        assert SuggestionType.TRENDING.value == "trending"
        assert SuggestionType.SEASONAL.value == "seasonal"
        assert SuggestionType.INTENT_BASED.value == "intent_based"
        assert SuggestionType.DIFFICULTY_BASED.value == "difficulty_based"


class TestSuggestionSource:
    """Test SuggestionSource enum"""
    
    def test_suggestion_source_values(self):
        """Test that all suggestion sources have valid values"""
        assert SuggestionSource.CLUSTERING.value == "clustering"
        assert SuggestionSource.SEMRUSH_API.value == "semrush_api"
        assert SuggestionSource.COMPETITOR_ANALYSIS.value == "competitor_analysis"
        assert SuggestionSource.TREND_ANALYSIS.value == "trend_analysis"
        assert SuggestionSource.USER_HISTORY.value == "user_history"
        assert SuggestionSource.AI_GENERATED.value == "ai_generated"


class TestKeywordSuggestion:
    """Test KeywordSuggestion dataclass"""
    
    def test_keyword_suggestion_creation(self):
        """Test creating a KeywordSuggestion instance"""
        suggestion = KeywordSuggestion(
            keyword="test keyword",
            suggestion_type=SuggestionType.RELATED,
            source=SuggestionSource.CLUSTERING,
            relevance_score=0.8
        )
        
        assert suggestion.keyword == "test keyword"
        assert suggestion.suggestion_type == SuggestionType.RELATED
        assert suggestion.source == SuggestionSource.CLUSTERING
        assert suggestion.relevance_score == 0.8
        assert suggestion.related_keywords == []
        assert suggestion.metadata == {}
    
    def test_keyword_suggestion_with_optional_fields(self):
        """Test creating a KeywordSuggestion with optional fields"""
        suggestion = KeywordSuggestion(
            keyword="test keyword",
            suggestion_type=SuggestionType.LONG_TAIL,
            source=SuggestionSource.AI_GENERATED,
            relevance_score=0.9,
            difficulty_score=0.6,
            search_volume=1000,
            cpc=1.5,
            competition="low",
            intent=KeywordIntent.INFORMATIONAL,
            keyword_type=KeywordType.PRIMARY,
            explanation="Test explanation",
            metadata={"test": "data"}
        )
        
        assert suggestion.difficulty_score == 0.6
        assert suggestion.search_volume == 1000
        assert suggestion.cpc == 1.5
        assert suggestion.competition == "low"
        assert suggestion.intent == KeywordIntent.INFORMATIONAL
        assert suggestion.keyword_type == KeywordType.PRIMARY
        assert suggestion.explanation == "Test explanation"
        assert suggestion.metadata == {"test": "data"}


class TestSuggestionRequest:
    """Test SuggestionRequest dataclass"""
    
    def test_suggestion_request_creation(self):
        """Test creating a SuggestionRequest instance"""
        request = SuggestionRequest(
            seed_keywords=["test", "keyword"],
            target_language="en",
            max_suggestions=100
        )
        
        assert request.seed_keywords == ["test", "keyword"]
        assert request.target_language == "en"
        assert request.max_suggestions == 100
        assert request.suggestion_types == [SuggestionType.RELATED, SuggestionType.LONG_TAIL]
        assert request.exclude_keywords == []
        assert request.competitor_domains == []
    
    def test_suggestion_request_with_custom_types(self):
        """Test creating a SuggestionRequest with custom suggestion types"""
        request = SuggestionRequest(
            seed_keywords=["test"],
            suggestion_types=[SuggestionType.TRENDING, SuggestionType.COMPETITOR]
        )
        
        assert request.suggestion_types == [SuggestionType.TRENDING, SuggestionType.COMPETITOR]


class TestSuggestionResponse:
    """Test SuggestionResponse dataclass"""
    
    def test_suggestion_response_creation(self):
        """Test creating a SuggestionResponse instance"""
        suggestions = [
            KeywordSuggestion(
                keyword="test1",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.8
            ),
            KeywordSuggestion(
                keyword="test2",
                suggestion_type=SuggestionType.LONG_TAIL,
                source=SuggestionSource.AI_GENERATED,
                relevance_score=0.7
            )
        ]
        
        response = SuggestionResponse(
            request_id="test_id",
            seed_keywords=["test"],
            suggestions=suggestions,
            total_suggestions=2,
            suggestion_breakdown={SuggestionType.RELATED: 1, SuggestionType.LONG_TAIL: 1},
            processing_time=1.5
        )
        
        assert response.request_id == "test_id"
        assert response.total_suggestions == 2
        assert response.processing_time == 1.5
        assert response.generated_at is not None


class TestKeywordSuggestionService:
    """Test the main KeywordSuggestionService class"""
    
    @pytest.fixture
    async def mock_service(self):
        """Create a mock service with mocked dependencies"""
        service = KeywordSuggestionService()
        
        # Mock the dependent services
        service.keyword_clusterer = Mock()
        service.keyword_analyzer = Mock()
        service.seo_service = Mock()
        
        # Mock initialization methods
        service.keyword_clusterer.initialize = AsyncMock()
        service.keyword_analyzer.initialize = AsyncMock()
        service.seo_service.initialize = AsyncMock()
        
        return service
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_service):
        """Test service initialization"""
        await mock_service.initialize()
        
        mock_service.keyword_clusterer.initialize.assert_called_once()
        mock_service.keyword_analyzer.initialize.assert_called_once()
        mock_service.seo_service.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_basic(self, mock_service):
        """Test basic suggestion generation"""
        # Mock the suggestion generation methods
        mock_service._generate_related_suggestions = AsyncMock(return_value=[])
        mock_service._generate_long_tail_suggestions = AsyncMock(return_value=[])
        mock_service._filter_suggestions = Mock(return_value=[])
        mock_service._rank_suggestions = Mock(return_value=[])
        mock_service._generate_request_id = Mock(return_value="test_id")
        mock_service._get_suggestion_breakdown = Mock(return_value={})
        mock_service._generate_metadata = Mock(return_value={})
        mock_service._cache_suggestions = Mock()
        
        request = SuggestionRequest(
            seed_keywords=["test"],
            suggestion_types=[SuggestionType.RELATED, SuggestionType.LONG_TAIL]
        )
        
        response = await mock_service.generate_suggestions(request)
        
        assert response.request_id == "test_id"
        assert response.seed_keywords == ["test"]
        assert response.total_suggestions == 0
        assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_with_cache(self, mock_service):
        """Test suggestion generation with cache hit"""
        # Mock cache hit
        cached_response = SuggestionResponse(
            request_id="cached_id",
            seed_keywords=["test"],
            suggestions=[],
            total_suggestions=0,
            suggestion_breakdown={},
            processing_time=0.1
        )
        
        mock_service._generate_request_id = Mock(return_value="cached_id")
        mock_service._get_cached_suggestions = Mock(return_value=cached_response)
        
        request = SuggestionRequest(seed_keywords=["test"])
        response = await mock_service.generate_suggestions(request)
        
        assert response.request_id == "cached_id"
        # Should not call other generation methods when cache hit
    
    @pytest.mark.asyncio
    async def test_generate_related_suggestions(self, mock_service):
        """Test related suggestions generation"""
        mock_opportunities = [
            {"keyword": "related1", "similarity_score": 0.8},
            {"keyword": "related2", "similarity_score": 0.7}
        ]
        
        mock_service.keyword_clusterer.find_keyword_opportunities = AsyncMock(
            return_value=mock_opportunities
        )
        
        request = SuggestionRequest(
            seed_keywords=["test"],
            exclude_keywords=["excluded"]
        )
        
        suggestions = await mock_service._generate_related_suggestions(request)
        
        assert len(suggestions) == 2
        assert suggestions[0].keyword == "related1"
        assert suggestions[0].suggestion_type == SuggestionType.RELATED
        assert suggestions[0].source == SuggestionSource.CLUSTERING
    
    @pytest.mark.asyncio
    async def test_generate_long_tail_suggestions(self, mock_service):
        """Test long-tail suggestions generation"""
        request = SuggestionRequest(
            seed_keywords=["test"],
            exclude_keywords=["excluded"]
        )
        
        suggestions = await mock_service._generate_long_tail_suggestions(request)
        
        # Should generate multiple long-tail variations
        assert len(suggestions) > 0
        assert all(s.suggestion_type == SuggestionType.LONG_TAIL for s in suggestions)
        assert all(s.source == SuggestionSource.AI_GENERATED for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_generate_question_suggestions(self, mock_service):
        """Test question-based suggestions generation"""
        request = SuggestionRequest(
            seed_keywords=["test"],
            exclude_keywords=["excluded"]
        )
        
        suggestions = await mock_service._generate_question_suggestions(request)
        
        # Should generate question-based variations
        assert len(suggestions) > 0
        assert all(s.suggestion_type == SuggestionType.QUESTION_BASED for s in suggestions)
        assert all(s.source == SuggestionSource.AI_GENERATED for s in suggestions)
        
        # Check that questions start with question words
        question_starters = ["what", "how", "why", "when", "where", "which", "who"]
        for suggestion in suggestions:
            assert any(suggestion.keyword.startswith(starter) for starter in question_starters)
    
    def test_generate_long_tail_variations(self, mock_service):
        """Test long-tail keyword variations generation"""
        variations = mock_service._generate_long_tail_variations("test")
        
        assert len(variations) > 0
        assert "best test" in variations
        assert "test guide" in variations
        assert "test near me" in variations
    
    def test_filter_suggestions(self, mock_service):
        """Test suggestion filtering"""
        suggestions = [
            KeywordSuggestion(
                keyword="high_score",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.9
            ),
            KeywordSuggestion(
                keyword="low_score",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.2
            ),
            KeywordSuggestion(
                keyword="excluded",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.8
            )
        ]
        
        request = SuggestionRequest(
            seed_keywords=["test"],
            exclude_keywords=["excluded"],
            min_relevance_score=0.5
        )
        
        filtered = mock_service._filter_suggestions(suggestions, request)
        
        assert len(filtered) == 1
        assert filtered[0].keyword == "high_score"
    
    def test_rank_suggestions(self, mock_service):
        """Test suggestion ranking"""
        suggestions = [
            KeywordSuggestion(
                keyword="low_relevance",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.5
            ),
            KeywordSuggestion(
                keyword="high_relevance",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.9
            ),
            KeywordSuggestion(
                keyword="medium_relevance",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.7
            )
        ]
        
        request = SuggestionRequest(seed_keywords=["test"])
        
        ranked = mock_service._rank_suggestions(suggestions, request)
        
        assert ranked[0].keyword == "high_relevance"
        assert ranked[1].keyword == "medium_relevance"
        assert ranked[2].keyword == "low_relevance"
    
    def test_get_suggestion_breakdown(self, mock_service):
        """Test suggestion breakdown generation"""
        suggestions = [
            KeywordSuggestion(
                keyword="related1",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.8
            ),
            KeywordSuggestion(
                keyword="related2",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.7
            ),
            KeywordSuggestion(
                keyword="long_tail1",
                suggestion_type=SuggestionType.LONG_TAIL,
                source=SuggestionSource.AI_GENERATED,
                relevance_score=0.6
            )
        ]
        
        breakdown = mock_service._get_suggestion_breakdown(suggestions)
        
        assert breakdown[SuggestionType.RELATED] == 2
        assert breakdown[SuggestionType.LONG_TAIL] == 1
    
    def test_generate_metadata(self, mock_service):
        """Test metadata generation"""
        suggestions = [
            KeywordSuggestion(
                keyword="test1",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.8
            ),
            KeywordSuggestion(
                keyword="test2",
                suggestion_type=SuggestionType.RELATED,
                source=SuggestionSource.CLUSTERING,
                relevance_score=0.6
            )
        ]
        
        request = SuggestionRequest(
            seed_keywords=["test"],
            target_language="en",
            exclude_keywords=["excluded"],
            competitor_domains=["competitor.com"]
        )
        
        metadata = mock_service._generate_metadata(request, suggestions)
        
        assert metadata["target_language"] == "en"
        assert metadata["average_relevance_score"] == 0.7
        assert "clustering" in metadata["sources_used"]
        assert metadata["filtering_applied"]["excluded_keywords_count"] == 1
        assert metadata["filtering_applied"]["competitor_domains_count"] == 1
    
    def test_generate_request_id(self, mock_service):
        """Test request ID generation"""
        request = SuggestionRequest(
            seed_keywords=["test", "keyword"],
            suggestion_types=[SuggestionType.RELATED],
            max_suggestions=50,
            min_relevance_score=0.3,
            target_language="en"
        )
        
        request_id = mock_service._generate_request_id(request)
        
        assert len(request_id) == 32  # MD5 hash length
        assert isinstance(request_id, str)
    
    def test_cache_operations(self, mock_service):
        """Test cache operations"""
        # Test caching
        mock_service._cache_suggestions("test_id", "test_response")
        assert "test_id" in mock_service.suggestion_cache
        
        # Test cache retrieval
        cached = mock_service._get_cached_suggestions("test_id")
        assert cached == "test_response"
        
        # Test cache expiration
        mock_service.suggestion_cache["test_id"]["timestamp"] = datetime.now() - timedelta(hours=2)
        cached = mock_service._get_cached_suggestions("test_id")
        assert cached is None
        assert "test_id" not in mock_service.suggestion_cache
    
    @pytest.mark.asyncio
    async def test_get_suggestion_statistics(self, mock_service):
        """Test statistics retrieval"""
        stats = await mock_service.get_suggestion_statistics()
        
        assert "cache_size" in stats
        assert "suggestion_types_generated" in stats
        assert "sources_available" in stats
        assert isinstance(stats["cache_size"], int)
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_service):
        """Test cache clearing"""
        # Add some test data to cache
        mock_service.suggestion_cache["test1"] = {"response": "data1", "timestamp": datetime.now()}
        mock_service.suggestion_cache["test2"] = {"response": "data2", "timestamp": datetime.now()}
        
        assert len(mock_service.suggestion_cache) == 2
        
        await mock_service.clear_cache()
        
        assert len(mock_service.suggestion_cache) == 0


class TestFactoryFunction:
    """Test the factory function"""
    
    @pytest.mark.asyncio
    async def test_create_keyword_suggestion_service(self):
        """Test service creation via factory function"""
        with patch('app.services.keyword_suggestion.KeywordSuggestionService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.initialize = AsyncMock()
            
            service = await create_keyword_suggestion_service()
            
            mock_service_class.assert_called_once()
            mock_service.initialize.assert_called_once()
            assert service == mock_service


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
