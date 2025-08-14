"""
Keyword Analysis Module for SEO Research and Content Strategy.

This module provides comprehensive keyword analysis capabilities:
- Keyword difficulty scoring
- Search volume analysis
- Relevance scoring
- Competition analysis
- Trend analysis
- Content gap identification
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

from loguru import logger

from app.services.semrush_client import SEMrushClient, KeywordData
from app.services.web_scraper import WebScraper, SERPData
from app.services.keyword_clustering import KeywordClusteringEngine


@dataclass
class KeywordAnalysis:
    """Comprehensive keyword analysis results."""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
    keyword_difficulty: Optional[int] = None
    relevance_score: float = 0.0
    opportunity_score: float = 0.0
    trend_direction: Optional[str] = None
    trend_strength: Optional[float] = None
    serp_features: List[str] = None
    competitor_domains: List[str] = None
    content_gaps: List[str] = None
    related_keywords: List[str] = None
    analysis_timestamp: datetime = None
    
    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
        if self.serp_features is None:
            self.serp_features = []
        if self.competitor_domains is None:
            self.competitor_domains = []
        if self.content_gaps is None:
            self.content_gaps = []
        if self.related_keywords is None:
            self.related_keywords = []


@dataclass
class ContentGap:
    """Represents a content gap opportunity."""
    topic: str
    search_volume: int
    keyword_difficulty: int
    existing_content_count: int
    opportunity_score: float
    suggested_content_types: List[str]
    target_keywords: List[str]


class KeywordAnalyzer:
    """
    Comprehensive keyword analysis engine.
    
    Features:
    - Multi-source keyword data collection
    - Advanced difficulty scoring algorithms
    - Relevance and opportunity scoring
    - Trend analysis and forecasting
    - Content gap identification
    - Competitor analysis
    """
    
    def __init__(self, 
                 semrush_client: Optional[SEMrushClient] = None,
                 web_scraper: Optional[WebScraper] = None,
                 clustering_engine: Optional[KeywordClusteringEngine] = None):
        """
        Initialize the keyword analyzer.
        
        Args:
            semrush_client: SEMrush API client
            web_scraper: Web scraping service
            clustering_engine: Keyword clustering engine
        """
        self.semrush_client = semrush_client
        self.web_scraper = web_scraper
        self.clustering_engine = clustering_engine
        
        # Analysis parameters
        self.min_search_volume = 100
        self.max_keyword_difficulty = 80
        self.min_opportunity_score = 50
        
        # Scoring weights
        self.scoring_weights = {
            'search_volume': 0.3,
            'keyword_difficulty': 0.25,
            'cpc': 0.2,
            'competition': 0.15,
            'relevance': 0.1
        }
        
        # Trend analysis parameters
        self.trend_window_days = 90
        self.trend_threshold = 0.1  # 10% change threshold
        
        logger.info("Keyword analyzer initialized")
    
    async def analyze_keyword(self, 
                            keyword: str, 
                            target_domain: Optional[str] = None,
                            include_serp_analysis: bool = True,
                            include_competitor_analysis: bool = True) -> KeywordAnalysis:
        """
        Perform comprehensive keyword analysis.
        
        Args:
            keyword: Target keyword to analyze
            target_domain: Domain to analyze against (optional)
            include_serp_analysis: Whether to include SERP analysis
            include_competitor_analysis: Whether to include competitor analysis
            
        Returns:
            Comprehensive KeywordAnalysis object
        """
        logger.info(f"Starting comprehensive analysis for keyword: {keyword}")
        
        analysis = KeywordAnalysis(keyword=keyword)
        
        try:
            # 1. Collect keyword data from SEMrush
            if self.semrush_client:
                await self._collect_semrush_data(analysis)
            
            # 2. Perform SERP analysis
            if include_serp_analysis and self.web_scraper:
                await self._analyze_serp(analysis)
            
            # 3. Analyze competition
            if include_competitor_analysis:
                await self._analyze_competition(analysis, target_domain)
            
            # 4. Calculate relevance and opportunity scores
            self._calculate_scores(analysis)
            
            # 5. Identify content gaps
            if include_serp_analysis:
                await self._identify_content_gaps(analysis)
            
            # 6. Find related keywords
            if self.semrush_client:
                await self._find_related_keywords(analysis)
            
            logger.info(f"Keyword analysis completed: {keyword}")
            
        except Exception as e:
            logger.error(f"Failed to analyze keyword {keyword}: {e}")
            raise
        
        return analysis
    
    async def _collect_semrush_data(self, analysis: KeywordAnalysis):
        """Collect keyword data from SEMrush API."""
        try:
            keyword_data = await self.semrush_client.get_keyword_overview(analysis.keyword)
            
            analysis.search_volume = keyword_data.search_volume
            analysis.cpc = keyword_data.cpc
            analysis.competition = keyword_data.competition
            analysis.keyword_difficulty = keyword_data.keyword_difficulty
            
            logger.debug(f"Collected SEMrush data for {analysis.keyword}")
            
        except Exception as e:
            logger.warning(f"Failed to collect SEMrush data: {e}")
    
    async def _analyze_serp(self, analysis: KeywordAnalysis):
        """Analyze search engine results page."""
        try:
            serp_data = await self.web_scraper.scrape_google_serp(analysis.keyword)
            
            # Extract SERP features
            analysis.serp_features = [feature.feature_type for feature in serp_data.features]
            
            # Extract competitor domains
            analysis.competitor_domains = [result.domain for result in serp_data.results[:10]]
            
            # Analyze content structure
            await self._analyze_content_structure(analysis, serp_data)
            
            logger.debug(f"SERP analysis completed for {analysis.keyword}")
            
        except Exception as e:
            logger.warning(f"Failed to analyze SERP: {e}")
    
    async def _analyze_content_structure(self, analysis: KeywordAnalysis, serp_data: SERPData):
        """Analyze content structure from SERP results."""
        try:
            content_types = []
            content_lengths = []
            
            for result in serp_data.results[:5]:  # Analyze top 5 results
                if result.url and result.url.startswith('http'):
                    try:
                        content_data = await self.web_scraper.scrape_website_content(result.url)
                        
                        # Analyze content type
                        if content_data.get('content', {}).get('headings'):
                            content_types.append('structured')
                        elif content_data.get('content', {}).get('paragraphs'):
                            content_types.append('article')
                        else:
                            content_types.append('minimal')
                        
                        # Analyze content length
                        main_content = content_data.get('content', {}).get('main', '')
                        content_lengths.append(len(main_content))
                        
                    except Exception as e:
                        logger.debug(f"Failed to analyze content for {result.url}: {e}")
                        continue
            
            # Store content analysis results
            if content_types:
                analysis.content_gaps = self._identify_content_gaps_from_analysis(content_types, content_lengths)
            
        except Exception as e:
            logger.warning(f"Failed to analyze content structure: {e}")
    
    def _identify_content_gaps_from_analysis(self, content_types: List[str], content_lengths: List[int]) -> List[str]:
        """Identify content gaps from content analysis."""
        gaps = []
        
        # Check for content type diversity
        if len(set(content_types)) < 2:
            gaps.append("Limited content type diversity")
        
        # Check for content length consistency
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            if avg_length < 1000:  # Less than 1000 characters
                gaps.append("Short content pieces")
            elif avg_length > 10000:  # More than 10k characters
                gaps.append("Very long content pieces")
        
        return gaps
    
    async def _analyze_competition(self, analysis: KeywordAnalysis, target_domain: Optional[str]):
        """Analyze competition for the keyword."""
        try:
            if not target_domain:
                return
            
            # Analyze competitor strength
            competitor_scores = []
            
            for domain in analysis.competitor_domains[:5]:  # Top 5 competitors
                if self.semrush_client:
                    try:
                        domain_data = await self.semrush_client.get_domain_overview(domain)
                        
                        # Calculate competitor score based on domain authority
                        if domain_data.authority_score:
                            competitor_scores.append(domain_data.authority_score)
                        
                    except Exception as e:
                        logger.debug(f"Failed to analyze competitor {domain}: {e}")
                        continue
            
            # Update competition analysis
            if competitor_scores:
                avg_competitor_score = sum(competitor_scores) / len(competitor_scores)
                analysis.competition = min(avg_competitor_score / 100, 1.0)  # Normalize to 0-1
                
                # Adjust keyword difficulty based on competition
                if analysis.keyword_difficulty:
                    competition_factor = analysis.competition * 20  # Competition can add up to 20 points
                    analysis.keyword_difficulty = min(100, analysis.keyword_difficulty + competition_factor)
            
        except Exception as e:
            logger.warning(f"Failed to analyze competition: {e}")
    
    def _calculate_scores(self, analysis: KeywordAnalysis):
        """Calculate relevance and opportunity scores."""
        try:
            # Calculate relevance score (0-100)
            relevance_factors = []
            
            # Search volume relevance
            if analysis.search_volume:
                if analysis.search_volume >= 10000:
                    relevance_factors.append(100)
                elif analysis.search_volume >= 5000:
                    relevance_factors.append(80)
                elif analysis.search_volume >= 1000:
                    relevance_factors.append(60)
                elif analysis.search_volume >= 100:
                    relevance_factors.append(40)
                else:
                    relevance_factors.append(20)
            else:
                relevance_factors.append(50)  # Default score
            
            # Keyword difficulty relevance (lower difficulty = higher relevance)
            if analysis.keyword_difficulty is not None:
                difficulty_score = max(0, 100 - analysis.keyword_difficulty)
                relevance_factors.append(difficulty_score)
            else:
                relevance_factors.append(50)
            
            # CPC relevance (higher CPC = higher relevance)
            if analysis.cpc:
                cpc_score = min(100, analysis.cpc * 20)  # Scale CPC to 0-100
                relevance_factors.append(cpc_score)
            else:
                relevance_factors.append(50)
            
            # Calculate average relevance score
            analysis.relevance_score = sum(relevance_factors) / len(relevance_factors)
            
            # Calculate opportunity score
            analysis.opportunity_score = self._calculate_opportunity_score(analysis)
            
        except Exception as e:
            logger.warning(f"Failed to calculate scores: {e}")
    
    def _calculate_opportunity_score(self, analysis: KeywordAnalysis) -> float:
        """Calculate comprehensive opportunity score."""
        try:
            scores = {}
            
            # Search volume score (0-100)
            if analysis.search_volume:
                volume_score = min(100, analysis.search_volume / 100)
                scores['search_volume'] = volume_score
            else:
                scores['search_volume'] = 50
            
            # Keyword difficulty score (lower difficulty = higher opportunity)
            if analysis.keyword_difficulty is not None:
                difficulty_score = max(0, 100 - analysis.keyword_difficulty)
                scores['keyword_difficulty'] = difficulty_score
            else:
                scores['keyword_difficulty'] = 50
            
            # CPC score (higher CPC = higher opportunity)
            if analysis.cpc:
                cpc_score = min(100, analysis.cpc * 20)
                scores['cpc'] = cpc_score
            else:
                scores['cpc'] = 50
            
            # Competition score (lower competition = higher opportunity)
            if analysis.competition is not None:
                competition_score = (1 - analysis.competition) * 100
                scores['competition'] = competition_score
            else:
                scores['competition'] = 50
            
            # Relevance score
            scores['relevance'] = analysis.relevance_score
            
            # Calculate weighted opportunity score
            opportunity_score = sum(
                scores[factor] * self.scoring_weights[factor]
                for factor in self.scoring_weights.keys()
            )
            
            return round(opportunity_score, 2)
            
        except Exception as e:
            logger.warning(f"Failed to calculate opportunity score: {e}")
            return 0.0
    
    async def _identify_content_gaps(self, analysis: KeywordAnalysis):
        """Identify content gaps and opportunities."""
        try:
            gaps = []
            
            # Check for featured snippet opportunity
            if 'featured_snippet' not in analysis.serp_features:
                gaps.append("Featured snippet opportunity")
            
            # Check for people also ask opportunity
            if 'people_also_ask' not in analysis.serp_features:
                gaps.append("People also ask opportunity")
            
            # Check for video opportunity
            if 'video' not in analysis.serp_features:
                gaps.append("Video content opportunity")
            
            # Check for local opportunity
            if 'local_pack' not in analysis.serp_features:
                gaps.append("Local SEO opportunity")
            
            # Add identified gaps from content analysis
            if analysis.content_gaps:
                gaps.extend(analysis.content_gaps)
            
            analysis.content_gaps = list(set(gaps))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"Failed to identify content gaps: {e}")
    
    async def _find_related_keywords(self, analysis: KeywordAnalysis):
        """Find related keywords and suggestions."""
        try:
            if self.semrush_client:
                related_keywords = await self.semrush_client.get_keyword_suggestions(
                    analysis.keyword, limit=20
                )
                
                # Extract keyword terms
                analysis.related_keywords = [
                    kw.keyword for kw in related_keywords
                ]
                
                logger.debug(f"Found {len(analysis.related_keywords)} related keywords")
            
        except Exception as e:
            logger.warning(f"Failed to find related keywords: {e}")
    
    async def analyze_keyword_batch(self, 
                                  keywords: List[str], 
                                  target_domain: Optional[str] = None,
                                  max_concurrent: int = 5) -> List[KeywordAnalysis]:
        """
        Analyze multiple keywords concurrently.
        
        Args:
            keywords: List of keywords to analyze
            target_domain: Domain to analyze against
            max_concurrent: Maximum concurrent analysis tasks
            
        Returns:
            List of KeywordAnalysis objects
        """
        logger.info(f"Starting batch analysis for {len(keywords)} keywords")
        
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single(keyword: str) -> KeywordAnalysis:
            async with semaphore:
                return await self.analyze_keyword(keyword, target_domain)
        
        # Create tasks for all keywords
        tasks = [analyze_single(keyword) for keyword in keywords]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        analyses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze keyword '{keywords[i]}': {result}")
            else:
                analyses.append(result)
        
        logger.info(f"Batch analysis completed: {len(analyses)} successful, {len(keywords) - len(analyses)} failed")
        return analyses
    
    def filter_keywords_by_criteria(self, 
                                  analyses: List[KeywordAnalysis],
                                  min_search_volume: Optional[int] = None,
                                  max_keyword_difficulty: Optional[int] = None,
                                  min_opportunity_score: Optional[float] = None,
                                  min_relevance_score: Optional[float] = None) -> List[KeywordAnalysis]:
        """
        Filter keyword analyses based on criteria.
        
        Args:
            analyses: List of KeywordAnalysis objects
            min_search_volume: Minimum search volume
            max_keyword_difficulty: Maximum keyword difficulty
            min_opportunity_score: Minimum opportunity score
            min_relevance_score: Minimum relevance score
            
        Returns:
            Filtered list of KeywordAnalysis objects
        """
        filtered = []
        
        for analysis in analyses:
            # Apply filters
            if min_search_volume and (not analysis.search_volume or analysis.search_volume < min_search_volume):
                continue
            
            if max_keyword_difficulty and (not analysis.keyword_difficulty or analysis.keyword_difficulty > max_keyword_difficulty):
                continue
            
            if min_opportunity_score and analysis.opportunity_score < min_opportunity_score:
                continue
            
            if min_relevance_score and analysis.relevance_score < min_relevance_score:
                continue
            
            filtered.append(analysis)
        
        return filtered
    
    def rank_keywords_by_opportunity(self, analyses: List[KeywordAnalysis]) -> List[KeywordAnalysis]:
        """Rank keywords by opportunity score (descending)."""
        return sorted(analyses, key=lambda x: x.opportunity_score, reverse=True)
    
    def rank_keywords_by_relevance(self, analyses: List[KeywordAnalysis]) -> List[KeywordAnalysis]:
        """Rank keywords by relevance score (descending)."""
        return sorted(analyses, key=lambda x: x.relevance_score, reverse=True)
    
    def get_keyword_recommendations(self, 
                                  analyses: List[KeywordAnalysis],
                                  max_recommendations: int = 10,
                                  strategy: str = "balanced") -> List[KeywordAnalysis]:
        """
        Get keyword recommendations based on strategy.
        
        Args:
            analyses: List of KeywordAnalysis objects
            max_recommendations: Maximum number of recommendations
            strategy: Recommendation strategy (balanced, opportunity, relevance, volume)
            
        Returns:
            List of recommended KeywordAnalysis objects
        """
        if strategy == "opportunity":
            ranked = self.rank_keywords_by_opportunity(analyses)
        elif strategy == "relevance":
            ranked = self.rank_keywords_by_relevance(analyses)
        elif strategy == "volume":
            ranked = sorted(analyses, key=lambda x: x.search_volume or 0, reverse=True)
        else:  # balanced
            # Calculate combined score
            for analysis in analyses:
                combined_score = (analysis.opportunity_score * 0.6 + 
                               analysis.relevance_score * 0.4)
                analysis.combined_score = combined_score
            
            ranked = sorted(analyses, key=lambda x: getattr(x, 'combined_score', 0), reverse=True)
        
        return ranked[:max_recommendations]
    
    def export_analysis_to_json(self, analyses: List[KeywordAnalysis], filepath: str = None) -> str:
        """
        Export keyword analyses to JSON format.
        
        Args:
            analyses: List of KeywordAnalysis objects
            filepath: Path to save JSON file (optional)
            
        Returns:
            JSON string or filepath
        """
        # Convert analyses to serializable format
        export_data = []
        for analysis in analyses:
            analysis_data = {
                'keyword': analysis.keyword,
                'search_volume': analysis.search_volume,
                'cpc': analysis.cpc,
                'competition': analysis.competition,
                'keyword_difficulty': analysis.keyword_difficulty,
                'relevance_score': analysis.relevance_score,
                'opportunity_score': analysis.opportunity_score,
                'serp_features': analysis.serp_features,
                'competitor_domains': analysis.competitor_domains,
                'content_gaps': analysis.content_gaps,
                'related_keywords': analysis.related_keywords,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat() if analysis.analysis_timestamp else None
            }
            export_data.append(analysis_data)
        
        json_string = json.dumps(export_data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_string)
            return filepath
        else:
            return json_string


# Example usage and testing
async def test_keyword_analyzer():
    """Test the keyword analyzer functionality."""
    try:
        # Initialize analyzer (without external dependencies for testing)
        analyzer = KeywordAnalyzer()
        
        print("Testing keyword analyzer...")
        
        # Test scoring calculations
        test_analysis = KeywordAnalysis(
            keyword="test keyword",
            search_volume=5000,
            keyword_difficulty=45,
            cpc=2.50,
            competition=0.6
        )
        
        # Calculate scores
        analyzer._calculate_scores(test_analysis)
        
        print(f"Keyword: {test_analysis.keyword}")
        print(f"Relevance Score: {test_analysis.relevance_score}")
        print(f"Opportunity Score: {test_analysis.opportunity_score}")
        
        print("\nKeyword analyzer is ready for use!")
        
    except Exception as e:
        logger.error(f"Keyword analyzer test failed: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_keyword_analyzer())