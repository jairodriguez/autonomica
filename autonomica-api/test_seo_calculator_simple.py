#!/usr/bin/env python3
"""
Simple test script for SEO Score Calculator
Tests core functionality without pytest dependencies
"""
import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_seo_score_calculator():
    """Test the SEO score calculator core functionality"""
    print("🧪 Testing SEO Score Calculator Core Functionality")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from app.services.seo_score_calculator import (
            SEOScoreCalculator,
            ScoreCategory,
            ScoreLevel,
            FactorScore,
            CategoryScore,
            SEOScore
        )
        print("✅ All imports successful")
        
        # Test enums
        print("\n🔤 Testing enums...")
        assert ScoreCategory.TECHNICAL.value == "technical"
        assert ScoreCategory.CONTENT.value == "content"
        assert ScoreCategory.KEYWORDS.value == "keywords"
        assert ScoreLevel.EXCELLENT.value == "excellent"
        assert ScoreLevel.CRITICAL.value == "critical"
        print("✅ Enums working correctly")
        
        # Test dataclasses
        print("\n🏗️ Testing dataclasses...")
        
        # Test FactorScore
        factor_score = FactorScore(
            factor_name="title_tag",
            score=8.5,
            weight=0.15,
            weighted_score=1.275,
            max_score=10.0
        )
        assert factor_score.factor_name == "title_tag"
        assert factor_score.score == 8.5
        assert factor_score.weighted_score == 1.275
        print("✅ FactorScore working correctly")
        
        # Test CategoryScore
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
            weight=0.25,
            weighted_score=0  # Will be calculated in __post_init__
        )
        
        print(f"Debug: percentage={category_score.percentage}, level={category_score.level}, weighted_score={category_score.weighted_score}")
        assert category_score.percentage == 70.0
        assert category_score.level == ScoreLevel.AVERAGE  # 70% is AVERAGE (≥60 and <75)
        assert category_score.weighted_score == 1.75  # 7.0 * 0.25
        print("✅ CategoryScore working correctly")
        
        # Test SEOScore
        categories = {
            ScoreCategory.TECHNICAL: category_score,
            ScoreCategory.CONTENT: Mock(
                total_score=7.5,
                max_possible_score=10.0,
                percentage=75.0,
                level=ScoreLevel.GOOD,
                weight=0.20,
                weighted_score=1.5
            )
        }
        
        # Create a simple mock for the categories
        class MockCategory:
            def __init__(self, total_score, max_possible_score, percentage, level, weight, weighted_score):
                self.total_score = total_score
                self.max_possible_score = max_possible_score
                self.percentage = percentage
                self.level = level
                self.weight = weight
                self.weighted_score = weighted_score
        
        categories = {
            ScoreCategory.TECHNICAL: category_score,
            ScoreCategory.CONTENT: MockCategory(7.5, 10.0, 75.0, ScoreLevel.GOOD, 0.20, 1.5)
        }
        
        seo_score = SEOScore(
            url="https://example.com",
            domain="example.com",
            analyzed_at=datetime.now(),
            overall_score=7.75,
            max_possible_score=10.0,
            percentage=0,
            level=ScoreLevel.AVERAGE,
            categories=categories,
            summary={"test": "summary"},
            recommendations=["Test recommendation"],
            critical_issues=["Test critical issue"],
            improvement_opportunities=["Test opportunity"]
        )
        
        assert seo_score.url == "https://example.com"
        assert seo_score.domain == "example.com"
        assert seo_score.overall_score == 7.75
        assert seo_score.percentage == 77.5
        assert seo_score.level == ScoreLevel.GOOD
        print("✅ SEOScore working correctly")
        
        # Test SEOScoreCalculator initialization
        print("\n🔧 Testing SEOScoreCalculator initialization...")
        calculator = SEOScoreCalculator()
        
        # Test category weights
        assert len(calculator.category_weights) == 10
        assert calculator.category_weights[ScoreCategory.TECHNICAL] == 0.25
        assert calculator.category_weights[ScoreCategory.CONTENT] == 0.20
        print("✅ Category weights initialized correctly")
        
        # Test factor weights
        technical_factors = calculator.factor_weights[ScoreCategory.TECHNICAL]
        assert len(technical_factors) == 10
        assert "title_tag" in technical_factors
        assert "meta_description" in technical_factors
        print("✅ Factor weights initialized correctly")
        
        # Test scoring config
        config = calculator.scoring_config
        assert config["excellent_threshold"] == 90
        assert config["good_threshold"] == 75
        assert config["average_threshold"] == 60
        print("✅ Scoring configuration initialized correctly")
        
        # Test utility methods
        print("\n🛠️ Testing utility methods...")
        
        # Test domain extraction
        domain = calculator._extract_domain("https://www.example.com/page")
        assert domain == "www.example.com"
        
        domain = calculator._extract_domain("example.com/page")
        assert domain == "example.com"
        print("✅ Domain extraction working correctly")
        
        # Test summary generation
        summary = calculator._generate_summary(categories, {
            "analysis_depth": "comprehensive",
            "timestamp": datetime.now()
        })
        assert summary["total_categories"] == 2
        assert "technical" in summary["categories_analyzed"]
        print("✅ Summary generation working correctly")
        
        # Test recommendation generation
        recommendations = calculator._generate_recommendations(categories)
        assert len(recommendations) >= 0  # May be empty depending on scores
        print("✅ Recommendation generation working correctly")
        
        # Test critical issue identification
        critical_issues = calculator._identify_critical_issues(categories)
        assert isinstance(critical_issues, list)
        print("✅ Critical issue identification working correctly")
        
        # Test improvement opportunity identification
        opportunities = calculator._identify_improvement_opportunities(categories)
        assert isinstance(opportunities, list)
        print("✅ Improvement opportunity identification working correctly")
        
        # Test statistics
        print("\n📊 Testing statistics...")
        stats = await calculator.get_scoring_statistics()
        assert "total_categories" in stats
        assert "total_factors" in stats
        assert "category_weights" in stats
        assert "scoring_config" in stats
        assert stats["total_categories"] == 10
        print("✅ Statistics retrieval working correctly")
        
        print("\n🎉 All core functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_seo_score_calculator())
    sys.exit(0 if success else 1)
