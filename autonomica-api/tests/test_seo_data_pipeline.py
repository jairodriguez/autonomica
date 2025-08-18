"""
Tests for SEO Data Processing Pipeline Module
Tests the integration of all SEO components into a cohesive pipeline
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.services.seo_data_pipeline import (
    SEODataPipeline,
    create_seo_data_pipeline,
    KeywordResearchRequest,
    PipelineResult,
    PipelineStatus,
    PipelineStage
)
from app.services.seo_service import SEOService
from app.services.keyword_clustering import KeywordClusterer
from app.services.competitor_analysis import CompetitorAnalyzer
from app.services.keyword_analysis import KeywordAnalyzer


class TestKeywordResearchRequest:
    """Test cases for the KeywordResearchRequest dataclass"""
    
    def test_keyword_research_request_creation(self):
        """Test creating a keyword research request"""
        request = KeywordResearchRequest(
            primary_keywords=["python tutorial", "python guide"],
            competitor_domains=["example.com", "competitor.com"],
            target_database="us",
            analysis_depth="comprehensive"
        )
        
        assert request.primary_keywords == ["python tutorial", "python guide"]
        assert request.competitor_domains == ["example.com", "competitor.com"]
        assert request.target_database == "us"
        assert request.analysis_depth == "comprehensive"
        assert request.include_competitors is True
        assert request.include_clustering is True
        assert request.include_opportunity_analysis is True
    
    def test_keyword_research_request_defaults(self):
        """Test default values for keyword research request"""
        request = KeywordResearchRequest(
            primary_keywords=["test"],
            competitor_domains=["test.com"]
        )
        
        assert request.target_database == "us"
        assert request.analysis_depth == "comprehensive"
        assert request.max_keywords_per_analysis == 100
        assert request.max_competitors_per_domain == 20


class TestPipelineResult:
    """Test cases for the PipelineResult dataclass"""
    
    def test_pipeline_result_creation(self):
        """Test creating a pipeline result"""
        result = PipelineResult(
            pipeline_id="test_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now()
        )
        
        assert result.pipeline_id == "test_pipeline"
        assert result.status == PipelineStatus.COMPLETED
        assert result.stages_completed == []
        assert result.results == {}
        assert result.errors == []
        assert result.metadata == {}
    
    def test_pipeline_result_with_optional_fields(self):
        """Test pipeline result with optional fields"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        result = PipelineResult(
            pipeline_id="test_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            stages_completed=[PipelineStage.KEYWORD_RESEARCH],
            current_stage=PipelineStage.COMPLETED,
            results={"test": "data"},
            errors=["test error"],
            metadata={"test": "metadata"}
        )
        
        assert result.end_time == end_time
        assert PipelineStage.KEYWORD_RESEARCH in result.stages_completed
        assert result.current_stage == PipelineStage.COMPLETED
        assert result.results["test"] == "data"
        assert "test error" in result.errors
        assert result.metadata["test"] == "metadata"


