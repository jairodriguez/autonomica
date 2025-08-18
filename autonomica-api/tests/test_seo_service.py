"""
Tests for SEO Service Module
Tests the SEMrush API integration, keyword clustering, and competitor analysis
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from app.services.seo_service import SEOService, create_seo_service
from app.services.keyword_clustering import KeywordClusterer
from app.services.competitor_analysis import CompetitorAnalyzer
from app.config.seo_config import validate_seo_config


class TestSEOService:
    """Test cases for the main SEO service"""
    
    @pytest.fixture
    def mock_seo_service(self):
        """Create a mock SEO service for testing"""
        with patch('app.services.seo_service.seo_settings') as mock_settings:
            mock_settings.SEMRUSH_API_KEY = "test_api_key"
            mock_settings.SEMRUSH_BASE_URL = "https://api.semrush.com"
            mock_settings.SEMRUSH_DATABASE = "us"
            
            service = SEOService()
            return service
    
    def test_seo_service_initialization(self, mock_seo_service):
        """Test SEO service initialization"""
        assert mock_seo_service is not None
        assert hasattr(mock_seo_service, 'semrush_api_key')
        assert hasattr(mock_seo_service, 'base_url')
    
    @pytest.mark.asyncio
    async def test_keyword_research_success(self, mock_seo_service):
        """Test successful keyword research"""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "keyword;search_volume;cpc;keyword_difficulty\npython tutorial;12000;2.50;45"
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await mock_seo_service.research_keyword("python tutorial")
            
            assert result is not None
            assert "keyword" in result
            assert "search_volume" in result
    
    @pytest.mark.asyncio
    async def test_keyword_research_api_error(self, mock_seo_service):
        """Test keyword research with API error"""
        with patch('httpx.AsyncClient.get', side_effect=Exception("API Error")):
            result = await mock_seo_service.research_keyword("test keyword")
            
            assert result is not None
            assert "error" in result
            assert result["status"] == "failed"
    
    def test_parse_semrush_response_valid(self, mock_seo_service):
        """Test parsing valid SEMrush response"""
        valid_response = "keyword;search_volume;cpc;keyword_difficulty\npython;10000;2.00;40"
        result = mock_seo_service._parse_semrush_response(valid_response)
        
        assert result is not None
        assert len(result) > 0
        assert "python" in result[0]["keyword"]
    
    def test_parse_semrush_response_invalid(self, mock_seo_service):
        """Test parsing invalid SEMrush response"""
        invalid_response = "invalid;format;response"
        result = mock_seo_service._parse_semrush_response(invalid_response)
        
        assert result is not None
        assert "error" in result
        assert result["status"] == "failed"


class TestKeywordClusterer:
    """Test cases for keyword clustering functionality"""
    
    @pytest.fixture
    def clusterer(self):
        """Create a keyword clusterer instance"""
        return KeywordClusterer(similarity_threshold=0.7)
    
    def test_clusterer_initialization(self, clusterer):
        """Test keyword clusterer initialization"""
        assert clusterer is not None
        assert clusterer.similarity_threshold == 0.7
        assert hasattr(clusterer, 'vectorizer')
    
    def test_preprocess_keyword(self, clusterer):
        """Test keyword preprocessing"""
        # Test basic preprocessing
        result = clusterer.preprocess_keyword("Python Tutorial 2024")
        assert "python" in result.lower()
        assert "tutorial" in result.lower()
        
        # Test with special characters
        result = clusterer.preprocess_keyword("Python & Tutorial!")
        assert "python" in result.lower()
        assert "tutorial" in result.lower()
        assert "&" not in result
        assert "!" not in result
    
    def test_extract_keyword_features(self, clusterer):
        """Test keyword feature extraction"""
        features = clusterer.extract_keyword_features("Python Tutorial 2024")
        
        assert features["length"] == 18
        assert features["word_count"] == 3
        assert features["has_numbers"] == True
        assert features["is_long_tail"] == False
        assert features["is_question"] == False
    
    def test_jaccard_similarity(self, clusterer):
        """Test Jaccard similarity calculation"""
        # Test identical strings
        similarity = clusterer._jaccard_similarity("python tutorial", "python tutorial")
        assert similarity == 1.0
        
        # Test similar strings
        similarity = clusterer._jaccard_similarity("python tutorial", "python guide")
        assert 0.0 < similarity < 1.0
        
        # Test different strings
        similarity = clusterer._jaccard_similarity("python", "javascript")
        assert similarity == 0.0
    
    def test_cluster_keywords_single(self, clusterer):
        """Test clustering with single keyword"""
        keywords = ["python tutorial"]
        result = clusterer.cluster_keywords(keywords)
        
        assert len(result) == 1
        assert result[0]["cluster_id"] == 0
        assert result[0]["size"] == 1
    
    def test_cluster_keywords_multiple(self, clusterer):
        """Test clustering with multiple keywords"""
        keywords = ["python tutorial", "python guide", "javascript tutorial", "javascript guide"]
        result = clusterer.cluster_keywords(keywords)
        
        assert len(result) > 0
        assert all("cluster_id" in cluster for cluster in result)
        assert all("size" in cluster for cluster in result)
    
    def test_find_keyword_opportunities(self, clusterer):
        """Test keyword opportunity identification"""
        # Create mock clusters
        clusters = [{
            "cluster_id": 0,
            "keywords": [
                {"keyword": "python tutorial", "search_volume": 5000, "difficulty": 30},
                {"keyword": "python guide", "search_volume": 3000, "difficulty": 40}
            ],
            "size": 2
        }]
        
        opportunities = clusterer.find_keyword_opportunities(clusters, min_volume=1000, max_difficulty=70)
        
        assert len(opportunities) > 0
        assert all("opportunity_score" in opp for opp in opportunities)
        assert all("reasoning" in opp for opp in opportunities)


class TestCompetitorAnalyzer:
    """Test cases for competitor analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a competitor analyzer instance"""
        return CompetitorAnalyzer(max_concurrent_requests=3, request_timeout=10)
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test competitor analyzer initialization"""
        assert analyzer is not None
        assert analyzer.max_concurrent_requests == 3
        assert analyzer.request_timeout == 10
    
    @pytest.mark.asyncio
    async def test_analyze_competitors_basic(self, analyzer):
        """Test basic competitor analysis"""
        domain = "example.com"
        competitors = ["competitor1.com", "competitor2.com"]
        
        # Mock the session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://competitor1.com"
        mock_response.headers = {
            "Server": "nginx",
            "Content-Type": "text/html",
            "X-Viewport-Meta": "width=device-width"
        }
        mock_response.text = AsyncMock(return_value="<html><title>Test</title><p>Content</p></html>")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(analyzer, 'session', mock_session):
            result = await analyzer.analyze_competitors(domain, competitors, "basic")
            
            assert result is not None
            assert "domain" in result
            assert "competitors_analyzed" in result
    
    def test_detect_content_type(self, analyzer):
        """Test content type detection"""
        from bs4 import BeautifulSoup
        
        # Test article content
        html = "<html><article><p>Content</p></article></html>"
        soup = BeautifulSoup(html, 'html.parser')
        content_type = analyzer._detect_content_type(soup)
        assert content_type == "article"
        
        # Test form content
        html = "<html><form><input type='text'/></form></html>"
        soup = BeautifulSoup(html, 'html.parser')
        content_type = analyzer._detect_content_type(soup)
        assert content_type == "form"
    
    def test_identify_content_patterns(self, analyzer):
        """Test content pattern identification"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <header>Header</header>
            <nav>Navigation</nav>
            <aside class="sidebar">Sidebar</aside>
            <footer>Footer</footer>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        patterns = analyzer._identify_content_patterns(soup)
        
        assert patterns["has_header"] == True
        assert patterns["has_navigation"] == True
        assert patterns["has_sidebar"] == True
        assert patterns["has_footer"] == True
    
    def test_check_mobile_friendliness(self, analyzer):
        """Test mobile friendliness checking"""
        headers = {"X-Viewport-Meta": "width=device-width, initial-scale=1.0"}
        result = analyzer._check_mobile_friendliness(headers)
        
        assert result["has_viewport_meta"] == True
        assert result["mobile_optimized"] == True
        
        # Test without viewport meta
        headers = {}
        result = analyzer._check_mobile_friendliness(headers)
        assert result["has_viewport_meta"] == False
        assert result["mobile_optimized"] == False


class TestSEOConfig:
    """Test cases for SEO configuration"""
    
    def test_validate_seo_config_missing_keys(self):
        """Test configuration validation with missing keys"""
        with patch('app.config.seo_config.seo_settings') as mock_settings:
            mock_settings.SEMRUSH_API_KEY = ""
            mock_settings.GOOGLE_API_KEY = ""
            
            result = validate_seo_config()
            
            assert result["valid"] == False
            assert "SEMRUSH_API_KEY" in result["missing_keys"]
            assert "GOOGLE_API_KEY" in result["missing_keys"]
    
    def test_validate_seo_config_valid(self):
        """Test configuration validation with valid keys"""
        with patch('app.config.seo_config.seo_settings') as mock_settings:
            mock_settings.SEMRUSH_API_KEY = "valid_key"
            mock_settings.GOOGLE_API_KEY = "valid_key"
            
            result = validate_seo_config()
            
            assert result["valid"] == True
            assert len(result["missing_keys"]) == 0
            assert result["semrush_configured"] == True
            assert result["google_configured"] == True


class TestIntegration:
    """Integration tests for SEO service components"""
    
    @pytest.mark.asyncio
    async def test_full_keyword_analysis_workflow(self):
        """Test complete keyword analysis workflow"""
        # This would test the integration between all components
        # For now, we'll test that the components can work together
        
        clusterer = KeywordClusterer()
        analyzer = CompetitorAnalyzer()
        
        # Test that both components can be instantiated
        assert clusterer is not None
        assert analyzer is not None
        
        # Test basic functionality
        keywords = ["python tutorial", "python guide", "javascript tutorial"]
        clusters = clusterer.cluster_keywords(keywords)
        
        assert len(clusters) > 0
        assert all("cluster_id" in cluster for cluster in clusters)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
