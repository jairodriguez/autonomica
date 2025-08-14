"""
SEO Data Processing Pipeline

This module provides a comprehensive data processing pipeline that integrates:
- SEMrush API data
- SERP scraping data
- Keyword clustering results
- Keyword analysis metrics
- Data cleaning and normalization
- Integration of multiple data sources
- Batch processing capabilities
- Data export and reporting
"""

import asyncio
import logging
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict
import numpy as np

from app.services.redis_service import RedisService
from app.services.seo_service import SEOService
from app.services.serp_scraper import SERPScraper
from app.services.keyword_clustering import KeywordClusteringService
from app.services.keyword_analyzer import KeywordAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ProcessedKeywordData:
    """Comprehensive processed keyword data"""
    keyword: str
    semrush_data: Optional[Dict[str, Any]] = None
    serp_data: Optional[Dict[str, Any]] = None
    clustering_data: Optional[Dict[str, Any]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    opportunity_score: Optional[float] = None
    cluster_id: Optional[int] = None
    intent_type: Optional[str] = None
    commercial_potential: Optional[float] = None
    ranking_difficulty: Optional[str] = None
    estimated_roi: Optional[float] = None
    time_to_rank: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class PipelineResult:
    """Result of data processing pipeline"""
    keywords_processed: int
    keywords_failed: int
    processing_time: float
    clusters_created: int
    data_summary: Dict[str, Any]
    recommendations: List[str]
    export_data: Optional[str] = None
    created_at: datetime

@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics"""
    total_keywords: int
    complete_data_count: int
    partial_data_count: int
    missing_data_count: int
    data_completeness: float
    data_accuracy: float
    processing_errors: List[str]
    quality_score: float

class SEODataPipeline:
    """Comprehensive SEO data processing pipeline"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.seo_service = SEOService()
        self.serp_scraper = SERPScraper()
        self.clustering_service = KeywordClusteringService()
        self.keyword_analyzer = KeywordAnalyzer()
        
        # Pipeline configuration
        self.pipeline_config = {
            "max_concurrent_requests": 5,
            "batch_size": 50,
            "retry_attempts": 3,
            "retry_delay": 2,
            "cache_ttl": 3600 * 24,  # 24 hours
            "data_quality_threshold": 0.8
        }
        
        # Data source priorities
        self.data_sources = [
            "semrush",
            "serp_scraping",
            "clustering",
            "analysis"
        ]
        
        # Required fields for complete data
        self.required_fields = {
            "semrush": ["search_volume", "cpc", "keyword_difficulty"],
            "serp": ["total_results", "results"],
            "clustering": ["cluster_id", "intent_type"],
            "analysis": ["opportunity_score", "difficulty_level"]
        }
    
    async def _get_cached_pipeline_data(self, keywords: List[str], pipeline_type: str) -> Optional[Any]:
        """Retrieve cached pipeline data from Redis"""
        keywords_hash = hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()
        cache_key = f"pipeline:{pipeline_type}:{keywords_hash}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached pipeline data: {e}")
        
        return None
    
    async def _cache_pipeline_data(self, keywords: List[str], pipeline_type: str, data: Any) -> bool:
        """Cache pipeline data in Redis"""
        keywords_hash = hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()
        cache_key = f"pipeline:{pipeline_type}:{keywords_hash}"
        
        try:
            await self.redis_service.set(
                cache_key,
                json.dumps(data, default=str),
                expire=self.pipeline_config["cache_ttl"] # Corrected from cache_ttreshold to cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache pipeline data: {e}")
            return False
    
    async def _process_semrush_data(self, keywords: List[str], country: str = "us") -> Dict[str, Any]:
        """Process SEMrush data for keywords"""
        semrush_results = {}
        
        # Process keywords in batches
        for i in range(0, len(keywords), self.pipeline_config["batch_size"]):
            batch = keywords[i:i + self.pipeline_config["batch_size"]]
            
            # Process batch concurrently
            tasks = []
            for keyword in batch:
                task = self.seo_service.get_semrush_keyword_data(keyword, country)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for keyword, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to get SEMrush data for '{keyword}': {result}")
                    semrush_results[keyword] = None
                else:
                    semrush_results[keyword] = result
        
        return semrush_results
    
    async def _process_serp_data(self, keywords: List[str], country: str = "us") -> Dict[str, Any]:
        """Process SERP data for keywords"""
        serp_results = {}
        
        try:
            async with self.serp_scraper as scraper:
                # Process keywords in batches
                for i in range(0, len(keywords), self.pipeline_config["batch_size"]):
                    batch = keywords[i:i + self.pipeline_config["batch_size"]]
                    
                    # Process batch concurrently
                    tasks = []
                    for keyword in batch:
                        task = scraper.scrape_serp_data(keyword, country)
                        tasks.append(task)
                    
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for keyword, result in zip(batch, batch_results):
                        if isinstance(result, Exception):
                            logger.warning(f"Failed to get SERP data for '{keyword}': {result}")
                            serp_results[keyword] = None
                        else:
                            serp_results[keyword] = result
                    
                    # Add delay between batches to respect rate limits
                    if i + self.pipeline_config["batch_size"] < len(keywords):
                        await asyncio.sleep(self.pipeline_config["retry_delay"])
        
        except Exception as e:
            logger.error(f"Failed to process SERP data: {e}")
            # Return empty results on failure
            for keyword in keywords:
                serp_results[keyword] = None
        
        return serp_results
    
    async def _process_clustering_data(self, keywords: List[str], algorithm: str = "auto") -> Dict[str, Any]:
        """Process keyword clustering data"""
        try:
            clustering_result = await self.clustering_service.cluster_keywords(
                keywords, algorithm, optimize=True
            )
            
            # Create keyword to cluster mapping
            clustering_data = {}
            for cluster_id, cluster in clustering_result.clusters.items():
                for keyword in cluster.keywords:
                    clustering_data[keyword] = {
                        "cluster_id": cluster_id,
                        "intent_type": cluster.intent_type,
                        "cluster_size": cluster.size,
                        "cluster_score": cluster.cluster_score,
                        "primary_keyword": cluster.primary_keyword
                    }
            
            return clustering_data
            
        except Exception as e:
            logger.error(f"Failed to process clustering data: {e}")
            return {}
    
    async def _process_analysis_data(self, keywords: List[str], country: str = "us") -> Dict[str, Any]:
        """Process keyword analysis data"""
        analysis_results = {}
        
        # Process keywords in batches
        for i in range(0, len(keywords), self.pipeline_config["batch_size"]):
            batch = keywords[i:i + self.pipeline_config["batch_size"]]
            
            # Process batch concurrently
            tasks = []
            for keyword in batch:
                task = self.keyword_analyzer.get_keyword_insights(keyword, country)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for keyword, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to get analysis data for '{keyword}': {result}")
                    analysis_results[keyword] = None
                else:
                    analysis_results[keyword] = result
        
        return analysis_results
    
    def _normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, ProcessedKeywordData]:
        """Normalize and clean raw data from all sources"""
        normalized_data = {}
        
        for keyword in raw_data.get("keywords", []):
            try:
                # Extract data from each source
                semrush_data = raw_data.get("semrush", {}).get(keyword)
                serp_data = raw_data.get("serp", {}).get(keyword)
                clustering_data = raw_data.get("clustering", {}).get(keyword)
                analysis_data = raw_data.get("analysis", {}).get(keyword)
                
                # Create normalized data structure
                processed_data = ProcessedKeywordData(
                    keyword=keyword,
                    semrush_data=semrush_data.__dict__ if semrush_data else None,
                    serp_data=serp_data.__dict__ if serp_data else None,
                    clustering_data=clustering_data,
                    analysis_data=analysis_data,
                    created_at=datetime.now()
                )
                
                # Extract key metrics
                if analysis_data:
                    processed_data.opportunity_score = analysis_data.get("opportunity", {}).get("opportunity_score")
                    processed_data.estimated_roi = analysis_data.get("opportunity", {}).get("estimated_roi")
                    processed_data.time_to_rank = analysis_data.get("opportunity", {}).get("time_to_rank")
                
                if clustering_data:
                    processed_data.cluster_id = clustering_data.get("cluster_id")
                    processed_data.intent_type = clustering_data.get("intent_type")
                
                if analysis_data and analysis_data.get("metrics"):
                    metrics = analysis_data["metrics"]
                    processed_data.commercial_potential = metrics.get("commercial_intent")
                    processed_data.ranking_difficulty = metrics.get("difficulty_score")
                
                normalized_data[keyword] = processed_data
                
            except Exception as e:
                logger.warning(f"Failed to normalize data for '{keyword}': {e}")
                # Create minimal data structure on failure
                normalized_data[keyword] = ProcessedKeywordData(
                    keyword=keyword,
                    created_at=datetime.now()
                )
        
        return normalized_data
    
    def _assess_data_quality(self, normalized_data: Dict[str, ProcessedKeywordData]) -> DataQualityMetrics:
        """Assess the quality of processed data"""
        total_keywords = len(normalized_data)
        complete_data_count = 0
        partial_data_count = 0
        missing_data_count = 0
        processing_errors = []
        
        for keyword, data in normalized_data.items():
            # Check data completeness
            data_sources = [
                data.semrush_data is not None,
                data.serp_data is not None,
                data.clustering_data is not None,
                data.analysis_data is not None
            ]
            
            completeness = sum(data_sources) / len(data_sources)
            
            if completeness >= self.pipeline_config["data_quality_threshold"]:
                complete_data_count += 1
            elif completeness > 0:
                partial_data_count += 1
            else:
                missing_data_count += 1
                processing_errors.append(f"No data for keyword: {keyword}")
        
        # Calculate quality metrics
        data_completeness = complete_data_count / total_keywords if total_keywords > 0 else 0
        data_accuracy = (complete_data_count + partial_data_count * 0.5) / total_keywords if total_keywords > 0 else 0
        quality_score = (data_completeness * 0.7 + data_accuracy * 0.3) * 100
        
        return DataQualityMetrics(
            total_keywords=total_keywords,
            complete_data_count=complete_data_count,
            partial_data_count=partial_data_count,
            missing_data_count=missing_data_count,
            data_completeness=data_completeness,
            data_accuracy=data_accuracy,
            processing_errors=processing_errors,
            quality_score=round(quality_score, 2)
        )
    
    async def process_keywords(self, keywords: List[str], country: str = "us", 
                             algorithm: str = "auto", include_serp: bool = True) -> PipelineResult:
        """
        Process keywords through the complete SEO pipeline
        
        Args:
            keywords: List of keywords to process
            country: Country for localized analysis
            algorithm: Clustering algorithm to use
            include_serp: Whether to include SERP scraping (can be slow)
        
        Returns:
            Complete pipeline result
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = f"pipeline_complete:{country}:{algorithm}:{include_serp}"
        cached_result = await self._get_cached_pipeline_data(keywords, cache_key)
        if cached_result:
            logger.info(f"Retrieved cached pipeline result for {len(keywords)} keywords")
            return PipelineResult(**cached_result)
        
        try:
            logger.info(f"Starting SEO pipeline for {len(keywords)} keywords")
            
            # Process data from all sources
            pipeline_data = {
                "keywords": keywords,
                "semrush": {},
                "serp": {},
                "clustering": {},
                "analysis": {}
            }
            
            # Process SEMrush data
            logger.info("Processing SEMrush data...")
            pipeline_data["semrush"] = await self._process_semrush_data(keywords, country)
            
            # Process SERP data (optional)
            if include_serp:
                logger.info("Processing SERP data...")
                pipeline_data["serp"] = await self._process_serp_data(keywords, country)
            
            # Process clustering data
            logger.info("Processing clustering data...")
            pipeline_data["clustering"] = await self._process_clustering_data(keywords, algorithm)
            
            # Process analysis data
            logger.info("Processing analysis data...")
            pipeline_data["analysis"] = await self._process_analysis_data(keywords, country)
            
            # Normalize and clean data
            logger.info("Normalizing data...")
            normalized_data = self._normalize_data(pipeline_data)
            
            # Assess data quality
            logger.info("Assessing data quality...")
            quality_metrics = self._assess_data_quality(normalized_data)
            
            # Generate recommendations
            recommendations = self._generate_pipeline_recommendations(quality_metrics, normalized_data)
            
            # Create data summary
            data_summary = self._create_data_summary(normalized_data, quality_metrics)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create pipeline result
            result = PipelineResult(
                keywords_processed=len(keywords),
                keywords_failed=quality_metrics.missing_data_count,
                processing_time=processing_time,
                clusters_created=len(set(data.get("cluster_id") for data in normalized_data.values() if data.get("cluster_id") is not None)),
                data_summary=data_summary,
                recommendations=recommendations,
                created_at=datetime.now()
            )
            
            # Cache the result
            await self._cache_pipeline_data(keywords, cache_key, asdict(result))
            
            logger.info(f"SEO pipeline completed successfully in {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"SEO pipeline failed: {e}")
            # Return minimal result on failure
            return PipelineResult(
                keywords_processed=0,
                keywords_failed=len(keywords),
                processing_time=0.0,
                clusters_created=0,
                data_summary={"error": str(e)},
                recommendations=["Pipeline failed - please check logs and try again"],
                created_at=datetime.now()
            )
    
    def _generate_pipeline_recommendations(self, quality_metrics: DataQualityMetrics,
                                         normalized_data: Dict[str, ProcessedKeywordData]) -> List[str]:
        """Generate recommendations based on pipeline results"""
        recommendations = []
        
        # Data quality recommendations
        if quality_metrics.data_completeness < 0.8:
            recommendations.append("Low data completeness - check API configurations and rate limits")
        
        if quality_metrics.missing_data_count > 0:
            recommendations.append(f"{quality_metrics.missing_data_count} keywords have missing data - consider reprocessing")
        
        # Clustering recommendations
        cluster_sizes = defaultdict(int)
        for data in normalized_data.values():
            if data.cluster_id is not None:
                cluster_sizes[data.cluster_id] += 1
        
        if len(cluster_sizes) > 10:
            recommendations.append("Many small clusters detected - consider adjusting clustering parameters")
        elif len(cluster_sizes) < 3:
            recommendations.append("Few clusters detected - consider decreasing similarity threshold")
        
        # Opportunity recommendations
        high_opportunity_keywords = [
            data.keyword for data in normalized_data.values()
            if data.opportunity_score and data.opportunity_score >= 80
        ]
        
        if high_opportunity_keywords:
            recommendations.append(f"Found {len(high_opportunity_keywords)} high-opportunity keywords - prioritize these")
        
        # Intent distribution recommendations
        intent_distribution = defaultdict(int)
        for data in normalized_data.values():
            if data.intent_type:
                intent_distribution[data.intent_type] += 1
        
        if intent_distribution:
            dominant_intent = max(intent_distribution, key=intent_distribution.get)
            recommendations.append(f"Dominant intent: {dominant_intent} - ensure content strategy aligns with user intent")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _create_data_summary(self, normalized_data: Dict[str, ProcessedKeywordData],
                           quality_metrics: DataQualityMetrics) -> Dict[str, Any]:
        """Create comprehensive data summary"""
        summary = {
            "total_keywords": quality_metrics.total_keywords,
            "data_quality": {
                "completeness": quality_metrics.data_completeness,
                "accuracy": quality_metrics.data_accuracy,
                "quality_score": quality_metrics.quality_score
            },
            "clustering": {
                "total_clusters": len(set(data.get("cluster_id") for data in normalized_data.values() if data.get("cluster_id") is not None)),
                "clustered_keywords": sum(1 for data in normalized_data.values() if data.get("cluster_id") is not None)
            },
            "opportunity_analysis": {
                "high_opportunity": sum(1 for data in normalized_data.values() if data.get("opportunity_score", 0) >= 80),
                "medium_opportunity": sum(1 for data in normalized_data.values() if 50 <= data.get("opportunity_score", 0) < 80),
                "low_opportunity": sum(1 for data in normalized_data.values() if data.get("opportunity_score", 0) < 50)
            },
            "intent_distribution": defaultdict(int),
            "difficulty_distribution": defaultdict(int),
            "commercial_potential": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Calculate distributions
        for data in normalized_data.values():
            if data.intent_type:
                summary["intent_distribution"][data.intent_type] += 1
            
            if data.ranking_difficulty:
                if data.ranking_difficulty >= 80:
                    summary["difficulty_distribution"]["very_high"] += 1
                elif data.ranking_difficulty >= 60:
                    summary["difficulty_distribution"]["high"] += 1
                elif data.ranking_difficulty >= 40:
                    summary["difficulty_distribution"]["medium"] += 1
                elif data.ranking_difficulty >= 20:
                    summary["difficulty_distribution"]["low"] += 1
                else:
                    summary["difficulty_distribution"]["very_low"] += 1
            
            if data.commercial_potential:
                if data.commercial_potential >= 80:
                    summary["commercial_potential"]["high"] += 1
                elif data.commercial_potential >= 50:
                    summary["commercial_potential"]["medium"] += 1
                else:
                    summary["commercial_potential"]["low"] += 1
        
        return summary
    
    async def export_pipeline_results(self, normalized_data: Dict[str, ProcessedKeywordData],
                                    format: str = "json") -> str:
        """
        Export pipeline results in various formats
        
        Args:
            normalized_data: Normalized keyword data
            format: Export format (json, csv, xlsx)
        
        Returns:
            Exported data as string or file path
        """
        try:
            if format.lower() == "json":
                # Convert to serializable format
                export_data = []
                for keyword, data in normalized_data.items():
                    data_dict = asdict(data)
                    # Convert datetime objects to strings
                    if data_dict.get("created_at"):
                        data_dict["created_at"] = data_dict["created_at"].isoformat()
                    export_data.append(data_dict)
                
                return json.dumps(export_data, indent=2, default=str)
                
            elif format.lower() == "csv":
                # Create CSV with key metrics
                csv_lines = [
                    "keyword,opportunity_score,cluster_id,intent_type,commercial_potential,ranking_difficulty,estimated_roi,time_to_rank"
                ]
                
                for keyword, data in normalized_data.items():
                    csv_lines.append(
                        f"{keyword},{data.opportunity_score or ''},{data.cluster_id or ''},"
                        f"{data.intent_type or ''},{data.commercial_potential or ''},"
                        f"{data.ranking_difficulty or ''},{data.estimated_roi or ''},"
                        f"{data.time_to_rank or ''}"
                    )
                
                return "\n".join(csv_lines)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export pipeline results: {e}")
            return json.dumps({"error": str(e)})
    
    async def get_pipeline_status(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Get status of pipeline processing for keywords
        
        Args:
            keywords: List of keywords to check
        
        Returns:
            Pipeline status information
        """
        try:
            status = {
                "keywords": keywords,
                "total_keywords": len(keywords),
                "data_sources": {},
                "processing_status": "unknown",
                "last_updated": None,
                "cache_status": "unknown"
            }
            
            # Check cache status for each data source
            for source in self.data_sources:
                cache_key = f"pipeline_{source}:{hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()}"
                
                try:
                    cached = await self.redis_service.get(cache_key)
                    status["data_sources"][source] = "cached" if cached else "not_cached"
                except Exception:
                    status["data_sources"][source] = "error"
            
            # Determine overall processing status
            cached_sources = sum(1 for source_status in status["data_sources"].values() if source_status == "cached")
            
            if cached_sources == len(self.data_sources):
                status["processing_status"] = "complete"
                status["cache_status"] = "fully_cached"
            elif cached_sources > 0:
                status["processing_status"] = "partial"
                status["cache_status"] = "partially_cached"
            else:
                status["processing_status"] = "not_started"
                status["cache_status"] = "not_cached"
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return {
                "keywords": keywords,
                "error": str(e),
                "processing_status": "error"
            }
    
    async def reprocess_failed_keywords(self, original_keywords: List[str], 
                                      country: str = "us") -> PipelineResult:
        """
        Reprocess keywords that failed in the initial pipeline run
        
        Args:
            original_keywords: List of keywords from original run
            country: Country for localized analysis
        
        Returns:
            Pipeline result for reprocessing
        """
        try:
            # Get pipeline status to identify failed keywords
            status = await self.get_pipeline_status(original_keywords)
            
            # Identify keywords that need reprocessing
            failed_keywords = []
            for keyword in original_keywords:
                keyword_status = await self._check_keyword_status(keyword, country)
                if keyword_status["status"] == "failed":
                    failed_keywords.append(keyword)
            
            if not failed_keywords:
                logger.info("No failed keywords to reprocess")
                return PipelineResult(
                    keywords_processed=0,
                    keywords_failed=0,
                    processing_time=0.0,
                    clusters_created=0,
                    data_summary={"message": "No failed keywords to reprocess"},
                    recommendations=["All keywords processed successfully"],
                    created_at=datetime.now()
                )
            
            logger.info(f"Reprocessing {len(failed_keywords)} failed keywords")
            
            # Reprocess only failed keywords
            return await self.process_keywords(failed_keywords, country, include_serp=True)
            
        except Exception as e:
            logger.error(f"Failed to reprocess keywords: {e}")
            return PipelineResult(
                keywords_processed=0,
                keywords_failed=len(original_keywords),
                processing_time=0.0,
                clusters_created=0,
                data_summary={"error": str(e)},
                recommendations=["Reprocessing failed - please check logs"],
                created_at=datetime.now()
            )
    
    async def _check_keyword_status(self, keyword: str, country: str) -> Dict[str, Any]:
        """Check individual keyword processing status"""
        try:
            status = {
                "keyword": keyword,
                "status": "unknown",
                "data_sources": {},
                "last_checked": datetime.now().isoformat()
            }
            
            # Check each data source
            try:
                semrush_data = await self.seo_service.get_semrush_keyword_data(keyword, country)
                status["data_sources"]["semrush"] = "available" if semrush_data else "failed"
            except Exception:
                status["data_sources"]["semrush"] = "error"
            
            try:
                analysis_data = await self.keyword_analyzer.get_keyword_insights(keyword, country)
                status["data_sources"]["analysis"] = "available" if analysis_data and "error" not in analysis_data else "failed"
            except Exception:
                status["data_sources"]["analysis"] = "error"
            
            # Determine overall status
            available_sources = sum(1 for source_status in status["data_sources"].values() if source_status == "available")
            
            if available_sources >= 2:
                status["status"] = "complete"
            elif available_sources >= 1:
                status["status"] = "partial"
            else:
                status["status"] = "failed"
            
            return status
            
        except Exception as e:
            return {
                "keyword": keyword,
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }