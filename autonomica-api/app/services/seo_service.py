"""
SEO Research and Keyword Analysis Service

This module provides comprehensive SEO research capabilities including:
- SEMrush API integration for keyword data
- SERP scraping with Playwright
- Keyword clustering algorithms
- Competitor analysis
- Keyword opportunity scoring
- Data processing pipeline
- Caching mechanism
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
from urllib.parse import urlparse, quote_plus

import aiohttp
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import redis.asyncio as redis

from app.services.redis_service import RedisService
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class KeywordRecord:
    """Data structure for keyword information"""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    keyword_difficulty: Optional[float] = None
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None
    cluster_id: Optional[int] = None
    opportunity_score: Optional[float] = None
    related_keywords: Optional[List[str]] = None
    serp_features: Optional[Dict[str, Any]] = None

@dataclass
class CompetitorAnalysis:
    """Data structure for competitor information"""
    domain: str
    ranking_position: int
    title: str
    url: str
    snippet: str
    featured_snippet: bool = False
    paa_questions: Optional[List[str]] = None
    structured_data: Optional[Dict[str, Any]] = None

@dataclass
class SEOAnalysis:
    """Data structure for comprehensive SEO analysis"""
    keyword: str
    keyword_data: KeywordRecord
    competitors: List[CompetitorAnalysis]
    serp_features: Dict[str, Any]
    seo_score: float
    recommendations: List[str]
    created_at: datetime

class SEOService:
    """Main SEO service for research and analysis"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API endpoints and configurations
        self.semrush_base_url = "https://api.semrush.com"
        self.semrush_endpoints = {
            "domain_overview": "/analytics/overview",
            "keyword_overview": "/analytics/overview",
            "keyword_ideas": "/analytics/overview",
            "competitors": "/analytics/overview"
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            "semrush": {"requests_per_minute": 10, "requests_per_day": 1000},
            "openai": {"requests_per_minute": 60, "requests_per_day": 10000}
        }
        
        # Caching configuration
        self.cache_ttl = {
            "keyword_data": 3600 * 24,  # 24 hours
            "serp_data": 3600 * 6,      # 6 hours
            "competitor_data": 3600 * 12,  # 12 hours
            "clustering": 3600 * 24      # 24 hours
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Autonomica-SEO-Bot/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data from Redis"""
        try:
            cached = await self.redis_service.get(f"seo:{key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached data for {key}: {e}")
        return None
    
    async def _set_cached_data(self, key: str, data: Any, ttl: int) -> bool:
        """Store data in Redis cache"""
        try:
            await self.redis_service.set(
                f"seo:{key}", 
                json.dumps(data, default=str), 
                expire=ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache data for {key}: {e}")
            return False
    
    def _generate_cache_key(self, *args) -> str:
        """Generate a unique cache key from arguments"""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _check_rate_limit(self, api_name: str) -> bool:
        """Check if we're within rate limits for the specified API"""
        cache_key = f"rate_limit:{api_name}:{datetime.now().strftime('%Y%m%d%H%M')}"
        
        try:
            current_requests = await self.redis_service.get(cache_key)
            if current_requests is None:
                await self.redis_service.set(cache_key, "1", expire=60)
                return True
            
            current_count = int(current_requests)
            if current_count >= self.rate_limits[api_name]["requests_per_minute"]:
                return False
            
            await self.redis_service.incr(cache_key)
            return True
        except Exception as e:
            logger.warning(f"Rate limit check failed for {api_name}: {e}")
            return True  # Allow request if rate limiting fails
    
    async def get_semrush_keyword_data(self, keyword: str, country: str = "us") -> Optional[KeywordRecord]:
        """
        Retrieve keyword data from SEMrush API
        
        Args:
            keyword: Target keyword to research
            country: Country code for localized data (default: us)
        
        Returns:
            KeywordRecord with SEMrush data or None if failed
        """
        if not self.semrush_api_key:
            logger.warning("SEMrush API key not configured")
            return None
        
        # Check rate limits
        if not await self._check_rate_limit("semrush"):
            logger.warning("SEMrush rate limit exceeded")
            return None
        
        # Check cache first
        cache_key = self._generate_cache_key("semrush_keyword", keyword, country)
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return KeywordRecord(**cached_data)
        
        try:
            params = {
                "key": self.semrush_api_key,
                "type": "phrase_this",
                "phrase": keyword,
                "database": country,
                "export": "json"
            }
            
            async with self.session.get(
                f"{self.semrush_base_url}/analytics/overview",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        keyword_data = data[0]
                        
                        record = KeywordRecord(
                            keyword=keyword,
                            search_volume=int(keyword_data.get("Nq", 0)),
                            cpc=float(keyword_data.get("Cp", 0)),
                            keyword_difficulty=float(keyword_data.get("Co", 0)),
                            created_at=datetime.now()
                        )
                        
                        # Cache the result
                        await self._set_cached_data(
                            cache_key, 
                            record.__dict__, 
                            self.cache_ttl["keyword_data"]
                        )
                        
                        return record
                    else:
                        logger.warning(f"No data returned from SEMrush for keyword: {keyword}")
                        return None
                else:
                    logger.error(f"SEMrush API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to retrieve SEMrush data for {keyword}: {e}")
            return None
    
    async def scrape_serp_data(self, keyword: str, country: str = "us") -> Dict[str, Any]:
        """
        Scrape SERP data using Playwright (to be implemented)
        
        Args:
            keyword: Target keyword to search
            country: Country for localized search results
        
        Returns:
            Dictionary containing SERP features and top results
        """
        # This will be implemented in the web scraping module
        # For now, return a placeholder structure
        cache_key = self._generate_cache_key("serp_data", keyword, country)
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Placeholder implementation
        serp_data = {
            "keyword": keyword,
            "total_results": 0,
            "featured_snippet": None,
            "people_also_ask": [],
            "related_searches": [],
            "top_results": [],
            "scraped_at": datetime.now().isoformat()
        }
        
        # Cache the placeholder data
        await self._set_cached_data(
            cache_key, 
            serp_data, 
            self.cache_ttl["serp_data"]
        )
        
        return serp_data
    
    async def generate_keyword_embeddings(self, keywords: List[str]) -> List[List[float]]:
        """
        Generate embeddings for keywords using OpenAI API
        
        Args:
            keywords: List of keywords to embed
        
        Returns:
            List of embedding vectors
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return []
        
        # Check rate limits
        if not await self._check_rate_limit("openai"):
            logger.warning("OpenAI rate limit exceeded")
            return []
        
        # Check cache first
        cache_key = self._generate_cache_key("embeddings", "|".join(sorted(keywords)))
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input": keywords,
                "model": "text-embedding-ada-002"
            }
            
            async with self.session.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    embeddings = [item["embedding"] for item in result["data"]]
                    
                    # Cache the embeddings
                    await self._set_cached_data(
                        cache_key, 
                        embeddings, 
                        self.cache_ttl["clustering"]
                    )
                    
                    return embeddings
                else:
                    logger.error(f"OpenAI API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []
    
    async def cluster_keywords(self, keywords: List[str], threshold: float = 0.85) -> Dict[int, List[str]]:
        """
        Cluster keywords based on semantic similarity
        
        Args:
            keywords: List of keywords to cluster
            threshold: Similarity threshold for clustering
        
        Returns:
            Dictionary mapping cluster IDs to keyword lists
        """
        if len(keywords) < 2:
            return {0: keywords}
        
        # Generate embeddings
        embeddings = await self.generate_keyword_embeddings(keywords)
        if not embeddings:
            return {0: keywords}
        
        try:
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings_array)
            
            # Apply hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1 - threshold,
                linkage='ward'
            )
            
            cluster_labels = clustering.fit_predict(embeddings_array)
            
            # Group keywords by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(keywords[i])
            
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            # Fallback to simple clustering
            return {0: keywords}
    
    async def calculate_opportunity_score(self, keyword_record: KeywordRecord) -> float:
        """
        Calculate keyword opportunity score based on multiple factors
        
        Args:
            keyword_record: Keyword data to analyze
        
        Returns:
            Opportunity score between 0 and 100
        """
        if not keyword_record.search_volume or not keyword_record.cpc or not keyword_record.keyword_difficulty:
            return 0.0
        
        try:
            # Normalize factors to 0-1 scale
            volume_score = min(keyword_record.search_volume / 10000, 1.0)  # Cap at 10k searches
            cpc_score = min(keyword_record.cpc / 5.0, 1.0)  # Cap at $5 CPC
            difficulty_score = 1.0 - (keyword_record.keyword_difficulty / 100.0)  # Lower difficulty = higher score
            
            # Weighted scoring (volume: 40%, CPC: 35%, difficulty: 25%)
            opportunity_score = (
                volume_score * 0.4 +
                cpc_score * 0.35 +
                difficulty_score * 0.25
            ) * 100
            
            return round(opportunity_score, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate opportunity score: {e}")
            return 0.0
    
    async def analyze_competitors(self, keyword: str, country: str = "us") -> List[CompetitorAnalysis]:
        """
        Analyze competitors for a given keyword
        
        Args:
            keyword: Target keyword
            country: Country for localized analysis
        
        Returns:
            List of competitor analysis objects
        """
        # This will be enhanced with actual competitor data
        # For now, return a placeholder structure
        cache_key = self._generate_cache_key("competitor_analysis", keyword, country)
        cached_data = await self._get_cached_data(cache_key)
        if cached_data:
            return [CompetitorAnalysis(**comp) for comp in cached_data]
        
        # Placeholder competitor data
        competitors = [
            CompetitorAnalysis(
                domain="example.com",
                ranking_position=1,
                title=f"Example Page for {keyword}",
                url=f"https://example.com/{keyword.replace(' ', '-')}",
                snippet=f"This is an example snippet for {keyword}",
                featured_snippet=False,
                paa_questions=[],
                structured_data={}
            )
        ]
        
        # Cache the competitor data
        await self._set_cached_data(
            cache_key, 
            [comp.__dict__ for comp in competitors], 
            self.cache_ttl["competitor_data"]
        )
        
        return competitors
    
    async def comprehensive_seo_analysis(self, keyword: str, country: str = "us") -> SEOAnalysis:
        """
        Perform comprehensive SEO analysis for a keyword
        
        Args:
            keyword: Target keyword to analyze
            country: Country for localized analysis
        
        Returns:
            Complete SEO analysis object
        """
        try:
            # Gather all data
            keyword_data = await self.get_semrush_keyword_data(keyword, country)
            serp_data = await self.scrape_serp_data(keyword, country)
            competitors = await self.analyze_competitors(keyword, country)
            
            # Calculate opportunity score
            if keyword_data:
                opportunity_score = await self.calculate_opportunity_score(keyword_data)
                keyword_data.opportunity_score = opportunity_score
            
            # Calculate overall SEO score
            seo_score = self._calculate_seo_score(keyword_data, serp_data, competitors)
            
            # Generate recommendations
            recommendations = self._generate_seo_recommendations(
                keyword_data, serp_data, competitors, seo_score
            )
            
            analysis = SEOAnalysis(
                keyword=keyword,
                keyword_data=keyword_data or KeywordRecord(keyword=keyword),
                competitors=competitors,
                serp_features=serp_data,
                seo_score=seo_score,
                recommendations=recommendations,
                created_at=datetime.now()
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Comprehensive SEO analysis failed for {keyword}: {e}")
            # Return minimal analysis on failure
            return SEOAnalysis(
                keyword=keyword,
                keyword_data=KeywordRecord(keyword=keyword),
                competitors=[],
                serp_features={},
                seo_score=0.0,
                recommendations=["Analysis failed - please try again"],
                created_at=datetime.now()
            )
    
    def _calculate_seo_score(self, keyword_data: Optional[KeywordRecord], 
                            serp_data: Dict[str, Any], 
                            competitors: List[CompetitorAnalysis]) -> float:
        """Calculate overall SEO score based on multiple factors"""
        score = 0.0
        factors = 0
        
        # Keyword data scoring
        if keyword_data:
            if keyword_data.opportunity_score:
                score += keyword_data.opportunity_score
                factors += 1
            
            if keyword_data.search_volume:
                volume_score = min(keyword_data.search_volume / 10000, 100)
                score += volume_score
                factors += 1
        
        # SERP features scoring
        if serp_data.get("featured_snippet"):
            score += 20
            factors += 1
        
        if serp_data.get("people_also_ask"):
            score += 15
            factors += 1
        
        # Competitor analysis scoring
        if competitors:
            avg_competitor_score = 100 - (len(competitors) * 5)  # Fewer competitors = higher score
            score += max(avg_competitor_score, 0)
            factors += 1
        
        return round(score / max(factors, 1), 2)
    
    def _generate_seo_recommendations(self, keyword_data: Optional[KeywordRecord],
                                    serp_data: Dict[str, Any],
                                    competitors: List[CompetitorAnalysis],
                                    seo_score: float) -> List[str]:
        """Generate actionable SEO recommendations"""
        recommendations = []
        
        if keyword_data:
            if keyword_data.keyword_difficulty and keyword_data.keyword_difficulty > 70:
                recommendations.append("Consider targeting long-tail variations with lower difficulty")
            
            if keyword_data.search_volume and keyword_data.search_volume < 100:
                recommendations.append("Low search volume - consider broader keyword variations")
            
            if keyword_data.cpc and keyword_data.cpc > 3.0:
                recommendations.append("High CPC indicates commercial intent - optimize for conversions")
        
        if not serp_data.get("featured_snippet"):
            recommendations.append("Target featured snippet with structured content and direct answers")
        
        if len(competitors) > 10:
            recommendations.append("High competition - focus on unique value proposition and long-tail keywords")
        
        if seo_score < 50:
            recommendations.append("Overall SEO score is low - implement comprehensive optimization strategy")
        
        if not recommendations:
            recommendations.append("Keyword shows good potential - focus on content quality and user experience")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def get_keyword_suggestions(self, seed_keyword: str, 
                                    max_suggestions: int = 20) -> List[str]:
        """
        Get keyword suggestions based on a seed keyword
        
        Args:
            seed_keyword: Base keyword to expand
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of suggested keywords
        """
        # This will be enhanced with actual keyword suggestion logic
        # For now, return basic variations
        suggestions = [seed_keyword]
        
        # Add common variations
        variations = [
            f"how to {seed_keyword}",
            f"best {seed_keyword}",
            f"{seed_keyword} guide",
            f"{seed_keyword} tips",
            f"{seed_keyword} examples",
            f"why {seed_keyword}",
            f"{seed_keyword} vs alternatives",
            f"top {seed_keyword}",
            f"{seed_keyword} for beginners",
            f"advanced {seed_keyword}"
        ]
        
        suggestions.extend(variations[:max_suggestions - 1])
        return suggestions[:max_suggestions]
    
    async def export_keyword_data(self, keywords: List[KeywordRecord], 
                                 format: str = "json") -> str:
        """
        Export keyword data in various formats
        
        Args:
            keywords: List of keyword records to export
            format: Export format (json, csv, xlsx)
        
        Returns:
            Exported data as string or file path
        """
        if format.lower() == "json":
            return json.dumps([kw.__dict__ for kw in keywords], default=str, indent=2)
        elif format.lower() == "csv":
            # Basic CSV export
            csv_lines = ["keyword,search_volume,cpc,keyword_difficulty,opportunity_score"]
            for kw in keywords:
                csv_lines.append(f"{kw.keyword},{kw.search_volume or ''},{kw.cpc or ''},{kw.keyword_difficulty or ''},{kw.opportunity_score or ''}")
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")