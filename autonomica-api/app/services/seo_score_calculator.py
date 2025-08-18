"""
SEO Score Calculator Module
Provides comprehensive SEO scoring for web pages based on multiple factors
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

from app.services.seo_service import SEOService
from app.services.keyword_analysis import KeywordAnalyzer, KeywordMetrics
from app.services.competitor_analysis import CompetitorAnalyzer
from app.config.seo_config import seo_settings

logger = logging.getLogger(__name__)

class ScoreCategory(Enum):
    """SEO score categories"""
    TECHNICAL = "technical"
    CONTENT = "content"
    KEYWORDS = "keywords"
    USER_EXPERIENCE = "user_experience"
    MOBILE = "mobile"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOCAL_SEO = "local_seo"
    E_COMMERCE = "e_commerce"
    SOCIAL = "social"

class ScoreLevel(Enum):
    """Score levels for categorization"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class FactorScore:
    """Individual factor score"""
    factor_name: str
    score: float
    weight: float
    weighted_score: float
    max_score: float
    details: Dict[str, Any] = None
    recommendations: List[str] = None
    status: str = "checked"

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.recommendations is None:
            self.recommendations = []
        self.weighted_score = self.score * self.weight

@dataclass
class CategoryScore:
    """Score for a specific category"""
    category: ScoreCategory
    total_score: float
    max_possible_score: float
    percentage: float
    level: ScoreLevel
    factors: List[FactorScore]
    weight: float
    weighted_score: float

    def __post_init__(self):
        self.percentage = (self.total_score / self.max_possible_score) * 100
        self.level = self._determine_level()
        self.weighted_score = self.total_score * self.weight

    def _determine_level(self) -> ScoreLevel:
        """Determine score level based on percentage"""
        if self.percentage >= 90:
            return ScoreLevel.EXCELLENT
        elif self.percentage >= 75:
            return ScoreLevel.GOOD
        elif self.percentage >= 60:
            return ScoreLevel.AVERAGE
        elif self.percentage >= 40:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.CRITICAL

@dataclass
class SEOScore:
    """Complete SEO score for a web page"""
    url: str
    domain: str
    analyzed_at: datetime
    overall_score: float
    max_possible_score: float
    percentage: float
    level: ScoreLevel
    categories: Dict[ScoreCategory, CategoryScore]
    summary: Dict[str, Any]
    recommendations: List[str]
    critical_issues: List[str]
    improvement_opportunities: List[str]
    competitor_comparison: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.percentage = (self.overall_score / self.max_possible_score) * 100
        self.level = self._determine_level()

    def _determine_level(self) -> ScoreLevel:
        """Determine overall score level"""
        if self.percentage >= 90:
            return ScoreLevel.EXCELLENT
        elif self.percentage >= 75:
            return ScoreLevel.GOOD
        elif self.percentage >= 60:
            return ScoreLevel.AVERAGE
        elif self.percentage >= 40:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.CRITICAL

