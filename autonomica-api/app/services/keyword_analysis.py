"""
Keyword Analysis Module
Implements comprehensive keyword analysis including difficulty, search volume, and relevance scoring
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class KeywordIntent(Enum):
    """Keyword search intent classification"""
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMMERCIAL = "commercial"


class KeywordType(Enum):
    """Keyword type classification"""
    SHORT_TAIL = "short_tail"
    MEDIUM_TAIL = "medium_tail"
    LONG_TAIL = "long_tail"
    BRANDED = "branded"
    NON_BRANDED = "non_branded"


@dataclass
class KeywordMetrics:
    """Comprehensive keyword analysis metrics"""
    keyword: str
    search_volume: int
    cpc: float
    keyword_difficulty: int
    competition: float
    relevance_score: float
    opportunity_score: float
    intent: KeywordIntent
    keyword_type: KeywordType
    seasonality_factor: float
    trend_direction: str
    estimated_clicks: int
    estimated_cost: float
    roi_potential: float


class KeywordAnalyzer:
    """Advanced keyword analysis and scoring engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Scoring weights for opportunity calculation
        self.weights = {
            'search_volume': 0.3,
            'cpc': 0.25,
            'difficulty': 0.25,
            'competition': 0.2
        }
        
        # Intent classification patterns
        self.intent_patterns = {
            'informational': [
                'what', 'how', 'why', 'when', 'where', 'guide', 'tutorial', 
                'learn', 'tips', 'examples', 'definition', 'explanation'
            ],
            'navigational': [
                'login', 'sign in', 'homepage', 'contact', 'about', 'support',
                'help', 'faq', 'sitemap', 'directory'
            ],
            'transactional': [
                'buy', 'purchase', 'order', 'shop', 'cart', 'checkout',
                'price', 'cost', 'deal', 'offer', 'discount', 'sale'
            ],
            'commercial': [
                'best', 'top', 'review', 'compare', 'vs', 'alternative',
                'recommendation', 'rating', 'pros cons'
            ]
        }
    
    def analyze_keyword(self, keyword_data: Dict[str, Any]) -> KeywordMetrics:
        """Perform comprehensive keyword analysis"""
        try:
            keyword = keyword_data.get('keyword', '')
            
            # Extract basic metrics
            search_volume = keyword_data.get('search_volume', 0)
            cpc = keyword_data.get('cpc', 0.0)
            difficulty = keyword_data.get('keyword_difficulty', 50)
            competition = keyword_data.get('competition', 0.5)
            
            # Analyze keyword characteristics
            intent = self._classify_intent(keyword)
            keyword_type = self._classify_keyword_type(keyword)
            seasonality = self._calculate_seasonality_factor(keyword)
            trend = self._analyze_trend_direction(keyword_data)
            
            # Calculate derived metrics
            relevance_score = self._calculate_relevance_score(keyword_data)
            opportunity_score = self._calculate_opportunity_score(
                search_volume, cpc, difficulty, competition
            )
            estimated_clicks = self._estimate_monthly_clicks(search_volume, difficulty)
            estimated_cost = self._estimate_monthly_cost(estimated_clicks, cpc)
            roi_potential = self._calculate_roi_potential(cpc, difficulty, competition)
            
            return KeywordMetrics(
                keyword=keyword,
                search_volume=search_volume,
                cpc=cpc,
                keyword_difficulty=difficulty,
                competition=competition,
                relevance_score=relevance_score,
                opportunity_score=opportunity_score,
                intent=intent,
                keyword_type=keyword_type,
                seasonality_factor=seasonality,
                trend_direction=trend,
                estimated_clicks=estimated_clicks,
                estimated_cost=estimated_cost,
                roi_potential=roi_potential
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing keyword {keyword_data.get('keyword', 'unknown')}: {e}")
            raise
    
    def _classify_intent(self, keyword: str) -> KeywordIntent:
        """Classify keyword search intent"""
        keyword_lower = keyword.lower()
        
        # Check for intent patterns
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in keyword_lower for pattern in patterns):
                return KeywordIntent(intent)
        
        # Default to informational if no clear pattern
        return KeywordIntent.INFORMATIONAL
    
    def _classify_keyword_type(self, keyword: str) -> KeywordType:
        """Classify keyword by length and brand presence"""
        word_count = len(keyword.split())
        
        # Check for branded terms (common brand names)
        branded_terms = [
            'apple', 'google', 'microsoft', 'amazon', 'netflix', 'facebook',
            'twitter', 'instagram', 'linkedin', 'youtube', 'spotify'
        ]
        
        is_branded = any(brand in keyword.lower() for brand in branded_terms)
        
        if is_branded:
            return KeywordType.BRANDED
        elif word_count == 1:
            return KeywordType.SHORT_TAIL
        elif word_count <= 3:
            return KeywordType.MEDIUM_TAIL
        else:
            return KeywordType.LONG_TAIL
    
    def _calculate_seasonality_factor(self, keyword: str) -> float:
        """Calculate seasonality factor for keyword"""
        keyword_lower = keyword.lower()
        
        # Seasonal keywords
        seasonal_terms = {
            'christmas': 0.3, 'holiday': 0.4, 'summer': 0.6, 'winter': 0.6,
            'spring': 0.7, 'fall': 0.7, 'autumn': 0.7, 'valentine': 0.3,
            'halloween': 0.3, 'thanksgiving': 0.3, 'new year': 0.3,
            'back to school': 0.5, 'black friday': 0.2, 'cyber monday': 0.2
        }
        
        for term, factor in seasonal_terms.items():
            if term in keyword_lower:
                return factor
        
        # Default to 1.0 (no seasonality)
        return 1.0
    
    def _analyze_trend_direction(self, keyword_data: Dict[str, Any]) -> str:
        """Analyze keyword trend direction"""
        # This would typically use historical data
        # For now, return a placeholder
        return "stable"
    
    def _calculate_relevance_score(self, keyword_data: Dict[str, Any]) -> float:
        """Calculate keyword relevance score (0-100)"""
        try:
            # Base relevance factors
            search_volume = keyword_data.get('search_volume', 0)
            cpc = keyword_data.get('cpc', 0.0)
            difficulty = keyword_data.get('keyword_difficulty', 50)
            
            # Normalize values
            volume_score = min(search_volume / 10000, 1.0) * 40  # Max 40 points
            cpc_score = min(cpc / 10.0, 1.0) * 30  # Max 30 points
            difficulty_score = max(0, 30 - (difficulty / 100 * 30))  # Max 30 points
            
            total_score = volume_score + cpc_score + difficulty_score
            
            return round(total_score, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    def _calculate_opportunity_score(self, search_volume: int, cpc: float, 
                                   difficulty: int, competition: float) -> float:
        """Calculate keyword opportunity score (0-100)"""
        try:
            # Normalize inputs
            volume_score = min(search_volume / 10000, 1.0) * 100
            cpc_score = min(cpc / 10.0, 1.0) * 100
            difficulty_score = max(0, 100 - difficulty)  # Lower difficulty = higher score
            competition_score = max(0, 100 - (competition * 100))  # Lower competition = higher score
            
            # Apply weights
            weighted_score = (
                volume_score * self.weights['search_volume'] +
                cpc_score * self.weights['cpc'] +
                difficulty_score * self.weights['difficulty'] +
                competition_score * self.weights['competition']
            )
            
            return round(weighted_score, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity score: {e}")
            return 0.0
    
    def _estimate_monthly_clicks(self, search_volume: int, difficulty: int) -> int:
        """Estimate monthly organic clicks based on search volume and difficulty"""
        try:
            # Base click-through rate (CTR) assumptions
            base_ctr = 0.15  # 15% CTR for top 3 positions
            
            # Adjust CTR based on difficulty
            if difficulty <= 30:
                position_multiplier = 0.8  # High chance of top 3
            elif difficulty <= 60:
                position_multiplier = 0.5  # Medium chance of top 3
            else:
                position_multiplier = 0.2  # Low chance of top 3
            
            estimated_clicks = int(search_volume * base_ctr * position_multiplier)
            
            return max(estimated_clicks, 0)
            
        except Exception as e:
            self.logger.error(f"Error estimating monthly clicks: {e}")
            return 0
    
    def _estimate_monthly_cost(self, estimated_clicks: int, cpc: float) -> float:
        """Estimate monthly PPC cost for the keyword"""
        try:
            # Assume 80% of estimated organic clicks would come from PPC
            ppc_clicks = estimated_clicks * 0.8
            monthly_cost = ppc_clicks * cpc
            
            return round(monthly_cost, 2)
            
        except Exception as e:
            self.logger.error(f"Error estimating monthly cost: {e}")
            return 0.0
    
    def _calculate_roi_potential(self, cpc: float, difficulty: int, competition: float) -> float:
        """Calculate ROI potential score (0-100)"""
        try:
            # Higher CPC = higher revenue potential
            cpc_score = min(cpc / 5.0, 1.0) * 40
            
            # Lower difficulty = easier to rank = higher ROI
            difficulty_score = max(0, 40 - (difficulty / 100 * 40))
            
            # Lower competition = easier to win = higher ROI
            competition_score = max(0, 20 - (competition * 20))
            
            roi_score = cpc_score + difficulty_score + competition_score
            
            return round(roi_score, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI potential: {e}")
            return 0.0
    
    def analyze_keyword_batch(self, keywords_data: List[Dict[str, Any]]) -> List[KeywordMetrics]:
        """Analyze multiple keywords in batch"""
        results = []
        
        for keyword_data in keywords_data:
            try:
                metrics = self.analyze_keyword(keyword_data)
                results.append(metrics)
            except Exception as e:
                self.logger.warning(f"Skipping keyword analysis due to error: {e}")
                continue
        
        # Sort by opportunity score (descending)
        results.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return results
    
    def generate_keyword_insights(self, metrics: KeywordMetrics) -> Dict[str, Any]:
        """Generate actionable insights for a keyword"""
        insights = {
            'keyword': metrics.keyword,
            'summary': self._generate_summary(metrics),
            'recommendations': self._generate_recommendations(metrics),
            'risks': self._identify_risks(metrics),
            'opportunities': self._identify_opportunities(metrics),
            'action_items': self._generate_action_items(metrics)
        }
        
        return insights
    
    def _generate_summary(self, metrics: KeywordMetrics) -> str:
        """Generate keyword summary"""
        if metrics.opportunity_score >= 80:
            return f"High-opportunity keyword with strong search volume ({metrics.search_volume:,}) and reasonable difficulty ({metrics.keyword_difficulty}%)"
        elif metrics.opportunity_score >= 60:
            return f"Good opportunity keyword with moderate search volume and manageable difficulty"
        elif metrics.opportunity_score >= 40:
            return f"Moderate opportunity keyword that may require more effort to rank for"
        else:
            return f"Low-opportunity keyword due to high difficulty or low search volume"
    
    def _generate_recommendations(self, metrics: KeywordMetrics) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if metrics.intent == KeywordIntent.INFORMATIONAL:
            recommendations.append("Create comprehensive, educational content")
            recommendations.append("Include step-by-step guides and examples")
        
        if metrics.keyword_type == KeywordType.LONG_TAIL:
            recommendations.append("Focus on specific user intent and pain points")
            recommendations.append("Create detailed, in-depth content")
        
        if metrics.keyword_difficulty > 70:
            recommendations.append("Consider building more backlinks and authority")
            recommendations.append("Focus on long-tail variations with lower difficulty")
        
        if metrics.cpc > 5.0:
            recommendations.append("High commercial value - consider PPC campaigns")
            recommendations.append("Optimize landing pages for conversion")
        
        return recommendations
    
    def _identify_risks(self, metrics: KeywordMetrics) -> List[str]:
        """Identify potential risks"""
        risks = []
        
        if metrics.keyword_difficulty > 80:
            risks.append("Very high difficulty - may take significant time and resources")
        
        if metrics.competition > 0.8:
            risks.append("High competition - difficult to stand out")
        
        if metrics.search_volume < 100:
            risks.append("Low search volume - limited traffic potential")
        
        if metrics.seasonality_factor < 0.5:
            risks.append("Highly seasonal - traffic will fluctuate significantly")
        
        return risks
    
    def _identify_opportunities(self, metrics: KeywordMetrics) -> List[str]:
        """Identify opportunities"""
        opportunities = []
        
        if metrics.opportunity_score > 80:
            opportunities.append("Excellent opportunity for quick wins")
        
        if metrics.keyword_difficulty < 30:
            opportunities.append("Low difficulty - easier to rank quickly")
        
        if metrics.cpc > 3.0:
            opportunities.append("High commercial value - good for monetization")
        
        if metrics.intent == KeywordIntent.TRANSACTIONAL:
            opportunities.append("High conversion potential")
        
        return opportunities
    
    def _generate_action_items(self, metrics: KeywordMetrics) -> List[str]:
        """Generate specific action items"""
        actions = []
        
        if metrics.opportunity_score > 70:
            actions.append("Prioritize this keyword in content calendar")
            actions.append("Create comprehensive content targeting this keyword")
        
        if metrics.keyword_difficulty > 60:
            actions.append("Build backlinks from relevant, authoritative sites")
            actions.append("Create linkable assets (infographics, studies, etc.)")
        
        if metrics.intent == KeywordIntent.INFORMATIONAL:
            actions.append("Create educational content with clear structure")
            actions.append("Include FAQ sections and practical examples")
        
        if metrics.cpc > 2.0:
            actions.append("Set up PPC campaigns for immediate traffic")
            actions.append("Optimize landing pages for conversion")
        
        return actions
