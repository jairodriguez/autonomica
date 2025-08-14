"""
Keyword Clustering Service

This module provides advanced keyword clustering capabilities:
- Multiple clustering algorithms (K-means, Hierarchical, DBSCAN)
- Semantic similarity using OpenAI embeddings
- Intent-based clustering (informational, navigational, transactional)
- Long-tail keyword grouping
- Cluster quality metrics and optimization
- Interactive cluster visualization data
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
from collections import defaultdict

from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pandas as pd

from app.services.redis_service import RedisService
from app.services.seo_service import SEOService

logger = logging.getLogger(__name__)

@dataclass
class KeywordCluster:
    """Data structure for a keyword cluster"""
    cluster_id: int
    keywords: List[str]
    centroid: Optional[List[float]] = None
    size: int = 0
    avg_volume: Optional[float] = None
    avg_cpc: Optional[float] = None
    avg_difficulty: Optional[float] = None
    intent_type: Optional[str] = None
    primary_keyword: Optional[str] = None
    related_keywords: List[str] = None
    cluster_score: Optional[float] = None
    created_at: Optional[datetime] = None

@dataclass
class ClusteringResult:
    """Data structure for clustering results"""
    clusters: Dict[int, KeywordCluster]
    algorithm: str
    parameters: Dict[str, Any]
    quality_metrics: Dict[str, float]
    total_keywords: int
    cluster_count: int
    processing_time: float
    created_at: datetime

@dataclass
class IntentAnalysis:
    """Data structure for keyword intent analysis"""
    keyword: str
    intent_type: str  # informational, navigational, transactional
    confidence: float
    commercial_indicators: List[str]
    search_volume: Optional[int] = None
    cpc: Optional[float] = None

class KeywordClusteringService:
    """Advanced keyword clustering service"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.seo_service = SEOService()
        
        # Clustering algorithms configuration
        self.algorithms = {
            "kmeans": {
                "class": KMeans,
                "params": {
                    "n_clusters": 5,
                    "random_state": 42,
                    "n_init": 10
                }
            },
            "hierarchical": {
                "class": AgglomerativeClustering,
                "params": {
                    "n_clusters": None,
                    "distance_threshold": 0.3,
                    "linkage": "ward"
                }
            },
            "dbscan": {
                "class": DBSCAN,
                "params": {
                    "eps": 0.3,
                    "min_samples": 2
                }
            }
        }
        
        # Intent classification patterns
        self.intent_patterns = {
            "informational": [
                "what", "how", "why", "when", "where", "guide", "tutorial", "learn",
                "tips", "examples", "explanation", "definition", "meaning"
            ],
            "navigational": [
                "login", "sign in", "account", "profile", "dashboard", "homepage",
                "contact", "about", "support", "help", "faq"
            ],
            "transactional": [
                "buy", "purchase", "order", "shop", "price", "cost", "deal", "offer",
                "discount", "coupon", "sale", "best", "top", "review", "compare"
            ]
        }
        
        # Caching configuration
        self.cache_ttl = 3600 * 24  # 24 hours
    
    async def _get_cached_embeddings(self, keywords: List[str]) -> Optional[List[List[float]]]:
        """Retrieve cached embeddings from Redis"""
        cache_key = f"embeddings:{hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached embeddings: {e}")
        
        return None
    
    async def _cache_embeddings(self, keywords: List[str], embeddings: List[List[float]]) -> bool:
        """Cache embeddings in Redis"""
        cache_key = f"embeddings:{hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()}"
        
        try:
            await self.redis_service.set(
                cache_key,
                json.dumps(embeddings),
                expire=self.cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache embeddings: {e}")
            return False
    
    async def _get_cached_clustering(self, keywords: List[str], algorithm: str, 
                                   parameters: Dict[str, Any]) -> Optional[ClusteringResult]:
        """Retrieve cached clustering results"""
        # Create a stable key from parameters
        param_key = json.dumps(parameters, sort_keys=True)
        cache_key = f"clustering:{hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()}:{algorithm}:{hashlib.md5(param_key.encode()).hexdigest()}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Convert string dates back to datetime objects
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                for cluster_data in data["clusters"].values():
                    if cluster_data.get("created_at"):
                        cluster_data["created_at"] = datetime.fromisoformat(cluster_data["created_at"])
                return ClusteringResult(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached clustering: {e}")
        
        return None
    
    async def _cache_clustering(self, clustering_result: ClusteringResult, 
                              keywords: List[str], algorithm: str, 
                              parameters: Dict[str, Any]) -> bool:
        """Cache clustering results"""
        param_key = json.dumps(parameters, sort_keys=True)
        cache_key = f"clustering:{hashlib.md5('|'.join(sorted(keywords)).encode()).hexdigest()}:{algorithm}:{hashlib.md5(param_key.encode()).hexdigest()}"
        
        try:
            # Convert datetime objects to strings for JSON serialization
            data_dict = clustering_result.__dict__.copy()
            data_dict["created_at"] = data_dict["created_at"].isoformat()
            
            for cluster_data in data_dict["clusters"].values():
                if cluster_data.get("created_at"):
                    cluster_data["created_at"] = cluster_data["created_at"].isoformat()
            
            await self.redis_service.set(
                cache_key,
                json.dumps(data_dict),
                expire=self.cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache clustering results: {e}")
            return False
    
    async def generate_embeddings(self, keywords: List[str]) -> List[List[float]]:
        """
        Generate embeddings for keywords using OpenAI API
        
        Args:
            keywords: List of keywords to embed
        
        Returns:
            List of embedding vectors
        """
        # Check cache first
        cached_embeddings = await self._get_cached_embeddings(keywords)
        if cached_embeddings:
            logger.info(f"Retrieved cached embeddings for {len(keywords)} keywords")
            return cached_embeddings
        
        # Generate new embeddings
        embeddings = await self.seo_service.generate_keyword_embeddings(keywords)
        
        if embeddings:
            # Cache the embeddings
            await self._cache_embeddings(keywords, embeddings)
            logger.info(f"Generated and cached embeddings for {len(keywords)} keywords")
        
        return embeddings
    
    def analyze_keyword_intent(self, keyword: str, search_volume: Optional[int] = None,
                              cpc: Optional[float] = None) -> IntentAnalysis:
        """
        Analyze keyword intent based on patterns and metrics
        
        Args:
            keyword: Target keyword
            search_volume: Search volume from API
            cpc: Cost per click from API
        
        Returns:
            Intent analysis result
        """
        keyword_lower = keyword.lower()
        
        # Check for intent patterns
        intent_scores = {
            "informational": 0,
            "navigational": 0,
            "transactional": 0
        }
        
        # Pattern matching
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in keyword_lower:
                    intent_scores[intent_type] += 1
        
        # CPC-based analysis (higher CPC often indicates transactional intent)
        if cpc:
            if cpc > 2.0:
                intent_scores["transactional"] += 2
            elif cpc > 1.0:
                intent_scores["transactional"] += 1
        
        # Volume-based analysis (very high volume often indicates informational)
        if search_volume:
            if search_volume > 10000:
                intent_scores["informational"] += 1
            elif search_volume < 100:
                intent_scores["navigational"] += 1
        
        # Determine primary intent
        primary_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[primary_intent]
        total_score = sum(intent_scores.values())
        
        confidence = max_score / total_score if total_score > 0 else 0.5
        
        # Identify commercial indicators
        commercial_indicators = []
        if cpc and cpc > 1.0:
            commercial_indicators.append(f"High CPC (${cpc:.2f})")
        if "buy" in keyword_lower or "purchase" in keyword_lower:
            commercial_indicators.append("Purchase intent words")
        if "price" in keyword_lower or "cost" in keyword_lower:
            commercial_indicators.append("Price-related terms")
        
        return IntentAnalysis(
            keyword=keyword,
            intent_type=primary_intent,
            confidence=confidence,
            commercial_indicators=commercial_indicators,
            search_volume=search_volume,
            cpc=cpc
        )
    
    def _calculate_cluster_quality(self, embeddings: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """Calculate clustering quality metrics"""
        metrics = {}
        
        try:
            # Silhouette score (higher is better, range: -1 to 1)
            if len(set(labels)) > 1:
                metrics["silhouette_score"] = silhouette_score(embeddings, labels)
            else:
                metrics["silhouette_score"] = 0.0
            
            # Calinski-Harabasz score (higher is better)
            if len(set(labels)) > 1:
                metrics["calinski_harabasz_score"] = calinski_harabasz_score(embeddings, labels)
            else:
                metrics["calinski_harabasz_score"] = 0.0
            
            # Inertia (lower is better for K-means)
            if hasattr(self, '_last_kmeans'):
                metrics["inertia"] = self._last_kmeans.inertia_
            
            # Number of clusters
            metrics["n_clusters"] = len(set(labels))
            
            # Average cluster size
            cluster_sizes = [np.sum(labels == i) for i in set(labels)]
            metrics["avg_cluster_size"] = np.mean(cluster_sizes)
            metrics["min_cluster_size"] = np.min(cluster_sizes)
            metrics["max_cluster_size"] = np.max(cluster_sizes)
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality metrics: {e}")
            metrics = {"error": str(e)}
        
        return metrics
    
    def _optimize_kmeans_parameters(self, embeddings: np.ndarray, max_clusters: int = 10) -> Dict[str, Any]:
        """Optimize K-means parameters using elbow method and silhouette analysis"""
        if len(embeddings) < 3:
            return {"n_clusters": min(len(embeddings), 2)}
        
        max_clusters = min(max_clusters, len(embeddings) - 1)
        
        inertias = []
        silhouette_scores = []
        k_values = range(2, max_clusters + 1)
        
        for k in k_values:
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                
                inertias.append(kmeans.inertia_)
                
                if len(set(labels)) > 1:
                    sil_score = silhouette_score(embeddings, labels)
                    silhouette_scores.append(sil_score)
                else:
                    silhouette_scores.append(0)
                    
            except Exception as e:
                logger.warning(f"K-means failed for k={k}: {e}")
                inertias.append(float('inf'))
                silhouette_scores.append(0)
        
        # Find optimal k using silhouette score
        if silhouette_scores:
            optimal_k = k_values[np.argmax(silhouette_scores)]
        else:
            optimal_k = 3  # Default fallback
        
        return {
            "n_clusters": optimal_k,
            "random_state": 42,
            "n_init": 10
        }
    
    async def cluster_keywords(self, keywords: List[str], algorithm: str = "auto",
                             parameters: Optional[Dict[str, Any]] = None,
                             optimize: bool = True) -> ClusteringResult:
        """
        Cluster keywords using specified algorithm
        
        Args:
            keywords: List of keywords to cluster
            algorithm: Clustering algorithm to use (auto, kmeans, hierarchical, dbscan)
            parameters: Algorithm-specific parameters
            optimize: Whether to optimize parameters automatically
        
        Returns:
            Clustering result with clusters and quality metrics
        """
        if len(keywords) < 2:
            # Return single cluster for insufficient keywords
            single_cluster = KeywordCluster(
                cluster_id=0,
                keywords=keywords,
                size=len(keywords),
                created_at=datetime.now()
            )
            
            return ClusteringResult(
                clusters={0: single_cluster},
                algorithm="single_cluster",
                parameters={},
                quality_metrics={"n_clusters": 1, "avg_cluster_size": len(keywords)},
                total_keywords=len(keywords),
                cluster_count=1,
                processing_time=0.0,
                created_at=datetime.now()
            )
        
        # Check cache first
        if parameters is None:
            parameters = {}
        
        cached_result = await self._get_cached_clustering(keywords, algorithm, parameters)
        if cached_result:
            logger.info(f"Retrieved cached clustering for {len(keywords)} keywords")
            return cached_result
        
        start_time = datetime.now()
        
        try:
            # Generate embeddings
            embeddings = await self.generate_embeddings(keywords)
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Auto-select algorithm if requested
            if algorithm == "auto":
                if len(keywords) < 50:
                    algorithm = "hierarchical"
                else:
                    algorithm = "kmeans"
            
            # Optimize parameters if requested
            if optimize and algorithm == "kmeans" and "n_clusters" not in parameters:
                optimal_params = self._optimize_kmeans_parameters(embeddings_array)
                parameters.update(optimal_params)
            
            # Apply clustering algorithm
            if algorithm == "kmeans":
                clustering = KMeans(**parameters)
                labels = clustering.fit_predict(embeddings_array)
                self._last_kmeans = clustering
                
            elif algorithm == "hierarchical":
                clustering = AgglomerativeClustering(**parameters)
                labels = clustering.fit_predict(embeddings_array)
                
            elif algorithm == "dbscan":
                clustering = DBSCAN(**parameters)
                labels = clustering.fit_predict(embeddings_array)
                
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Create clusters
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = KeywordCluster(
                        cluster_id=label,
                        keywords=[],
                        size=0,
                        created_at=datetime.now()
                    )
                
                clusters[label].keywords.append(keywords[i])
                clusters[label].size += 1
            
            # Calculate cluster centroids and analyze intent
            for cluster in clusters.values():
                if cluster.keywords:
                    # Calculate centroid
                    cluster_indices = [keywords.index(kw) for kw in cluster.keywords]
                    cluster_embeddings = embeddings_array[cluster_indices]
                    cluster.centroid = np.mean(cluster_embeddings, axis=0).tolist()
                    
                    # Analyze primary keyword
                    cluster.primary_keyword = cluster.keywords[0]
                    
                    # Analyze intent
                    intent_analysis = self.analyze_keyword_intent(cluster.primary_keyword)
                    cluster.intent_type = intent_analysis.intent_type
                    
                    # Calculate cluster score based on size and cohesion
                    if cluster.size > 1:
                        cluster_similarities = []
                        for i, kw1 in enumerate(cluster.keywords):
                            for j, kw2 in enumerate(cluster.keywords[i+1:], i+1):
                                sim = cosine_similarity([embeddings_array[i]], [embeddings_array[j]])[0][0]
                                cluster_similarities.append(sim)
                        
                        if cluster_similarities:
                            cluster.cluster_score = np.mean(cluster_similarities)
                        else:
                            cluster.cluster_score = 0.0
                    else:
                        cluster.cluster_score = 1.0
            
            # Calculate quality metrics
            quality_metrics = self._calculate_cluster_quality(embeddings_array, labels)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create clustering result
            result = ClusteringResult(
                clusters=clusters,
                algorithm=algorithm,
                parameters=parameters,
                quality_metrics=quality_metrics,
                total_keywords=len(keywords),
                cluster_count=len(clusters),
                processing_time=processing_time,
                created_at=datetime.now()
            )
            
            # Cache the result
            await self._cache_clustering(result, keywords, algorithm, parameters)
            
            logger.info(f"Successfully clustered {len(keywords)} keywords into {len(clusters)} clusters using {algorithm}")
            
            return result
            
        except Exception as e:
            logger.error(f"Keyword clustering failed: {e}")
            # Return minimal result on failure
            return ClusteringResult(
                clusters={},
                algorithm=algorithm,
                parameters=parameters or {},
                quality_metrics={"error": str(e)},
                total_keywords=len(keywords),
                cluster_count=0,
                processing_time=0.0,
                created_at=datetime.now()
            )
    
    async def hierarchical_clustering_with_threshold(self, keywords: List[str], 
                                                   threshold: float = 0.3) -> ClusteringResult:
        """
        Perform hierarchical clustering with custom similarity threshold
        
        Args:
            keywords: List of keywords to cluster
            threshold: Similarity threshold for clustering (0-1)
        
        Returns:
            Clustering result
        """
        parameters = {
            "n_clusters": None,
            "distance_threshold": 1 - threshold,  # Convert similarity to distance
            "linkage": "ward"
        }
        
        return await self.cluster_keywords(keywords, "hierarchical", parameters, optimize=False)
    
    async def get_cluster_recommendations(self, cluster: KeywordCluster) -> List[str]:
        """
        Generate keyword recommendations for a cluster
        
        Args:
            cluster: Keyword cluster to analyze
        
        Returns:
            List of recommended keywords
        """
        recommendations = []
        
        if not cluster.keywords:
            return recommendations
        
        # Get keyword suggestions for primary keyword
        try:
            suggestions = await self.seo_service.get_keyword_suggestions(cluster.primary_keyword, 10)
            recommendations.extend(suggestions)
        except Exception as e:
            logger.warning(f"Failed to get keyword suggestions: {e}")
        
        # Generate intent-based recommendations
        if cluster.intent_type == "informational":
            base_keywords = ["guide", "tutorial", "how to", "tips", "examples"]
        elif cluster.intent_type == "transactional":
            base_keywords = ["best", "top", "review", "compare", "buy"]
        else:
            base_keywords = ["information", "details", "about"]
        
        for base in base_keywords:
            for keyword in cluster.keywords[:3]:  # Use top 3 keywords from cluster
                recommendation = f"{base} {keyword}"
                if recommendation not in recommendations:
                    recommendations.append(recommendation)
        
        return recommendations[:15]  # Limit to 15 recommendations
    
    async def analyze_cluster_competition(self, cluster: KeywordCluster, 
                                        country: str = "us") -> Dict[str, Any]:
        """
        Analyze competition level for keywords in a cluster
        
        Args:
            cluster: Keyword cluster to analyze
            country: Country for localized analysis
        
        Returns:
            Competition analysis results
        """
        competition_data = {
            "cluster_id": cluster.cluster_id,
            "total_keywords": cluster.size,
            "avg_keyword_difficulty": 0.0,
            "avg_cpc": 0.0,
            "competition_level": "unknown",
            "keyword_details": []
        }
        
        if not cluster.keywords:
            return competition_data
        
        total_difficulty = 0
        total_cpc = 0
        valid_keywords = 0
        
        for keyword in cluster.keywords[:5]:  # Analyze top 5 keywords
            try:
                keyword_data = await self.seo_service.get_semrush_keyword_data(keyword, country)
                
                if keyword_data:
                    keyword_detail = {
                        "keyword": keyword,
                        "search_volume": keyword_data.search_volume,
                        "cpc": keyword_data.cpc,
                        "keyword_difficulty": keyword_data.keyword_difficulty,
                        "opportunity_score": keyword_data.opportunity_score
                    }
                    
                    competition_data["keyword_details"].append(keyword_detail)
                    
                    if keyword_data.keyword_difficulty:
                        total_difficulty += keyword_data.keyword_difficulty
                    if keyword_data.cpc:
                        total_cpc += keyword_data.cpc
                    valid_keywords += 1
                    
            except Exception as e:
                logger.warning(f"Failed to analyze keyword '{keyword}': {e}")
        
        # Calculate averages
        if valid_keywords > 0:
            competition_data["avg_keyword_difficulty"] = total_difficulty / valid_keywords
            competition_data["avg_cpc"] = total_cpc / valid_keywords
            
            # Determine competition level
            if competition_data["avg_keyword_difficulty"] > 70:
                competition_data["competition_level"] = "high"
            elif competition_data["avg_keyword_difficulty"] > 40:
                competition_data["competition_level"] = "medium"
            else:
                competition_data["competition_level"] = "low"
        
        return competition_data
    
    def export_clustering_data(self, clustering_result: ClusteringResult, 
                              format: str = "json") -> str:
        """
        Export clustering results in various formats
        
        Args:
            clustering_result: Clustering results to export
            format: Export format (json, csv, xlsx)
        
        Returns:
            Exported data as string or file path
        """
        if format.lower() == "json":
            # Convert datetime objects to strings for JSON serialization
            export_data = clustering_result.__dict__.copy()
            export_data["created_at"] = export_data["created_at"].isoformat()
            
            for cluster_data in export_data["clusters"].values():
                if cluster_data.get("created_at"):
                    cluster_data["created_at"] = cluster_data["created_at"].isoformat()
            
            return json.dumps(export_data, indent=2, default=str)
            
        elif format.lower() == "csv":
            # Create CSV with cluster information
            csv_lines = ["cluster_id,keyword,position,cluster_size,intent_type,cluster_score"]
            
            for cluster_id, cluster in clustering_result.clusters.items():
                for i, keyword in enumerate(cluster.keywords):
                    csv_lines.append(f"{cluster_id},{keyword},{i+1},{cluster.size},{cluster.intent_type or 'unknown'},{cluster.cluster_score or 0}")
            
            return "\n".join(csv_lines)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def get_clustering_summary(self, clustering_result: ClusteringResult) -> Dict[str, Any]:
        """
        Generate a summary of clustering results
        
        Args:
            clustering_result: Clustering results to summarize
        
        Returns:
            Summary statistics and insights
        """
        summary = {
            "total_keywords": clustering_result.total_keywords,
            "cluster_count": clustering_result.cluster_count,
            "algorithm": clustering_result.algorithm,
            "processing_time": clustering_result.processing_time,
            "quality_metrics": clustering_result.quality_metrics,
            "cluster_distribution": {},
            "intent_distribution": {},
            "size_distribution": {},
            "recommendations": []
        }
        
        # Analyze cluster distribution
        for cluster in clustering_result.clusters.values():
            # Size distribution
            size_range = f"{cluster.size}-{cluster.size + 4}" if cluster.size < 5 else "5+"
            summary["size_distribution"][size_range] = summary["size_distribution"].get(size_range, 0) + 1
            
            # Intent distribution
            intent = cluster.intent_type or "unknown"
            summary["intent_distribution"][intent] = summary["intent_distribution"].get(intent, 0) + 1
        
        # Generate recommendations
        if clustering_result.cluster_count > 10:
            summary["recommendations"].append("Consider increasing similarity threshold to reduce cluster count")
        elif clustering_result.cluster_count < 3:
            summary["recommendations"].append("Consider decreasing similarity threshold to create more specific clusters")
        
        if clustering_result.quality_metrics.get("silhouette_score", 0) < 0.3:
            summary["recommendations"].append("Low silhouette score indicates poor cluster separation - consider adjusting parameters")
        
        return summary