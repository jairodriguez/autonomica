"""
Advanced Keyword Suggestion Service

This module provides intelligent keyword suggestion capabilities:
- Semantic keyword expansion using embeddings
- Intent-based keyword suggestions
- Long-tail keyword generation
- Competitor keyword analysis
- Seasonal keyword suggestions
- Related keyword discovery
- Keyword opportunity ranking
- Personalized recommendations
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
from app.services.keyword_clustering import KeywordClusteringService
from app.services.keyword_analyzer import KeywordAnalyzer
from app.services.serp_scraper import SERPScraper

logger = logging.getLogger(__name__)

@dataclass
class KeywordSuggestion:
    """Individual keyword suggestion with metadata"""
    keyword: str
    suggestion_type: str  # semantic, intent, long_tail, competitor, seasonal
    relevance_score: float
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    keyword_difficulty: Optional[float] = None
    opportunity_score: Optional[float] = None
    intent_type: Optional[str] = None
    commercial_potential: Optional[float] = None
    seasonal_pattern: Optional[str] = None
    related_keywords: List[str] = None
    created_at: Optional[datetime] = None

@dataclass
class SuggestionResult:
    """Complete keyword suggestion result"""
    seed_keyword: str
    suggestions: List[KeywordSuggestion]
    total_suggestions: int
    suggestion_types: Dict[str, int]
    processing_time: float
    recommendations: List[str]
    created_at: datetime

@dataclass
class SuggestionContext:
    """Context for generating keyword suggestions"""
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    content_type: Optional[str] = None
    business_goals: Optional[List[str]] = None
    competitor_domains: Optional[List[str]] = None
    seasonal_focus: Optional[List[str]] = None
    content_strategy: Optional[str] = None

class KeywordSuggester:
    """Advanced keyword suggestion service"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.seo_service = SEOService()
        self.clustering_service = KeywordClusteringService()
        self.keyword_analyzer = KeywordAnalyzer()
        self.serp_scraper = SERPScraper()
        
        # Suggestion configuration
        self.suggestion_config = {
            "max_suggestions_per_type": 20,
            "min_relevance_score": 0.3,
            "max_processing_time": 30,
            "batch_size": 10,
            "cache_ttl": 3600 * 24  # 24 hours
        }
        
        # Keyword expansion patterns
        self.expansion_patterns = {
            "informational": [
                "how to {keyword}",
                "what is {keyword}",
                "why {keyword}",
                "when {keyword}",
                "where {keyword}",
                "{keyword} guide",
                "{keyword} tutorial",
                "{keyword} tips",
                "{keyword} examples",
                "{keyword} explanation",
                "{keyword} definition",
                "{keyword} meaning",
                "learn {keyword}",
                "understand {keyword}",
                "{keyword} for beginners",
                "{keyword} basics",
                "{keyword} fundamentals"
            ],
            "transactional": [
                "buy {keyword}",
                "purchase {keyword}",
                "order {keyword}",
                "shop {keyword}",
                "best {keyword}",
                "top {keyword}",
                "cheap {keyword}",
                "affordable {keyword}",
                "discount {keyword}",
                "deal {keyword}",
                "offer {keyword}",
                "sale {keyword}",
                "compare {keyword}",
                "review {keyword}",
                "{keyword} price",
                "{keyword} cost",
                "{keyword} value",
                "premium {keyword}",
                "quality {keyword}"
            ],
            "navigational": [
                "{keyword} login",
                "{keyword} sign in",
                "{keyword} account",
                "{keyword} profile",
                "{keyword} dashboard",
                "{keyword} homepage",
                "{keyword} contact",
                "{keyword} about",
                "{keyword} support",
                "{keyword} help",
                "{keyword} faq",
                "{keyword} customer service",
                "{keyword} location",
                "{keyword} hours",
                "{keyword} phone number"
            ]
        }
        
        # Seasonal keywords
        self.seasonal_keywords = {
            "christmas": ["christmas", "holiday", "gift", "december", "winter"],
            "summer": ["summer", "vacation", "beach", "outdoor", "june", "july", "august"],
            "spring": ["spring", "garden", "outdoor", "march", "april", "may"],
            "fall": ["fall", "autumn", "harvest", "september", "october", "november"],
            "back_to_school": ["school", "education", "student", "back to school", "september"],
            "black_friday": ["black friday", "cyber monday", "sale", "discount", "november"]
        }
        
        # Industry-specific keywords
        self.industry_keywords = {
            "ecommerce": ["shop", "buy", "purchase", "product", "shopping cart", "checkout"],
            "saas": ["software", "app", "platform", "subscription", "trial", "demo"],
            "healthcare": ["health", "medical", "doctor", "treatment", "symptoms", "wellness"],
            "finance": ["money", "investment", "banking", "credit", "loan", "financial"],
            "education": ["learn", "course", "training", "education", "certification", "skill"],
            "real_estate": ["property", "house", "real estate", "buying", "selling", "mortgage"]
        }
    
    async def _get_cached_suggestions(self, seed_keyword: str, context: SuggestionContext) -> Optional[SuggestionResult]:
        """Retrieve cached keyword suggestions"""
        context_hash = self._hash_context(context)
        cache_key = f"suggestions:{hashlib.md5(seed_keyword.encode()).hexdigest()}:{context_hash}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Convert string dates back to datetime objects
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                for suggestion in data["suggestions"]:
                    if suggestion.get("created_at"):
                        suggestion["created_at"] = datetime.fromisoformat(suggestion["created_at"])
                return SuggestionResult(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached suggestions: {e}")
        
        return None
    
    async def _cache_suggestions(self, seed_keyword: str, context: SuggestionContext, 
                               suggestions: SuggestionResult) -> bool:
        """Cache keyword suggestions"""
        context_hash = self._hash_context(context)
        cache_key = f"suggestions:{hashlib.md5(seed_keyword.encode()).hexdigest()}:{context_hash}"
        
        try:
            # Convert datetime objects to strings for JSON serialization
            data_dict = suggestions.__dict__.copy()
            data_dict["created_at"] = data_dict["created_at"].isoformat()
            
            for suggestion in data_dict["suggestions"]:
                if suggestion.get("created_at"):
                    suggestion["created_at"] = suggestion["created_at"].isoformat()
            
            await self.redis_service.set(
                cache_key,
                json.dumps(data_dict),
                expire=self.suggestion_config["cache_ttl"]
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache suggestions: {e}")
            return False
    
    def _hash_context(self, context: SuggestionContext) -> str:
        """Create hash from suggestion context"""
        context_str = json.dumps({
            "industry": context.industry,
            "target_audience": context.target_audience,
            "content_type": context.content_type,
            "business_goals": context.business_goals,
            "competitor_domains": context.competitor_domains,
            "seasonal_focus": context.seasonal_focus,
            "content_strategy": context.content_strategy
        }, sort_keys=True)
        
        return hashlib.md5(context_str.encode()).hexdigest()
    
    async def _generate_semantic_suggestions(self, seed_keyword: str, 
                                           context: SuggestionContext) -> List[KeywordSuggestion]:
        """Generate semantic keyword suggestions using embeddings"""
        try:
            # Get keyword suggestions from SEO service
            base_suggestions = await self.seo_service.get_keyword_suggestions(seed_keyword, 30)
            
            semantic_suggestions = []
            
            for suggestion in base_suggestions:
                # Calculate relevance score based on similarity to seed keyword
                relevance_score = self._calculate_semantic_relevance(seed_keyword, suggestion)
                
                if relevance_score >= self.suggestion_config["min_relevance_score"]:
                    semantic_suggestion = KeywordSuggestion(
                        keyword=suggestion,
                        suggestion_type="semantic",
                        relevance_score=relevance_score,
                        created_at=datetime.now()
                    )
                    semantic_suggestions.append(semantic_suggestion)
            
            # Sort by relevance score
            semantic_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return semantic_suggestions[:self.suggestion_config["max_suggestions_per_type"]]
            
        except Exception as e:
            logger.error(f"Failed to generate semantic suggestions: {e}")
            return []
    
    def _calculate_semantic_relevance(self, seed_keyword: str, suggestion: str) -> float:
        """Calculate semantic relevance between seed keyword and suggestion"""
        # Simple word overlap relevance
        seed_words = set(seed_keyword.lower().split())
        suggestion_words = set(suggestion.lower().split())
        
        if not seed_words or not suggestion_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(seed_words.intersection(suggestion_words))
        union = len(seed_words.union(suggestion_words))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Boost score for exact matches and substrings
        if seed_keyword.lower() in suggestion.lower():
            jaccard_similarity += 0.3
        elif suggestion.lower() in seed_keyword.lower():
            jaccard_similarity += 0.2
        
        # Boost score for similar length
        length_diff = abs(len(seed_keyword.split()) - len(suggestion.split()))
        if length_diff <= 1:
            jaccard_similarity += 0.1
        elif length_diff <= 2:
            jaccard_similarity += 0.05
        
        return min(jaccard_similarity, 1.0)
    
    async def _generate_intent_based_suggestions(self, seed_keyword: str, 
                                               context: SuggestionContext) -> List[KeywordSuggestion]:
        """Generate intent-based keyword suggestions"""
        try:
            intent_suggestions = []
            
            # Analyze seed keyword intent
            intent_analysis = self.clustering_service.analyze_keyword_intent(seed_keyword)
            primary_intent = intent_analysis.intent_type
            
            # Generate suggestions for each intent type
            for intent_type, patterns in self.expansion_patterns.items():
                # Focus on primary intent but include others
                if intent_type == primary_intent:
                    max_patterns = len(patterns)
                else:
                    max_patterns = len(patterns) // 2
                
                for pattern in patterns[:max_patterns]:
                    try:
                        suggestion = pattern.format(keyword=seed_keyword)
                        
                        # Calculate relevance score
                        relevance_score = self._calculate_intent_relevance(seed_keyword, suggestion, intent_type)
                        
                        if relevance_score >= self.suggestion_config["min_relevance_score"]:
                            intent_suggestion = KeywordSuggestion(
                                keyword=suggestion,
                                suggestion_type="intent",
                                relevance_score=relevance_score,
                                intent_type=intent_type,
                                created_at=datetime.now()
                            )
                            intent_suggestions.append(intent_suggestion)
                    
                    except Exception as e:
                        logger.warning(f"Failed to generate intent suggestion: {e}")
                        continue
            
            # Sort by relevance score
            intent_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return intent_suggestions[:self.suggestion_config["max_suggestions_per_type"]]
            
        except Exception as e:
            logger.error(f"Failed to generate intent-based suggestions: {e}")
            return []
    
    def _calculate_intent_relevance(self, seed_keyword: str, suggestion: str, intent_type: str) -> float:
        """Calculate relevance score for intent-based suggestions"""
        base_score = 0.5
        
        # Boost score for semantic similarity
        semantic_score = self._calculate_semantic_relevance(seed_keyword, suggestion)
        base_score += semantic_score * 0.3
        
        # Boost score for intent alignment
        if intent_type == "informational" and any(word in suggestion.lower() for word in ["how", "what", "why", "guide", "tutorial"]):
            base_score += 0.2
        elif intent_type == "transactional" and any(word in suggestion.lower() for word in ["buy", "best", "price", "review"]):
            base_score += 0.2
        elif intent_type == "navigational" and any(word in suggestion.lower() for word in ["login", "contact", "about"]):
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    async def _generate_long_tail_suggestions(self, seed_keyword: str, 
                                            context: SuggestionContext) -> List[KeywordSuggestion]:
        """Generate long-tail keyword suggestions"""
        try:
            long_tail_suggestions = []
            
            # Get long-tail analysis from keyword analyzer
            long_tail_analysis = await self.keyword_analyzer.analyze_long_tail_keywords(seed_keyword)
            
            for analysis in long_tail_analysis:
                if analysis.get("long_tail_score", 0) >= 50:  # Only include good long-tail keywords
                    long_tail_suggestion = KeywordSuggestion(
                        keyword=analysis["keyword"],
                        suggestion_type="long_tail",
                        relevance_score=analysis.get("long_tail_score", 0) / 100,
                        search_volume=analysis.get("search_volume"),
                        cpc=analysis.get("cpc"),
                        keyword_difficulty=analysis.get("difficulty"),
                        opportunity_score=analysis.get("opportunity_score"),
                        created_at=datetime.now()
                    )
                    long_tail_suggestions.append(long_tail_suggestion)
            
            # Sort by long-tail score
            long_tail_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return long_tail_suggestions[:self.suggestion_config["max_suggestions_per_type"]]
            
        except Exception as e:
            logger.error(f"Failed to generate long-tail suggestions: {e}")
            return []
    
    async def _generate_competitor_suggestions(self, seed_keyword: str, 
                                             context: SuggestionContext) -> List[KeywordSuggestion]:
        """Generate competitor-based keyword suggestions"""
        try:
            competitor_suggestions = []
            
            # Get competitor domains from context or analyze SERP
            competitor_domains = context.competitor_domains or []
            
            if not competitor_domains:
                # Analyze SERP to find competitors
                try:
                    async with self.serp_scraper as scraper:
                        serp_data = await scraper.scrape_serp_data(seed_keyword, "us")
                        competitor_domains = [result.domain for result in serp_data.results[:5]]
                except Exception as e:
                    logger.warning(f"Failed to get competitor domains: {e}")
                    return []
            
            # Generate suggestions based on competitor analysis
            for domain in competitor_domains[:3]:  # Limit to top 3 competitors
                try:
                    # Generate domain-specific suggestions
                    domain_suggestions = [
                        f"{seed_keyword} {domain}",
                        f"{domain} {seed_keyword}",
                        f"best {seed_keyword} {domain}",
                        f"{seed_keyword} vs {domain}",
                        f"compare {seed_keyword} {domain}"
                    ]
                    
                    for suggestion in domain_suggestions:
                        relevance_score = self._calculate_competitor_relevance(seed_keyword, suggestion, domain)
                        
                        if relevance_score >= self.suggestion_config["min_relevance_score"]:
                            competitor_suggestion = KeywordSuggestion(
                                keyword=suggestion,
                                suggestion_type="competitor",
                                relevance_score=relevance_score,
                                created_at=datetime.now()
                            )
                            competitor_suggestions.append(competitor_suggestion)
                
                except Exception as e:
                    logger.warning(f"Failed to generate competitor suggestion for {domain}: {e}")
                    continue
            
            # Sort by relevance score
            competitor_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return competitor_suggestions[:self.suggestion_config["max_suggestions_per_type"]]
            
        except Exception as e:
            logger.error(f"Failed to generate competitor suggestions: {e}")
            return []
    
    def _calculate_competitor_relevance(self, seed_keyword: str, suggestion: str, domain: str) -> float:
        """Calculate relevance score for competitor-based suggestions"""
        base_score = 0.4
        
        # Boost score for semantic similarity
        semantic_score = self._calculate_semantic_relevance(seed_keyword, suggestion)
        base_score += semantic_score * 0.3
        
        # Boost score for domain inclusion
        if domain in suggestion.lower():
            base_score += 0.2
        
        # Boost score for comparison words
        if any(word in suggestion.lower() for word in ["vs", "compare", "alternative", "competitor"]):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    async def _generate_seasonal_suggestions(self, seed_keyword: str, 
                                           context: SuggestionContext) -> List[KeywordSuggestion]:
        """Generate seasonal keyword suggestions"""
        try:
            seasonal_suggestions = []
            
            # Determine seasonal focus from context or detect from seed keyword
            seasonal_focus = context.seasonal_focus or []
            
            if not seasonal_focus:
                # Auto-detect seasonal patterns
                for season, keywords in self.seasonal_keywords.items():
                    if any(keyword in seed_keyword.lower() for keyword in keywords):
                        seasonal_focus.append(season)
                        break
            
            # Generate seasonal suggestions
            for season in seasonal_focus:
                season_keywords = self.seasonal_keywords.get(season, [])
                
                for season_keyword in season_keywords[:5]:  # Limit to top 5 seasonal keywords
                    suggestions = [
                        f"{seed_keyword} {season_keyword}",
                        f"{season_keyword} {seed_keyword}",
                        f"{seed_keyword} {season}",
                        f"{season} {seed_keyword}"
                    ]
                    
                    for suggestion in suggestions:
                        relevance_score = self._calculate_seasonal_relevance(seed_keyword, suggestion, season)
                        
                        if relevance_score >= self.suggestion_config["min_relevance_score"]:
                            seasonal_suggestion = KeywordSuggestion(
                                keyword=suggestion,
                                suggestion_type="seasonal",
                                relevance_score=relevance_score,
                                seasonal_pattern=season,
                                created_at=datetime.now()
                            )
                            seasonal_suggestions.append(seasonal_suggestion)
            
            # Sort by relevance score
            seasonal_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return seasonal_suggestions[:self.suggestion_config["max_suggestions_per_type"]]
            
        except Exception as e:
            logger.error(f"Failed to generate seasonal suggestions: {e}")
            return []
    
    def _calculate_seasonal_relevance(self, seed_keyword: str, suggestion: str, season: str) -> float:
        """Calculate relevance score for seasonal suggestions"""
        base_score = 0.4
        
        # Boost score for semantic similarity
        semantic_score = self._calculate_semantic_relevance(seed_keyword, suggestion)
        base_score += semantic_score * 0.3
        
        # Boost score for seasonal relevance
        season_keywords = self.seasonal_keywords.get(season, [])
        if any(keyword in suggestion.lower() for keyword in season_keywords):
            base_score += 0.2
        
        # Boost score for season name inclusion
        if season in suggestion.lower():
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    async def _enrich_suggestions(self, suggestions: List[KeywordSuggestion], 
                                 country: str = "us") -> List[KeywordSuggestion]:
        """Enrich suggestions with additional data"""
        try:
            enriched_suggestions = []
            
            # Process suggestions in batches
            for i in range(0, len(suggestions), self.suggestion_config["batch_size"]):
                batch = suggestions[i:i + self.suggestion_config["batch_size"]]
                
                # Get keyword insights for batch
                tasks = []
                for suggestion in batch:
                    task = self.keyword_analyzer.get_keyword_insights(suggestion.keyword, country)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Enrich suggestions with data
                for suggestion, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to enrich suggestion '{suggestion.keyword}': {result}")
                        enriched_suggestions.append(suggestion)
                    else:
                        # Update suggestion with additional data
                        if result and "error" not in result:
                            metrics = result.get("metrics", {})
                            opportunity = result.get("opportunity", {})
                            
                            suggestion.search_volume = metrics.get("search_volume")
                            suggestion.cpc = metrics.get("cpc")
                            suggestion.keyword_difficulty = metrics.get("difficulty_score")
                            suggestion.opportunity_score = opportunity.get("opportunity_score")
                            suggestion.commercial_potential = metrics.get("commercial_intent")
                        
                        enriched_suggestions.append(suggestion)
                
                # Add delay between batches
                if i + self.suggestion_config["batch_size"] < len(suggestions):
                    await asyncio.sleep(1)
            
            return enriched_suggestions
            
        except Exception as e:
            logger.error(f"Failed to enrich suggestions: {e}")
            return suggestions
    
    async def suggest_keywords(self, seed_keyword: str, context: SuggestionContext = None,
                             country: str = "us", max_suggestions: int = 100) -> SuggestionResult:
        """
        Generate comprehensive keyword suggestions
        
        Args:
            seed_keyword: Base keyword to expand
            context: Context for generating suggestions
            country: Country for localized analysis
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            Complete keyword suggestion result
        """
        start_time = datetime.now()
        
        # Use default context if none provided
        if context is None:
            context = SuggestionContext()
        
        # Check cache first
        cached_result = await self._get_cached_suggestions(seed_keyword, context)
        if cached_result:
            logger.info(f"Retrieved cached suggestions for '{seed_keyword}'")
            return cached_result
        
        try:
            logger.info(f"Generating keyword suggestions for '{seed_keyword}'")
            
            all_suggestions = []
            
            # Generate suggestions from all sources
            semantic_suggestions = await self._generate_semantic_suggestions(seed_keyword, context)
            all_suggestions.extend(semantic_suggestions)
            
            intent_suggestions = await self._generate_intent_based_suggestions(seed_keyword, context)
            all_suggestions.extend(intent_suggestions)
            
            long_tail_suggestions = await self._generate_long_tail_suggestions(seed_keyword, context)
            all_suggestions.extend(long_tail_suggestions)
            
            competitor_suggestions = await self._generate_competitor_suggestions(seed_keyword, context)
            all_suggestions.extend(competitor_suggestions)
            
            seasonal_suggestions = await self._generate_seasonal_suggestions(seed_keyword, context)
            all_suggestions.extend(seasonal_suggestions)
            
            # Remove duplicates based on keyword
            unique_suggestions = {}
            for suggestion in all_suggestions:
                if suggestion.keyword not in unique_suggestions:
                    unique_suggestions[suggestion.keyword] = suggestion
                else:
                    # Keep the suggestion with higher relevance score
                    if suggestion.relevance_score > unique_suggestions[suggestion.keyword].relevance_score:
                        unique_suggestions[suggestion.keyword] = suggestion
            
            # Convert back to list and sort by relevance score
            unique_suggestions_list = list(unique_suggestions.values())
            unique_suggestions_list.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit to max suggestions
            final_suggestions = unique_suggestions_list[:max_suggestions]
            
            # Enrich suggestions with additional data
            enriched_suggestions = await self._enrich_suggestions(final_suggestions, country)
            
            # Calculate suggestion type distribution
            suggestion_types = defaultdict(int)
            for suggestion in enriched_suggestions:
                suggestion_types[suggestion.suggestion_type] += 1
            
            # Generate recommendations
            recommendations = self._generate_suggestion_recommendations(enriched_suggestions, context)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create suggestion result
            result = SuggestionResult(
                seed_keyword=seed_keyword,
                suggestions=enriched_suggestions,
                total_suggestions=len(enriched_suggestions),
                suggestion_types=dict(suggestion_types),
                processing_time=processing_time,
                recommendations=recommendations,
                created_at=datetime.now()
            )
            
            # Cache the result
            await self._cache_suggestions(seed_keyword, context, result)
            
            logger.info(f"Generated {len(enriched_suggestions)} keyword suggestions in {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate keyword suggestions: {e}")
            # Return minimal result on failure
            return SuggestionResult(
                seed_keyword=seed_keyword,
                suggestions=[],
                total_suggestions=0,
                suggestion_types={},
                processing_time=0.0,
                recommendations=["Suggestion generation failed - please try again"],
                created_at=datetime.now()
            )
    
    def _generate_suggestion_recommendations(self, suggestions: List[KeywordSuggestion],
                                           context: SuggestionContext) -> List[str]:
        """Generate recommendations based on suggestion results"""
        recommendations = []
        
        if not suggestions:
            recommendations.append("No suggestions generated - consider broadening your seed keyword")
            return recommendations
        
        # Analyze suggestion distribution
        suggestion_types = defaultdict(int)
        for suggestion in suggestions:
            suggestion_types[suggestion.suggestion_type] += 1
        
        # Type-specific recommendations
        if suggestion_types.get("semantic", 0) > 10:
            recommendations.append("Many semantic variations found - focus on high-relevance keywords")
        
        if suggestion_types.get("long_tail", 0) > 5:
            recommendations.append("Good long-tail opportunities available - consider targeting specific user intents")
        
        if suggestion_types.get("seasonal", 0) > 3:
            recommendations.append("Seasonal patterns detected - plan content calendar accordingly")
        
        # Opportunity-based recommendations
        high_opportunity_count = sum(1 for s in suggestions if s.opportunity_score and s.opportunity_score >= 80)
        if high_opportunity_count > 0:
            recommendations.append(f"Found {high_opportunity_count} high-opportunity keywords - prioritize these")
        
        # Intent-based recommendations
        intent_distribution = defaultdict(int)
        for suggestion in suggestions:
            if suggestion.intent_type:
                intent_distribution[suggestion.intent_type] += 1
        
        if intent_distribution:
            dominant_intent = max(intent_distribution, key=intent_distribution.get)
            recommendations.append(f"Dominant intent: {dominant_intent} - align content strategy with user intent")
        
        # Volume-based recommendations
        high_volume_count = sum(1 for s in suggestions if s.search_volume and s.search_volume >= 1000)
        if high_volume_count > 0:
            recommendations.append(f"Found {high_volume_count} high-volume keywords - ensure strong content strategy")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def get_suggestions_by_type(self, seed_keyword: str, suggestion_type: str,
                                    context: SuggestionContext = None, 
                                    country: str = "us") -> List[KeywordSuggestion]:
        """
        Get keyword suggestions filtered by type
        
        Args:
            seed_keyword: Base keyword to expand
            suggestion_type: Type of suggestions to return
            context: Context for generating suggestions
            country: Country for localized analysis
        
        Returns:
            List of keyword suggestions of specified type
        """
        try:
            # Get all suggestions first
            all_suggestions = await self.suggest_keywords(seed_keyword, context, country)
            
            # Filter by type
            filtered_suggestions = [
                suggestion for suggestion in all_suggestions.suggestions
                if suggestion.suggestion_type == suggestion_type
            ]
            
            return filtered_suggestions
            
        except Exception as e:
            logger.error(f"Failed to get suggestions by type: {e}")
            return []
    
    async def export_suggestions(self, suggestions: List[KeywordSuggestion], 
                               format: str = "json") -> str:
        """
        Export keyword suggestions in various formats
        
        Args:
            suggestions: List of keyword suggestions to export
            format: Export format (json, csv)
        
        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "json":
                # Convert to serializable format
                export_data = []
                for suggestion in suggestions:
                    data_dict = suggestion.__dict__.copy()
                    # Convert datetime objects to strings
                    if data_dict.get("created_at"):
                        data_dict["created_at"] = data_dict["created_at"].isoformat()
                    export_data.append(data_dict)
                
                return json.dumps(export_data, indent=2, default=str)
                
            elif format.lower() == "csv":
                # Create CSV with key metrics
                csv_lines = [
                    "keyword,suggestion_type,relevance_score,search_volume,cpc,keyword_difficulty,opportunity_score,intent_type,commercial_potential,seasonal_pattern"
                ]
                
                for suggestion in suggestions:
                    csv_lines.append(
                        f"{suggestion.keyword},{suggestion.suggestion_type},{suggestion.relevance_score},"
                        f"{suggestion.search_volume or ''},{suggestion.cpc or ''},{suggestion.keyword_difficulty or ''},"
                        f"{suggestion.opportunity_score or ''},{suggestion.intent_type or ''},"
                        f"{suggestion.commercial_potential or ''},{suggestion.seasonal_pattern or ''}"
                    )
                
                return "\n".join(csv_lines)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export suggestions: {e}")
            return json.dumps({"error": str(e)})