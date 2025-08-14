"""
Keyword Analysis Service

This module provides comprehensive keyword analysis capabilities:
- Keyword difficulty scoring and analysis
- Search volume analysis and trends
- CPC (Cost Per Click) analysis
- Keyword opportunity scoring
- Competition analysis
- Seasonal trend detection
- Long-tail keyword identification
- Commercial intent analysis
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict
import re

from app.services.redis_service import RedisService
from app.services.seo_service import SEOService
from app.services.serp_scraper import SERPScraper

logger = logging.getLogger(__name__)

@dataclass
class KeywordMetrics:
    """Comprehensive keyword metrics"""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    keyword_difficulty: Optional[float] = None
    competition_index: Optional[float] = None
    opportunity_score: Optional[float] = None
    commercial_intent: Optional[float] = None
    seasonal_trend: Optional[str] = None
    long_tail_score: Optional[float] = None
    serp_features_count: Optional[int] = None
    competitor_count: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class KeywordOpportunity:
    """Keyword opportunity analysis"""
    keyword: str
    opportunity_score: float
    volume_potential: float
    difficulty_level: str
    competition_level: str
    commercial_potential: float
    recommended_actions: List[str]
    estimated_roi: Optional[float] = None
    time_to_rank: Optional[str] = None

@dataclass
class CompetitionAnalysis:
    """Competition analysis for keywords"""
    keyword: str
    competitor_domains: List[str]
    avg_domain_authority: Optional[float] = None
    content_gaps: List[str]
    ranking_difficulty: str
    content_opportunities: List[str]
    backlink_requirements: Optional[int] = None

@dataclass
class SeasonalTrend:
    """Seasonal trend analysis"""
    keyword: str
    trend_pattern: str  # increasing, decreasing, seasonal, stable
    peak_months: List[int]
    low_months: List[int]
    seasonality_score: float
    trend_direction: str  # up, down, stable
    confidence: float

class KeywordAnalyzer:
    """Advanced keyword analysis service"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.seo_service = SEOService()
        self.serp_scraper = SERPScraper()
        
        # Difficulty scoring weights
        self.difficulty_weights = {
            "search_volume": 0.25,
            "cpc": 0.20,
            "competitor_count": 0.30,
            "serp_features": 0.15,
            "domain_authority": 0.10
        }
        
        # Opportunity scoring weights
        self.opportunity_weights = {
            "volume_potential": 0.35,
            "difficulty_ease": 0.25,
            "commercial_intent": 0.20,
            "competition_gaps": 0.20
        }
        
        # Commercial intent indicators
        self.commercial_indicators = [
            "buy", "purchase", "order", "shop", "price", "cost", "deal", "offer",
            "discount", "coupon", "sale", "best", "top", "review", "compare",
            "cheap", "affordable", "budget", "value", "quality", "premium"
        ]
        
        # Seasonal patterns
        self.seasonal_patterns = {
            "christmas": [11, 12],
            "summer": [6, 7, 8],
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "fall": [9, 10, 11],
            "back_to_school": [8, 9],
            "holiday": [11, 12, 1]
        }
        
        # Caching configuration
        self.cache_ttl = 3600 * 24  # 24 hours
    
    async def _get_cached_analysis(self, keyword: str, analysis_type: str) -> Optional[Any]:
        """Retrieve cached analysis from Redis"""
        cache_key = f"keyword_analysis:{analysis_type}:{hashlib.md5(keyword.encode()).hexdigest()}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached analysis for {keyword}: {e}")
        
        return None
    
    async def _cache_analysis(self, keyword: str, analysis_type: str, data: Any) -> bool:
        """Cache analysis results in Redis"""
        cache_key = f"keyword_analysis:{analysis_type}:{hashlib.md5(keyword.encode()).hexdigest()}"
        
        try:
            await self.redis_service.set(
                cache_key,
                json.dumps(data, default=str),
                expire=self.cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache analysis for {keyword}: {e}")
            return False
    
    async def analyze_keyword_difficulty(self, keyword: str, country: str = "us") -> float:
        """
        Calculate comprehensive keyword difficulty score
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            Difficulty score (0-100, higher = more difficult)
        """
        # Check cache first
        cached_score = await self._get_cached_analysis(keyword, "difficulty")
        if cached_score is not None:
            return cached_score
        
        try:
            difficulty_score = 0.0
            factors = 0
            
            # Get SEMrush data
            keyword_data = await self.seo_service.get_semrush_keyword_data(keyword, country)
            if keyword_data:
                # Search volume factor (higher volume = higher difficulty)
                if keyword_data.search_volume:
                    volume_score = min(keyword_data.search_volume / 10000, 1.0) * 100
                    difficulty_score += volume_score * self.difficulty_weights["search_volume"]
                    factors += 1
                
                # CPC factor (higher CPC = higher difficulty)
                if keyword_data.cpc:
                    cpc_score = min(keyword_data.cpc / 5.0, 1.0) * 100
                    difficulty_score += cpc_score * self.difficulty_weights["cpc"]
                    factors += 1
                
                # Keyword difficulty from SEMrush
                if keyword_data.keyword_difficulty:
                    difficulty_score += keyword_data.keyword_difficulty * self.difficulty_weights["domain_authority"]
                    factors += 1
            
            # Get SERP data for additional factors
            serp_data = await self.serp_scraper.scrape_serp_data(keyword, country)
            if serp_data:
                # Competitor count factor
                competitor_count = len(serp_data.get("results", []))
                if competitor_count > 0:
                    competitor_score = min(competitor_count / 20, 1.0) * 100
                    difficulty_score += competitor_score * self.difficulty_weights["competitor_count"]
                    factors += 1
                
                # SERP features factor
                serp_features = 0
                if serp_data.get("featured_snippet"):
                    serp_features += 1
                if serp_data.get("people_also_ask"):
                    serp_features += len(serp_data["people_also_ask"])
                if serp_data.get("knowledge_panel"):
                    serp_features += 1
                
                if serp_features > 0:
                    features_score = min(serp_features / 5, 1.0) * 100
                    difficulty_score += features_score * self.difficulty_weights["serp_features"]
                    factors += 1
            
            # Calculate final score
            if factors > 0:
                final_score = difficulty_score / factors
            else:
                final_score = 50.0  # Default medium difficulty
            
            # Cache the result
            await self._cache_analysis(keyword, "difficulty", final_score)
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Failed to analyze keyword difficulty for '{keyword}': {e}")
            return 50.0  # Default medium difficulty
    
    async def analyze_search_volume(self, keyword: str, country: str = "us") -> Dict[str, Any]:
        """
        Analyze search volume patterns and trends
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            Search volume analysis results
        """
        # Check cache first
        cached_analysis = await self._get_cached_analysis(keyword, "volume_analysis")
        if cached_analysis:
            return cached_analysis
        
        try:
            analysis = {
                "keyword": keyword,
                "current_volume": None,
                "volume_category": "unknown",
                "trend_direction": "stable",
                "seasonal_pattern": None,
                "volume_potential": "medium",
                "recommendations": []
            }
            
            # Get SEMrush data
            keyword_data = await self.seo_service.get_semrush_keyword_data(keyword, country)
            if keyword_data and keyword_data.search_volume:
                analysis["current_volume"] = keyword_data.search_volume
                
                # Categorize volume
                if keyword_data.search_volume >= 10000:
                    analysis["volume_category"] = "very_high"
                    analysis["volume_potential"] = "very_high"
                elif keyword_data.search_volume >= 1000:
                    analysis["volume_category"] = "high"
                    analysis["volume_potential"] = "high"
                elif keyword_data.search_volume >= 100:
                    analysis["volume_category"] = "medium"
                    analysis["volume_potential"] = "medium"
                elif keyword_data.search_volume >= 10:
                    analysis["volume_category"] = "low"
                    analysis["volume_potential"] = "low"
                else:
                    analysis["volume_category"] = "very_low"
                    analysis["volume_potential"] = "very_low"
                
                # Generate recommendations
                if keyword_data.search_volume < 100:
                    analysis["recommendations"].append("Consider targeting broader keyword variations")
                    analysis["recommendations"].append("Focus on long-tail keywords with higher volume")
                elif keyword_data.search_volume > 5000:
                    analysis["recommendations"].append("High volume keyword - ensure strong content strategy")
                    analysis["recommendations"].append("Consider creating comprehensive content hub")
                
                # Detect seasonal patterns
                seasonal_pattern = self._detect_seasonal_pattern(keyword)
                if seasonal_pattern:
                    analysis["seasonal_pattern"] = seasonal_pattern
                    analysis["recommendations"].append(f"Seasonal keyword - optimize content for {seasonal_pattern} months")
            
            # Cache the analysis
            await self._cache_analysis(keyword, "volume_analysis", analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze search volume for '{keyword}': {e}")
            return {
                "keyword": keyword,
                "error": str(e)
            }
    
    def _detect_seasonal_pattern(self, keyword: str) -> Optional[str]:
        """Detect seasonal patterns in keywords"""
        keyword_lower = keyword.lower()
        
        for season, months in self.seasonal_patterns.items():
            if season in keyword_lower:
                return season
        
        # Check for month-related keywords
        month_keywords = ["january", "february", "march", "april", "may", "june",
                         "july", "august", "september", "october", "november", "december"]
        
        for month in month_keywords:
            if month in keyword_lower:
                return "monthly"
        
        return None
    
    async def analyze_cpc_trends(self, keyword: str, country: str = "us") -> Dict[str, Any]:
        """
        Analyze CPC trends and commercial potential
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            CPC analysis results
        """
        # Check cache first
        cached_analysis = await self._get_cached_analysis(keyword, "cpc_analysis")
        if cached_analysis:
            return cached_analysis
        
        try:
            analysis = {
                "keyword": keyword,
                "current_cpc": None,
                "cpc_category": "unknown",
                "commercial_intent": "low",
                "ad_competition": "low",
                "roi_potential": "low",
                "recommendations": []
            }
            
            # Get SEMrush data
            keyword_data = await self.seo_service.get_semrush_keyword_data(keyword, country)
            if keyword_data and keyword_data.cpc:
                analysis["current_cpc"] = keyword_data.cpc
                
                # Categorize CPC
                if keyword_data.cpc >= 5.0:
                    analysis["cpc_category"] = "very_high"
                    analysis["commercial_intent"] = "very_high"
                    analysis["ad_competition"] = "very_high"
                    analysis["roi_potential"] = "very_high"
                elif keyword_data.cpc >= 2.0:
                    analysis["cpc_category"] = "high"
                    analysis["commercial_intent"] = "high"
                    analysis["ad_competition"] = "high"
                    analysis["roi_potential"] = "high"
                elif keyword_data.cpc >= 1.0:
                    analysis["cpc_category"] = "medium"
                    analysis["commercial_intent"] = "medium"
                    analysis["ad_competition"] = "medium"
                    analysis["roi_potential"] = "medium"
                elif keyword_data.cpc >= 0.5:
                    analysis["cpc_category"] = "low"
                    analysis["commercial_intent"] = "low"
                    analysis["ad_competition"] = "low"
                    analysis["roi_potential"] = "low"
                else:
                    analysis["cpc_category"] = "very_low"
                    analysis["commercial_intent"] = "very_low"
                    analysis["ad_competition"] = "very_low"
                    analysis["roi_potential"] = "very_low"
                
                # Generate recommendations
                if keyword_data.cpc > 3.0:
                    analysis["recommendations"].append("High CPC indicates strong commercial intent")
                    analysis["recommendations"].append("Consider PPC campaigns for immediate traffic")
                    analysis["recommendations"].append("Focus on conversion optimization")
                elif keyword_data.cpc < 0.5:
                    analysis["recommendations"].append("Low CPC suggests informational intent")
                    analysis["recommendations"].append("Focus on organic content strategy")
                    analysis["recommendations"].append("Consider educational content approach")
            
            # Cache the analysis
            await self._cache_analysis(keyword, "cpc_analysis", analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze CPC trends for '{keyword}': {e}")
            return {
                "keyword": keyword,
                "error": str(e)
            }
    
    async def calculate_opportunity_score(self, keyword: str, country: str = "us") -> KeywordOpportunity:
        """
        Calculate comprehensive keyword opportunity score
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            Keyword opportunity analysis
        """
        try:
            # Gather all analysis data
            difficulty_score = await self.analyze_keyword_difficulty(keyword, country)
            volume_analysis = await self.analyze_search_volume(keyword, country)
            cpc_analysis = await self.analyze_cpc_trends(keyword, country)
            
            # Calculate opportunity components
            volume_potential = self._calculate_volume_potential(volume_analysis)
            difficulty_ease = 100 - difficulty_score  # Lower difficulty = higher ease
            commercial_intent = self._calculate_commercial_intent(keyword, cpc_analysis)
            competition_gaps = await self._analyze_competition_gaps(keyword, country)
            
            # Calculate weighted opportunity score
            opportunity_score = (
                volume_potential * self.opportunity_weights["volume_potential"] +
                difficulty_ease * self.opportunity_weights["difficulty_ease"] +
                commercial_intent * self.opportunity_weights["commercial_intent"] +
                competition_gaps * self.opportunity_weights["competition_gaps"]
            )
            
            # Determine difficulty and competition levels
            difficulty_level = self._categorize_difficulty(difficulty_score)
            competition_level = self._categorize_competition(competition_gaps)
            
            # Generate recommendations
            recommendations = self._generate_opportunity_recommendations(
                opportunity_score, volume_analysis, cpc_analysis, difficulty_score
            )
            
            # Estimate ROI and time to rank
            estimated_roi = self._estimate_roi(volume_analysis, cpc_analysis, difficulty_score)
            time_to_rank = self._estimate_time_to_rank(difficulty_score, competition_gaps)
            
            opportunity = KeywordOpportunity(
                keyword=keyword,
                opportunity_score=round(opportunity_score, 2),
                volume_potential=volume_potential,
                difficulty_level=difficulty_level,
                competition_level=competition_level,
                commercial_potential=commercial_intent,
                recommended_actions=recommendations,
                estimated_roi=estimated_roi,
                time_to_rank=time_to_rank
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to calculate opportunity score for '{keyword}': {e}")
            # Return minimal opportunity data on failure
            return KeywordOpportunity(
                keyword=keyword,
                opportunity_score=0.0,
                volume_potential=0.0,
                difficulty_level="unknown",
                competition_level="unknown",
                commercial_potential=0.0,
                recommended_actions=["Analysis failed - please try again"]
            )
    
    def _calculate_volume_potential(self, volume_analysis: Dict[str, Any]) -> float:
        """Calculate volume potential score"""
        volume_category = volume_analysis.get("volume_category", "unknown")
        
        volume_scores = {
            "very_high": 100,
            "high": 80,
            "medium": 60,
            "low": 40,
            "very_low": 20,
            "unknown": 50
        }
        
        return volume_scores.get(volume_category, 50)
    
    def _calculate_commercial_intent(self, keyword: str, cpc_analysis: Dict[str, Any]) -> float:
        """Calculate commercial intent score"""
        # Base score from CPC analysis
        commercial_intent = cpc_analysis.get("commercial_intent", "low")
        intent_scores = {
            "very_high": 100,
            "high": 80,
            "medium": 60,
            "low": 40,
            "very_low": 20
        }
        
        base_score = intent_scores.get(commercial_intent, 40)
        
        # Additional scoring based on keyword patterns
        keyword_lower = keyword.lower()
        commercial_indicators = sum(1 for indicator in self.commercial_indicators if indicator in keyword_lower)
        
        # Boost score for commercial indicators
        if commercial_indicators > 0:
            base_score = min(100, base_score + (commercial_indicators * 10))
        
        return base_score
    
    async def _analyze_competition_gaps(self, keyword: str, country: str) -> float:
        """Analyze competition gaps and opportunities"""
        try:
            # Get SERP data
            serp_data = await self.serp_scraper.scrape_serp_data(keyword, country)
            
            if not serp_data or not serp_data.get("results"):
                return 50.0  # Default score
            
            results = serp_data["results"]
            
            # Analyze content quality gaps
            content_gaps = 0
            total_results = len(results)
            
            for result in results[:5]:  # Analyze top 5 results
                # Simple content gap detection
                if len(result.get("snippet", "")) < 100:
                    content_gaps += 1
                if not result.get("title") or len(result.get("title", "")) < 20:
                    content_gaps += 1
            
            # Calculate gap score (higher gaps = higher opportunity)
            gap_score = (content_gaps / total_results) * 100 if total_results > 0 else 50
            
            # Boost score for featured snippets and SERP features
            if serp_data.get("featured_snippet"):
                gap_score = min(100, gap_score + 20)
            if serp_data.get("people_also_ask"):
                gap_score = min(100, gap_score + 15)
            
            return gap_score
            
        except Exception as e:
            logger.warning(f"Failed to analyze competition gaps for '{keyword}': {e}")
            return 50.0
    
    def _categorize_difficulty(self, difficulty_score: float) -> str:
        """Categorize difficulty level"""
        if difficulty_score >= 80:
            return "very_high"
        elif difficulty_score >= 60:
            return "high"
        elif difficulty_score >= 40:
            return "medium"
        elif difficulty_score >= 20:
            return "low"
        else:
            return "very_low"
    
    def _categorize_competition(self, competition_score: float) -> str:
        """Categorize competition level"""
        if competition_score >= 80:
            return "very_low"  # High opportunity
        elif competition_score >= 60:
            return "low"
        elif competition_score >= 40:
            return "medium"
        elif competition_score >= 20:
            return "high"
        else:
            return "very_high"  # Low opportunity
    
    def _generate_opportunity_recommendations(self, opportunity_score: float,
                                           volume_analysis: Dict[str, Any],
                                           cpc_analysis: Dict[str, Any],
                                           difficulty_score: float) -> List[str]:
        """Generate actionable recommendations based on opportunity analysis"""
        recommendations = []
        
        # High opportunity recommendations
        if opportunity_score >= 80:
            recommendations.append("Excellent opportunity - prioritize this keyword")
            recommendations.append("Create comprehensive, high-quality content")
            recommendations.append("Consider building internal link structure")
        elif opportunity_score >= 60:
            recommendations.append("Good opportunity - worth pursuing")
            recommendations.append("Focus on content quality and user experience")
            recommendations.append("Build relevant backlinks")
        elif opportunity_score >= 40:
            recommendations.append("Moderate opportunity - evaluate carefully")
            recommendations.append("Consider long-tail variations")
            recommendations.append("Focus on niche content")
        else:
            recommendations.append("Low opportunity - consider alternatives")
            recommendations.append("Look for related keywords with better potential")
            recommendations.append("Focus on less competitive terms")
        
        # Volume-based recommendations
        volume_recs = volume_analysis.get("recommendations", [])
        recommendations.extend(volume_recs[:2])  # Limit to top 2
        
        # CPC-based recommendations
        cpc_recs = cpc_analysis.get("recommendations", [])
        recommendations.extend(cpc_recs[:2])  # Limit to top 2
        
        # Difficulty-based recommendations
        if difficulty_score > 70:
            recommendations.append("High difficulty - consider long-tail variations")
        elif difficulty_score < 30:
            recommendations.append("Low difficulty - good chance for quick wins")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _estimate_roi(self, volume_analysis: Dict[str, Any], 
                      cpc_analysis: Dict[str, Any], 
                      difficulty_score: float) -> Optional[float]:
        """Estimate potential ROI for the keyword"""
        try:
            current_volume = volume_analysis.get("current_volume", 0)
            current_cpc = cpc_analysis.get("current_cpc", 0)
            
            if not current_volume or not current_cpc:
                return None
            
            # Simple ROI estimation
            # Assume 1% click-through rate and 5% conversion rate
            estimated_clicks = current_volume * 0.01
            estimated_conversions = estimated_clicks * 0.05
            
            # Assume average order value of $50 (adjustable)
            avg_order_value = 50.0
            
            # Calculate potential revenue
            potential_revenue = estimated_conversions * avg_order_value
            
            # Calculate potential ad spend
            potential_ad_spend = estimated_clicks * current_cpc
            
            # Calculate ROI
            if potential_ad_spend > 0:
                roi = ((potential_revenue - potential_ad_spend) / potential_ad_spend) * 100
                return round(roi, 2)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to estimate ROI: {e}")
            return None
    
    def _estimate_time_to_rank(self, difficulty_score: float, competition_gaps: float) -> str:
        """Estimate time to rank for the keyword"""
        # Simple time estimation based on difficulty and competition
        if difficulty_score < 30 and competition_gaps > 70:
            return "1-3 months"
        elif difficulty_score < 50 and competition_gaps > 50:
            return "3-6 months"
        elif difficulty_score < 70 and competition_gaps > 30:
            return "6-12 months"
        else:
            return "12+ months"
    
    async def analyze_long_tail_keywords(self, seed_keyword: str, 
                                       country: str = "us") -> List[Dict[str, Any]]:
        """
        Analyze long-tail keyword variations
        
        Args:
            seed_keyword: Base keyword to expand
            country: Country for localized analysis
        
        Returns:
            List of long-tail keyword analyses
        """
        try:
            # Get keyword suggestions
            suggestions = await self.seo_service.get_keyword_suggestions(seed_keyword, 30)
            
            long_tail_analyses = []
            
            for suggestion in suggestions:
                try:
                    # Analyze each suggestion
                    difficulty = await self.analyze_keyword_difficulty(suggestion, country)
                    volume_analysis = await self.analyze_search_volume(suggestion, country)
                    cpc_analysis = await self.analyze_cpc_trends(suggestion, country)
                    
                    # Calculate long-tail score
                    long_tail_score = self._calculate_long_tail_score(suggestion, seed_keyword)
                    
                    analysis = {
                        "keyword": suggestion,
                        "long_tail_score": long_tail_score,
                        "difficulty": difficulty,
                        "search_volume": volume_analysis.get("current_volume"),
                        "cpc": cpc_analysis.get("current_cpc"),
                        "opportunity": "high" if long_tail_score > 70 else "medium" if long_tail_score > 50 else "low"
                    }
                    
                    long_tail_analyses.append(analysis)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze long-tail keyword '{suggestion}': {e}")
                    continue
            
            # Sort by long-tail score
            long_tail_analyses.sort(key=lambda x: x.get("long_tail_score", 0), reverse=True)
            
            return long_tail_analyses[:20]  # Return top 20
            
        except Exception as e:
            logger.error(f"Failed to analyze long-tail keywords for '{seed_keyword}': {e}")
            return []
    
    def _calculate_long_tail_score(self, keyword: str, seed_keyword: str) -> float:
        """Calculate long-tail keyword score"""
        # Long-tail keywords are typically longer and more specific
        word_count = len(keyword.split())
        seed_word_count = len(seed_keyword.split())
        
        # Base score from word count difference
        word_score = min((word_count - seed_word_count) * 20, 60)
        
        # Additional scoring for specificity
        specificity_indicators = ["how", "what", "why", "when", "where", "best", "top", "guide", "tutorial"]
        specificity_score = sum(10 for indicator in specificity_indicators if indicator in keyword.lower())
        
        # Total score
        total_score = word_score + specificity_score
        
        return min(total_score, 100)
    
    async def get_keyword_insights(self, keyword: str, country: str = "us") -> Dict[str, Any]:
        """
        Get comprehensive keyword insights
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            Comprehensive keyword insights
        """
        try:
            insights = {
                "keyword": keyword,
                "analysis_timestamp": datetime.now().isoformat(),
                "metrics": {},
                "opportunity": {},
                "recommendations": [],
                "long_tail_variations": []
            }
            
            # Get all analysis data
            difficulty = await self.analyze_keyword_difficulty(keyword, country)
            volume_analysis = await self.analyze_search_volume(keyword, country)
            cpc_analysis = await self.analyze_cpc_trends(keyword, country)
            opportunity = await self.calculate_opportunity_score(keyword, country)
            long_tail = await self.analyze_long_tail_keywords(keyword, country)
            
            # Compile metrics
            insights["metrics"] = {
                "difficulty_score": difficulty,
                "search_volume": volume_analysis.get("current_volume"),
                "cpc": cpc_analysis.get("current_cpc"),
                "volume_category": volume_analysis.get("volume_category"),
                "commercial_intent": cpc_analysis.get("commercial_intent")
            }
            
            # Compile opportunity data
            insights["opportunity"] = {
                "opportunity_score": opportunity.opportunity_score,
                "difficulty_level": opportunity.difficulty_level,
                "competition_level": opportunity.competition_level,
                "estimated_roi": opportunity.estimated_roi,
                "time_to_rank": opportunity.time_to_rank
            }
            
            # Compile recommendations
            insights["recommendations"] = opportunity.recommended_actions
            
            # Add long-tail variations
            insights["long_tail_variations"] = long_tail[:10]  # Top 10
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get keyword insights for '{keyword}': {e}")
            return {
                "keyword": keyword,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    async def export_keyword_analysis(self, keywords: List[str], 
                                    country: str = "us", 
                                    format: str = "json") -> str:
        """
        Export comprehensive keyword analysis for multiple keywords
        
        Args:
            keywords: List of keywords to analyze
            country: Country for localized analysis
            format: Export format (json, csv)
        
        Returns:
            Exported analysis data
        """
        try:
            all_analyses = []
            
            for keyword in keywords:
                try:
                    analysis = await self.get_keyword_insights(keyword, country)
                    all_analyses.append(analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze keyword '{keyword}': {e}")
                    all_analyses.append({
                        "keyword": keyword,
                        "error": str(e),
                        "analysis_timestamp": datetime.now().isoformat()
                    })
            
            if format.lower() == "json":
                return json.dumps(all_analyses, indent=2, default=str)
                
            elif format.lower() == "csv":
                # Create CSV with key metrics
                csv_lines = ["keyword,difficulty_score,search_volume,cpc,opportunity_score,recommendations"]
                
                for analysis in all_analyses:
                    if "error" not in analysis:
                        metrics = analysis.get("metrics", {})
                        opportunity = analysis.get("opportunity", {})
                        recommendations = "; ".join(analysis.get("recommendations", []))
                        
                        csv_lines.append(f"{analysis['keyword']},{metrics.get('difficulty_score', '')},{metrics.get('search_volume', '')},{metrics.get('cpc', '')},{opportunity.get('opportunity_score', '')},\"{recommendations}\"")
                    else:
                        csv_lines.append(f"{analysis['keyword']},error,error,error,error,{analysis.get('error', '')}")
                
                return "\n".join(csv_lines)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export keyword analysis: {e}")
            return json.dumps({"error": str(e)})