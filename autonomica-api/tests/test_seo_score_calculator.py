"""
Tests for SEO Score Calculator Module
Tests the comprehensive SEO scoring functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.services.seo_score_calculator import (
    SEOScoreCalculator,
    create_seo_score_calculator,
    ScoreCategory,
    ScoreLevel,
    FactorScore,
    CategoryScore,
    SEOScore
)


class TestScoreCategory:
    """Test ScoreCategory enum"""
    
    def test_score_category_values(self):
        """Test that all score categories have valid values"""
        assert ScoreCategory.TECHNICAL.value == "technical"
        assert ScoreCategory.CONTENT.value == "content"
        assert ScoreCategory.KEYWORDS.value == "keywords"
        assert ScoreCategory.USER_EXPERIENCE.value == "user_experience"
        assert ScoreCategory.MOBILE.value == "mobile"
        assert ScoreCategory.PERFORMANCE.value == "performance"
        assert ScoreCategory.SECURITY.value == "security"
        assert ScoreCategory.LOCAL_SEO.value == "local_seo"
        assert ScoreCategory.E_COMMERCE.value == "e_commerce"
        assert ScoreCategory.SOCIAL.value == "social"


class TestScoreLevel:
    """Test ScoreLevel enum"""
    
    def test_score_level_values(self):
        """Test that all score levels have valid values"""
        assert ScoreLevel.EXCELLENT.value == "excellent"
        assert ScoreLevel.GOOD.value == "good"
        assert ScoreLevel.AVERAGE.value == "average"
        assert ScoreLevel.POOR.value == "poor"
        assert ScoreLevel.CRITICAL.value == "critical"


class TestFactorScore:
    """Test FactorScore dataclass"""
    
    def test_factor_score_creation(self):
        """Test creating a FactorScore instance"""
        factor_score = FactorScore(
            factor_name="test_factor",
            score=8.5,
            weight=0.15,
            weighted_score=1.275,
            max_score=10.0
        )
        
        assert factor_score.factor_name == "test_factor"
        assert factor_score.score == 8.5
        assert factor_score.weight == 0.15
        assert factor_score.weighted_score == 1.275
        assert factor_score.max_score == 10.0
        assert factor_score.details == {}
        assert factor_score.recommendations == []
        assert factor_score.status == "checked"
    
    def test_factor_score_with_optional_fields(self):
        """Test creating a FactorScore with optional fields"""
        factor_score = FactorScore(
            factor_name="test_factor",
            score=7.0,
            weight=0.20,
            weighted_score=1.4,
            max_score=10.0,
            details={"test": "data"},
            recommendations=["Test recommendation"],
            status="failed"
        )
        
        assert factor_score.details == {"test": "data"}
        assert factor_score.recommendations == ["Test recommendation"]
        assert factor_score.status == "failed"


class TestCategoryScore:
    """Test CategoryScore dataclass"""
    
    def test_category_score_creation(self):
        """Test creating a CategoryScore instance"""
        factors = [
            FactorScore(
                factor_name="factor1",
                score=8.0,
                weight=0.5,
                weighted_score=4.0,
                max_score=10.0
            ),
            FactorScore(
                factor_name="factor2",
                score=6.0,
                weight=0.5,
                weighted_score=3.0,
                max_score=10.0
            )
        ]
        
        category_score = CategoryScore(
            category=ScoreCategory.TECHNICAL,
            total_score=7.0,
            max_possible_score=10.0,
            percentage=0,  # Will be calculated in __post_init__
            level=ScoreLevel.AVERAGE,  # Will be calculated in __post_init__
            factors=factors,
            weight=0.25
        )
        
        assert category_score.category == ScoreCategory.TECHNICAL
        assert category_score.total_score == 7.0
        assert category_score.max_possible_score == 10.0
        assert category_score.percentage == 70.0
        assert category_score.level == ScoreLevel.GOOD
        assert category_score.weight == 0.25
        assert category_score.weighted_score == 1.75
    
    def test_category_score_level_determination(self):
        """Test automatic level determination based on percentage"""
        # Test excellent level
        excellent_score = CategoryScore(
            category=ScoreCategory.CONTENT,
            total_score=9.5,
            max_possible_score=10.0,
            percentage=0,
            level=ScoreLevel.AVERAGE,
            factors=[],
            weight=0.20
        )
        assert excellent_score.level == ScoreLevel.EXCELLENT
        
        # Test critical level
        critical_score = CategoryScore(
            category=ScoreCategory.KEYWORDS,
            total_score=2.0,
            max_possible_score=10.0,
            percentage=0,
            level=ScoreLevel.AVERAGE,
            factors=[],
            weight=0.20
        )
        assert critical_score.level == ScoreLevel.CRITICAL


class TestSEOScore:
    """Test SEOScore dataclass"""
    
    def test_seo_score_creation(self):
        """Test creating a SEOScore instance"""
        categories = {
            ScoreCategory.TECHNICAL: Mock(
                total_score=8.0,
                max_possible_score=10.0,
                percentage=80.0,
                level=ScoreLevel.GOOD,
                weight=0.25,
                weighted_score=2.0
            ),
            ScoreCategory.CONTENT: Mock(
                total_score=7.5,
                max_possible_score=10.0,
                percentage=75.0,
                level=ScoreLevel.GOOD,
                weight=0.20,
                weighted_score=1.5
            )
        }
        
        seo_score = SEOScore(
            url="https://example.com",
            domain="example.com",
            analyzed_at=datetime.now(),
            overall_score=7.75,
            max_possible_score=10.0,
            percentage=0,  # Will be calculated in __post_init__
            level=ScoreLevel.AVERAGE,  # Will be calculated in __post_init__
            categories=categories,
            summary={"test": "summary"},
            recommendations=["Test recommendation"],
            critical_issues=["Test critical issue"],
            improvement_opportunities=["Test opportunity"]
        )
        
        assert seo_score.url == "https://example.com"
        assert seo_score.domain == "example.com"
        assert seo_score.overall_score == 7.75
        assert seo_score.max_possible_score == 10.0
        assert seo_score.percentage == 77.5
        assert seo_score.level == ScoreLevel.GOOD
        assert len(seo_score.categories) == 2


class TestSEOScoreCalculator:
    """Test the main SEOScoreCalculator class"""
    
    @pytest.fixture
    async def mock_calculator(self):
        """Create a mock calculator with mocked dependencies"""
        calculator = SEOScoreCalculator()
        
        # Mock the dependent services
        calculator.seo_service = Mock()
        calculator.keyword_analyzer = Mock()
        calculator.competitor_analyzer = Mock()
        
        # Mock initialization methods
        calculator.seo_service.initialize = AsyncMock()
        calculator.keyword_analyzer.initialize = AsyncMock()
        calculator.competitor_analyzer.initialize = AsyncMock()
        
        return calculator
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_calculator):
        """Test calculator initialization"""
        await mock_calculator.initialize()
        
        mock_calculator.seo_service.initialize.assert_called_once()
        mock_calculator.keyword_analyzer.initialize.assert_called_once()
        mock_calculator.competitor_analyzer.initialize.assert_called_once()
    
    def test_category_weights_initialization(self, mock_calculator):
        """Test that category weights are properly initialized"""
        assert len(mock_calculator.category_weights) == 10
        assert mock_calculator.category_weights[ScoreCategory.TECHNICAL] == 0.25
        assert mock_calculator.category_weights[ScoreCategory.CONTENT] == 0.20
        assert mock_calculator.category_weights[ScoreCategory.KEYWORDS] == 0.20
    
    def test_factor_weights_initialization(self, mock_calculator):
        """Test that factor weights are properly initialized"""
        technical_factors = mock_calculator.factor_weights[ScoreCategory.TECHNICAL]
        assert len(technical_factors) == 10
        assert "title_tag" in technical_factors
        assert "meta_description" in technical_factors
        assert "heading_structure" in technical_factors
    
    def test_scoring_config_initialization(self, mock_calculator):
        """Test that scoring configuration is properly initialized"""
        config = mock_calculator.scoring_config
        assert config["excellent_threshold"] == 90
        assert config["good_threshold"] == 75
        assert config["average_threshold"] == 60
        assert config["poor_threshold"] == 40
    
    @pytest.mark.asyncio
    async def test_calculate_seo_score_basic(self, mock_calculator):
        """Test basic SEO score calculation"""
        # Mock the analysis methods
        mock_calculator._analyze_page = AsyncMock(return_value={
            "url": "https://example.com",
            "analysis_depth": "basic",
            "timestamp": datetime.now(),
            "page_data": {},
            "technical_data": {},
            "content_data": {},
            "keyword_data": {},
            "performance_data": {},
            "security_data": {}
        })
        
        mock_calculator._calculate_category_score = AsyncMock(return_value=Mock(
            category=ScoreCategory.TECHNICAL,
            total_score=8.0,
            max_possible_score=10.0,
            percentage=80.0,
            level=ScoreLevel.GOOD,
            factors=[],
            weight=0.25,
            weighted_score=2.0
        ))
        
        mock_calculator._generate_summary = Mock(return_value={"test": "summary"})
        mock_calculator._generate_recommendations = Mock(return_value=["Test recommendation"])
        mock_calculator._identify_critical_issues = Mock(return_value=[])
        mock_calculator._identify_improvement_opportunities = Mock(return_value=["Test opportunity"])
        
        # Calculate score
        seo_score = await mock_calculator.calculate_seo_score("https://example.com", "basic")
        
        assert seo_score.url == "https://example.com"
        assert seo_score.domain == "example.com"
        assert seo_score.overall_score > 0
        assert len(seo_score.categories) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_category_score(self, mock_calculator):
        """Test category score calculation"""
        # Mock factor score calculation
        mock_calculator._calculate_factor_score = AsyncMock(return_value=FactorScore(
            factor_name="test_factor",
            score=8.0,
            weight=0.5,
            weighted_score=4.0,
            max_score=10.0
        ))
        
        page_analysis = {"test": "data"}
        
        category_score = await mock_calculator._calculate_category_score(
            ScoreCategory.TECHNICAL,
            page_analysis,
            "comprehensive"
        )
        
        assert category_score.category == ScoreCategory.TECHNICAL
        assert category_score.total_score > 0
        assert len(category_score.factors) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_factor_score(self, mock_calculator):
        """Test factor score calculation"""
        factor_score = await mock_calculator._calculate_factor_score(
            "title_tag",
            ScoreCategory.TECHNICAL,
            {"test": "data"},
            "comprehensive"
        )
        
        assert factor_score.factor_name == "title_tag"
        assert factor_score.score == 7.0  # Default placeholder score
        assert factor_score.max_score == 10.0
        assert factor_score.status == "placeholder"
    
    def test_extract_domain(self, mock_calculator):
        """Test domain extraction from URLs"""
        # Test with full URL
        domain = mock_calculator._extract_domain("https://www.example.com/page")
        assert domain == "www.example.com"
        
        # Test with URL without protocol
        domain = mock_calculator._extract_domain("example.com/page")
        assert domain == "example.com"
        
        # Test with just domain
        domain = mock_calculator._extract_domain("example.com")
        assert domain == "example.com"
    
    def test_generate_summary(self, mock_calculator):
        """Test summary generation"""
        category_scores = {
            ScoreCategory.TECHNICAL: Mock(
                total_score=8.0,
                max_possible_score=10.0,
                percentage=80.0,
                level=ScoreLevel.GOOD
            ),
            ScoreCategory.CONTENT: Mock(
                total_score=7.5,
                max_possible_score=10.0,
                percentage=75.0,
                level=ScoreLevel.GOOD
            )
        }
        
        page_analysis = {
            "analysis_depth": "comprehensive",
            "timestamp": datetime.now()
        }
        
        summary = mock_calculator._generate_summary(category_scores, page_analysis)
        
        assert summary["total_categories"] == 2
        assert "technical" in summary["categories_analyzed"]
        assert "content" in summary["categories_analyzed"]
        assert summary["analysis_depth"] == "comprehensive"
    
    def test_generate_recommendations(self, mock_calculator):
        """Test recommendation generation"""
        category_scores = {
            ScoreCategory.TECHNICAL: Mock(
                level=ScoreLevel.EXCELLENT,
                factors=[
                    Mock(score=9.0, recommendations=[]),
                    Mock(score=4.0, recommendations=["Fix this issue"])
                ]
            ),
            ScoreCategory.CONTENT: Mock(
                level=ScoreLevel.CRITICAL,
                factors=[
                    Mock(score=2.0, recommendations=["Critical content issue"])
                ]
            )
        }
        
        recommendations = mock_calculator._generate_recommendations(category_scores)
        
        assert len(recommendations) > 0
        assert "Focus on improving content" in recommendations
        assert "Fix this issue" in recommendations
    
    def test_identify_critical_issues(self, mock_calculator):
        """Test critical issue identification"""
        category_scores = {
            ScoreCategory.TECHNICAL: Mock(
                level=ScoreLevel.CRITICAL,
                factors=[
                    Mock(score=2.0),
                    Mock(score=8.0)
                ]
            ),
            ScoreCategory.CONTENT: Mock(
                level=ScoreLevel.GOOD,
                factors=[
                    Mock(score=7.0),
                    Mock(score=2.5)
                ]
            )
        }
        
        critical_issues = mock_calculator._identify_critical_issues(category_scores)
        
        assert len(critical_issues) > 0
        assert "Critical issues in technical" in critical_issues
        assert "Critical issue: factor" in critical_issues
    
    def test_identify_improvement_opportunities(self, mock_calculator):
        """Test improvement opportunity identification"""
        category_scores = {
            ScoreCategory.TECHNICAL: Mock(
                level=ScoreLevel.AVERAGE,
                factors=[
                    Mock(score=6.0),
                    Mock(score=7.0)
                ]
            ),
            ScoreCategory.CONTENT: Mock(
                level=ScoreLevel.GOOD,
                factors=[
                    Mock(score=8.0),
                    Mock(score=6.5)
                ]
            )
        }
        
        opportunities = mock_calculator._identify_improvement_opportunities(category_scores)
        
        assert len(opportunities) > 0
        assert "Improve technical" in opportunities
        assert "Optimize factor" in opportunities
    
    @pytest.mark.asyncio
    async def test_get_scoring_statistics(self, mock_calculator):
        """Test scoring statistics retrieval"""
        stats = await mock_calculator.get_scoring_statistics()
        
        assert "total_categories" in stats
        assert "total_factors" in stats
        assert "category_weights" in stats
        assert "scoring_config" in stats
        assert stats["total_categories"] == 10
        assert isinstance(stats["total_factors"], int)


class TestFactoryFunction:
    """Test the factory function"""
    
    @pytest.mark.asyncio
    async def test_create_seo_score_calculator(self):
        """Test calculator creation via factory function"""
        with patch('app.services.seo_score_calculator.SEOScoreCalculator') as mock_calculator_class:
            mock_calculator = Mock()
            mock_calculator_class.return_value = mock_calculator
            mock_calculator.initialize = AsyncMock()
            
            calculator = await create_seo_score_calculator()
            
            mock_calculator_class.assert_called_once()
            mock_calculator.initialize.assert_called_once()
            assert calculator == mock_calculator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