class SEOScoreCalculator:
    """Main SEO score calculator that analyzes and scores web pages"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.seo_service = None
        self.keyword_analyzer = None
        self.competitor_analyzer = None
        
        # Default weights for different categories
        self.category_weights = {
            ScoreCategory.TECHNICAL: 0.25,
            ScoreCategory.CONTENT: 0.20,
            ScoreCategory.KEYWORDS: 0.20,
            ScoreCategory.USER_EXPERIENCE: 0.15,
            ScoreCategory.MOBILE: 0.10,
            ScoreCategory.PERFORMANCE: 0.05,
            ScoreCategory.SECURITY: 0.03,
            ScoreCategory.LOCAL_SEO: 0.01,
            ScoreCategory.E_COMMERCE: 0.01,
            ScoreCategory.SOCIAL: 0.01
        }
        
        # Factor weights within each category
        self.factor_weights = self._initialize_factor_weights()
        
        # Scoring thresholds and configurations
        self.scoring_config = self._initialize_scoring_config()

    async def initialize(self):
        """Initialize all required services"""
        try:
            self.seo_service = SEOService()
            self.keyword_analyzer = KeywordAnalyzer()
            self.competitor_analyzer = CompetitorAnalyzer()
            
            # Initialize services
            await self.seo_service.initialize()
            await self.keyword_analyzer.initialize()
            await self.competitor_analyzer.initialize()
            
            self.logger.info("SEOScoreCalculator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SEOScoreCalculator: {e}")
            raise

    def _initialize_factor_weights(self) -> Dict[ScoreCategory, Dict[str, float]]:
        """Initialize weights for individual factors within each category"""
        return {
            ScoreCategory.TECHNICAL: {
                "title_tag": 0.15,
                "meta_description": 0.10,
                "heading_structure": 0.15,
                "url_structure": 0.10,
                "internal_linking": 0.10,
                "schema_markup": 0.10,
                "canonical_tags": 0.10,
                "robots_txt": 0.05,
                "sitemap": 0.05,
                "ssl_certificate": 0.10
            },
            ScoreCategory.CONTENT: {
                "content_length": 0.15,
                "content_quality": 0.25,
                "readability": 0.15,
                "content_freshness": 0.10,
                "multimedia_content": 0.10,
                "content_structure": 0.15,
                "internal_linking": 0.10
            },
            ScoreCategory.KEYWORDS: {
                "keyword_density": 0.20,
                "keyword_placement": 0.20,
                "long_tail_keywords": 0.15,
                "keyword_relevance": 0.25,
                "keyword_competition": 0.20
            },
            ScoreCategory.USER_EXPERIENCE: {
                "page_speed": 0.25,
                "navigation": 0.20,
                "accessibility": 0.20,
                "mobile_friendliness": 0.20,
                "user_engagement": 0.15
            },
            ScoreCategory.MOBILE: {
                "responsive_design": 0.30,
                "mobile_speed": 0.25,
                "touch_friendly": 0.20,
                "mobile_navigation": 0.25
            },
            ScoreCategory.PERFORMANCE: {
                "page_load_time": 0.40,
                "core_web_vitals": 0.30,
                "resource_optimization": 0.30
            },
            ScoreCategory.SECURITY: {
                "ssl_https": 0.40,
                "security_headers": 0.30,
                "vulnerability_scan": 0.30
            },
            ScoreCategory.LOCAL_SEO: {
                "google_my_business": 0.40,
                "local_citations": 0.30,
                "local_keywords": 0.30
            },
            ScoreCategory.E_COMMERCE: {
                "product_pages": 0.30,
                "shopping_cart": 0.25,
                "payment_security": 0.25,
                "product_reviews": 0.20
            },
            ScoreCategory.SOCIAL: {
                "social_sharing": 0.40,
                "social_proof": 0.30,
                "social_engagement": 0.30
            }
        }

    def _initialize_scoring_config(self) -> Dict[str, Any]:
        """Initialize scoring configuration and thresholds"""
        return {
            "excellent_threshold": 90,
            "good_threshold": 75,
            "average_threshold": 60,
            "poor_threshold": 40,
            "critical_threshold": 0,
            "min_content_length": 300,
            "optimal_content_length": 1500,
            "max_content_length": 5000,
            "optimal_keyword_density": 0.02,
            "max_keyword_density": 0.05,
            "min_page_speed": 3.0,
            "optimal_page_speed": 1.5,
            "max_page_speed": 5.0
        }

    async def calculate_seo_score(self, url: str, analysis_depth: str = "comprehensive") -> SEOScore:
        """Calculate comprehensive SEO score for a web page"""
        try:
            self.logger.info(f"Starting SEO score calculation for: {url}")
            start_time = datetime.now()
            
            # Extract domain from URL
            domain = self._extract_domain(url)
            
            # Analyze the page
            page_analysis = await self._analyze_page(url, analysis_depth)
            
            # Calculate scores for each category
            category_scores = {}
            total_score = 0
            max_possible_score = 0
            
            for category in ScoreCategory:
                category_score = await self._calculate_category_score(
                    category, page_analysis, analysis_depth
                )
                category_scores[category] = category_score
                total_score += category_score.weighted_score
                max_possible_score += category_score.max_possible_score * category_score.weight
            
            # Calculate overall score
            overall_score = total_score
            max_possible = max_possible_score
            
            # Generate summary and recommendations
            summary = self._generate_summary(category_scores, page_analysis)
            recommendations = self._generate_recommendations(category_scores)
            critical_issues = self._identify_critical_issues(category_scores)
            improvement_opportunities = self._identify_improvement_opportunities(category_scores)
            
            # Create SEO score object
            seo_score = SEOScore(
                url=url,
                domain=domain,
                analyzed_at=start_time,
                overall_score=overall_score,
                max_possible_score=max_possible,
                percentage=0,  # Will be calculated in __post_init__
                level=ScoreLevel.AVERAGE,  # Will be calculated in __post_init__
                categories=category_scores,
                summary=summary,
                recommendations=recommendations,
                critical_issues=critical_issues,
                improvement_opportunities=improvement_opportunities
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"SEO score calculation completed in {processing_time:.2f}s")
            
            return seo_score
            
        except Exception as e:
            self.logger.error(f"Error calculating SEO score for {url}: {e}")
            raise

    async def _analyze_page(self, url: str, analysis_depth: str) -> Dict[str, Any]:
        """Analyze the web page to gather data for scoring"""
        analysis = {
            "url": url,
            "analysis_depth": analysis_depth,
            "timestamp": datetime.now(),
            "page_data": {},
            "technical_data": {},
            "content_data": {},
            "keyword_data": {},
            "performance_data": {},
            "security_data": {}
        }
        
        try:
            # Basic page analysis
            if analysis_depth in ["basic", "comprehensive", "deep"]:
                analysis["page_data"] = await self._get_basic_page_data(url)
                analysis["technical_data"] = await self._get_technical_data(url)
            
            # Content analysis
            if analysis_depth in ["comprehensive", "deep"]:
                analysis["content_data"] = await self._get_content_data(url)
                analysis["keyword_data"] = await self._get_keyword_data(url)
            
            # Performance and security analysis
            if analysis_depth == "deep":
                analysis["performance_data"] = await self._get_performance_data(url)
                analysis["security_data"] = await self._get_security_data(url)
            
        except Exception as e:
            self.logger.warning(f"Error during page analysis: {e}")
            # Continue with partial data
        
        return analysis

    async def _calculate_category_score(
        self, 
        category: ScoreCategory, 
        page_analysis: Dict[str, Any], 
        analysis_depth: str
    ) -> CategoryScore:
        """Calculate score for a specific category"""
        factors = []
        total_score = 0
        max_possible_score = 0
        
        # Get factors for this category
        category_factors = self.factor_weights.get(category, {})
        
        for factor_name, weight in category_factors.items():
            try:
                # Calculate individual factor score
                factor_score = await self._calculate_factor_score(
                    factor_name, category, page_analysis, analysis_depth
                )
                factors.append(factor_score)
                total_score += factor_score.weighted_score
                max_possible_score += factor_score.max_score * weight
                
            except Exception as e:
                self.logger.warning(f"Error calculating factor {factor_name}: {e}")
                # Add failed factor with zero score
                failed_factor = FactorScore(
                    factor_name=factor_name,
                    score=0,
                    weight=weight,
                    weighted_score=0,
                    max_score=10,
                    details={"error": str(e)},
                    recommendations=["Fix technical issues to enable analysis"],
                    status="failed"
                )
                factors.append(failed_factor)
        
        # Create category score
        category_score = CategoryScore(
            category=category,
            total_score=total_score,
            max_possible_score=max_possible_score,
            percentage=0,  # Will be calculated in __post_init__
            level=ScoreLevel.AVERAGE,  # Will be calculated in __post_init__
            factors=factors,
            weight=self.category_weights.get(category, 0.01)
        )
        
        return category_score

    async def _calculate_factor_score(
        self, 
        factor_name: str, 
        category: ScoreCategory, 
        page_analysis: Dict[str, Any], 
        analysis_depth: str
    ) -> FactorScore:
        """Calculate score for an individual factor"""
        # This is a placeholder - the actual implementation will be in the next part
        # For now, return a basic score
        score = 7.0  # Default score
        max_score = 10.0
        weight = self.factor_weights.get(category, {}).get(factor_name, 1.0)
        
        return FactorScore(
            factor_name=factor_name,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            max_score=max_score,
            details={"status": "placeholder"},
            recommendations=["Implement detailed factor analysis"]
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # If netloc is empty (no scheme), fall back to path-based extraction
            if parsed.netloc:
                return parsed.netloc
            else:
                # Extract domain from path
                path_parts = parsed.path.split('/')
                return path_parts[0] if path_parts[0] else url
        except Exception:
            # Fallback: extract domain from URL
            if url.startswith('http'):
                return url.split('/')[2] if len(url.split('/')) > 2 else url.split('/')[0]
            else:
                # For URLs without protocol, split by '/' and take first part
                parts = url.split('/')
                return parts[0] if parts[0] else url

    def _generate_summary(self, category_scores: Dict[ScoreCategory, CategoryScore], page_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of SEO analysis"""
        return {
            "total_categories": len(category_scores),
            "categories_analyzed": [cat.value for cat in category_scores.keys()],
            "score_distribution": {
                cat.value: {
                    "score": score.total_score,
                    "percentage": score.percentage,
                    "level": score.level.value
                }
                for cat, score in category_scores.items()
            },
            "analysis_depth": page_analysis.get("analysis_depth", "basic"),
            "analysis_timestamp": page_analysis.get("timestamp", datetime.now()).isoformat()
        }

    def _generate_recommendations(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> List[str]:
        """Generate actionable recommendations based on scores"""
        recommendations = []
        
        for category, score in category_scores.items():
            if score.level in [ScoreLevel.POOR, ScoreLevel.CRITICAL]:
                recommendations.append(f"Focus on improving {category.value.replace('_', ' ')} - current score: {score.percentage:.1f}%")
            
            # Add specific factor recommendations
            for factor in score.factors:
                if factor.score < 5.0 and factor.recommendations:
                    recommendations.extend(factor.recommendations)
        
        return list(set(recommendations))  # Remove duplicates

    def _identify_critical_issues(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> List[str]:
        """Identify critical issues that need immediate attention"""
        critical_issues = []
        
        for category, score in category_scores.items():
            if score.level == ScoreLevel.CRITICAL:
                critical_issues.append(f"Critical issues in {category.value.replace('_', ' ')}")
            
            # Check individual factors
            for factor in score.factors:
                if factor.score < 3.0:
                    critical_issues.append(f"Critical issue: {factor.factor_name} in {category.value}")
        
        return critical_issues

    def _identify_improvement_opportunities(self, category_scores: Dict[ScoreCategory, CategoryScore]) -> List[str]:
        """Identify areas with high improvement potential"""
        opportunities = []
        
        for category, score in category_scores.items():
            if score.level in [ScoreLevel.AVERAGE, ScoreLevel.GOOD]:
                opportunities.append(f"Improve {category.value.replace('_', ' ')} from {score.level.value} to excellent")
            
            # Check individual factors
            for factor in score.factors:
                if 5.0 <= factor.score < 8.0:
                    opportunities.append(f"Optimize {factor.factor_name} in {category.value}")
        
        return opportunities

    async def get_scoring_statistics(self) -> Dict[str, Any]:
        """Get statistics about scoring calculations"""
        return {
            "total_categories": len(ScoreCategory),
            "total_factors": sum(len(weights) for weights in self.factor_weights.values()),
            "category_weights": {cat.value: weight for cat, weight in self.category_weights.items()},
            "scoring_config": self.scoring_config
        }

async def create_seo_score_calculator() -> SEOScoreCalculator:
    """Create and initialize a new SEO score calculator instance"""
    calculator = SEOScoreCalculator()
    await calculator.initialize()
    return calculator
