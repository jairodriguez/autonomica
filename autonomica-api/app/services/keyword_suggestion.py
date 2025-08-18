"""
Keyword Suggestion Service Module
Provides intelligent keyword suggestions based on clustering and analysis
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path

from app.services.keyword_clustering import KeywordClusterer
from app.services.keyword_analysis import KeywordAnalyzer, KeywordMetrics, KeywordIntent, KeywordType
from app.services.seo_service import SEOService
from app.config.seo_config import seo_settings

logger = logging.getLogger(__name__)

class SuggestionType(Enum):
    """Types of keyword suggestions"""
    RELATED = "related"
    LONG_TAIL = "long_tail"
    QUESTION_BASED = "question_based"
    COMPETITOR = "competitor"
    TRENDING = "trending"
    SEASONAL = "seasonal"
    INTENT_BASED = "intent_based"
    DIFFICULTY_BASED = "difficulty_based"

class SuggestionSource(Enum):
    """Sources of keyword suggestions"""
    CLUSTERING = "clustering"
    SEMRUSH_API = "semrush_api"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TREND_ANALYSIS = "trend_analysis"
    USER_HISTORY = "user_history"
    AI_GENERATED = "ai_generated"

@dataclass
class KeywordSuggestion:
    """Individual keyword suggestion"""
    keyword: str
    suggestion_type: SuggestionType
    source: SuggestionSource
    relevance_score: float
    difficulty_score: Optional[float] = None
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[str] = None
    intent: Optional[KeywordIntent] = None
    keyword_type: Optional[KeywordType] = None
    related_keywords: List[str] = None
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.related_keywords is None:
            self.related_keywords = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SuggestionRequest:
    """Request for keyword suggestions"""
    seed_keywords: List[str]
    target_language: str = "en"
    suggestion_types: List[SuggestionType] = None
    max_suggestions: int = 50
    min_relevance_score: float = 0.3
    include_metrics: bool = True
    include_explanations: bool = True
    target_difficulty: Optional[str] = None  # "easy", "medium", "hard"
    target_intent: Optional[KeywordIntent] = None
    exclude_keywords: List[str] = None
    competitor_domains: List[str] = None

    def __post_init__(self):
        if self.suggestion_types is None:
            self.suggestion_types = [SuggestionType.RELATED, SuggestionType.LONG_TAIL]
        if self.exclude_keywords is None:
            self.exclude_keywords = []
        if self.competitor_domains is None:
            self.competitor_domains = []

@dataclass
class SuggestionResponse:
    """Response containing keyword suggestions"""
    request_id: str
    seed_keywords: List[str]
    suggestions: List[KeywordSuggestion]
    total_suggestions: int
    suggestion_breakdown: Dict[SuggestionType, int]
    processing_time: float
    metadata: Dict[str, Any] = None
    generated_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.generated_at is None:
            self.generated_at = datetime.now()

class KeywordSuggestionService:
    """Main service for generating intelligent keyword suggestions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.keyword_clusterer = None
        self.keyword_analyzer = None
        self.seo_service = None
        self.suggestion_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.max_cache_size = 1000
        self.enable_caching = True

    async def initialize(self):
        """Initialize all required services"""
        try:
            self.keyword_clusterer = KeywordClusterer()
            self.keyword_analyzer = KeywordAnalyzer()
            self.seo_service = SEOService()
            
            # Initialize services
            await self.keyword_clusterer.initialize()
            await self.keyword_analyzer.initialize()
            await self.seo_service.initialize()
            
            self.logger.info("KeywordSuggestionService initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize KeywordSuggestionService: {e}")
            raise

    async def generate_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Generate comprehensive keyword suggestions based on request"""
        start_time = datetime.now()
        request_id = self._generate_request_id(request)
        
        # Check cache first
        if self.enable_caching:
            cached_response = self._get_cached_suggestions(request_id)
            if cached_response:
                self.logger.info(f"Returning cached suggestions for request {request_id}")
                return cached_response

        try:
            self.logger.info(f"Generating suggestions for {len(request.seed_keywords)} seed keywords")
            
            # Collect suggestions from different sources
            all_suggestions = []
            
            # 1. Related keywords through clustering
            if SuggestionType.RELATED in request.suggestion_types:
                related_suggestions = await self._generate_related_suggestions(request)
                all_suggestions.extend(related_suggestions)
            
            # 2. Long-tail keyword variations
            if SuggestionType.LONG_TAIL in request.suggestion_types:
                long_tail_suggestions = await self._generate_long_tail_suggestions(request)
                all_suggestions.extend(long_tail_suggestions)
            
            # 3. Question-based keywords
            if SuggestionType.QUESTION_BASED in request.suggestion_types:
                question_suggestions = await self._generate_question_suggestions(request)
                all_suggestions.extend(question_suggestions)
            
            # 4. Competitor-based suggestions
            if SuggestionType.COMPETITOR in request.suggestion_types and request.competitor_domains:
                competitor_suggestions = await self._generate_competitor_suggestions(request)
                all_suggestions.extend(competitor_suggestions)
            
            # 5. Trending keywords
            if SuggestionType.TRENDING in request.suggestion_types:
                trending_suggestions = await self._generate_trending_suggestions(request)
                all_suggestions.extend(trending_suggestions)
            
            # 6. Intent-based suggestions
            if SuggestionType.INTENT_BASED in request.suggestion_types:
                intent_suggestions = await self._generate_intent_based_suggestions(request)
                all_suggestions.extend(intent_suggestions)
            
            # 7. Difficulty-based suggestions
            if SuggestionType.DIFFICULTY_BASED in request.suggestion_types:
                difficulty_suggestions = await self._generate_difficulty_based_suggestions(request)
                all_suggestions.extend(difficulty_suggestions)

            # Filter and rank suggestions
            filtered_suggestions = self._filter_suggestions(all_suggestions, request)
            ranked_suggestions = self._rank_suggestions(filtered_suggestions, request)
            
            # Limit to requested number
            final_suggestions = ranked_suggestions[:request.max_suggestions]
            
            # Generate response
            processing_time = (datetime.now() - start_time).total_seconds()
            response = SuggestionResponse(
                request_id=request_id,
                seed_keywords=request.seed_keywords,
                suggestions=final_suggestions,
                total_suggestions=len(final_suggestions),
                suggestion_breakdown=self._get_suggestion_breakdown(final_suggestions),
                processing_time=processing_time,
                metadata=self._generate_metadata(request, final_suggestions)
            )
            
            # Cache the response
            if self.enable_caching:
                self._cache_suggestions(request_id, response)
            
            self.logger.info(f"Generated {len(final_suggestions)} suggestions in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            raise

    async def _generate_related_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate related keywords using clustering"""
        suggestions = []
        
        try:
            # Use keyword clustering to find related terms
            for seed_keyword in request.seed_keywords:
                # Get related keywords through clustering
                related_keywords = await self.keyword_clusterer.find_keyword_opportunities(
                    [seed_keyword], 
                    max_keywords=20
                )
                
                for related in related_keywords:
                    if related['keyword'] not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=related['keyword'],
                            suggestion_type=SuggestionType.RELATED,
                            source=SuggestionSource.CLUSTERING,
                            relevance_score=related.get('similarity_score', 0.7),
                            explanation=f"Related to '{seed_keyword}' based on semantic similarity"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating related suggestions: {e}")
        
        return suggestions

    async def _generate_long_tail_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate long-tail keyword variations"""
        suggestions = []
        
        try:
            for seed_keyword in request.seed_keywords:
                # Generate long-tail variations
                variations = self._generate_long_tail_variations(seed_keyword)
                
                for variation in variations:
                    if variation not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=variation,
                            suggestion_type=SuggestionType.LONG_TAIL,
                            source=SuggestionSource.AI_GENERATED,
                            relevance_score=0.8,
                            explanation=f"Long-tail variation of '{seed_keyword}'"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating long-tail suggestions: {e}")
        
        return suggestions

    async def _generate_question_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate question-based keywords"""
        suggestions = []
        
        try:
            question_starters = [
                "what", "how", "why", "when", "where", "which", "who", "can", "do", "does",
                "best", "top", "guide", "tutorial", "tips", "examples", "vs", "difference"
            ]
            
            for seed_keyword in request.seed_keywords:
                for starter in question_starters:
                    question_keyword = f"{starter} {seed_keyword}"
                    if question_keyword not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=question_keyword,
                            suggestion_type=SuggestionType.QUESTION_BASED,
                            source=SuggestionSource.AI_GENERATED,
                            relevance_score=0.75,
                            explanation=f"Question-based variation of '{seed_keyword}'"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating question suggestions: {e}")
        
        return suggestions

    async def _generate_competitor_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate suggestions based on competitor analysis"""
        suggestions = []
        
        try:
            for domain in request.competitor_domains:
                # Get competitor keywords from SEO service
                competitor_keywords = await self.seo_service.get_competitor_keywords(
                    domain, 
                    max_keywords=20
                )
                
                for keyword_data in competitor_keywords:
                    if keyword_data['keyword'] not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=keyword_data['keyword'],
                            suggestion_type=SuggestionType.COMPETITOR,
                            source=SuggestionSource.COMPETITOR_ANALYSIS,
                            relevance_score=0.6,
                            search_volume=keyword_data.get('search_volume'),
                            cpc=keyword_data.get('cpc'),
                            competition=keyword_data.get('competition'),
                            explanation=f"Keyword used by competitor domain '{domain}'"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating competitor suggestions: {e}")
        
        return suggestions

    async def _generate_trending_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate trending keyword suggestions"""
        suggestions = []
        
        try:
            # Get trending keywords from SEO service
            trending_keywords = await self.seo_service.get_trending_keywords(
                request.target_language,
                max_keywords=30
            )
            
            for keyword_data in trending_keywords:
                if keyword_data['keyword'] not in request.exclude_keywords:
                    suggestion = KeywordSuggestion(
                        keyword=keyword_data['keyword'],
                        suggestion_type=SuggestionType.TRENDING,
                        source=SuggestionSource.TREND_ANALYSIS,
                        relevance_score=0.5,  # Lower relevance for trending
                        search_volume=keyword_data.get('search_volume'),
                        explanation=f"Trending keyword with {keyword_data.get('trend_percentage', 0)}% growth"
                    )
                    suggestions.append(suggestion)
                    
        except Exception as e:
            self.logger.warning(f"Error generating trending suggestions: {e}")
        
        return suggestions

    async def _generate_intent_based_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate intent-based keyword suggestions"""
        suggestions = []
        
        try:
            if request.target_intent:
                # Generate keywords with specific intent
                intent_keywords = await self.keyword_analyzer.generate_intent_keywords(
                    request.seed_keywords,
                    target_intent=request.target_intent,
                    max_keywords=20
                )
                
                for keyword_data in intent_keywords:
                    if keyword_data['keyword'] not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=keyword_data['keyword'],
                            suggestion_type=SuggestionType.INTENT_BASED,
                            source=SuggestionSource.AI_GENERATED,
                            relevance_score=0.8,
                            intent=keyword_data.get('intent'),
                            explanation=f"Intent-based keyword targeting '{request.target_intent.value}' intent"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating intent-based suggestions: {e}")
        
        return suggestions

    async def _generate_difficulty_based_suggestions(self, request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Generate difficulty-based keyword suggestions"""
        suggestions = []
        
        try:
            if request.target_difficulty:
                # Get keywords with specific difficulty level
                difficulty_keywords = await self.seo_service.get_keywords_by_difficulty(
                    request.target_difficulty,
                    max_keywords=20
                )
                
                for keyword_data in difficulty_keywords:
                    if keyword_data['keyword'] not in request.exclude_keywords:
                        suggestion = KeywordSuggestion(
                            keyword=keyword_data['keyword'],
                            suggestion_type=SuggestionType.DIFFICULTY_BASED,
                            source=SuggestionSource.SEMRUSH_API,
                            relevance_score=0.6,
                            difficulty_score=keyword_data.get('difficulty'),
                            search_volume=keyword_data.get('search_volume'),
                            explanation=f"Keyword with '{request.target_difficulty}' difficulty level"
                        )
                        suggestions.append(suggestion)
                        
        except Exception as e:
            self.logger.warning(f"Error generating difficulty-based suggestions: {e}")
        
        return suggestions

    def _generate_long_tail_variations(self, seed_keyword: str) -> List[str]:
        """Generate long-tail keyword variations"""
        variations = []
        
        # Common modifiers
        modifiers = [
            "best", "top", "guide", "how to", "tutorial", "examples", "tips", "tricks",
            "free", "online", "2024", "latest", "review", "comparison", "vs", "alternative",
            "software", "tool", "app", "website", "service", "company", "agency"
        ]
        
        # Generate variations
        for modifier in modifiers:
            variations.append(f"{modifier} {seed_keyword}")
            variations.append(f"{seed_keyword} {modifier}")
        
        # Add location-based variations
        locations = ["near me", "local", "online", "remote"]
        for location in locations:
            variations.append(f"{seed_keyword} {location}")
        
        return variations

    def _filter_suggestions(self, suggestions: List[KeywordSuggestion], request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Filter suggestions based on request criteria"""
        filtered = []
        
        for suggestion in suggestions:
            # Check relevance score
            if suggestion.relevance_score < request.min_relevance_score:
                continue
                
            # Check if keyword is excluded
            if suggestion.keyword in request.exclude_keywords:
                continue
                
            # Check if keyword is already in seed keywords
            if suggestion.keyword in request.seed_keywords:
                continue
                
            filtered.append(suggestion)
        
        return filtered

    def _rank_suggestions(self, suggestions: List[KeywordSuggestion], request: SuggestionRequest) -> List[KeywordSuggestion]:
        """Rank suggestions by relevance and quality"""
        def sort_key(suggestion):
            # Base score from relevance
            score = suggestion.relevance_score
            
            # Bonus for high search volume
            if suggestion.search_volume and suggestion.search_volume > 1000:
                score += 0.1
                
            # Bonus for low competition
            if suggestion.competition == "low":
                score += 0.1
                
            # Bonus for high CPC (commercial intent)
            if suggestion.cpc and suggestion.cpc > 1.0:
                score += 0.05
                
            return score
        
        return sorted(suggestions, key=sort_key, reverse=True)

    def _get_suggestion_breakdown(self, suggestions: List[KeywordSuggestion]) -> Dict[SuggestionType, int]:
        """Get breakdown of suggestions by type"""
        breakdown = {}
        for suggestion in suggestions:
            suggestion_type = suggestion.suggestion_type
            breakdown[suggestion_type] = breakdown.get(suggestion_type, 0) + 1
        return breakdown

    def _generate_metadata(self, request: SuggestionRequest, suggestions: List[KeywordSuggestion]) -> Dict[str, Any]:
        """Generate metadata for the suggestion response"""
        return {
            "request_timestamp": datetime.now().isoformat(),
            "target_language": request.target_language,
            "suggestion_types_requested": [t.value for t in request.suggestion_types],
            "average_relevance_score": sum(s.relevance_score for s in suggestions) / len(suggestions) if suggestions else 0,
            "sources_used": list(set(s.source.value for s in suggestions)),
            "filtering_applied": {
                "min_relevance_score": request.min_relevance_score,
                "excluded_keywords_count": len(request.exclude_keywords),
                "competitor_domains_count": len(request.competitor_domains)
            }
        }

    def _generate_request_id(self, request: SuggestionRequest) -> str:
        """Generate unique request ID"""
        request_data = {
            "seed_keywords": sorted(request.seed_keywords),
            "suggestion_types": [t.value for t in request.suggestion_types],
            "max_suggestions": request.max_suggestions,
            "min_relevance_score": request.min_relevance_score,
            "target_language": request.target_language
        }
        
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()

    def _get_cached_suggestions(self, request_id: str) -> Optional[SuggestionResponse]:
        """Get cached suggestions if available and valid"""
        if request_id in self.suggestion_cache:
            cached_data = self.suggestion_cache[request_id]
            if self._is_cache_valid(cached_data):
                return cached_data['response']
            else:
                # Remove expired cache entry
                del self.suggestion_cache[request_id]
        return None

    def _cache_suggestions(self, request_id: str, response: SuggestionResponse):
        """Cache suggestion response"""
        if len(self.suggestion_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.suggestion_cache.keys(), 
                           key=lambda k: self.suggestion_cache[k]['timestamp'])
            del self.suggestion_cache[oldest_key]
        
        self.suggestion_cache[request_id] = {
            'response': response,
            'timestamp': datetime.now()
        }

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid"""
        cache_age = datetime.now() - cached_data['timestamp']
        return cache_age.total_seconds() < self.cache_ttl

    async def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about suggestion generation"""
        return {
            "cache_size": len(self.suggestion_cache),
            "cache_hit_rate": 0.0,  # Placeholder for future implementation
            "total_requests_processed": 0,  # Placeholder for future implementation
            "average_processing_time": 0.0,  # Placeholder for future implementation
            "suggestion_types_generated": [t.value for t in SuggestionType],
            "sources_available": [s.value for s in SuggestionSource]
        }

    async def clear_cache(self):
        """Clear suggestion cache"""
        self.suggestion_cache.clear()
        self.logger.info("Suggestion cache cleared")

async def create_keyword_suggestion_service() -> KeywordSuggestionService:
    """Create and initialize a new keyword suggestion service instance"""
    service = KeywordSuggestionService()
    await service.initialize()
    return service