class TestSEODataPipeline:
    """Test cases for the main SEO data processing pipeline"""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline instance"""
        with patch('app.services.seo_data_pipeline.validate_seo_config') as mock_config:
            mock_config.return_value = {"valid": True, "missing_keys": []}
            
            with patch('app.services.seo_data_pipeline.create_seo_service') as mock_service:
                mock_service.return_value = AsyncMock()
                
                pipeline = SEODataPipeline()
                return pipeline
    
    @pytest.fixture
    def mock_services(self, mock_pipeline):
        """Mock all service dependencies"""
        mock_pipeline.seo_service = AsyncMock()
        mock_pipeline.keyword_clusterer = Mock()
        mock_pipeline.competitor_analyzer = Mock()
        mock_pipeline.keyword_analyzer = Mock()
        
        return mock_pipeline
    
    def test_pipeline_initialization(self, mock_pipeline):
        """Test pipeline initialization"""
        assert mock_pipeline is not None
        assert mock_pipeline.max_concurrent_pipelines == 3
        assert mock_pipeline.pipeline_timeout == 300
        assert mock_pipeline.enable_caching is True
        assert mock_pipeline.cache_ttl == 3600
    
    @pytest.mark.asyncio
    async def test_pipeline_initialize_success(self, mock_pipeline):
        """Test successful pipeline initialization"""
        with patch('app.services.seo_data_pipeline.validate_seo_config') as mock_config:
            mock_config.return_value = {"valid": True, "missing_keys": []}
            
            with patch('app.services.seo_data_pipeline.create_seo_service') as mock_service:
                mock_service.return_value = AsyncMock()
                
                with patch('app.services.seo_data_pipeline.KeywordClusterer') as mock_clusterer:
                    mock_clusterer.return_value = Mock()
                    
                    with patch('app.services.seo_data_pipeline.CompetitorAnalyzer') as mock_analyzer:
                        mock_analyzer.return_value = Mock()
                        
                        with patch('app.services.seo_data_pipeline.KeywordAnalyzer') as mock_kw_analyzer:
                            mock_kw_analyzer.return_value = Mock()
                            
                            result = await mock_pipeline.initialize()
                            assert result is True
    
    @pytest.mark.asyncio
    async def test_pipeline_initialize_config_error(self, mock_pipeline):
        """Test pipeline initialization with config error"""
        with patch('app.services.seo_data_pipeline.validate_seo_config') as mock_config:
            mock_config.return_value = {"valid": False, "missing_keys": ["SEMRUSH_API_KEY"]}
            
            with pytest.raises(ValueError, match="Missing required API keys"):
                await mock_pipeline.initialize()
    
    def test_generate_pipeline_id(self, mock_pipeline):
        """Test pipeline ID generation"""
        request = KeywordResearchRequest(
            primary_keywords=["test"],
            competitor_domains=["test.com"]
        )
        
        pipeline_id = mock_pipeline._generate_pipeline_id(request)
        
        assert pipeline_id.startswith("seo_pipeline_")
        assert len(pipeline_id) > 20  # Should include timestamp and hash
    
    def test_is_cache_valid(self, mock_pipeline):
        """Test cache validation"""
        # Test with valid cache
        result = PipelineResult(
            pipeline_id="test",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=30)  # 30 minutes ago
        )
        
        assert mock_pipeline._is_cache_valid(result) is True
        
        # Test with expired cache
        result.end_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
        assert mock_pipeline._is_cache_valid(result) is False
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_success(self, mock_services):
        """Test successful pipeline execution"""
        request = KeywordResearchRequest(
            primary_keywords=["python tutorial"],
            competitor_domains=["example.com"]
        )
        
        # Mock the pipeline stages
        with patch.object(mock_services, '_execute_pipeline_stages') as mock_stages:
            mock_stages.return_value = None
            
            result = await mock_services.execute_pipeline(request)
            
            assert result.status == PipelineStatus.COMPLETED
            assert result.pipeline_id.startswith("seo_pipeline_")
            assert result.current_stage == PipelineStage.COMPLETED
            assert result.end_time is not None
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_already_running(self, mock_services):
        """Test pipeline execution when already running"""
        request = KeywordResearchRequest(
            primary_keywords=["python tutorial"],
            competitor_domains=["example.com"]
        )
        
        # Add to active pipelines
        mock_services.active_pipelines["test_pipeline"] = Mock()
        
        with pytest.raises(RuntimeError, match="is already running"):
            await mock_services.execute_pipeline(request)
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_cache_hit(self, mock_services):
        """Test pipeline execution with cache hit"""
        request = KeywordResearchRequest(
            primary_keywords=["python tutorial"],
            competitor_domains=["example.com"]
        )
        
        # Create cached result
        cached_result = PipelineResult(
            pipeline_id="cached_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now() - timedelta(minutes=25)
        )
        
        mock_services.pipeline_cache["cached_pipeline"] = cached_result
        
        # Mock the ID generation to return cached ID
        with patch.object(mock_services, '_generate_pipeline_id', return_value="cached_pipeline"):
            result = await mock_services.execute_pipeline(request)
            
            assert result.pipeline_id == "cached_pipeline"
            assert result.status == PipelineStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_pipeline_failure(self, mock_services):
        """Test pipeline execution failure"""
        request = KeywordResearchRequest(
            primary_keywords=["python tutorial"],
            competitor_domains=["example.com"]
        )
        
        # Mock the pipeline stages to raise an exception
        with patch.object(mock_services, '_execute_pipeline_stages', side_effect=Exception("Test error")):
            result = await mock_services.execute_pipeline(request)
            
            assert result.status == PipelineStatus.FAILED
            assert result.errors == ["Test error"]
            assert result.end_time is not None
    
    @pytest.mark.asyncio
    async def test_get_pipeline_status(self, mock_services):
        """Test getting pipeline status"""
        # Test with active pipeline
        active_result = PipelineResult(
            pipeline_id="active_pipeline",
            status=PipelineStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        mock_services.active_pipelines["active_pipeline"] = active_result
        
        result = await mock_services.get_pipeline_status("active_pipeline")
        assert result.pipeline_id == "active_pipeline"
        assert result.status == PipelineStatus.IN_PROGRESS
        
        # Test with cached pipeline
        cached_result = PipelineResult(
            pipeline_id="cached_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now() - timedelta(minutes=25)
        )
        mock_services.pipeline_cache["cached_pipeline"] = cached_result
        
        result = await mock_services.get_pipeline_status("cached_pipeline")
        assert result.pipeline_id == "cached_pipeline"
        assert result.status == PipelineStatus.COMPLETED
        
        # Test with non-existent pipeline
        result = await mock_services.get_pipeline_status("non_existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cancel_pipeline(self, mock_services):
        """Test pipeline cancellation"""
        # Test with active pipeline
        active_result = PipelineResult(
            pipeline_id="active_pipeline",
            status=PipelineStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        mock_services.active_pipelines["active_pipeline"] = active_result
        
        success = await mock_services.cancel_pipeline("active_pipeline")
        assert success is True
        assert active_result.status == PipelineStatus.CANCELLED
        assert "active_pipeline" not in mock_services.active_pipelines
        
        # Test with non-existent pipeline
        success = await mock_services.cancel_pipeline("non_existent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_cache(self, mock_services):
        """Test cache cleanup"""
        # Add expired cache entry
        expired_result = PipelineResult(
            pipeline_id="expired_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now() - timedelta(hours=2),
            end_time=datetime.now() - timedelta(hours=1, minutes=55)
        )
        mock_services.pipeline_cache["expired_pipeline"] = expired_result
        
        # Add valid cache entry
        valid_result = PipelineResult(
            pipeline_id="valid_pipeline",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now() - timedelta(minutes=25)
        )
        mock_services.pipeline_cache["valid_pipeline"] = valid_result
        
        await mock_services.cleanup_expired_cache()
        
        assert "expired_pipeline" not in mock_services.pipeline_cache
        assert "valid_pipeline" in mock_services.pipeline_cache
    
    def test_get_pipeline_statistics(self, mock_services):
        """Test pipeline statistics"""
        # Add some test data
        mock_services.active_pipelines["pipeline1"] = Mock()
        mock_services.active_pipelines["pipeline2"] = Mock()
        mock_services.pipeline_cache["cached1"] = Mock()
        
        stats = mock_services.get_pipeline_statistics()
        
        assert stats["active_pipelines"] == 2
        assert stats["cached_results"] == 1
        assert stats["total_pipelines_executed"] == 3


class TestPipelineStages:
    """Test cases for individual pipeline stages"""
    
    @pytest.fixture
    def mock_pipeline_with_services(self):
        """Create a pipeline with mocked services"""
        with patch('app.services.seo_data_pipeline.validate_seo_config') as mock_config:
            mock_config.return_value = {"valid": True, "missing_keys": []}
            
            pipeline = SEODataPipeline()
            pipeline.seo_service = AsyncMock()
            pipeline.keyword_clusterer = Mock()
            pipeline.competitor_analyzer = Mock()
            pipeline.keyword_analyzer = Mock()
            
            return pipeline
    
    @pytest.fixture
    def mock_pipeline_result(self):
        """Create a mock pipeline result"""
        return PipelineResult(
            pipeline_id="test_pipeline",
            status=PipelineStatus.IN_PROGRESS,
            start_time=datetime.now(),
            current_stage=PipelineStage.INITIALIZATION
        )
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock keyword research request"""
        return KeywordResearchRequest(
            primary_keywords=["python tutorial", "python guide"],
            competitor_domains=["example.com", "competitor.com"],
            target_database="us",
            analysis_depth="comprehensive"
        )
    
    @pytest.mark.asyncio
    async def test_execute_keyword_research_stage(self, mock_pipeline_with_services, mock_pipeline_result, mock_request):
        """Test keyword research stage execution"""
        # Mock the SEO service response
        mock_pipeline_with_services.seo_service.research_keyword.return_value = {
            "keyword": "python tutorial",
            "search_volume": 10000,
            "cpc": 2.50,
            "keyword_difficulty": 45,
            "status": "success"
        }
        
        await mock_pipeline_with_services._execute_keyword_research_stage(mock_pipeline_result, mock_request)
        
        assert PipelineStage.KEYWORD_RESEARCH in mock_pipeline_result.stages_completed
        assert "keyword_research" in mock_pipeline_result.results
        assert mock_pipeline_result.results["keyword_research"]["keywords_analyzed"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_competitor_analysis_stage(self, mock_pipeline_with_services, mock_pipeline_result, mock_request):
        """Test competitor analysis stage execution"""
        # Mock the competitor analyzer
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_competitors.return_value = {
            "domain": "example.com",
            "analysis_status": "completed",
            "competitors_analyzed": 1
        }
        
        mock_pipeline_with_services.competitor_analyzer.__aenter__.return_value = mock_analyzer
        mock_pipeline_with_services.competitor_analyzer.__aexit__.return_value = None
        
        await mock_pipeline_with_services._execute_competitor_analysis_stage(mock_pipeline_result, mock_request)
        
        assert PipelineStage.COMPETITOR_ANALYSIS in mock_pipeline_result.stages_completed
        assert "competitor_analysis" in mock_pipeline_result.results
        assert mock_pipeline_result.results["competitor_analysis"]["competitors_analyzed"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_keyword_clustering_stage(self, mock_pipeline_with_services, mock_pipeline_result, mock_request):
        """Test keyword clustering stage execution"""
        # Add keyword research results to pipeline
        mock_pipeline_result.results["keyword_research"] = {
            "results": [
                {"keyword": "python tutorial", "search_volume": 10000, "keyword_difficulty": 45},
                {"keyword": "python guide", "search_volume": 8000, "keyword_difficulty": 50}
            ]
        }
        
        # Mock the keyword clusterer
        mock_pipeline_with_services.keyword_clusterer.cluster_keywords.return_value = [
            {
                "cluster_id": 0,
                "keywords": [{"keyword": "python tutorial"}, {"keyword": "python guide"}],
                "size": 2
            }
        ]
        
        mock_pipeline_with_services.keyword_clusterer.find_keyword_opportunities.return_value = [
            {"keyword": "python tutorial", "opportunity_score": 85.0}
        ]
        
        await mock_pipeline_with_services._execute_keyword_clustering_stage(mock_pipeline_result, mock_request)
        
        assert PipelineStage.KEYWORD_CLUSTERING in mock_pipeline_result.stages_completed
        assert "keyword_clustering" in mock_pipeline_result.results
        assert mock_pipeline_result.results["keyword_clustering"]["total_clusters"] == 1
        assert mock_pipeline_result.results["keyword_clustering"]["high_opportunity_keywords"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_keyword_analysis_stage(self, mock_pipeline_with_services, mock_pipeline_result, mock_request):
        """Test keyword analysis stage execution"""
        # Add keyword research results to pipeline
        mock_pipeline_result.results["keyword_research"] = {
            "results": [
                {"keyword": "python tutorial", "search_volume": 10000, "keyword_difficulty": 45},
                {"keyword": "python guide", "search_volume": 8000, "keyword_difficulty": 50}
            ]
        }
        
        # Mock the keyword analyzer
        mock_metrics = Mock()
        mock_metrics.keyword = "python tutorial"
        mock_metrics.opportunity_score = 85.0
        mock_metrics.intent.value = "informational"
        
        mock_insights = {
            "recommendations": ["Create comprehensive content", "Include examples"]
        }
        
        mock_pipeline_with_services.keyword_analyzer.analyze_keyword.return_value = mock_metrics
        mock_pipeline_with_services.keyword_analyzer.generate_keyword_insights.return_value = mock_insights
        
        await mock_pipeline_with_services._execute_keyword_analysis_stage(mock_pipeline_result, mock_request)
        
        assert PipelineStage.KEYWORD_ANALYSIS in mock_pipeline_result.stages_completed
        assert "keyword_analysis" in mock_pipeline_result.results
        assert mock_pipeline_result.results["keyword_analysis"]["total_analyzed"] == 2


class TestFactoryFunction:
    """Test cases for the factory function"""
    
    @pytest.mark.asyncio
    async def test_create_seo_data_pipeline(self):
        """Test the factory function for creating pipeline instances"""
        with patch('app.services.seo_data_pipeline.SEODataPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.initialize = AsyncMock(return_value=True)
            mock_pipeline_class.return_value = mock_pipeline
            
            result = await create_seo_data_pipeline()
            
            assert result == mock_pipeline
            mock_pipeline.initialize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
