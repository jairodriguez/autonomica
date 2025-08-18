"""
SEO Data Processing Pipeline Module
Integrates all SEO components into a cohesive data processing system
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
from pathlib import Path

from app.services.seo_service import SEOService, create_seo_service
from app.services.keyword_clustering import KeywordClusterer
from app.services.competitor_analysis import CompetitorAnalyzer
from app.services.keyword_analysis import KeywordAnalyzer, KeywordMetrics, KeywordIntent, KeywordType
from app.config.seo_config import seo_settings, validate_seo_config

# Configure logging
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline processing stages"""
    INITIALIZATION = "initialization"
    KEYWORD_RESEARCH = "keyword_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    KEYWORD_CLUSTERING = "keyword_clustering"
    KEYWORD_ANALYSIS = "keyword_analysis"
    INSIGHTS_GENERATION = "insights_generation"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    pipeline_id: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    stages_completed: List[PipelineStage] = None
    current_stage: Optional[PipelineStage] = None
    results: Dict[str, Any] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.stages_completed is None:
            self.stages_completed = []
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class KeywordResearchRequest:
    """Request for keyword research pipeline"""
    primary_keywords: List[str]
    competitor_domains: List[str]
    target_database: str = "us"
    analysis_depth: str = "comprehensive"
    include_competitors: bool = True
    include_clustering: bool = True
    include_opportunity_analysis: bool = True
    max_keywords_per_analysis: int = 100
    max_competitors_per_domain: int = 20


class SEODataPipeline:
    """Main SEO data processing pipeline that orchestrates all components"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.seo_service = None
        self.keyword_clusterer = None
        self.competitor_analyzer = None
        self.keyword_analyzer = None
        self.pipeline_cache = {}
        self.active_pipelines = {}
        
        # Pipeline configuration
        self.max_concurrent_pipelines = 3
        self.pipeline_timeout = 300  # 5 minutes
        self.enable_caching = True
        self.cache_ttl = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize all SEO service components"""
        try:
            self.logger.info("Initializing SEO Data Pipeline...")
            
            # Validate configuration
            config_status = validate_seo_config()
            if not config_status["valid"]:
                missing_keys = config_status["missing_keys"]
                raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
            
            # Initialize services
            self.seo_service = await create_seo_service()
            self.keyword_clusterer = KeywordClusterer(
                similarity_threshold=seo_settings.KEYWORD_CLUSTERING_THRESHOLD
            )
            self.competitor_analyzer = CompetitorAnalyzer(
                max_concurrent_requests=seo_settings.MAX_CONCURRENT_REQUESTS,
                request_timeout=seo_settings.REQUEST_TIMEOUT
            )
            self.keyword_analyzer = KeywordAnalyzer()
            
            self.logger.info("SEO Data Pipeline initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SEO Data Pipeline: {e}")
            raise
    
    async def execute_pipeline(self, request: KeywordResearchRequest) -> PipelineResult:
        """Execute the complete SEO data processing pipeline"""
        pipeline_id = self._generate_pipeline_id(request)
        
        # Check if pipeline is already running
        if pipeline_id in self.active_pipelines:
            raise RuntimeError(f"Pipeline {pipeline_id} is already running")
        
        # Check cache for existing results
        if self.enable_caching and pipeline_id in self.pipeline_cache:
            cached_result = self.pipeline_cache[pipeline_id]
            if self._is_cache_valid(cached_result):
                self.logger.info(f"Returning cached results for pipeline {pipeline_id}")
                return cached_result
        
        # Create pipeline result
        pipeline_result = PipelineResult(
            pipeline_id=pipeline_id,
            status=PipelineStatus.IN_PROGRESS,
            start_time=datetime.now(),
            current_stage=PipelineStage.INITIALIZATION,
            metadata={
                "request": asdict(request),
                "config": {
                    "max_keywords": request.max_keywords_per_analysis,
                    "max_competitors": request.max_competitors_per_domain,
                    "analysis_depth": request.analysis_depth
                }
            }
        )
        
        try:
            # Add to active pipelines
            self.active_pipelines[pipeline_id] = pipeline_result
            
            # Execute pipeline stages
            await self._execute_pipeline_stages(pipeline_result, request)
            
            # Mark as completed
            pipeline_result.status = PipelineStatus.COMPLETED
            pipeline_result.end_time = datetime.now()
            pipeline_result.current_stage = PipelineStage.COMPLETED
            
            # Cache results
            if self.enable_caching:
                self.pipeline_cache[pipeline_id] = pipeline_result
            
            self.logger.info(f"Pipeline {pipeline_id} completed successfully")
            
        except Exception as e:
            pipeline_result.status = PipelineStatus.FAILED
            pipeline_result.end_time = datetime.now()
            pipeline_result.errors.append(str(e))
            self.logger.error(f"Pipeline {pipeline_id} failed: {e}")
            
        finally:
            # Remove from active pipelines
            if pipeline_id in self.active_pipelines:
                del self.active_pipelines[pipeline_id]
        
        return pipeline_result
    
    async def _execute_pipeline_stages(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute individual pipeline stages"""
        
        # Stage 1: Keyword Research
        await self._execute_keyword_research_stage(pipeline_result, request)
        
        # Stage 2: Competitor Analysis
        if request.include_competitors:
            await self._execute_competitor_analysis_stage(pipeline_result, request)
        
        # Stage 3: Keyword Clustering
        if request.include_clustering:
            await self._execute_keyword_clustering_stage(pipeline_result, request)
        
        # Stage 4: Keyword Analysis
        if request.include_opportunity_analysis:
            await self._execute_keyword_analysis_stage(pipeline_result, request)
        
        # Stage 5: Insights Generation
        await self._execute_insights_generation_stage(pipeline_result, request)
        
        # Stage 6: Report Generation
        await self._execute_report_generation_stage(pipeline_result, request)
    
    async def _execute_keyword_research_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute keyword research stage"""
        try:
            self.logger.info(f"Executing keyword research stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.KEYWORD_RESEARCH
            
            keyword_results = []
            
            for keyword in request.primary_keywords[:request.max_keywords_per_analysis]:
                try:
                    result = await self.seo_service.research_keyword(
                        keyword=keyword,
                        database=request.target_database
                    )
                    
                    if result and result.get("status") != "failed":
                        keyword_results.append(result)
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to research keyword '{keyword}': {e}")
                    continue
            
            pipeline_result.results["keyword_research"] = {
                "keywords_analyzed": len(keyword_results),
                "results": keyword_results,
                "stage_completed": datetime.now().isoformat()
            }
            
            pipeline_result.stages_completed.append(PipelineStage.KEYWORD_RESEARCH)
            self.logger.info(f"Keyword research stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Keyword research stage failed: {e}")
            pipeline_result.errors.append(f"Keyword research stage failed: {e}")
            raise
    
    async def _execute_competitor_analysis_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute competitor analysis stage"""
        try:
            self.logger.info(f"Executing competitor analysis stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.COMPETITOR_ANALYSIS
            
            competitor_results = []
            
            for domain in request.competitor_domains[:request.max_competitors_per_domain]:
                try:
                    async with self.competitor_analyzer as analyzer:
                        result = await analyzer.analyze_competitors(
                            domain=domain,
                            competitor_domains=[d for d in request.competitor_domains if d != domain],
                            analysis_depth=request.analysis_depth
                        )
                        
                        if result and result.get("analysis_status") != "failed":
                            competitor_results.append(result)
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to analyze competitor '{domain}': {e}")
                    continue
            
            pipeline_result.results["competitor_analysis"] = {
                "competitors_analyzed": len(competitor_results),
                "results": competitor_results,
                "stage_completed": datetime.now().isoformat()
            }
            
            pipeline_result.stages_completed.append(PipelineStage.COMPETITOR_ANALYSIS)
            self.logger.info(f"Competitor analysis stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Competitor analysis stage failed: {e}")
            pipeline_result.errors.append(f"Competitor analysis stage failed: {e}")
            raise
    
    async def _execute_keyword_clustering_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute keyword clustering stage"""
        try:
            self.logger.info(f"Executing keyword clustering stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.KEYWORD_CLUSTERING
            
            keyword_data = pipeline_result.results.get("keyword_research", {}).get("results", [])
            
            if not keyword_data:
                self.logger.warning("No keyword data available for clustering")
                return
            
            # Extract keywords and metrics for clustering
            keywords = []
            search_volumes = []
            difficulties = []
            
            for kw_data in keyword_data:
                if isinstance(kw_data, dict):
                    keywords.append(kw_data.get("keyword", ""))
                    search_volumes.append(kw_data.get("search_volume", 0))
                    difficulties.append(kw_data.get("keyword_difficulty", 50))
            
            # Perform clustering
            clusters = self.keyword_clusterer.cluster_keywords(
                keywords=keywords,
                search_volumes=search_volumes,
                difficulties=difficulties
            )
            
            # Find keyword opportunities
            opportunities = self.keyword_clusterer.find_keyword_opportunities(
                clusters=clusters,
                min_volume=1000,
                max_difficulty=70
            )
            
            pipeline_result.results["keyword_clustering"] = {
                "clusters": clusters,
                "opportunities": opportunities,
                "total_keywords": len(keywords),
                "total_clusters": len(clusters),
                "high_opportunity_keywords": len(opportunities),
                "stage_completed": datetime.now().isoformat()
            }
            
            pipeline_result.stages_completed.append(PipelineStage.KEYWORD_CLUSTERING)
            self.logger.info(f"Keyword clustering stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Keyword clustering stage failed: {e}")
            pipeline_result.errors.append(f"Keyword clustering stage failed: {e}")
            raise
    
    async def _execute_keyword_analysis_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute keyword analysis stage"""
        try:
            self.logger.info(f"Executing keyword analysis stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.KEYWORD_ANALYSIS
            
            keyword_data = pipeline_result.results.get("keyword_research", {}).get("results", [])
            
            if not keyword_data:
                self.logger.warning("No keyword data available for analysis")
                return
            
            # Analyze each keyword
            analyzed_keywords = []
            insights_summary = []
            
            for kw_data in keyword_data:
                try:
                    if isinstance(kw_data, dict):
                        metrics = self.keyword_analyzer.analyze_keyword(kw_data)
                        insights = self.keyword_analyzer.generate_keyword_insights(metrics)
                        
                        analyzed_keywords.append({
                            "metrics": asdict(metrics),
                            "insights": insights
                        })
                        
                        insights_summary.append({
                            "keyword": metrics.keyword,
                            "opportunity_score": metrics.opportunity_score,
                            "intent": metrics.intent.value,
                            "recommendations": insights["recommendations"][:3]  # Top 3
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Failed to analyze keyword: {e}")
                    continue
            
            # Sort by opportunity score
            analyzed_keywords.sort(key=lambda x: x["metrics"]["opportunity_score"], reverse=True)
            insights_summary.sort(key=lambda x: x["opportunity_score"], reverse=True)
            
            pipeline_result.results["keyword_analysis"] = {
                "analyzed_keywords": analyzed_keywords,
                "insights_summary": insights_summary,
                "total_analyzed": len(analyzed_keywords),
                "top_opportunities": insights_summary[:10],
                "stage_completed": datetime.now().isoformat()
            }
            
            pipeline_result.stages_completed.append(PipelineStage.KEYWORD_ANALYSIS)
            self.logger.info(f"Keyword analysis stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Keyword analysis stage failed: {e}")
            pipeline_result.errors.append(f"Keyword analysis stage failed: {e}")
            raise
    
    async def _execute_insights_generation_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute insights generation stage"""
        try:
            self.logger.info(f"Executing insights generation stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.INSIGHTS_GENERATION
            
            # Generate comprehensive insights
            insights = self._generate_comprehensive_insights(pipeline_result, request)
            
            pipeline_result.results["insights"] = insights
            pipeline_result.stages_completed.append(PipelineStage.INSIGHTS_GENERATION)
            self.logger.info(f"Insights generation stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Insights generation stage failed: {e}")
            pipeline_result.errors.append(f"Insights generation stage failed: {e}")
            raise
    
    async def _execute_report_generation_stage(self, pipeline_result: PipelineResult, request: KeywordResearchRequest):
        """Execute report generation stage"""
        try:
            self.logger.info(f"Executing report generation stage for pipeline {pipeline_result.pipeline_id}")
            pipeline_result.current_stage = PipelineStage.REPORT_GENERATION
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(pipeline_result, request)
            
            pipeline_result.results["report"] = report
            pipeline_result.stages_completed.append(PipelineStage.REPORT_GENERATION)
            self.logger.info(f"Report generation stage completed for pipeline {pipeline_result.pipeline_id}")
            
        except Exception as e:
            self.logger.error(f"Report generation stage failed: {e}")
            pipeline_result.errors.append(f"Report generation stage failed: {e}")
            raise
    
    def _generate_comprehensive_insights(self, pipeline_result: PipelineResult, request: KeywordResearchRequest) -> Dict[str, Any]:
        """Generate comprehensive insights from all pipeline stages"""
        insights = {
            "summary": {
                "total_keywords_analyzed": 0,
                "total_competitors_analyzed": 0,
                "total_clusters_identified": 0,
                "high_opportunity_keywords": 0,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "key_findings": [],
            "recommendations": [],
            "risks": [],
            "opportunities": []
        }
        
        # Extract data from pipeline results
        keyword_research = pipeline_result.results.get("keyword_research", {})
        competitor_analysis = pipeline_result.results.get("competitor_analysis", {})
        keyword_clustering = pipeline_result.results.get("keyword_clustering", {})
        keyword_analysis = pipeline_result.results.get("keyword_analysis", {})
        
        # Update summary
        insights["summary"]["total_keywords_analyzed"] = keyword_research.get("keywords_analyzed", 0)
        insights["summary"]["total_competitors_analyzed"] = competitor_analysis.get("competitors_analyzed", 0)
        insights["summary"]["total_clusters_identified"] = keyword_clustering.get("total_clusters", 0)
        insights["summary"]["high_opportunity_keywords"] = keyword_clustering.get("high_opportunity_keywords", 0)
        
        # Generate key findings
        if keyword_analysis.get("top_opportunities"):
            top_opportunities = keyword_analysis["top_opportunities"]
            insights["key_findings"].append({
                "type": "opportunity",
                "description": f"Found {len(top_opportunities)} high-opportunity keywords",
                "details": f"Top keyword: '{top_opportunities[0]['keyword']}' with score {top_opportunities[0]['opportunity_score']}"
            })
        
        if keyword_clustering.get("clusters"):
            insights["key_findings"].append({
                "type": "clustering",
                "description": f"Identified {len(keyword_clustering['clusters'])} keyword clusters",
                "details": "Keywords grouped by semantic similarity for better content strategy"
            })
        
        # Generate recommendations
        if keyword_analysis.get("insights_summary"):
            for insight in keyword_analysis["insights_summary"][:5]:  # Top 5
                if insight.get("recommendations"):
                    insights["recommendations"].extend(insight["recommendations"])
        
        # Remove duplicates and limit
        insights["recommendations"] = list(set(insights["recommendations"]))[:10]
        
        return insights
    
    def _generate_comprehensive_report(self, pipeline_result: PipelineResult, request: KeywordResearchRequest) -> Dict[str, Any]:
        """Generate comprehensive SEO report"""
        report = {
            "executive_summary": {
                "pipeline_id": pipeline_result.pipeline_id,
                "execution_date": pipeline_result.start_time.isoformat(),
                "total_execution_time": None,
                "status": pipeline_result.status.value,
                "stages_completed": len(pipeline_result.stages_completed)
            },
            "request_summary": {
                "primary_keywords": request.primary_keywords,
                "competitor_domains": request.competitor_domains,
                "analysis_depth": request.analysis_depth,
                "target_database": request.target_database
            },
            "results_summary": {},
            "detailed_results": pipeline_result.results,
            "insights": pipeline_result.results.get("insights", {}),
            "errors": pipeline_result.errors,
            "metadata": pipeline_result.metadata
        }
        
        # Calculate execution time
        if pipeline_result.end_time:
            execution_time = pipeline_result.end_time - pipeline_result.start_time
            report["executive_summary"]["total_execution_time"] = str(execution_time)
        
        # Generate results summary
        results_summary = {}
        for stage_name, stage_results in pipeline_result.results.items():
            if isinstance(stage_results, dict):
                results_summary[stage_name] = {
                    "status": "completed",
                    "items_processed": stage_results.get("keywords_analyzed", 0) or 
                                     stage_results.get("competitors_analyzed", 0) or
                                     stage_results.get("total_keywords", 0) or 0
                }
        
        report["results_summary"] = results_summary
        
        return report
    
    def _generate_pipeline_id(self, request: KeywordResearchRequest) -> str:
        """Generate unique pipeline ID based on request parameters"""
        request_hash = hashlib.md5(
            json.dumps(asdict(request), sort_keys=True).encode()
        ).hexdigest()[:8]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"seo_pipeline_{timestamp}_{request_hash}"
    
    def _is_cache_valid(self, cached_result: PipelineResult) -> bool:
        """Check if cached result is still valid"""
        if not cached_result.end_time:
            return False
        
        age = datetime.now() - cached_result.end_time
        return age.total_seconds() < self.cache_ttl
    
    async def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineResult]:
        """Get status of a specific pipeline"""
        # Check active pipelines
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id]
        
        # Check cached results
        if pipeline_id in self.pipeline_cache:
            return self.pipeline_cache[pipeline_id]
        
        return None
    
    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        if pipeline_id in self.active_pipelines:
            pipeline_result = self.active_pipelines[pipeline_id]
            pipeline_result.status = PipelineStatus.CANCELLED
            pipeline_result.end_time = datetime.now()
            
            del self.active_pipelines[pipeline_id]
            return True
        
        return False
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for pipeline_id, cached_result in self.pipeline_cache.items():
            if not self._is_cache_valid(cached_result):
                expired_keys.append(pipeline_id)
        
        for key in expired_keys:
            del self.pipeline_cache[key]
        
        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        return {
            "active_pipelines": len(self.active_pipelines),
            "cached_results": len(self.pipeline_cache),
            "total_pipelines_executed": len(self.pipeline_cache) + len(self.active_pipelines),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "average_execution_time": self._calculate_average_execution_time()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would need to be implemented with actual hit tracking
        return 0.0
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average pipeline execution time"""
        # This would need to be implemented with actual timing data
        return 0.0


# Factory function for creating pipeline instances
async def create_seo_data_pipeline() -> SEODataPipeline:
    """Create and initialize a new SEO data pipeline instance"""
    pipeline = SEODataPipeline()
    await pipeline.initialize()
    return pipeline
