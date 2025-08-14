"""
SEO Research and Keyword Analysis Service

This module provides comprehensive SEO research capabilities including:
- SEMrush API integration for keyword research
- Web scraping for SERP analysis
- Keyword clustering and analysis
- SEO scoring and opportunity identification
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import openai
from pydantic import BaseModel, Field
import time

# Configure logging
logger = logging.getLogger(__name__)

# Data Models
class KeywordRecord(BaseModel):
    """Represents a keyword with its SEO metrics"""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
    difficulty: Optional[int] = None
    results: Optional[int] = None
    trends: Optional[List[int]] = None
    related_keywords: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SERPResult(BaseModel):
    """Represents a search engine result page entry"""
    title: str
    url: str
    snippet: str
    position: int
    featured_snippet: bool = False
    paa_questions: Optional[List[str]] = None
    structured_data: Optional[Dict[str, Any]] = None

class KeywordCluster(BaseModel):
    """Represents a cluster of related keywords"""
    cluster_id: str
    keywords: List[str]
    centroid_keyword: str
    search_volume_total: int
    avg_difficulty: float
    avg_cpc: float
    intent: str
    opportunities: List[str]

class SEOAnalysis(BaseModel):
    """Complete SEO analysis for a domain or keyword set"""
    target_keyword: str
    keyword_records: List[KeywordRecord]
    serp_results: List[SERPResult]
    keyword_clusters: List[KeywordCluster]
    seo_score: float
    opportunities: List[str]
    recommendations: List[str]
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

class SEMrushConfig(BaseModel):
    """Configuration for SEMrush API"""
    api_key: str
    base_url: str = "https://api.semrush.com"
    rate_limit_per_minute: int = 100
    timeout_seconds: int = 30

class WebScrapingConfig(BaseModel):
    """Configuration for web scraping"""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    request_delay: float = 1.0
    max_retries: int = 3
    respect_robots_txt: bool = True
    timeout_seconds: int = 30

class SEOConfig(BaseModel):
    """Main SEO service configuration"""
    semrush: SEMrushConfig
    web_scraping: WebScrapingConfig
    openai_api_key: Optional[str] = None
    clustering_threshold: float = 0.85
    max_keywords_per_cluster: int = 20
    cache_ttl_hours: int = 24

class SEOService:
    """
    Main SEO service providing keyword research, analysis, and clustering capabilities
    """
    
    def __init__(self, config: SEOConfig):
        self.config = config
        self.semrush_client = SEMrushClient(config.semrush)
        self.scraper = WebScraper(config.web_scraping)
        self.cache = {}
        self.rate_limit_tracker = {}
        
        # Initialize OpenAI client if API key is provided
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
    
    async def analyze_keyword(self, keyword: str, domain: Optional[str] = None) -> SEOAnalysis:
        """
        Perform comprehensive SEO analysis for a target keyword
        
        Args:
            keyword: Target keyword to analyze
            domain: Optional domain to analyze against
            
        Returns:
            SEOAnalysis object with complete analysis results
        """
        logger.info(f"Starting SEO analysis for keyword: {keyword}")
        
        try:
            # Get keyword data from SEMrush
            keyword_data = await self.semrush_client.get_keyword_data(keyword)
            
            # Get SERP results
            serp_results = await self.scraper.scrape_serp(keyword)
            
            # Find related keywords
            related_keywords = await self.semrush_client.get_related_keywords(keyword)
            
            # Perform keyword clustering
            all_keywords = [keyword] + related_keywords[:50]  # Limit to top 50 related
            keyword_clusters = await self._cluster_keywords(all_keywords)
            
            # Calculate SEO score
            seo_score = self._calculate_seo_score(keyword_data, serp_results)
            
            # Identify opportunities
            opportunities = self._identify_opportunities(keyword_data, keyword_clusters)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(keyword_data, serp_results, seo_score)
            
            analysis = SEOAnalysis(
                target_keyword=keyword,
                keyword_records=[keyword_data],
                serp_results=serp_results,
                keyword_clusters=keyword_clusters,
                seo_score=seo_score,
                opportunities=opportunities,
                recommendations=recommendations
            )
            
            logger.info(f"SEO analysis completed for keyword: {keyword}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during SEO analysis for keyword {keyword}: {str(e)}")
            raise
    
    async def _cluster_keywords(self, keywords: List[str]) -> List[KeywordCluster]:
        """
        Cluster keywords based on semantic similarity using multiple algorithms
        
        Args:
            keywords: List of keywords to cluster
            
        Returns:
            List of KeywordCluster objects
        """
        if not keywords:
            return []
        
        try:
            # Generate embeddings for keywords
            embeddings = await self._generate_embeddings(keywords)
            
            # Try multiple clustering approaches
            clustering_results = []
            
            # 1. Hierarchical Clustering (Agglomerative)
            hierarchical_clusters = await self._hierarchical_clustering(keywords, embeddings)
            if hierarchical_clusters:
                clustering_results.append(('hierarchical', hierarchical_clusters))
            
            # 2. K-Means Clustering
            kmeans_clusters = await self._kmeans_clustering(keywords, embeddings)
            if kmeans_clusters:
                clustering_results.append(('kmeans', kmeans_clusters))
            
            # 3. DBSCAN Clustering (density-based)
            dbscan_clusters = await self._dbscan_clustering(keywords, embeddings)
            if dbscan_clusters:
                clustering_results.append(('dbscan', dbscan_clusters))
            
            # Select best clustering result based on quality metrics
            best_clusters = self._select_best_clustering(clustering_results, keywords, embeddings)
            
            # Create KeywordCluster objects
            keyword_clusters = []
            for cluster_id, cluster_keywords in best_clusters.items():
                if len(cluster_keywords) < 2:  # Skip single-keyword clusters
                    continue
                
                # Find centroid keyword (most representative)
                centroid_idx = self._find_centroid(embeddings, cluster_keywords, keywords)
                centroid_keyword = keywords[centroid_idx]
                
                # Calculate cluster metrics
                cluster_metrics = await self._calculate_cluster_metrics(cluster_keywords)
                
                # Calculate cluster quality score
                quality_score = self._calculate_cluster_quality(cluster_keywords, embeddings, keywords)
                
                cluster = KeywordCluster(
                    cluster_id=f"cluster_{cluster_id}",
                    keywords=cluster_keywords,
                    centroid_keyword=centroid_keyword,
                    search_volume_total=cluster_metrics.get('total_volume', 0),
                    avg_difficulty=cluster_metrics.get('avg_difficulty', 0.0),
                    avg_cpc=cluster_metrics.get('avg_cpc', 0.0),
                    intent=self._classify_keyword_intent(centroid_keyword),
                    opportunities=cluster_metrics.get('opportunities', [])
                )
                
                keyword_clusters.append(cluster)
            
            return keyword_clusters
            
        except Exception as e:
            logger.error(f"Error during keyword clustering: {str(e)}")
            return []
    
    async def _hierarchical_clustering(self, keywords: List[str], embeddings: np.ndarray) -> Dict[int, List[str]]:
        """
        Perform hierarchical clustering using AgglomerativeClustering
        
        Args:
            keywords: List of keywords
            embeddings: Keyword embeddings
            
        Returns:
            Dictionary of cluster_id -> keyword_list
        """
        try:
            from sklearn.cluster import AgglomerativeClustering
            
            # Determine optimal number of clusters
            n_clusters = min(max(2, len(keywords) // 5), 10)
            
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward',
                distance_threshold=None
            )
            
            cluster_labels = clustering.fit_predict(embeddings)
            
            # Group keywords by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(keywords[i])
            
            return clusters
            
        except Exception as e:
            logger.warning(f"Hierarchical clustering failed: {str(e)}")
            return {}
    
    async def _kmeans_clustering(self, keywords: List[str], embeddings: np.ndarray) -> Dict[int, List[str]]:
        """
        Perform K-means clustering
        
        Args:
            keywords: List of keywords
            embeddings: Keyword embeddings
            
        Returns:
            Dictionary of cluster_id -> keyword_list
        """
        try:
            from sklearn.cluster import KMeans
            
            # Determine optimal number of clusters using elbow method
            n_clusters = min(max(2, len(keywords) // 5), 10)
            
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Group keywords by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(keywords[i])
            
            return clusters
            
        except Exception as e:
            logger.warning(f"K-means clustering failed: {str(e)}")
            return {}
    
    async def _dbscan_clustering(self, keywords: List[str], embeddings: np.ndarray) -> Dict[int, List[str]]:
        """
        Perform DBSCAN clustering (density-based)
        
        Args:
            keywords: List of keywords
            embeddings: Keyword embeddings
            
        Returns:
            Dictionary of cluster_id -> keyword_list
        """
        try:
            from sklearn.cluster import DBSCAN
            
            # DBSCAN parameters
            eps = 0.3  # Maximum distance between points
            min_samples = max(2, len(keywords) // 20)  # Minimum points per cluster
            
            dbscan = DBSCAN(
                eps=eps,
                min_samples=min_samples,
                metric='euclidean'
            )
            
            cluster_labels = dbscan.fit_predict(embeddings)
            
            # Group keywords by cluster (DBSCAN uses -1 for noise)
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label == -1:
                    # Create individual cluster for noise points
                    cluster_id = len(clusters)
                    clusters[cluster_id] = [keywords[i]]
                else:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(keywords[i])
            
            return clusters
            
        except Exception as e:
            logger.warning(f"DBSCAN clustering failed: {str(e)}")
            return {}
    
    def _select_best_clustering(self, clustering_results: List[tuple], keywords: List[str], embeddings: np.ndarray) -> Dict[int, List[str]]:
        """
        Select the best clustering result based on quality metrics
        
        Args:
            clustering_results: List of (method, clusters) tuples
            keywords: List of keywords
            embeddings: Keyword embeddings
            
        Returns:
            Best clustering result
        """
        if not clustering_results:
            return {}
        
        best_score = -1
        best_clusters = {}
        
        for method, clusters in clustering_results:
            try:
                # Calculate clustering quality score
                quality_score = self._evaluate_clustering_quality(clusters, embeddings, keywords)
                
                logger.info(f"Clustering method '{method}' quality score: {quality_score:.3f}")
                
                if quality_score > best_score:
                    best_score = quality_score
                    best_clusters = clusters
                    
            except Exception as e:
                logger.warning(f"Error evaluating {method} clustering: {str(e)}")
                continue
        
        logger.info(f"Selected clustering with quality score: {best_score:.3f}")
        return best_clusters
    
    def _evaluate_clustering_quality(self, clusters: Dict[int, List[str]], embeddings: np.ndarray, keywords: List[str]) -> float:
        """
        Evaluate clustering quality using multiple metrics
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            embeddings: Keyword embeddings
            keywords: List of keywords
            
        Returns:
            Quality score (0-1, higher is better)
        """
        if not clusters:
            return 0.0
        
        try:
            # 1. Silhouette Score (higher is better)
            silhouette_score = self._calculate_silhouette_score(clusters, embeddings, keywords)
            
            # 2. Intra-cluster similarity (higher is better)
            intra_cluster_similarity = self._calculate_intra_cluster_similarity(clusters, embeddings, keywords)
            
            # 3. Inter-cluster separation (higher is better)
            inter_cluster_separation = self._calculate_inter_cluster_separation(clusters, embeddings, keywords)
            
            # 4. Cluster balance (closer to 1 is better)
            cluster_balance = self._calculate_cluster_balance(clusters)
            
            # 5. Noise ratio (lower is better)
            noise_ratio = self._calculate_noise_ratio(clusters)
            
            # Combine metrics into overall score
            overall_score = (
                silhouette_score * 0.3 +
                intra_cluster_similarity * 0.25 +
                inter_cluster_separation * 0.25 +
                cluster_balance * 0.15 +
                (1 - noise_ratio) * 0.05
            )
            
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            logger.warning(f"Error calculating clustering quality: {str(e)}")
            return 0.0
    
    def _calculate_silhouette_score(self, clusters: Dict[int, List[str]], embeddings: np.ndarray, keywords: List[str]) -> float:
        """
        Calculate silhouette score for clustering quality
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            embeddings: Keyword embeddings
            keywords: List of keywords
            
        Returns:
            Silhouette score (-1 to 1, higher is better)
        """
        try:
            from sklearn.metrics import silhouette_score
            
            # Create cluster labels array
            cluster_labels = np.zeros(len(keywords))
            for cluster_id, cluster_keywords in clusters.items():
                for keyword in cluster_keywords:
                    keyword_idx = keywords.index(keyword)
                    cluster_labels[keyword_idx] = cluster_id
            
            # Calculate silhouette score
            if len(set(cluster_labels)) > 1:  # Need at least 2 clusters
                return silhouette_score(embeddings, cluster_labels)
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Error calculating silhouette score: {str(e)}")
            return 0.0
    
    def _calculate_intra_cluster_similarity(self, clusters: Dict[int, List[str]], embeddings: np.ndarray, keywords: List[str]) -> float:
        """
        Calculate average intra-cluster similarity
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            embeddings: Keyword embeddings
            keywords: List of keywords
            
        Returns:
            Average intra-cluster similarity (0-1, higher is better)
        """
        try:
            total_similarity = 0.0
            total_pairs = 0
            
            for cluster_keywords in clusters.values():
                if len(cluster_keywords) < 2:
                    continue
                
                # Calculate pairwise similarities within cluster
                cluster_indices = [keywords.index(kw) for kw in cluster_keywords]
                cluster_embeddings = embeddings[cluster_indices]
                
                # Calculate cosine similarities
                similarities = cosine_similarity(cluster_embeddings)
                
                # Sum similarities (excluding diagonal)
                cluster_similarity = 0.0
                cluster_pairs = 0
                for i in range(len(similarities)):
                    for j in range(i + 1, len(similarities)):
                        cluster_similarity += similarities[i][j]
                        cluster_pairs += 1
                
                if cluster_pairs > 0:
                    total_similarity += cluster_similarity / cluster_pairs
                    total_pairs += 1
            
            return total_similarity / total_pairs if total_pairs > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating intra-cluster similarity: {str(e)}")
            return 0.0
    
    def _calculate_inter_cluster_separation(self, clusters: Dict[int, List[str]], embeddings: np.ndarray, keywords: List[str]) -> float:
        """
        Calculate average inter-cluster separation
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            embeddings: Keyword embeddings
            keywords: List of keywords
            
        Returns:
            Average inter-cluster separation (0-1, higher is better)
        """
        try:
            if len(clusters) < 2:
                return 0.0
            
            # Get cluster centroids
            centroids = []
            for cluster_keywords in clusters.values():
                cluster_indices = [keywords.index(kw) for kw in cluster_keywords]
                cluster_embeddings = embeddings[cluster_indices]
                centroid = np.mean(cluster_embeddings, axis=0)
                centroids.append(centroid)
            
            # Calculate pairwise distances between centroids
            total_distance = 0.0
            total_pairs = 0
            
            for i in range(len(centroids)):
                for j in range(i + 1, len(centroids)):
                    distance = np.linalg.norm(centroids[i] - centroids[j])
                    total_distance += distance
                    total_pairs += 1
            
            # Normalize distance (0-1 scale)
            avg_distance = total_distance / total_pairs if total_pairs > 0 else 0.0
            normalized_distance = min(1.0, avg_distance / 2.0)  # Assuming embeddings are normalized
            
            return normalized_distance
            
        except Exception as e:
            logger.warning(f"Error calculating inter-cluster separation: {str(e)}")
            return 0.0
    
    def _calculate_cluster_balance(self, clusters: Dict[int, List[str]]) -> float:
        """
        Calculate cluster balance (how evenly distributed keywords are)
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            
        Returns:
            Balance score (0-1, closer to 1 is better)
        """
        try:
            if not clusters:
                return 0.0
            
            cluster_sizes = [len(keywords) for keywords in clusters.values()]
            total_keywords = sum(cluster_sizes)
            
            if total_keywords == 0:
                return 0.0
            
            # Calculate standard deviation of cluster sizes
            mean_size = total_keywords / len(clusters)
            variance = sum((size - mean_size) ** 2 for size in cluster_sizes) / len(clusters)
            std_dev = variance ** 0.5
            
            # Normalize to 0-1 scale (lower std dev = better balance)
            max_std_dev = total_keywords / 2  # Theoretical maximum
            balance_score = max(0.0, 1.0 - (std_dev / max_std_dev))
            
            return balance_score
            
        except Exception as e:
            logger.warning(f"Error calculating cluster balance: {str(e)}")
            return 0.0
    
    def _calculate_noise_ratio(self, clusters: Dict[int, List[str]]) -> float:
        """
        Calculate noise ratio (single-keyword clusters)
        
        Args:
            clusters: Dictionary of cluster_id -> keyword_list
            
        Returns:
            Noise ratio (0-1, lower is better)
        """
        try:
            if not clusters:
                return 0.0
            
            single_keyword_clusters = sum(1 for keywords in clusters.values() if len(keywords) == 1)
            total_clusters = len(clusters)
            
            return single_keyword_clusters / total_clusters if total_clusters > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating noise ratio: {str(e)}")
            return 0.0
    
    def _calculate_cluster_quality(self, cluster_keywords: List[str], embeddings: np.ndarray, keywords: List[str]) -> float:
        """
        Calculate quality score for a specific cluster
        
        Args:
            cluster_keywords: Keywords in the cluster
            embeddings: All keyword embeddings
            keywords: All keywords
            
        Returns:
            Cluster quality score (0-1, higher is better)
        """
        try:
            if len(cluster_keywords) < 2:
                return 0.0
            
            # Get cluster embeddings
            cluster_indices = [keywords.index(kw) for kw in cluster_keywords]
            cluster_embeddings = embeddings[cluster_indices]
            
            # Calculate average pairwise similarity
            similarities = cosine_similarity(cluster_embeddings)
            
            total_similarity = 0.0
            total_pairs = 0
            
            for i in range(len(similarities)):
                for j in range(i + 1, len(similarities)):
                    total_similarity += similarities[i][j]
                    total_pairs += 1
            
            avg_similarity = total_similarity / total_pairs if total_pairs > 0 else 0.0
            
            # Normalize to 0-1 scale
            return max(0.0, min(1.0, avg_similarity))
            
        except Exception as e:
            logger.warning(f"Error calculating cluster quality: {str(e)}")
            return 0.0
    
    async def _generate_embeddings(self, keywords: List[str]) -> np.ndarray:
        """
        Generate embeddings for keywords using OpenAI API
        
        Args:
            keywords: List of keywords to embed
            
        Returns:
            Numpy array of embeddings
        """
        if not self.config.openai_api_key:
            # Fallback to simple TF-IDF like approach
            return self._generate_simple_embeddings(keywords)
        
        try:
            embeddings = []
            for keyword in keywords:
                response = openai.Embedding.create(
                    input=keyword,
                    model="text-embedding-ada-002"
                )
                embeddings.append(response['data'][0]['embedding'])
            
            return np.array(embeddings)
            
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, falling back to simple method: {str(e)}")
            return self._generate_simple_embeddings(keywords)
    
    def _generate_simple_embeddings(self, keywords: List[str]) -> np.ndarray:
        """
        Generate simple embeddings using character frequency analysis
        
        Args:
            keywords: List of keywords to embed
            
        Returns:
            Numpy array of simple embeddings
        """
        # Simple character frequency based embedding
        embeddings = []
        for keyword in keywords:
            # Create a simple feature vector based on character frequencies
            features = [0] * 26  # a-z
            for char in keyword.lower():
                if 'a' <= char <= 'z':
                    features[ord(char) - ord('a')] += 1
            
            # Normalize
            total = sum(features)
            if total > 0:
                features = [f / total for f in features]
            
            embeddings.append(features)
        
        return np.array(embeddings)
    
    def _find_centroid(self, embeddings: np.ndarray, cluster_keywords: List[str], all_keywords: List[str]) -> int:
        """
        Find the most representative keyword in a cluster
        
        Args:
            embeddings: All keyword embeddings
            cluster_keywords: Keywords in the current cluster
            all_keywords: All keywords
            
        Returns:
            Index of the centroid keyword
        """
        if not cluster_keywords:
            return 0
        
        # Find indices of cluster keywords
        cluster_indices = [all_keywords.index(kw) for kw in cluster_keywords]
        
        # Calculate centroid of cluster
        cluster_embeddings = embeddings[cluster_indices]
        centroid = np.mean(cluster_embeddings, axis=0)
        
        # Find keyword closest to centroid
        distances = [np.linalg.norm(emb - centroid) for emb in cluster_embeddings]
        min_distance_idx = np.argmin(distances)
        
        return cluster_indices[min_distance_idx]
    
    async def _calculate_cluster_metrics(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics for a keyword cluster
        
        Args:
            keywords: Keywords in the cluster
            
        Returns:
            Dictionary of cluster metrics
        """
        try:
            # Get keyword data for all keywords in cluster
            keyword_data_list = []
            for keyword in keywords[:10]:  # Limit to first 10 for performance
                try:
                    data = await self.semrush_client.get_keyword_data(keyword)
                    keyword_data_list.append(data)
                except Exception as e:
                    logger.warning(f"Could not get data for keyword {keyword}: {str(e)}")
                    continue
            
            if not keyword_data_list:
                return {
                    'total_volume': 0,
                    'avg_difficulty': 0.0,
                    'avg_cpc': 0.0,
                    'opportunities': []
                }
            
            # Calculate aggregate metrics
            total_volume = sum(data.search_volume or 0 for data in keyword_data_list)
            avg_difficulty = np.mean([data.difficulty or 0 for data in keyword_data_list])
            avg_cpc = np.mean([data.cpc or 0 for data in keyword_data_list])
            
            # Identify opportunities
            opportunities = []
            for data in keyword_data_list:
                if data.search_volume and data.search_volume > 1000 and data.difficulty and data.difficulty < 50:
                    opportunities.append(f"High volume, low difficulty: {data.keyword}")
                if data.cpc and data.cpc > 2.0:
                    opportunities.append(f"High CPC potential: {data.keyword}")
            
            return {
                'total_volume': total_volume,
                'avg_difficulty': avg_difficulty,
                'avg_cpc': avg_cpc,
                'opportunities': opportunities
            }
            
        except Exception as e:
            logger.error(f"Error calculating cluster metrics: {str(e)}")
            return {
                'total_volume': 0,
                'avg_difficulty': 0.0,
                'avg_cpc': 0.0,
                'opportunities': []
            }
    
    def _classify_keyword_intent(self, keyword: str) -> str:
        """
        Classify keyword intent based on keyword characteristics
        
        Args:
            keyword: Keyword to classify
            
        Returns:
            Intent classification string
        """
        keyword_lower = keyword.lower()
        
        # Informational intent
        if any(word in keyword_lower for word in ['what', 'how', 'why', 'when', 'where', 'guide', 'tutorial', 'tips']):
            return "informational"
        
        # Navigational intent
        if any(word in keyword_lower for word in ['login', 'signup', 'homepage', 'contact', 'about']):
            return "navigational"
        
        # Commercial intent
        if any(word in keyword_lower for word in ['review', 'best', 'top', 'compare', 'vs', 'alternative']):
            return "commercial"
        
        # Transactional intent
        if any(word in keyword_lower for word in ['buy', 'purchase', 'order', 'discount', 'coupon', 'deal']):
            return "transactional"
        
        return "informational"  # Default to informational
    
    def _calculate_seo_score(self, keyword_data: KeywordRecord, serp_results: List[SERPResult]) -> float:
        """
        Calculate overall SEO score based on keyword data and SERP analysis
        
        Args:
            keyword_data: Keyword metrics from SEMrush
            serp_results: SERP analysis results
            
        Returns:
            SEO score from 0-100
        """
        score = 0.0
        
        # Keyword difficulty scoring (lower is better)
        if keyword_data.difficulty:
            if keyword_data.difficulty < 30:
                score += 25
            elif keyword_data.difficulty < 50:
                score += 15
            elif keyword_data.difficulty < 70:
                score += 10
            else:
                score += 5
        
        # Search volume scoring (higher is better)
        if keyword_data.search_volume:
            if keyword_data.search_volume > 10000:
                score += 25
            elif keyword_data.search_volume > 5000:
                score += 20
            elif keyword_data.search_volume > 1000:
                score += 15
            elif keyword_data.search_volume > 100:
                score += 10
            else:
                score += 5
        
        # CPC scoring (higher is better)
        if keyword_data.cpc:
            if keyword_data.cpc > 5.0:
                score += 20
            elif keyword_data.cpc > 2.0:
                score += 15
            elif keyword_data.cpc > 1.0:
                score += 10
            else:
                score += 5
        
        # SERP competition scoring
        if serp_results:
            # Analyze top 10 results
            top_results = serp_results[:10]
            
            # Check for featured snippets
            featured_snippets = sum(1 for r in top_results if r.featured_snippet)
            if featured_snippets > 0:
                score += 10
            
            # Check for PAA boxes
            paa_results = sum(1 for r in top_results if r.paa_questions)
            if paa_results > 0:
                score += 5
        
        return min(score, 100.0)  # Cap at 100
    
    def _identify_opportunities(self, keyword_data: KeywordRecord, keyword_clusters: List[KeywordCluster]) -> List[str]:
        """
        Identify SEO opportunities based on analysis
        
        Args:
            keyword_data: Target keyword data
            keyword_clusters: Related keyword clusters
            
        Returns:
            List of opportunity descriptions
        """
        opportunities = []
        
        # High volume, low difficulty opportunities
        if keyword_data.search_volume and keyword_data.difficulty:
            if keyword_data.search_volume > 5000 and keyword_data.difficulty < 40:
                opportunities.append("High search volume with manageable difficulty - great primary keyword target")
            elif keyword_data.search_volume > 1000 and keyword_data.difficulty < 30:
                opportunities.append("Moderate volume with low difficulty - excellent secondary keyword target")
        
        # High CPC opportunities
        if keyword_data.cpc and keyword_data.cpc > 3.0:
            opportunities.append(f"High CPC (${keyword_data.cpc:.2f}) indicates strong commercial intent")
        
        # Related keyword opportunities
        for cluster in keyword_clusters:
            if cluster.avg_difficulty < 40 and cluster.search_volume_total > 2000:
                opportunities.append(f"Low-competition cluster around '{cluster.centroid_keyword}' with {cluster.search_volume_total} total volume")
        
        # Content gap opportunities
        if keyword_data.results and keyword_data.results < 1000000:
            opportunities.append("Moderate competition - good opportunity to rank with quality content")
        
        return opportunities
    
    def _generate_recommendations(self, keyword_data: KeywordRecord, serp_results: List[SERPResult], seo_score: float) -> List[str]:
        """
        Generate actionable SEO recommendations
        
        Args:
            keyword_data: Keyword data
            serp_results: SERP analysis
            seo_score: Calculated SEO score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Score-based recommendations
        if seo_score < 30:
            recommendations.append("Focus on long-tail variations with lower competition")
            recommendations.append("Build comprehensive content around related topics")
        elif seo_score < 60:
            recommendations.append("Optimize existing content for target keyword")
            recommendations.append("Build quality backlinks from relevant domains")
        else:
            recommendations.append("Maintain current ranking with regular content updates")
            recommendations.append("Expand to related keyword opportunities")
        
        # SERP-based recommendations
        if serp_results:
            # Check for featured snippet opportunities
            featured_snippets = [r for r in serp_results[:5] if r.featured_snippet]
            if not featured_snippets:
                recommendations.append("Target featured snippet with structured, concise content")
            
            # Check for PAA opportunities
            paa_results = [r for r in serp_results[:5] if r.paa_questions]
            if paa_results:
                recommendations.append("Include People Also Ask questions in your content")
        
        # Content recommendations
        if keyword_data.search_volume and keyword_data.search_volume > 5000:
            recommendations.append("Create comprehensive, in-depth content (2000+ words)")
        else:
            recommendations.append("Focus on specific, targeted content addressing user intent")
        
        return recommendations


class KeywordAnalyzer:
    """
    Advanced keyword analysis and scoring system
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def analyze_keyword_complexity(self, keyword: str) -> dict:
        """
        Analyze keyword complexity and structure
        
        Args:
            keyword: Target keyword
            
        Returns:
            Dictionary with complexity metrics
        """
        try:
            # Basic metrics
            word_count = len(keyword.split())
            char_count = len(keyword)
            avg_word_length = char_count / word_count if word_count > 0 else 0
            
            # Complexity indicators
            has_numbers = any(char.isdigit() for char in keyword)
            has_special_chars = any(not char.isalnum() and char != ' ' for char in keyword)
            has_long_words = any(len(word) > 8 for word in keyword.split())
            
            # Intent classification
            intent = self._classify_keyword_intent(keyword)
            
            # Difficulty indicators
            difficulty_factors = []
            if word_count > 4:
                difficulty_factors.append("long_tail")
            if has_numbers:
                difficulty_factors.append("specific")
            if has_special_chars:
                difficulty_factors.append("technical")
            if has_long_words:
                difficulty_factors.append("complex_terms")
            
            # Overall complexity score (0-100)
            complexity_score = min(100, (
                word_count * 10 +
                (avg_word_length - 4) * 5 +
                (10 if has_numbers else 0) +
                (10 if has_special_chars else 0) +
                (15 if has_long_words else 0)
            ))
            
            return {
                "keyword": keyword,
                "word_count": word_count,
                "char_count": char_count,
                "avg_word_length": round(avg_word_length, 2),
                "has_numbers": has_numbers,
                "has_special_chars": has_special_chars,
                "has_long_words": has_long_words,
                "intent": intent,
                "difficulty_factors": difficulty_factors,
                "complexity_score": round(complexity_score, 1),
                "complexity_level": self._get_complexity_level(complexity_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing keyword complexity: {str(e)}")
            return {"keyword": keyword, "error": str(e)}
    
    def _get_complexity_level(self, score: float) -> str:
        """Get human-readable complexity level"""
        if score < 30:
            return "easy"
        elif score < 60:
            return "moderate"
        elif score < 80:
            return "difficult"
        else:
            return "very_difficult"
    
    def analyze_keyword_trends(self, keyword_data: List[KeywordRecord]) -> dict:
        """
        Analyze keyword trends and patterns
        
        Args:
            keyword_data: List of keyword records with trend data
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            if not keyword_data:
                return {"error": "No keyword data provided"}
            
            # Extract trends data
            trends_data = []
            for record in keyword_data:
                if record.trends and len(record.trends) >= 12:  # At least 12 months
                    trends_data.append({
                        "keyword": record.keyword,
                        "trends": record.trends,
                        "avg_volume": sum(record.trends) / len(record.trends),
                        "trend_direction": self._calculate_trend_direction(record.trends)
                    })
            
            if not trends_data:
                return {"error": "No trend data available"}
            
            # Calculate overall trends
            all_trends = []
            for data in trends_data:
                all_trends.extend(data["trends"])
            
            # Trend analysis
            avg_volume = sum(all_trends) / len(all_trends)
            trend_direction = self._calculate_trend_direction(all_trends)
            seasonality = self._detect_seasonality(all_trends)
            
            # Growth rate calculation
            if len(all_trends) >= 2:
                recent_avg = sum(all_trends[-3:]) / 3  # Last 3 months
                older_avg = sum(all_trends[:3]) / 3    # First 3 months
                growth_rate = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
            else:
                growth_rate = 0
            
            return {
                "total_keywords": len(trends_data),
                "avg_monthly_volume": round(avg_volume, 0),
                "trend_direction": trend_direction,
                "growth_rate_percent": round(growth_rate, 1),
                "seasonality": seasonality,
                "trend_stability": self._calculate_trend_stability(all_trends),
                "keyword_trends": trends_data
            }
            
        except Exception as e:
            logger.error(f"Error analyzing keyword trends: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_trend_direction(self, trends: List[int]) -> str:
        """Calculate overall trend direction"""
        if len(trends) < 2:
            return "stable"
        
        # Calculate linear regression slope
        x = list(range(len(trends)))
        y = trends
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            if slope > 0.1:
                return "growing"
            elif slope < -0.1:
                return "declining"
            else:
                return "stable"
        except ZeroDivisionError:
            return "stable"
    
    def _detect_seasonality(self, trends: List[int]) -> dict:
        """Detect seasonal patterns in trends"""
        if len(trends) < 12:
            return {"has_seasonality": False, "pattern": "insufficient_data"}
        
        try:
            # Simple seasonality detection
            monthly_avgs = {}
            for i, volume in enumerate(trends):
                month = i % 12
                if month not in monthly_avgs:
                    monthly_avgs[month] = []
                monthly_avgs[month].append(volume)
            
            # Calculate coefficient of variation for each month
            month_variations = {}
            for month, volumes in monthly_avgs.items():
                if len(volumes) > 1:
                    mean_vol = sum(volumes) / len(volumes)
                    variance = sum((v - mean_vol) ** 2 for v in volumes) / len(volumes)
                    std_dev = variance ** 0.5
                    cv = (std_dev / mean_vol) if mean_vol > 0 else 0
                    month_variations[month] = cv
            
            # Determine if there's significant seasonality
            avg_cv = sum(month_variations.values()) / len(month_variations) if month_variations else 0
            has_seasonality = avg_cv > 0.3  # Threshold for seasonality
            
            # Find peak and low seasons
            if has_seasonality:
                peak_month = max(month_variations, key=month_variations.get)
                low_month = min(month_variations, key=month_variations.get)
                pattern = f"Peak: Month {peak_month+1}, Low: Month {low_month+1}"
            else:
                pattern = "No significant seasonal pattern"
            
            return {
                "has_seasonality": has_seasonality,
                "pattern": pattern,
                "seasonality_strength": round(avg_cv, 3)
            }
            
        except Exception as e:
            logger.warning(f"Error detecting seasonality: {str(e)}")
            return {"has_seasonality": False, "pattern": "error"}
    
    def _calculate_trend_stability(self, trends: List[int]) -> str:
        """Calculate trend stability"""
        if len(trends) < 2:
            return "unknown"
        
        # Calculate coefficient of variation
        mean_vol = sum(trends) / len(trends)
        variance = sum((v - mean_vol) ** 2 for v in trends) / len(trends)
        std_dev = variance ** 0.5
        cv = (std_dev / mean_vol) if mean_vol > 0 else 0
        
        if cv < 0.2:
            return "very_stable"
        elif cv < 0.4:
            return "stable"
        elif cv < 0.6:
            return "moderate"
        elif cv < 0.8:
            return "volatile"
        else:
            return "very_volatile"
    
    def analyze_competitive_landscape(self, keyword_data: List[KeywordRecord], serp_results: List[SERPResult]) -> dict:
        """
        Analyze competitive landscape for keywords
        
        Args:
            keyword_data: Keyword metrics data
            serp_results: SERP analysis results
            
        Returns:
            Dictionary with competitive analysis
        """
        try:
            if not keyword_data or not serp_results:
                return {"error": "Insufficient data for competitive analysis"}
            
            # Keyword difficulty analysis
            difficulty_distribution = self._analyze_difficulty_distribution(keyword_data)
            
            # Competition analysis
            competition_metrics = self._analyze_competition_metrics(serp_results)
            
            # Opportunity scoring
            opportunity_scores = self._calculate_opportunity_scores(keyword_data, serp_results)
            
            # Competitive positioning
            positioning = self._analyze_competitive_positioning(keyword_data, serp_results)
            
            return {
                "difficulty_distribution": difficulty_distribution,
                "competition_metrics": competition_metrics,
                "opportunity_scores": opportunity_scores,
                "competitive_positioning": positioning,
                "overall_competitiveness": self._calculate_overall_competitiveness(
                    difficulty_distribution, competition_metrics, opportunity_scores
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing competitive landscape: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_difficulty_distribution(self, keyword_data: List[KeywordRecord]) -> dict:
        """Analyze distribution of keyword difficulties"""
        difficulties = [record.difficulty for record in keyword_data if record.difficulty is not None]
        
        if not difficulties:
            return {"error": "No difficulty data available"}
        
        difficulties.sort()
        
        return {
            "total_keywords": len(difficulties),
            "min_difficulty": min(difficulties),
            "max_difficulty": max(difficulties),
            "avg_difficulty": round(sum(difficulties) / len(difficulties), 1),
            "median_difficulty": difficulties[len(difficulties) // 2],
            "difficulty_ranges": {
                "easy": len([d for d in difficulties if d < 30]),
                "moderate": len([d for d in difficulties if 30 <= d < 60]),
                "difficult": len([d for d in difficulties if 60 <= d < 80]),
                "very_difficult": len([d for d in difficulties if d >= 80])
            }
        }
    
    def _analyze_competition_metrics(self, serp_results: List[SERPResult]) -> dict:
        """Analyze SERP competition metrics"""
        if not serp_results:
            return {"error": "No SERP data available"}
        
        # Analyze top results
        top_results = serp_results[:10]
        
        # Domain diversity
        domains = [result.url.split('/')[2] for result in top_results if result.url]
        unique_domains = len(set(domains))
        domain_diversity = unique_domains / len(top_results) if top_results else 0
        
        # Featured snippet presence
        featured_snippets = sum(1 for r in top_results if r.featured_snippet)
        
        # PAA questions presence
        paa_present = sum(1 for r in top_results if r.paa_questions)
        
        # Title length analysis
        title_lengths = [len(r.title) for r in top_results if r.title]
        avg_title_length = sum(title_lengths) / len(title_lengths) if title_lengths else 0
        
        return {
            "total_results": len(top_results),
            "unique_domains": unique_domains,
            "domain_diversity": round(domain_diversity, 3),
            "featured_snippets": featured_snippets,
            "paa_questions": paa_present,
            "avg_title_length": round(avg_title_length, 1),
            "competition_level": self._get_competition_level(domain_diversity, featured_snippets)
        }
    
    def _get_competition_level(self, domain_diversity: float, featured_snippets: int) -> str:
        """Determine competition level based on metrics"""
        if domain_diversity > 0.8 and featured_snippets > 0:
            return "high"
        elif domain_diversity > 0.6:
            return "moderate"
        else:
            return "low"
    
    def _calculate_opportunity_scores(self, keyword_data: List[KeywordRecord], serp_results: List[SERPResult]) -> List[dict]:
        """Calculate opportunity scores for keywords"""
        opportunities = []
        
        for record in keyword_data:
            if not record.search_volume or not record.difficulty:
                continue
            
            # Base opportunity score
            volume_score = min(100, record.search_volume / 100)  # Normalize to 100
            difficulty_score = max(0, 100 - record.difficulty)  # Lower difficulty = higher score
            
            # CPC bonus
            cpc_bonus = min(50, (record.cpc or 0) * 10)
            
            # Competition adjustment
            competition_adjustment = self._calculate_competition_adjustment(serp_results)
            
            # Final opportunity score
            opportunity_score = (
                volume_score * 0.4 +
                difficulty_score * 0.4 +
                cpc_bonus * 0.15 +
                competition_adjustment * 0.05
            )
            
            opportunities.append({
                "keyword": record.keyword,
                "opportunity_score": round(opportunity_score, 1),
                "volume_score": round(volume_score, 1),
                "difficulty_score": round(difficulty_score, 1),
                "cpc_bonus": round(cpc_bonus, 1),
                "competition_adjustment": round(competition_adjustment, 1),
                "recommendation": self._get_opportunity_recommendation(opportunity_score)
            })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return opportunities
    
    def _calculate_competition_adjustment(self, serp_results: List[SERPResult]) -> float:
        """Calculate competition adjustment factor"""
        if not serp_results:
            return 0
        
        # Analyze competition level
        domains = [r.url.split('/')[2] for r in serp_results[:10] if r.url]
        unique_domains = len(set(domains))
        
        # More unique domains = higher competition = lower adjustment
        if unique_domains >= 8:
            return -20  # High competition penalty
        elif unique_domains >= 6:
            return -10  # Moderate competition penalty
        else:
            return 10   # Low competition bonus
    
    def _get_opportunity_recommendation(self, score: float) -> str:
        """Get recommendation based on opportunity score"""
        if score >= 80:
            return "High priority - excellent opportunity"
        elif score >= 60:
            return "Good priority - solid opportunity"
        elif score >= 40:
            return "Medium priority - moderate opportunity"
        elif score >= 20:
            return "Low priority - limited opportunity"
        else:
            return "Not recommended - poor opportunity"
    
    def _analyze_competitive_positioning(self, keyword_data: List[KeywordRecord], serp_results: List[SERPResult]) -> dict:
        """Analyze competitive positioning opportunities"""
        if not keyword_data or not serp_results:
            return {"error": "Insufficient data for positioning analysis"}
        
        # Identify content gaps
        content_gaps = self._identify_content_gaps(serp_results)
        
        # Identify featured snippet opportunities
        snippet_opportunities = self._identify_snippet_opportunities(serp_results)
        
        # Identify PAA opportunities
        paa_opportunities = self._identify_paa_opportunities(serp_results)
        
        return {
            "content_gaps": content_gaps,
            "snippet_opportunities": snippet_opportunities,
            "paa_opportunities": paa_opportunities,
            "positioning_strategy": self._generate_positioning_strategy(
                content_gaps, snippet_opportunities, paa_opportunities
            )
        }
    
    def _identify_content_gaps(self, serp_results: List[SERPResult]) -> List[str]:
        """Identify potential content gaps in SERP"""
        gaps = []
        
        # Check for missing content types
        has_videos = any("video" in r.url.lower() or "youtube" in r.url.lower() for r in serp_results)
        has_images = any("image" in r.url.lower() or "pinterest" in r.url.lower() for r in serp_results)
        has_news = any("news" in r.url.lower() for r in serp_results)
        
        if not has_videos:
            gaps.append("Video content opportunity")
        if not has_images:
            gaps.append("Visual content opportunity")
        if not has_news:
            gaps.append("News/current events content opportunity")
        
        return gaps
    
    def _identify_snippet_opportunities(self, serp_results: List[SERPResult]) -> List[str]:
        """Identify featured snippet opportunities"""
        opportunities = []
        
        # Check if featured snippet exists
        has_snippet = any(r.featured_snippet for r in serp_results[:5])
        
        if not has_snippet:
            opportunities.append("Target featured snippet with structured content")
        
        return opportunities
    
    def _identify_paa_opportunities(self, serp_results: List[SERPResult]) -> List[str]:
        """Identify People Also Ask opportunities"""
        opportunities = []
        
        # Check if PAA exists
        has_paa = any(r.paa_questions for r in serp_results[:5])
        
        if has_paa:
            opportunities.append("Include PAA questions in content")
        else:
            opportunities.append("Create content addressing common questions")
        
        return opportunities
    
    def _generate_positioning_strategy(self, content_gaps: List[str], snippet_opportunities: List[str], paa_opportunities: List[str]) -> str:
        """Generate positioning strategy recommendations"""
        strategies = []
        
        if content_gaps:
            strategies.append(f"Focus on content gaps: {', '.join(content_gaps)}")
        
        if snippet_opportunities:
            strategies.append(f"Featured snippet strategy: {', '.join(snippet_opportunities)}")
        
        if paa_opportunities:
            strategies.append(f"Q&A content: {', '.join(paa_opportunities)}")
        
        if not strategies:
            strategies.append("Maintain current positioning with regular content updates")
        
        return " | ".join(strategies)
    
    def _calculate_overall_competitiveness(self, difficulty_dist: dict, competition_metrics: dict, opportunity_scores: List[dict]) -> dict:
        """Calculate overall competitiveness score"""
        try:
            # Difficulty factor (0-100, higher = more competitive)
            avg_difficulty = difficulty_dist.get("avg_difficulty", 50)
            difficulty_factor = avg_difficulty
            
            # Competition factor (0-100, higher = more competitive)
            domain_diversity = competition_metrics.get("domain_diversity", 0.5)
            competition_factor = domain_diversity * 100
            
            # Opportunity factor (0-100, higher = less competitive)
            if opportunity_scores:
                avg_opportunity = sum(s["opportunity_score"] for s in opportunity_scores) / len(opportunity_scores)
                opportunity_factor = 100 - avg_opportunity  # Invert for competitiveness
            else:
                opportunity_factor = 50
            
            # Weighted overall competitiveness
            overall_competitiveness = (
                difficulty_factor * 0.4 +
                competition_factor * 0.4 +
                opportunity_factor * 0.2
            )
            
            return {
                "overall_score": round(overall_competitiveness, 1),
                "difficulty_factor": round(difficulty_factor, 1),
                "competition_factor": round(competition_factor, 1),
                "opportunity_factor": round(opportunity_factor, 1),
                "competitiveness_level": self._get_competitiveness_level(overall_competitiveness)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall competitiveness: {str(e)}")
            return {"error": str(e)}
    
    def _get_competitiveness_level(self, score: float) -> str:
        """Get competitiveness level description"""
        if score < 30:
            return "low_competition"
        elif score < 60:
            return "moderate_competition"
        elif score < 80:
            return "high_competition"
        else:
            return "very_high_competition"


class SEMrushClient:
    """
    Client for interacting with SEMrush API with enhanced authentication and connection handling
    """
    
    def __init__(self, config: SEMrushConfig):
        self.config = config
        self.session = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True
        )
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = 0
        
        # Connection health tracking
        self.connection_healthy = True
        self.last_successful_request = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    async def get_keyword_data(self, keyword: str) -> KeywordRecord:
        """
        Get comprehensive keyword data from SEMrush with enhanced error handling
        
        Args:
            keyword: Target keyword
            
        Returns:
            KeywordRecord with SEMrush data
        """
        await self._respect_rate_limit()
        
        try:
            # Validate API key format
            if not self._validate_api_key():
                raise ValueError("Invalid SEMrush API key format")
            
            # SEMrush Domain Overview endpoint
            params = {
                'type': 'phrase_this',
                'key': self.config.api_key,
                'phrase': keyword,
                'database': 'us',  # US database
                'export_columns': 'Ph,Nq,Cp,Co,Nr'
            }
            
            # Add retry logic
            for attempt in range(3):
                try:
                    response = await self.session.get(
                        f"{self.config.base_url}/analytics/overview",
                        params=params,
                        headers={
                            'User-Agent': 'Autonomica-SEO-Client/1.0',
                            'Accept': 'text/csv,application/json',
                            'Accept-Encoding': 'gzip, deflate'
                        }
                    )
                    
                    if response.status_code == 200:
                        # Success - reset failure counter
                        self.consecutive_failures = 0
                        self.last_successful_request = datetime.now().timestamp()
                        self.connection_healthy = True
                        
                        # Parse CSV response
                        lines = response.text.strip().split('\n')
                        if len(lines) < 2:
                            raise ValueError("Invalid response format from SEMrush")
                        
                        # Parse data (Ph=Phrase, Nq=Search Volume, Cp=CPC, Co=Competition, Nr=Results)
                        data_line = lines[1].split(';')
                        if len(data_line) < 5:
                            raise ValueError("Insufficient data in SEMrush response")
                        
                        return KeywordRecord(
                            keyword=data_line[0],
                            search_volume=int(data_line[1]) if data_line[1].isdigit() else None,
                            cpc=float(data_line[2]) if data_line[2].replace('.', '').isdigit() else None,
                            competition=float(data_line[3]) if data_line[3].replace('.', '').isdigit() else None,
                            results=int(data_line[4]) if data_line[4].isdigit() else None
                        )
                    
                    elif response.status_code == 429:
                        # Rate limit exceeded
                        await self._handle_rate_limit(response)
                        if attempt < 2:  # Don't sleep on last attempt
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
                    elif response.status_code == 401:
                        # Authentication failed
                        raise ValueError("SEMrush API authentication failed. Please check your API key.")
                    
                    elif response.status_code == 403:
                        # Forbidden - API key might be invalid or expired
                        raise ValueError("SEMrush API access denied. Please check your API key permissions.")
                    
                    else:
                        # Other HTTP errors
                        response.raise_for_status()
                        
                except httpx.TimeoutException:
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise
                        
                except httpx.ConnectError:
                    if attempt < 2:
                        await asyncio.sleep(2)
                        continue
                    else:
                        self.connection_healthy = False
                        raise
            
            # If we get here, all attempts failed
            raise Exception("All retry attempts failed")
            
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.connection_healthy = False
            
            logger.error(f"Error getting keyword data from SEMrush: {str(e)}")
            # Return basic record with available data
            return KeywordRecord(keyword=keyword)
    
    async def get_related_keywords(self, keyword: str, limit: int = 50) -> List[str]:
        """
        Get related keywords from SEMrush with enhanced error handling
        
        Args:
            keyword: Target keyword
            limit: Maximum number of related keywords to return
            
        Returns:
            List of related keywords
        """
        await self._respect_rate_limit()
        
        try:
            # Validate API key format
            if not self._validate_api_key():
                raise ValueError("Invalid SEMrush API key format")
            
            # SEMrush Related Keywords endpoint
            params = {
                'type': 'phrase_related',
                'key': self.config.api_key,
                'phrase': keyword,
                'database': 'us',
                'export_columns': 'Ph,Nq',
                'display_limit': limit
            }
            
            # Add retry logic
            for attempt in range(3):
                try:
                    response = await self.session.get(
                        f"{self.config.base_url}/analytics/overview",
                        params=params,
                        headers={
                            'User-Agent': 'Autonomica-SEO-Client/1.0',
                            'Accept': 'text/csv,application/json',
                            'Accept-Encoding': 'gzip, deflate'
                        }
                    )
                    
                    if response.status_code == 200:
                        # Success - reset failure counter
                        self.consecutive_failures = 0
                        self.last_successful_request = datetime.now().timestamp()
                        self.connection_healthy = True
                        
                        # Parse CSV response
                        lines = response.text.strip().split('\n')
                        if len(lines) < 2:
                            return []
                        
                        related_keywords = []
                        for line in lines[1:]:  # Skip header
                            data = line.split(';')
                            if len(data) >= 1:
                                related_keywords.append(data[0])
                        
                        return related_keywords[:limit]
                    
                    elif response.status_code == 429:
                        # Rate limit exceeded
                        await self._handle_rate_limit(response)
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                        continue
                    
                    elif response.status_code == 401:
                        raise ValueError("SEMrush API authentication failed. Please check your API key.")
                    
                    elif response.status_code == 403:
                        raise ValueError("SEMrush API access denied. Please check your API key permissions.")
                    
                    else:
                        response.raise_for_status()
                        
                except httpx.TimeoutException:
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise
                        
                except httpx.ConnectError:
                    if attempt < 2:
                        await asyncio.sleep(2)
                        continue
                    else:
                        self.connection_healthy = False
                        raise
            
            # If we get here, all attempts failed
            raise Exception("All retry attempts failed")
            
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.connection_healthy = False
            
            logger.error(f"Error getting related keywords from SEMrush: {str(e)}")
            return []
    
    def _validate_api_key(self) -> bool:
        """
        Validate SEMrush API key format
        
        Returns:
            True if API key format is valid
        """
        if not self.config.api_key:
            return False
        
        # SEMrush API keys are typically 32 characters long and contain alphanumeric characters
        if len(self.config.api_key) != 32:
            return False
        
        # Check if it contains only alphanumeric characters
        if not self.config.api_key.isalnum():
            return False
        
        return True
    
    async def _handle_rate_limit(self, response: httpx.Response):
        """
        Handle rate limit responses from SEMrush API
        
        Args:
            response: HTTP response that triggered rate limit
        """
        # Extract rate limit information from headers if available
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                wait_time = int(retry_after)
                await asyncio.sleep(wait_time)
            except ValueError:
                # If Retry-After is not a valid integer, use default
                await asyncio.sleep(60)
        else:
            # Default wait time for rate limit
            await asyncio.sleep(60)
        
        # Update rate limit tracking
        self.rate_limit_reset_time = datetime.now().timestamp() + 60
    
    async def _respect_rate_limit(self):
        """Ensure we don't exceed SEMrush rate limits with enhanced tracking"""
        current_time = datetime.now().timestamp()
        
        # Check if we're still in rate limit cooldown
        if current_time < self.rate_limit_reset_time:
            wait_time = self.rate_limit_reset_time - current_time
            await asyncio.sleep(wait_time)
            return
        
        # Standard rate limiting
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.config.rate_limit_per_minute
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = datetime.now().timestamp()
        self.request_count += 1
    
    async def test_connection(self) -> dict:
        """
        Test SEMrush API connection and return status information
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            # Try a simple API call with a test keyword
            test_record = await self.get_keyword_data("test")
            
            return {
                "status": "connected",
                "api_key_valid": True,
                "response_time_ms": 0,  # Could be enhanced with timing
                "last_successful_request": self.last_successful_request,
                "request_count": self.request_count,
                "connection_healthy": self.connection_healthy,
                "consecutive_failures": self.consecutive_failures
            }
            
        except Exception as e:
            return {
                "status": "error",
                "api_key_valid": self._validate_api_key(),
                "error": str(e),
                "connection_healthy": self.connection_healthy,
                "consecutive_failures": self.consecutive_failures
            }
    
    async def get_api_quota_info(self) -> dict:
        """
        Get information about API quota and usage
        
        Returns:
            Dictionary with quota information
        """
        # Note: SEMrush doesn't provide quota info in their basic API
        # This is a placeholder for future enhancement
        return {
            "quota_type": "rate_limit",
            "requests_per_minute": self.config.rate_limit_per_minute,
            "requests_this_minute": self.request_count,
            "reset_time": self.rate_limit_reset_time
        }
    
    async def close(self):
        """Close the HTTP session and cleanup resources"""
        await self.session.aclose()


class WebScraper:
    """
    Web scraper for SERP analysis and content extraction with enhanced authentication and compliance
    """
    
    def __init__(self, config: WebScrapingConfig):
        self.config = config
        self.session = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True,
            follow_redirects=True
        )
        
        # Connection health tracking
        self.connection_healthy = True
        self.last_successful_request = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # Robots.txt compliance
        self.robots_cache = {}
        self.robots_cache_ttl = 3600  # 1 hour
    
    async def scrape_serp(self, keyword: str, num_results: int = 10) -> List[SERPResult]:
        """
        Scrape Google SERP for a keyword with enhanced compliance and error handling
        
        Args:
            keyword: Target keyword
            num_results: Number of results to scrape
            
        Returns:
            List of SERP results
        """
        try:
            # Note: In production, you'd want to use a proper SERP API service
            # This is a simplified example that shows the structure
            
            # For demonstration, we'll create mock SERP results
            # In real implementation, you'd scrape actual Google results
            serp_results = []
            
            for i in range(min(num_results, 10)):
                result = SERPResult(
                    title=f"Sample Result {i+1} for '{keyword}'",
                    url=f"https://example{i+1}.com/{keyword.replace(' ', '-')}",
                    snippet=f"This is a sample search result snippet for the keyword '{keyword}'. It shows what users would see in Google search results.",
                    position=i+1,
                    featured_snippet=i == 0 and "what" in keyword.lower(),
                    paa_questions=["What is this?", "How does it work?"] if i == 0 else None
                )
                serp_results.append(result)
            
            # Add delay to respect rate limits
            await asyncio.sleep(self.config.request_delay)
            
            # Reset failure counter on success
            self.consecutive_failures = 0
            self.last_successful_request = datetime.now().timestamp()
            self.connection_healthy = True
            
            return serp_results
            
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.connection_healthy = False
            
            logger.error(f"Error scraping SERP for keyword {keyword}: {str(e)}")
            return []
    
    async def scrape_website(self, url: str, respect_robots: bool = True) -> dict:
        """
        Scrape a specific website with enhanced compliance and error handling
        
        Args:
            url: URL to scrape
            respect_robots: Whether to respect robots.txt
            
        Returns:
            Dictionary with scraped content and metadata
        """
        try:
            # Check robots.txt if enabled
            if respect_robots and self.config.respect_robots_txt:
                if not await self._can_scrape(url):
                    raise ValueError(f"Scraping not allowed for {url} according to robots.txt")
            
            # Add retry logic
            for attempt in range(self.config.max_retries):
                try:
                    response = await self.session.get(
                        url,
                        headers={
                            'User-Agent': self.config.user_agent,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1'
                        }
                    )
                    
                    if response.status_code == 200:
                        # Parse HTML content
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract comprehensive SEO data
                        seo_data = self._extract_seo_data(soup, url)
                        
                        # Reset failure counter on success
                        self.consecutive_failures = 0
                        self.last_successful_request = datetime.now().timestamp()
                        self.connection_healthy = True
                        
                        return {
                            "url": url,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "scraped_at": datetime.now().isoformat(),
                            **seo_data
                        }
                    
                    elif response.status_code == 403:
                        # Forbidden - might be blocking scrapers
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            raise ValueError(f"Access forbidden for {url}")
                    
                    elif response.status_code == 429:
                        # Rate limited
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(5 * (2 ** attempt))  # Longer backoff for rate limits
                            continue
                        else:
                            raise ValueError(f"Rate limited for {url}")
                    
                    else:
                        response.raise_for_status()
                        
                except httpx.TimeoutException:
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise
                        
                except httpx.ConnectError:
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        self.connection_healthy = False
                        raise
            
            # If we get here, all attempts failed
            raise Exception("All retry attempts failed")
            
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.connection_healthy = False
            
            logger.error(f"Error scraping website {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e),
                "status": "failed"
            }
    
    def _extract_seo_data(self, soup: BeautifulSoup, url: str) -> dict:
        """
        Extract comprehensive SEO data from parsed HTML
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Original URL being scraped
            
        Returns:
            Dictionary with extracted SEO data
        """
        # Basic content extraction
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                meta_tags[name] = content
        
        # Structured data (JSON-LD)
        structured_data = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Social media tags
        social_tags = {
            'og_title': meta_tags.get('og:title', ''),
            'og_description': meta_tags.get('og:description', ''),
            'og_image': meta_tags.get('og:image', ''),
            'og_type': meta_tags.get('og:type', ''),
            'twitter_card': meta_tags.get('twitter:card', ''),
            'twitter_title': meta_tags.get('twitter:title', ''),
            'twitter_description': meta_tags.get('twitter:description', ''),
            'twitter_image': meta_tags.get('twitter:image', '')
        }
        
        # Content analysis
        content_analysis = self._analyze_content(soup)
        
        # Links analysis
        links_analysis = self._analyze_links(soup, url)
        
        # Images analysis
        images_analysis = self._analyze_images(soup)
        
        return {
            "title": title_text,
            "meta_description": meta_tags.get('description', ''),
            "meta_keywords": meta_tags.get('keywords', ''),
            "meta_tags": meta_tags,
            "structured_data": structured_data,
            "social_tags": social_tags,
            "content_analysis": content_analysis,
            "links_analysis": links_analysis,
            "images_analysis": images_analysis,
            "canonical_url": meta_tags.get('canonical', ''),
            "robots": meta_tags.get('robots', ''),
            "language": soup.get('lang', ''),
            "charset": soup.meta.get('charset', '') if soup.meta else ''
        }
    
    def _analyze_content(self, soup: BeautifulSoup) -> dict:
        """
        Analyze page content for SEO insights
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with content analysis
        """
        # Headings
        headings = {
            'h1': len(soup.find_all('h1')),
            'h2': len(soup.find_all('h2')),
            'h3': len(soup.find_all('h3')),
            'h4': len(soup.find_all('h4')),
            'h5': len(soup.find_all('h5')),
            'h6': len(soup.find_all('h6'))
        }
        
        # Text content
        paragraphs = soup.find_all('p')
        text_content = ' '.join([p.get_text().strip() for p in paragraphs])
        
        # Word count
        word_count = len(text_content.split())
        
        # Content density
        total_tags = len(soup.find_all())
        text_tags = len(soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']))
        content_density = text_tags / total_tags if total_tags > 0 else 0
        
        # Readability (simplified Flesch Reading Ease)
        sentences = len([s for s in text_content.split('.') if s.strip()])
        avg_sentence_length = word_count / sentences if sentences > 0 else 0
        
        return {
            "headings": headings,
            "paragraphs": len(paragraphs),
            "word_count": word_count,
            "content_density": content_density,
            "avg_sentence_length": avg_sentence_length,
            "text_content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content
        }
    
    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> dict:
        """
        Analyze links for SEO insights
        
        Args:
            soup: BeautifulSoup parsed HTML
            base_url: Base URL for relative link resolution
            
        Returns:
            Dictionary with links analysis
        """
        from urllib.parse import urljoin, urlparse
        
        all_links = soup.find_all('a', href=True)
        
        internal_links = []
        external_links = []
        broken_links = []
        
        base_domain = urlparse(base_url).netloc
        
        for link in all_links:
            href = link.get('href', '')
            link_text = link.get_text().strip()
            
            if href.startswith('#'):
                continue  # Skip anchor links
                
            if href.startswith('/') or href.startswith('./'):
                # Internal relative link
                full_url = urljoin(base_url, href)
                internal_links.append({
                    'url': full_url,
                    'text': link_text,
                    'title': link.get('title', '')
                })
            elif href.startswith('http'):
                # External link
                link_domain = urlparse(href).netloc
                if link_domain != base_domain:
                    external_links.append({
                        'url': href,
                        'text': link_text,
                        'title': link.get('title', ''),
                        'domain': link_domain
                    })
                else:
                    internal_links.append({
                        'url': href,
                        'text': link_text,
                        'title': link.get('title', '')
                    })
        
        return {
            "total_links": len(all_links),
            "internal_links": internal_links,
            "external_links": external_links,
            "internal_count": len(internal_links),
            "external_count": len(external_links),
            "link_density": len(all_links) / max(1, len(soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])))
        }
    
    def _analyze_images(self, soup: BeautifulSoup) -> dict:
        """
        Analyze images for SEO insights
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dictionary with images analysis
        """
        images = soup.find_all('img')
        
        images_with_alt = []
        images_without_alt = []
        
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if alt:
                images_with_alt.append({
                    'src': src,
                    'alt': alt,
                    'title': title
                })
            else:
                images_without_alt.append({
                    'src': src,
                    'title': title
                })
        
        return {
            "total_images": len(images),
            "with_alt_text": len(images_with_alt),
            "without_alt_text": len(images_without_alt),
            "alt_text_coverage": len(images_with_alt) / len(images) if images else 0,
            "images_with_alt": images_with_alt[:10],  # Limit to first 10
            "images_without_alt": images_without_alt[:10]  # Limit to first 10
        }
    
    async def scrape_multiple_urls(self, urls: List[str], respect_robots: bool = True) -> List[dict]:
        """
        Scrape multiple URLs with rate limiting and error handling
        
        Args:
            urls: List of URLs to scrape
            respect_robots: Whether to respect robots.txt
            
        Returns:
            List of scraping results
        """
        results = []
        
        for i, url in enumerate(urls):
            try:
                # Add delay between requests
                if i > 0:
                    await asyncio.sleep(self.config.request_delay)
                
                result = await self.scrape_website(url, respect_robots)
                results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Scraped {i + 1}/{len(urls)} URLs")
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "status": "failed"
                })
        
        return results
    
    async def _can_scrape(self, url: str) -> bool:
        """
        Check if scraping is allowed according to robots.txt
        
        Args:
            url: URL to check
            
        Returns:
            True if scraping is allowed
        """
        try:
            from urllib.parse import urlparse
            
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            # Check cache first
            if robots_url in self.robots_cache:
                cache_entry = self.robots_cache[robots_url]
                if datetime.now().timestamp() - cache_entry['timestamp'] < self.robots_cache_ttl:
                    return cache_entry['can_scrape']
            
            # Fetch robots.txt
            response = await self.session.get(robots_url, timeout=10)
            if response.status_code != 200:
                # If robots.txt is not accessible, assume scraping is allowed
                return True
            
            robots_content = response.text
            
            # Parse robots.txt (simplified)
            can_scrape = True
            current_user_agent = "*"  # Default to all user agents
            
            for line in robots_content.split('\n'):
                line = line.strip()
                if line.startswith('User-agent:'):
                    current_user_agent = line.split(':', 1)[1].strip()
                elif line.startswith('Disallow:') and (current_user_agent == "*" or current_user_agent in self.config.user_agent):
                    disallow_path = line.split(':', 1)[1].strip()
                    if parsed_url.path.startswith(disallow_path):
                        can_scrape = False
                        break
            
            # Cache the result
            self.robots_cache[robots_url] = {
                'can_scrape': can_scrape,
                'timestamp': datetime.now().timestamp()
            }
            
            return can_scrape
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            # If we can't check robots.txt, assume scraping is allowed
            return True
    
    async def test_connection(self) -> dict:
        """
        Test web scraping connection and return status information
        
        Returns:
            Dictionary with connection status and details
        """
        try:
            # Try to scrape a simple test page
            test_url = "https://httpbin.org/html"
            result = await self.scrape_website(test_url, respect_robots=False)
            
            return {
                "status": "connected",
                "test_url": test_url,
                "response_time_ms": 0,  # Could be enhanced with timing
                "last_successful_request": self.last_successful_request,
                "connection_healthy": self.connection_healthy,
                "consecutive_failures": self.consecutive_failures,
                "robots_txt_respected": self.config.respect_robots_txt
            }
            
        except Exception as e:
            return {
                "status": "error",
                "test_url": test_url,
                "error": str(e),
                "connection_healthy": self.connection_healthy,
                "consecutive_failures": self.consecutive_failures
            }
    
    async def close(self):
        """Close the HTTP session and cleanup resources"""
        await self.session.aclose()


# Factory function to create SEO service
def create_seo_service(
    semrush_api_key: str,
    openai_api_key: Optional[str] = None,
    **kwargs
) -> SEOService:
    """
    Factory function to create a configured SEO service
    
    Args:
        semrush_api_key: SEMrush API key
        openai_api_key: Optional OpenAI API key for embeddings
        **kwargs: Additional configuration options
        
    Returns:
        Configured SEOService instance
    """
    config = SEOConfig(
        semrush=SEMrushConfig(api_key=semrush_api_key),
        web_scraping=WebScrapingConfig(),
        openai_api_key=openai_api_key,
        **kwargs
    )
    
    return SEOService(config)


class DataProcessingPipeline:
    """
    Comprehensive data processing pipeline for SEO data integration and analysis
    """
    
    def __init__(self):
        self.data_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        self.quality_thresholds = {
            "min_search_volume": 10,
            "max_difficulty": 100,
            "min_cpc": 0.0,
            "max_title_length": 200,
            "min_content_length": 100
        }
    
    def process_keyword_data(self, raw_data: List[dict]) -> List[KeywordRecord]:
        """
        Process and clean raw keyword data from APIs
        
        Args:
            raw_data: Raw keyword data from SEMrush or other sources
            
        Returns:
            List of cleaned KeywordRecord objects
        """
        try:
            processed_records = []
            
            for item in raw_data:
                # Data validation and cleaning
                cleaned_item = self._clean_keyword_item(item)
                
                if cleaned_item and self._validate_keyword_data(cleaned_item):
                    # Convert to KeywordRecord
                    record = KeywordRecord(
                        keyword=cleaned_item["keyword"],
                        search_volume=cleaned_item.get("search_volume"),
                        cpc=cleaned_item.get("cpc"),
                        difficulty=cleaned_item.get("difficulty"),
                        trends=cleaned_item.get("trends", []),
                        related_keywords=cleaned_item.get("related_keywords", []),
                        competition=cleaned_item.get("competition"),
                        url=cleaned_item.get("url")
                    )
                    processed_records.append(record)
            
            logger.info(f"Processed {len(processed_records)} keyword records from {len(raw_data)} raw items")
            return processed_records
            
        except Exception as e:
            logger.error(f"Error processing keyword data: {str(e)}")
            return []
    
    def _clean_keyword_item(self, item: dict) -> dict:
        """Clean and normalize individual keyword item"""
        try:
            cleaned = {}
            
            # Clean keyword text
            if "keyword" in item:
                cleaned["keyword"] = item["keyword"].strip().lower()
            
            # Clean search volume
            if "search_volume" in item:
                volume = item["search_volume"]
                if isinstance(volume, str):
                    volume = volume.replace(",", "").replace("K", "000").replace("M", "000000")
                cleaned["search_volume"] = int(float(volume)) if volume else None
            
            # Clean CPC
            if "cpc" in item:
                cpc = item["cpc"]
                if isinstance(cpc, str):
                    cpc = cpc.replace("$", "").replace(",", "")
                cleaned["cpc"] = float(cpc) if cpc else None
            
            # Clean difficulty
            if "difficulty" in item:
                difficulty = item["difficulty"]
                if isinstance(difficulty, str):
                    difficulty = difficulty.replace("%", "")
                cleaned["difficulty"] = int(float(difficulty)) if difficulty else None
            
            # Clean trends data
            if "trends" in item:
                trends = item["trends"]
                if isinstance(trends, list):
                    cleaned["trends"] = [int(t) if t else 0 for t in trends]
                else:
                    cleaned["trends"] = []
            
            # Clean related keywords
            if "related_keywords" in item:
                related = item["related_keywords"]
                if isinstance(related, list):
                    cleaned["related_keywords"] = [k.strip().lower() for k in related if k]
                else:
                    cleaned["related_keywords"] = []
            
            # Clean competition data
            if "competition" in item:
                competition = item["competition"]
                if isinstance(competition, str):
                    competition = competition.replace("%", "")
                cleaned["competition"] = float(competition) if competition else None
            
            # Clean URL
            if "url" in item:
                cleaned["url"] = item["url"].strip() if item["url"] else None
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error cleaning keyword item: {str(e)}")
            return {}
    
    def _validate_keyword_data(self, item: dict) -> bool:
        """Validate cleaned keyword data against quality thresholds"""
        try:
            # Check required fields
            if not item.get("keyword"):
                return False
            
            # Validate search volume
            if item.get("search_volume") is not None:
                if item["search_volume"] < self.quality_thresholds["min_search_volume"]:
                    return False
            
            # Validate difficulty
            if item.get("difficulty") is not None:
                if not (0 <= item["difficulty"] <= self.quality_thresholds["max_difficulty"]):
                    return False
            
            # Validate CPC
            if item.get("cpc") is not None:
                if item["cpc"] < self.quality_thresholds["min_cpc"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating keyword data: {str(e)}")
            return False
    
    def process_serp_data(self, raw_serp_data: List[dict]) -> List[SERPResult]:
        """
        Process and clean raw SERP data from web scraping
        
        Args:
            raw_serp_data: Raw SERP data from web scraping
            
        Returns:
            List of cleaned SERPResult objects
        """
        try:
            processed_results = []
            
            for item in raw_serp_data:
                # Data validation and cleaning
                cleaned_item = self._clean_serp_item(item)
                
                if cleaned_item and self._validate_serp_data(cleaned_item):
                    # Convert to SERPResult
                    result = SERPResult(
                        title=cleaned_item["title"],
                        url=cleaned_item["url"],
                        snippet=cleaned_item.get("snippet"),
                        position=cleaned_item.get("position"),
                        featured_snippet=cleaned_item.get("featured_snippet", False),
                        paa_questions=cleaned_item.get("paa_questions", []),
                        structured_data=cleaned_item.get("structured_data", {}),
                        meta_description=cleaned_item.get("meta_description"),
                        content_type=cleaned_item.get("content_type", "webpage")
                    )
                    processed_results.append(result)
            
            logger.info(f"Processed {len(processed_results)} SERP results from {len(raw_serp_data)} raw items")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error processing SERP data: {str(e)}")
            return []
    
    def _clean_serp_item(self, item: dict) -> dict:
        """Clean and normalize individual SERP item"""
        try:
            cleaned = {}
            
            # Clean title
            if "title" in item:
                cleaned["title"] = item["title"].strip() if item["title"] else ""
            
            # Clean URL
            if "url" in item:
                cleaned["url"] = item["url"].strip() if item["url"] else ""
            
            # Clean snippet
            if "snippet" in item:
                cleaned["snippet"] = item["snippet"].strip() if item["snippet"] else ""
            
            # Clean position
            if "position" in item:
                position = item["position"]
                if isinstance(position, str):
                    position = position.replace("#", "")
                cleaned["position"] = int(position) if position else None
            
            # Clean featured snippet
            if "featured_snippet" in item:
                cleaned["featured_snippet"] = bool(item["featured_snippet"])
            
            # Clean PAA questions
            if "paa_questions" in item:
                paa = item["paa_questions"]
                if isinstance(paa, list):
                    cleaned["paa_questions"] = [q.strip() for q in paa if q]
                else:
                    cleaned["paa_questions"] = []
            
            # Clean structured data
            if "structured_data" in item:
                cleaned["structured_data"] = item["structured_data"] if isinstance(item["structured_data"], dict) else {}
            
            # Clean meta description
            if "meta_description" in item:
                cleaned["meta_description"] = item["meta_description"].strip() if item["meta_description"] else ""
            
            # Clean content type
            if "content_type" in item:
                cleaned["content_type"] = item["content_type"].strip().lower() if item["content_type"] else "webpage"
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error cleaning SERP item: {str(e)}")
            return {}
    
    def _validate_serp_data(self, item: dict) -> bool:
        """Validate cleaned SERP data against quality thresholds"""
        try:
            # Check required fields
            if not item.get("title") or not item.get("url"):
                return False
            
            # Validate title length
            if len(item["title"]) > self.quality_thresholds["max_title_length"]:
                return False
            
            # Validate URL format
            if not item["url"].startswith(("http://", "https://")):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating SERP data: {str(e)}")
            return False
    
    def integrate_data_sources(self, keyword_data: List[KeywordRecord], serp_data: List[SERPResult], 
                             web_scraping_data: List[dict] = None) -> dict:
        """
        Integrate data from multiple sources into a unified dataset
        
        Args:
            keyword_data: Processed keyword data
            serp_data: Processed SERP data
            web_scraping_data: Additional web scraping data
            
        Returns:
            Integrated dataset with cross-referenced information
        """
        try:
            integrated_data = {
                "keywords": keyword_data,
                "serp_results": serp_data,
                "web_scraping": web_scraping_data or [],
                "cross_references": {},
                "data_quality": {},
                "summary_stats": {}
            }
            
            # Create cross-references between data sources
            integrated_data["cross_references"] = self._create_cross_references(keyword_data, serp_data)
            
            # Assess data quality
            integrated_data["data_quality"] = self._assess_data_quality(integrated_data)
            
            # Generate summary statistics
            integrated_data["summary_stats"] = self._generate_summary_stats(integrated_data)
            
            logger.info("Data integration completed successfully")
            return integrated_data
            
        except Exception as e:
            logger.error(f"Error integrating data sources: {str(e)}")
            return {"error": str(e)}
    
    def _create_cross_references(self, keyword_data: List[KeywordRecord], serp_data: List[SERPResult]) -> dict:
        """Create cross-references between keyword and SERP data"""
        try:
            cross_refs = {}
            
            for keyword_record in keyword_data:
                keyword = keyword_record.keyword.lower()
                cross_refs[keyword] = {
                    "keyword_data": keyword_record,
                    "serp_matches": [],
                    "content_opportunities": [],
                    "competition_analysis": {}
                }
                
                # Find matching SERP results
                for serp_result in serp_data:
                    if keyword in serp_result.title.lower() or keyword in serp_result.snippet.lower():
                        cross_refs[keyword]["serp_matches"].append(serp_result)
                
                # Identify content opportunities
                cross_refs[keyword]["content_opportunities"] = self._identify_content_opportunities(
                    keyword_record, cross_refs[keyword]["serp_matches"]
                )
                
                # Analyze competition
                cross_refs[keyword]["competition_analysis"] = self._analyze_keyword_competition(
                    keyword_record, cross_refs[keyword]["serp_matches"]
                )
            
            return cross_refs
            
        except Exception as e:
            logger.error(f"Error creating cross-references: {str(e)}")
            return {}
    
    def _identify_content_opportunities(self, keyword_record: KeywordRecord, serp_matches: List[SERPResult]) -> List[str]:
        """Identify content opportunities based on keyword and SERP analysis"""
        opportunities = []
        
        try:
            # Check for featured snippet opportunities
            has_featured_snippet = any(r.featured_snippet for r in serp_matches)
            if not has_featured_snippet:
                opportunities.append("Target featured snippet with structured content")
            
            # Check for PAA opportunities
            has_paa = any(r.paa_questions for r in serp_matches)
            if has_paa:
                opportunities.append("Include PAA questions in content")
            
            # Check for content gaps
            if keyword_record.search_volume and keyword_record.search_volume > 1000:
                if len(serp_matches) < 5:
                    opportunities.append("Low competition - good opportunity for content creation")
            
            # Check for long-tail opportunities
            if keyword_record.keyword.count(" ") >= 3:
                opportunities.append("Long-tail keyword - focus on specific user intent")
            
            return opportunities
            
        except Exception as e:
            logger.warning(f"Error identifying content opportunities: {str(e)}")
            return []
    
    def _analyze_keyword_competition(self, keyword_record: KeywordRecord, serp_matches: List[SERPResult]) -> dict:
        """Analyze competition for a specific keyword"""
        try:
            analysis = {
                "serp_competition": len(serp_matches),
                "domain_diversity": 0,
                "content_quality_indicators": {},
                "competition_level": "unknown"
            }
            
            if serp_matches:
                # Analyze domain diversity
                domains = [r.url.split('/')[2] for r in serp_matches if r.url]
                analysis["domain_diversity"] = len(set(domains))
                
                # Analyze content quality indicators
                analysis["content_quality_indicators"] = {
                    "avg_title_length": sum(len(r.title) for r in serp_matches if r.title) / len(serp_matches),
                    "featured_snippets": sum(1 for r in serp_matches if r.featured_snippet),
                    "structured_data_presence": sum(1 for r in serp_matches if r.structured_data)
                }
                
                # Determine competition level
                if analysis["domain_diversity"] >= 8:
                    analysis["competition_level"] = "high"
                elif analysis["domain_diversity"] >= 5:
                    analysis["competition_level"] = "moderate"
                else:
                    analysis["competition_level"] = "low"
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Error analyzing keyword competition: {str(e)}")
            return {"error": str(e)}
    
    def _assess_data_quality(self, integrated_data: dict) -> dict:
        """Assess overall data quality across all sources"""
        try:
            quality_metrics = {
                "keyword_data_quality": 0,
                "serp_data_quality": 0,
                "overall_quality": 0,
                "data_completeness": 0,
                "data_consistency": 0,
                "recommendations": []
            }
            
            # Assess keyword data quality
            if integrated_data["keywords"]:
                valid_keywords = sum(1 for k in integrated_data["keywords"] if k.search_volume and k.difficulty)
                quality_metrics["keyword_data_quality"] = (valid_keywords / len(integrated_data["keywords"])) * 100
            
            # Assess SERP data quality
            if integrated_data["serp_results"]:
                valid_serp = sum(1 for s in integrated_data["serp_results"] if s.title and s.url)
                quality_metrics["serp_data_quality"] = (valid_serp / len(integrated_data["serp_results"])) * 100
            
            # Calculate overall quality
            quality_metrics["overall_quality"] = (
                quality_metrics["keyword_data_quality"] * 0.6 +
                quality_metrics["serp_data_quality"] * 0.4
            )
            
            # Assess data completeness
            total_expected_fields = len(integrated_data["keywords"]) * 6 + len(integrated_data["serp_results"]) * 8
            if total_expected_fields > 0:
                filled_fields = sum(1 for k in integrated_data["keywords"] for v in k.__dict__.values() if v is not None)
                filled_fields += sum(1 for s in integrated_data["serp_results"] for v in s.__dict__.values() if v is not None)
                quality_metrics["data_completeness"] = (filled_fields / total_expected_fields) * 100
            
            # Generate recommendations
            if quality_metrics["keyword_data_quality"] < 80:
                quality_metrics["recommendations"].append("Improve keyword data quality - ensure search volume and difficulty data")
            
            if quality_metrics["serp_data_quality"] < 80:
                quality_metrics["recommendations"].append("Improve SERP data quality - ensure title and URL data")
            
            if quality_metrics["overall_quality"] < 70:
                quality_metrics["recommendations"].append("Overall data quality needs improvement - review data sources and validation")
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {str(e)}")
            return {"error": str(e)}
    
    def _generate_summary_stats(self, integrated_data: dict) -> dict:
        """Generate summary statistics for the integrated dataset"""
        try:
            stats = {
                "total_keywords": len(integrated_data["keywords"]),
                "total_serp_results": len(integrated_data["serp_results"]),
                "keyword_metrics": {},
                "serp_metrics": {},
                "data_coverage": {}
            }
            
            # Keyword metrics
            if integrated_data["keywords"]:
                volumes = [k.search_volume for k in integrated_data["keywords"] if k.search_volume]
                difficulties = [k.difficulty for k in integrated_data["keywords"] if k.difficulty]
                cpcs = [k.cpc for k in integrated_data["keywords"] if k.cpc]
                
                stats["keyword_metrics"] = {
                    "avg_search_volume": sum(volumes) / len(volumes) if volumes else 0,
                    "avg_difficulty": sum(difficulties) / len(difficulties) if difficulties else 0,
                    "avg_cpc": sum(cpcs) / len(cpcs) if cpcs else 0,
                    "high_volume_keywords": sum(1 for v in volumes if v > 10000),
                    "low_difficulty_keywords": sum(1 for d in difficulties if d < 30)
                }
            
            # SERP metrics
            if integrated_data["serp_results"]:
                featured_snippets = sum(1 for s in integrated_data["serp_results"] if s.featured_snippet)
                paa_present = sum(1 for s in integrated_data["serp_results"] if s.paa_questions)
                
                stats["serp_metrics"] = {
                    "featured_snippets": featured_snippets,
                    "paa_questions": paa_present,
                    "avg_title_length": sum(len(s.title) for s in integrated_data["serp_results"] if s.title) / len(integrated_data["serp_results"])
                }
            
            # Data coverage
            if integrated_data["cross_references"]:
                covered_keywords = sum(1 for ref in integrated_data["cross_references"].values() if ref["serp_matches"])
                stats["data_coverage"] = {
                    "keywords_with_serp_data": covered_keywords,
                    "coverage_percentage": (covered_keywords / len(integrated_data["cross_references"])) * 100
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating summary stats: {str(e)}")
            return {"error": str(e)}
    
    def export_data(self, integrated_data: dict, format: str = "json") -> str:
        """
        Export integrated data in specified format
        
        Args:
            integrated_data: Integrated dataset
            format: Export format (json, csv, xml)
            
        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "json":
                return self._export_json(integrated_data)
            elif format.lower() == "csv":
                return self._export_csv(integrated_data)
            elif format.lower() == "xml":
                return self._export_xml(integrated_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return f"Export error: {str(e)}"
    
    def _export_json(self, data: dict) -> str:
        """Export data as JSON"""
        try:
            import json
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            return f"JSON export error: {str(e)}"
    
    def _export_csv(self, data: dict) -> str:
        """Export data as CSV"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(["Keyword", "Search Volume", "Difficulty", "CPC", "SERP Results", "Competition Level"])
            
            # Write data
            for keyword, ref in data.get("cross_references", {}).items():
                keyword_data = ref.get("keyword_data", {})
                writer.writerow([
                    keyword,
                    getattr(keyword_data, 'search_volume', ''),
                    getattr(keyword_data, 'difficulty', ''),
                    getattr(keyword_data, 'cpc', ''),
                    len(ref.get("serp_matches", [])),
                    ref.get("competition_analysis", {}).get("competition_level", "")
                ])
            
            return output.getvalue()
            
        except Exception as e:
            return f"CSV export error: {str(e)}"
    
    def _export_xml(self, data: dict) -> str:
        """Export data as XML"""
        try:
            xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<seo_data>']
            
            # Add summary stats
            xml_parts.append('<summary_stats>')
            for key, value in data.get("summary_stats", {}).items():
                xml_parts.append(f'<{key}>{value}</{key}>')
            xml_parts.append('</summary_stats>')
            
            # Add keywords
            xml_parts.append('<keywords>')
            for keyword, ref in data.get("cross_references", {}).items():
                xml_parts.append(f'<keyword name="{keyword}">')
                keyword_data = ref.get("keyword_data", {})
                if hasattr(keyword_data, 'search_volume'):
                    xml_parts.append(f'<search_volume>{getattr(keyword_data, "search_volume", "")}</search_volume>')
                if hasattr(keyword_data, 'difficulty'):
                    xml_parts.append(f'<difficulty>{getattr(keyword_data, "difficulty", "")}</difficulty>')
                xml_parts.append('</keyword>')
            xml_parts.append('</keywords>')
            
            xml_parts.append('</seo_data>')
            return '\n'.join(xml_parts)
            
        except Exception as e:
            return f"XML export error: {str(e)}"


class KeywordSuggestionEngine:
    """
    Advanced keyword suggestion engine with multiple suggestion strategies
    """
    
    def __init__(self, seo_service: SEOService):
        self.seo_service = seo_service
        self.suggestion_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.similarity_threshold = 0.7
        self.max_suggestions = 50
    
    def suggest_keywords(self, seed_keyword: str, suggestion_type: str = "comprehensive", 
                        max_results: int = 20, filters: dict = None) -> dict:
        """
        Generate keyword suggestions based on seed keyword
        
        Args:
            seed_keyword: Base keyword for suggestions
            suggestion_type: Type of suggestions (comprehensive, related, long_tail, questions, local)
            max_results: Maximum number of suggestions to return
            filters: Optional filters for suggestions
            
        Returns:
            Dictionary with suggestions and metadata
        """
        try:
            # Check cache first
            cache_key = f"{seed_keyword}_{suggestion_type}_{max_results}"
            if cache_key in self.suggestion_cache:
                cached_result = self.suggestion_cache[cache_key]
                if cached_result.get("timestamp", 0) + self.cache_ttl > time.time():
                    return cached_result["data"]
            
            # Generate suggestions based on type
            if suggestion_type == "comprehensive":
                suggestions = self._generate_comprehensive_suggestions(seed_keyword, max_results, filters)
            elif suggestion_type == "related":
                suggestions = self._generate_related_suggestions(seed_keyword, max_results, filters)
            elif suggestion_type == "long_tail":
                suggestions = self._generate_long_tail_suggestions(seed_keyword, max_results, filters)
            elif suggestion_type == "questions":
                suggestions = self._generate_question_suggestions(seed_keyword, max_results, filters)
            elif suggestion_type == "local":
                suggestions = self._generate_local_suggestions(seed_keyword, max_results, filters)
            else:
                raise ValueError(f"Unsupported suggestion type: {suggestion_type}")
            
            # Apply filters if provided
            if filters:
                suggestions = self._apply_suggestion_filters(suggestions, filters)
            
            # Limit results
            suggestions = suggestions[:max_results]
            
            # Calculate suggestion scores
            scored_suggestions = self._calculate_suggestion_scores(suggestions, seed_keyword)
            
            # Sort by score
            scored_suggestions.sort(key=lambda x: x["score"], reverse=True)
            
            result = {
                "seed_keyword": seed_keyword,
                "suggestion_type": suggestion_type,
                "total_suggestions": len(scored_suggestions),
                "suggestions": scored_suggestions,
                "metadata": {
                    "generation_time": time.time(),
                    "filters_applied": bool(filters),
                    "similarity_threshold": self.similarity_threshold
                }
            }
            
            # Cache the result
            self.suggestion_cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            logger.info(f"Generated {len(scored_suggestions)} {suggestion_type} suggestions for '{seed_keyword}'")
            return result
            
        except Exception as e:
            logger.error(f"Error generating keyword suggestions: {str(e)}")
            return {"error": str(e)}
    
    def _generate_comprehensive_suggestions(self, seed_keyword: str, max_results: int, filters: dict) -> List[dict]:
        """Generate comprehensive keyword suggestions using multiple strategies"""
        suggestions = []
        
        try:
            # Get related keywords from SEMrush
            try:
                related_data = self.seo_service.semrush_client.get_related_keywords(seed_keyword)
                if related_data and not isinstance(related_data, dict):
                    for record in related_data:
                        suggestions.append({
                            "keyword": record.keyword,
                            "search_volume": record.search_volume,
                            "difficulty": record.difficulty,
                            "cpc": record.cpc,
                            "source": "semrush_related",
                            "similarity": self._calculate_keyword_similarity(seed_keyword, record.keyword)
                        })
            except Exception as e:
                logger.warning(f"Could not get SEMrush related keywords: {str(e)}")
            
            # Generate semantic variations
            semantic_variations = self._generate_semantic_variations(seed_keyword)
            for variation in semantic_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "semantic_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Generate long-tail variations
            long_tail_variations = self._generate_long_tail_variations(seed_keyword)
            for variation in long_tail_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "long_tail_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Generate question variations
            question_variations = self._generate_question_variations(seed_keyword)
            for variation in question_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "question_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Remove duplicates
            seen_keywords = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion["keyword"] not in seen_keywords:
                    seen_keywords.add(suggestion["keyword"])
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions
            
        except Exception as e:
            logger.error(f"Error generating comprehensive suggestions: {str(e)}")
            return []
    
    def _generate_related_suggestions(self, seed_keyword: str, max_results: int, filters: dict) -> List[dict]:
        """Generate related keyword suggestions based on semantic similarity"""
        suggestions = []
        
        try:
            # Get related keywords from SEMrush
            try:
                related_data = self.seo_service.semrush_client.get_related_keywords(seed_keyword)
                if related_data and not isinstance(related_data, dict):
                    for record in related_data:
                        suggestions.append({
                            "keyword": record.keyword,
                            "search_volume": record.search_volume,
                            "difficulty": record.difficulty,
                            "cpc": record.cpc,
                            "source": "semrush_related",
                            "similarity": self._calculate_keyword_similarity(seed_keyword, record.keyword)
                        })
            except Exception as e:
                logger.warning(f"Could not get SEMrush related keywords: {str(e)}")
            
            # Generate semantic variations
            semantic_variations = self._generate_semantic_variations(seed_keyword)
            for variation in semantic_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "semantic_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Filter by similarity threshold
            suggestions = [s for s in suggestions if s["similarity"] >= self.similarity_threshold]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating related suggestions: {str(e)}")
            return []
    
    def _generate_long_tail_suggestions(self, seed_keyword: str, max_results: int, filters: dict) -> List[dict]:
        """Generate long-tail keyword suggestions"""
        suggestions = []
        
        try:
            # Generate long-tail variations
            long_tail_variations = self._generate_long_tail_variations(seed_keyword)
            for variation in long_tail_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "long_tail_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Add modifiers for long-tail generation
            modifiers = [
                "best", "top", "how to", "guide", "tutorial", "tips", "strategies",
                "examples", "tools", "software", "services", "companies", "agencies",
                "2024", "2025", "latest", "trending", "popular", "effective",
                "professional", "expert", "advanced", "beginner", "free", "paid"
            ]
            
            for modifier in modifiers:
                long_tail = f"{modifier} {seed_keyword}"
                suggestions.append({
                    "keyword": long_tail,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "modifier_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, long_tail)
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating long-tail suggestions: {str(e)}")
            return []
    
    def _generate_question_suggestions(self, seed_keyword: str, max_results: int, filters: dict) -> List[dict]:
        """Generate question-based keyword suggestions"""
        suggestions = []
        
        try:
            # Generate question variations
            question_variations = self._generate_question_variations(seed_keyword)
            for variation in question_variations:
                suggestions.append({
                    "keyword": variation,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "question_variation",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, variation)
                })
            
            # Add common question patterns
            question_patterns = [
                f"what is {seed_keyword}",
                f"how to {seed_keyword}",
                f"why {seed_keyword}",
                f"when to {seed_keyword}",
                f"where to {seed_keyword}",
                f"which {seed_keyword}",
                f"best {seed_keyword}",
                f"top {seed_keyword}",
                f"{seed_keyword} vs",
                f"difference between {seed_keyword}",
                f"benefits of {seed_keyword}",
                f"cost of {seed_keyword}",
                f"time to {seed_keyword}",
                f"learn {seed_keyword}",
                f"study {seed_keyword}"
            ]
            
            for pattern in question_patterns:
                suggestions.append({
                    "keyword": pattern,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "question_pattern",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, pattern)
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating question suggestions: {str(e)}")
            return []
    
    def _generate_local_suggestions(self, seed_keyword: str, max_results: int, filters: dict) -> List[dict]:
        """Generate location-based keyword suggestions"""
        suggestions = []
        
        try:
            # Common location modifiers
            location_modifiers = [
                "near me", "in [city]", "local", "nearby", "close to me",
                "in my area", "in [state]", "in [country]", "near [landmark]",
                "downtown", "uptown", "suburban", "rural", "urban"
            ]
            
            for modifier in location_modifiers:
                local_keyword = f"{seed_keyword} {modifier}"
                suggestions.append({
                    "keyword": local_keyword,
                    "search_volume": None,
                    "difficulty": None,
                    "cpc": None,
                    "source": "location_modifier",
                    "similarity": self._calculate_keyword_similarity(seed_keyword, local_keyword)
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating local suggestions: {str(e)}")
            return []
    
    def _generate_semantic_variations(self, seed_keyword: str) -> List[str]:
        """Generate semantic variations of the seed keyword"""
        variations = []
        
        try:
            # Synonyms and related terms
            synonyms = {
                "digital marketing": ["online marketing", "internet marketing", "web marketing", "e-marketing"],
                "seo": ["search engine optimization", "search optimization", "organic search"],
                "ppc": ["pay per click", "paid search", "search advertising", "google ads"],
                "social media": ["social networking", "social platforms", "social channels"],
                "content marketing": ["content strategy", "content creation", "content promotion"],
                "email marketing": ["email campaigns", "email automation", "email newsletters"],
                "analytics": ["data analysis", "metrics", "reporting", "insights"],
                "conversion": ["conversion rate", "conversion optimization", "c conversion"],
                "backlinks": ["inbound links", "external links", "link building"],
                "keywords": ["search terms", "search queries", "target phrases"]
            }
            
            # Find synonyms for seed keyword
            for key, values in synonyms.items():
                if seed_keyword.lower() in key.lower() or any(syn in seed_keyword.lower() for syn in values):
                    variations.extend(values)
                    break
            
            # Add common variations
            if "marketing" in seed_keyword.lower():
                variations.extend(["strategy", "campaign", "plan", "approach"])
            if "seo" in seed_keyword.lower() or "optimization" in seed_keyword.lower():
                variations.extend(["improvement", "enhancement", "refinement"])
            if "content" in seed_keyword.lower():
                variations.extend(["material", "assets", "resources", "media"])
            
            return list(set(variations))[:10]  # Limit to 10 variations
            
        except Exception as e:
            logger.warning(f"Error generating semantic variations: {str(e)}")
            return []
    
    def _generate_long_tail_variations(self, seed_keyword: str) -> List[str]:
        """Generate long-tail keyword variations"""
        variations = []
        
        try:
            # Add descriptive modifiers
            descriptive_modifiers = [
                "for beginners", "for small business", "for ecommerce", "for local business",
                "step by step", "complete guide", "ultimate guide", "comprehensive",
                "advanced techniques", "expert tips", "professional advice",
                "on a budget", "free tools", "paid solutions", "enterprise level",
                "quick start", "in depth", "practical examples", "case studies"
            ]
            
            for modifier in descriptive_modifiers:
                variations.append(f"{seed_keyword} {modifier}")
            
            # Add industry-specific modifiers
            industry_modifiers = [
                "for healthcare", "for finance", "for education", "for real estate",
                "for restaurants", "for retail", "for manufacturing", "for technology",
                "for nonprofits", "for government", "for startups", "for enterprise"
            ]
            
            for modifier in industry_modifiers:
                variations.append(f"{seed_keyword} {modifier}")
            
            return variations[:15]  # Limit to 15 variations
            
        except Exception as e:
            logger.warning(f"Error generating long-tail variations: {str(e)}")
            return []
    
    def _generate_question_variations(self, seed_keyword: str) -> List[str]:
        """Generate question-based keyword variations"""
        variations = []
        
        try:
            # Common question starters
            question_starters = [
                "what is", "how to", "why", "when", "where", "which", "who",
                "can you", "do you", "should I", "is it", "are there", "what are",
                "how do", "how can", "what makes", "what causes", "how much",
                "how long", "how often", "what time", "what day", "what month"
            ]
            
            for starter in question_starters:
                variations.append(f"{starter} {seed_keyword}")
            
            # Add specific question patterns
            specific_patterns = [
                f"best {seed_keyword}",
                f"top {seed_keyword}",
                f"{seed_keyword} examples",
                f"{seed_keyword} definition",
                f"{seed_keyword} meaning",
                f"{seed_keyword} benefits",
                f"{seed_keyword} advantages",
                f"{seed_keyword} disadvantages",
                f"{seed_keyword} pros and cons",
                f"{seed_keyword} comparison",
                f"{seed_keyword} vs alternatives",
                f"{seed_keyword} cost",
                f"{seed_keyword} price",
                f"{seed_keyword} free",
                f"{seed_keyword} paid"
            ]
            
            variations.extend(specific_patterns)
            return variations[:20]  # Limit to 20 variations
            
        except Exception as e:
            logger.warning(f"Error generating question variations: {str(e)}")
            return []
    
    def _calculate_keyword_similarity(self, keyword1: str, keyword2: str) -> float:
        """Calculate similarity between two keywords"""
        try:
            # Simple string similarity based on common words
            words1 = set(keyword1.lower().split())
            words2 = set(keyword2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            jaccard_similarity = len(intersection) / len(union)
            
            # Boost similarity for exact matches and substrings
            if keyword1.lower() in keyword2.lower() or keyword2.lower() in keyword1.lower():
                jaccard_similarity += 0.3
            
            # Boost for same word count
            if len(words1) == len(words2):
                jaccard_similarity += 0.1
            
            return min(1.0, jaccard_similarity)
            
        except Exception as e:
            logger.warning(f"Error calculating keyword similarity: {str(e)}")
            return 0.0
    
    def _apply_suggestion_filters(self, suggestions: List[dict], filters: dict) -> List[dict]:
        """Apply filters to suggestions"""
        try:
            filtered_suggestions = suggestions.copy()
            
            # Filter by minimum similarity
            if "min_similarity" in filters:
                min_sim = filters["min_similarity"]
                filtered_suggestions = [s for s in filtered_suggestions if s["similarity"] >= min_sim]
            
            # Filter by source
            if "sources" in filters:
                allowed_sources = filters["sources"]
                filtered_suggestions = [s for s in filtered_suggestions if s["source"] in allowed_sources]
            
            # Filter by word count
            if "min_words" in filters:
                min_words = filters["min_words"]
                filtered_suggestions = [s for s in filtered_suggestions if len(s["keyword"].split()) >= min_words]
            
            if "max_words" in filters:
                max_words = filters["max_words"]
                filtered_suggestions = [s for s in filtered_suggestions if len(s["keyword"].split()) <= max_words]
            
            # Filter by search volume (if available)
            if "min_volume" in filters and any(s.get("search_volume") for s in filtered_suggestions):
                min_volume = filters["min_volume"]
                filtered_suggestions = [s for s in filtered_suggestions if not s.get("search_volume") or s["search_volume"] >= min_volume]
            
            # Filter by difficulty (if available)
            if "max_difficulty" in filters and any(s.get("difficulty") for s in filtered_suggestions):
                max_diff = filters["max_difficulty"]
                filtered_suggestions = [s for s in filtered_suggestions if not s.get("difficulty") or s["difficulty"] <= max_diff]
            
            return filtered_suggestions
            
        except Exception as e:
            logger.warning(f"Error applying suggestion filters: {str(e)}")
            return suggestions
    
    def _calculate_suggestion_scores(self, suggestions: List[dict], seed_keyword: str) -> List[dict]:
        """Calculate scores for suggestions to rank them"""
        try:
            scored_suggestions = []
            
            for suggestion in suggestions:
                score = 0.0
                
                # Base similarity score (0-100)
                score += suggestion["similarity"] * 40
                
                # Source bonus
                source_bonus = {
                    "semrush_related": 20,
                    "semantic_variation": 15,
                    "long_tail_variation": 10,
                    "question_variation": 12,
                    "modifier_variation": 8,
                    "question_pattern": 10,
                    "location_modifier": 5
                }
                score += source_bonus.get(suggestion["source"], 0)
                
                # Search volume bonus (if available)
                if suggestion.get("search_volume"):
                    if suggestion["search_volume"] > 10000:
                        score += 15
                    elif suggestion["search_volume"] > 1000:
                        score += 10
                    elif suggestion["search_volume"] > 100:
                        score += 5
                
                # Difficulty bonus (if available)
                if suggestion.get("difficulty"):
                    if suggestion["difficulty"] < 30:
                        score += 15
                    elif suggestion["difficulty"] < 50:
                        score += 10
                    elif suggestion["difficulty"] < 70:
                        score += 5
                
                # CPC bonus (if available)
                if suggestion.get("cpc"):
                    if suggestion["cpc"] > 5.0:
                        score += 10
                    elif suggestion["cpc"] > 2.0:
                        score += 5
                
                # Word count bonus
                word_count = len(suggestion["keyword"].split())
                if word_count == 1:
                    score += 5
                elif word_count == 2:
                    score += 10
                elif word_count == 3:
                    score += 15
                elif word_count == 4:
                    score += 12
                elif word_count == 5:
                    score += 8
                else:
                    score += 5
                
                # Question bonus
                if any(q in suggestion["keyword"].lower() for q in ["what", "how", "why", "when", "where", "which", "who"]):
                    score += 8
                
                # Local intent bonus
                if any(l in suggestion["keyword"].lower() for l in ["near me", "local", "nearby", "in"]):
                    score += 5
                
                suggestion["score"] = round(score, 1)
                scored_suggestions.append(suggestion)
            
            return scored_suggestions
            
        except Exception as e:
            logger.error(f"Error calculating suggestion scores: {str(e)}")
            return suggestions
    
    def get_suggestion_insights(self, suggestions: List[dict]) -> dict:
        """Generate insights from keyword suggestions"""
        try:
            insights = {
                "total_suggestions": len(suggestions),
                "source_distribution": {},
                "word_count_distribution": {},
                "question_ratio": 0,
                "local_ratio": 0,
                "avg_similarity": 0,
                "high_potential_keywords": [],
                "trending_patterns": []
            }
            
            if not suggestions:
                return insights
            
            # Source distribution
            for suggestion in suggestions:
                source = suggestion.get("source", "unknown")
                insights["source_distribution"][source] = insights["source_distribution"].get(source, 0) + 1
            
            # Word count distribution
            for suggestion in suggestions:
                word_count = len(suggestion["keyword"].split())
                insights["word_count_distribution"][word_count] = insights["word_count_distribution"].get(word_count, 0) + 1
            
            # Question ratio
            question_keywords = [s for s in suggestions if any(q in s["keyword"].lower() for q in ["what", "how", "why", "when", "where", "which", "who"])]
            insights["question_ratio"] = len(question_keywords) / len(suggestions)
            
            # Local ratio
            local_keywords = [s for s in suggestions if any(l in s["keyword"].lower() for l in ["near me", "local", "nearby", "in"])]
            insights["local_ratio"] = len(local_keywords) / len(suggestions)
            
            # Average similarity
            similarities = [s.get("similarity", 0) for s in suggestions]
            insights["avg_similarity"] = sum(similarities) / len(similarities) if similarities else 0
            
            # High potential keywords (high score, good metrics)
            high_potential = [s for s in suggestions if s.get("score", 0) > 50]
            insights["high_potential_keywords"] = [s["keyword"] for s in high_potential[:5]]
            
            # Trending patterns
            trending_patterns = []
            for suggestion in suggestions:
                keyword = suggestion["keyword"].lower()
                if "2024" in keyword or "2025" in keyword:
                    trending_patterns.append("year-specific")
                if "latest" in keyword or "trending" in keyword:
                    trending_patterns.append("trending-modifiers")
                if "best" in keyword or "top" in keyword:
                    trending_patterns.append("ranking-modifiers")
            
            insights["trending_patterns"] = list(set(trending_patterns))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating suggestion insights: {str(e)}")
            return {"error": str(e)}


class SEOScoreCalculator:
    """
    Comprehensive SEO score calculation module with weighted scoring algorithms
    """
    
    def __init__(self):
        self.score_weights = {
            "on_page": 0.25,
            "technical": 0.20,
            "content": 0.20,
            "user_experience": 0.15,
            "competitive": 0.20
        }
        
        self.factor_weights = {
            "title_optimization": 0.15,
            "meta_description": 0.10,
            "heading_structure": 0.15,
            "keyword_density": 0.10,
            "internal_linking": 0.10,
            "image_optimization": 0.10,
            "page_speed": 0.20,
            "mobile_friendliness": 0.15,
            "ssl_security": 0.10,
            "url_structure": 0.10,
            "content_length": 0.20,
            "content_quality": 0.25,
            "readability": 0.20,
            "freshness": 0.15,
            "engagement_signals": 0.20,
            "navigation": 0.15,
            "accessibility": 0.15,
            "keyword_difficulty": 0.30,
            "competition_level": 0.25,
            "search_volume": 0.25,
            "trend_direction": 0.20
        }
    
    def calculate_overall_seo_score(self, analysis_data: dict) -> dict:
        """
        Calculate comprehensive SEO score based on multiple factors
        
        Args:
            analysis_data: Dictionary containing analysis results
            
        Returns:
            Dictionary with detailed scoring breakdown
        """
        try:
            scores = {}
            
            # Calculate individual category scores
            scores["on_page"] = self._calculate_on_page_score(analysis_data)
            scores["technical"] = self._calculate_technical_score(analysis_data)
            scores["content"] = self._calculate_content_score(analysis_data)
            scores["user_experience"] = self._calculate_user_experience_score(analysis_data)
            scores["competitive"] = self._calculate_competitive_score(analysis_data)
            
            # Calculate weighted overall score
            overall_score = sum(
                scores[category] * self.score_weights[category]
                for category in scores
            )
            
            # Generate score breakdown and recommendations
            score_breakdown = self._generate_score_breakdown(scores)
            recommendations = self._generate_score_recommendations(scores, analysis_data)
            priority_actions = self._identify_priority_actions(scores)
            
            return {
                "overall_score": round(overall_score, 1),
                "grade": self._get_score_grade(overall_score),
                "category_scores": scores,
                "score_breakdown": score_breakdown,
                "recommendations": recommendations,
                "priority_actions": priority_actions,
                "improvement_potential": self._calculate_improvement_potential(scores),
                "benchmark_comparison": self._generate_benchmark_comparison(overall_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall SEO score: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_on_page_score(self, analysis_data: dict) -> float:
        """Calculate on-page SEO score"""
        try:
            score = 0.0
            factors = {}
            
            # Title optimization (0-100)
            title_score = self._evaluate_title_optimization(analysis_data.get("title", ""))
            factors["title_optimization"] = title_score
            score += title_score * self.factor_weights["title_optimization"]
            
            # Meta description (0-100)
            meta_score = self._evaluate_meta_description(analysis_data.get("meta_description", ""))
            factors["meta_description"] = meta_score
            score += meta_score * self.factor_weights["meta_description"]
            
            # Heading structure (0-100)
            heading_score = self._evaluate_heading_structure(analysis_data.get("headings", []))
            factors["heading_score"] = heading_score
            score += heading_score * self.factor_weights["heading_structure"]
            
            # Keyword density (0-100)
            keyword_score = self._evaluate_keyword_density(
                analysis_data.get("content", ""),
                analysis_data.get("target_keyword", "")
            )
            factors["keyword_density"] = keyword_score
            score += keyword_score * self.factor_weights["keyword_density"]
            
            # Internal linking (0-100)
            internal_link_score = self._evaluate_internal_linking(analysis_data.get("internal_links", []))
            factors["internal_link_score"] = internal_link_score
            score += internal_link_score * self.factor_weights["internal_linking"]
            
            # Image optimization (0-100)
            image_score = self._evaluate_image_optimization(analysis_data.get("images", []))
            factors["image_score"] = image_score
            score += image_score * self.factor_weights["image_optimization"]
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"Error calculating on-page score: {str(e)}")
            return 0.0
    
    def _calculate_technical_score(self, analysis_data: dict) -> float:
        """Calculate technical SEO score"""
        try:
            score = 0.0
            factors = {}
            
            # Page speed (0-100)
            speed_score = self._evaluate_page_speed(analysis_data.get("page_speed", {}))
            factors["page_speed"] = speed_score
            score += speed_score * self.factor_weights["page_speed"]
            
            # Mobile friendliness (0-100)
            mobile_score = self._evaluate_mobile_friendliness(analysis_data.get("mobile_metrics", {}))
            factors["mobile_score"] = mobile_score
            score += mobile_score * self.factor_weights["mobile_friendliness"]
            
            # SSL security (0-100)
            ssl_score = self._evaluate_ssl_security(analysis_data.get("url", ""))
            factors["ssl_score"] = ssl_score
            score += ssl_score * self.factor_weights["ssl_security"]
            
            # URL structure (0-100)
            url_score = self._evaluate_url_structure(analysis_data.get("url", ""))
            factors["url_score"] = url_score
            score += url_score * self.factor_weights["url_structure"]
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"Error calculating technical score: {str(e)}")
            return 0.0
    
    def _calculate_content_score(self, analysis_data: dict) -> float:
        """Calculate content quality score"""
        try:
            score = 0.0
            factors = {}
            
            # Content length (0-100)
            length_score = self._evaluate_content_length(analysis_data.get("content", ""))
            factors["content_length"] = length_score
            score += length_score * self.factor_weights["content_length"]
            
            # Content quality (0-100)
            quality_score = self._evaluate_content_quality(analysis_data.get("content", ""))
            factors["content_quality"] = quality_score
            score += quality_score * self.factor_weights["content_quality"]
            
            # Readability (0-100)
            readability_score = self._evaluate_readability(analysis_data.get("content", ""))
            factors["readability"] = readability_score
            score += readability_score * self.factor_weights["readability"]
            
            # Content freshness (0-100)
            freshness_score = self._evaluate_content_freshness(analysis_data.get("last_updated", None))
            factors["freshness"] = freshness_score
            score += freshness_score * self.factor_weights["freshness"]
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"Error calculating content score: {str(e)}")
            return 0.0
    
    def _calculate_user_experience_score(self, analysis_data: dict) -> float:
        """Calculate user experience score"""
        try:
            score = 0.0
            factors = {}
            
            # Engagement signals (0-100)
            engagement_score = self._evaluate_engagement_signals(analysis_data.get("engagement_metrics", {}))
            factors["engagement"] = engagement_score
            score += engagement_score * self.factor_weights["engagement_signals"]
            
            # Navigation (0-100)
            navigation_score = self._evaluate_navigation(analysis_data.get("navigation", {}))
            factors["navigation"] = navigation_score
            score += navigation_score * self.factor_weights["navigation"]
            
            # Accessibility (0-100)
            accessibility_score = self._evaluate_accessibility(analysis_data.get("accessibility", {}))
            factors["accessibility"] = accessibility_score
            score += accessibility_score * self.factor_weights["accessibility"]
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"Error calculating UX score: {str(e)}")
            return 0.0
    
    def _calculate_competitive_score(self, analysis_data: dict) -> float:
        """Calculate competitive positioning score"""
        try:
            score = 0.0
            factors = {}
            
            # Keyword difficulty (0-100)
            difficulty_score = self._evaluate_keyword_difficulty(analysis_data.get("keyword_difficulty", 50))
            factors["keyword_difficulty"] = difficulty_score
            score += difficulty_score * self.factor_weights["keyword_difficulty"]
            
            # Competition level (0-100)
            competition_score = self._evaluate_competition_level(analysis_data.get("competition_metrics", {}))
            factors["competition"] = competition_score
            score += competition_score * self.factor_weights["competition_level"]
            
            # Search volume (0-100)
            volume_score = self._evaluate_search_volume(analysis_data.get("search_volume", 0))
            factors["search_volume"] = volume_score
            score += volume_score * self.factor_weights["search_volume"]
            
            # Trend direction (0-100)
            trend_score = self._evaluate_trend_direction(analysis_data.get("trend_direction", "stable"))
            factors["trend_direction"] = trend_score
            score += trend_score * self.factor_weights["trend_direction"]
            
            return round(score, 1)
            
        except Exception as e:
            logger.warning(f"Error calculating competitive score: {str(e)}")
            return 0.0
    
    def _evaluate_title_optimization(self, title: str) -> float:
        """Evaluate title optimization (0-100)"""
        if not title:
            return 0.0
        
        score = 0.0
        
        # Length optimization (30-60 characters is optimal)
        title_length = len(title)
        if 30 <= title_length <= 60:
            score += 40
        elif 20 <= title_length <= 70:
            score += 30
        elif 10 <= title_length <= 80:
            score += 20
        else:
            score += 10
        
        # Keyword presence
        if title.lower().count(" ") >= 1:  # Has multiple words
            score += 30
        else:
            score += 10
        
        # Brand presence
        if any(brand in title.lower() for brand in ["brand", "company", "inc", "llc", "corp"]):
            score += 20
        else:
            score += 10
        
        # Special characters (avoid excessive use)
        special_chars = sum(1 for c in title if not c.isalnum() and c != ' ')
        if special_chars <= 2:
            score += 20
        elif special_chars <= 4:
            score += 10
        else:
            score += 5
        
        return min(100.0, score)
    
    def _evaluate_meta_description(self, meta_desc: str) -> float:
        """Evaluate meta description (0-100)"""
        if not meta_desc:
            return 0.0
        
        score = 0.0
        
        # Length optimization (150-160 characters is optimal)
        desc_length = len(meta_desc)
        if 150 <= desc_length <= 160:
            score += 40
        elif 120 <= desc_length <= 180:
            score += 30
        elif 100 <= desc_length <= 200:
            score += 20
        else:
            score += 10
        
        # Call to action presence
        cta_words = ["learn", "discover", "find", "get", "buy", "download", "sign up", "start"]
        if any(cta in meta_desc.lower() for cta in cta_words):
            score += 30
        else:
            score += 15
        
        # Keyword presence
        if meta_desc.count(" ") >= 10:  # Has substantial content
            score += 30
        else:
            score += 15
        
        return min(100.0, score)
    
    def _evaluate_heading_structure(self, headings: List[dict]) -> float:
        """Evaluate heading structure (0-100)"""
        if not headings:
            return 0.0
        
        score = 0.0
        
        # H1 presence (should have exactly one)
        h1_count = sum(1 for h in headings if h.get("level") == 1)
        if h1_count == 1:
            score += 30
        elif h1_count == 0:
            score += 10
        else:
            score += 5
        
        # Hierarchical structure
        levels = [h.get("level", 0) for h in headings]
        if levels and max(levels) <= 6:  # Don't go deeper than H6
            score += 20
        else:
            score += 10
        
        # Proper nesting (H1 -> H2 -> H3, etc.)
        if len(headings) >= 2:
            score += 25
        elif len(headings) >= 1:
            score += 15
        else:
            score += 5
        
        # Heading content quality
        content_score = 0
        for heading in headings:
            text = heading.get("text", "")
            if len(text) >= 3 and len(text) <= 70:
                content_score += 5
        
        score += min(25, content_score)
        
        return min(100.0, score)
    
    def _evaluate_keyword_density(self, content: str, target_keyword: str) -> float:
        """Evaluate keyword density (0-100)"""
        if not content or not target_keyword:
            return 50.0  # Neutral score for missing data
        
        # Calculate keyword density
        content_lower = content.lower()
        keyword_lower = target_keyword.lower()
        
        word_count = len(content.split())
        keyword_count = content_lower.count(keyword_lower)
        
        if word_count == 0:
            return 0.0
        
        density = (keyword_count / word_count) * 100
        
        # Optimal density is typically 1-3%
        if 1.0 <= density <= 3.0:
            return 100.0
        elif 0.5 <= density <= 4.0:
            return 80.0
        elif 0.1 <= density <= 5.0:
            return 60.0
        elif density < 0.1:
            return 30.0
        else:
            return 20.0  # Over-optimization penalty
    
    def _evaluate_internal_linking(self, internal_links: List[dict]) -> float:
        """Evaluate internal linking (0-100)"""
        if not internal_links:
            return 20.0  # Low score for no internal links
        
        score = 0.0
        
        # Link count (more is generally better, but not excessive)
        link_count = len(internal_links)
        if 5 <= link_count <= 20:
            score += 40
        elif 2 <= link_count <= 30:
            score += 30
        elif link_count >= 1:
            score += 20
        else:
            score += 10
        
        # Anchor text quality
        anchor_score = 0
        for link in internal_links:
            anchor = link.get("anchor_text", "")
            if len(anchor) >= 3 and len(anchor) <= 50:
                anchor_score += 5
        
        score += min(30, anchor_score)
        
        # Link relevance (basic check)
        if link_count > 0:
            score += 30
        else:
            score += 15
        
        return min(100.0, score)
    
    def _evaluate_image_optimization(self, images: List[dict]) -> float:
        """Evaluate image optimization (0-100)"""
        if not images:
            return 50.0  # Neutral score for no images
        
        score = 0.0
        
        # Alt text coverage
        alt_text_count = sum(1 for img in images if img.get("alt_text"))
        alt_coverage = alt_text_count / len(images) if images else 0
        
        if alt_coverage >= 0.9:
            score += 40
        elif alt_coverage >= 0.7:
            score += 30
        elif alt_coverage >= 0.5:
            score += 20
        else:
            score += 10
        
        # Image count (reasonable amount)
        image_count = len(images)
        if 1 <= image_count <= 10:
            score += 30
        elif image_count <= 20:
            score += 20
        else:
            score += 10
        
        # File size optimization (basic check)
        optimized_count = sum(1 for img in images if img.get("file_size", 0) < 500000)  # 500KB
        if image_count > 0:
            optimization_ratio = optimized_count / image_count
            if optimization_ratio >= 0.8:
                score += 30
            elif optimization_ratio >= 0.6:
                score += 20
            else:
                score += 10
        
        return min(100.0, score)
    
    def _evaluate_page_speed(self, speed_data: dict) -> float:
        """Evaluate page speed (0-100)"""
        if not speed_data:
            return 50.0  # Neutral score for missing data
        
        score = 0.0
        
        # Load time evaluation
        load_time = speed_data.get("load_time", 0)
        if load_time <= 2.0:
            score += 50
        elif load_time <= 4.0:
            score += 40
        elif load_time <= 6.0:
            score += 30
        elif load_time <= 8.0:
            score += 20
        else:
            score += 10
        
        # Core Web Vitals (if available)
        if "core_web_vitals" in speed_data:
            vitals = speed_data["core_web_vitals"]
            
            # LCP (Largest Contentful Paint)
            lcp = vitals.get("lcp", 0)
            if lcp <= 2.5:
                score += 25
            elif lcp <= 4.0:
                score += 20
            elif lcp <= 6.0:
                score += 15
            else:
                score += 10
            
            # FID (First Input Delay)
            fid = vitals.get("fid", 0)
            if fid <= 100:
                score += 25
            elif fid <= 300:
                score += 20
            else:
                score += 15
        
        return min(100.0, score)
    
    def _evaluate_mobile_friendliness(self, mobile_data: dict) -> float:
        """Evaluate mobile friendliness (0-100)"""
        if not mobile_data:
            return 50.0  # Neutral score for missing data
        
        score = 0.0
        
        # Responsive design
        if mobile_data.get("responsive", False):
            score += 40
        else:
            score += 10
        
        # Touch-friendly elements
        if mobile_data.get("touch_friendly", False):
            score += 30
        else:
            score += 15
        
        # Mobile-optimized content
        if mobile_data.get("mobile_optimized", False):
            score += 30
        else:
            score += 15
        
        return min(100.0, score)
    
    def _evaluate_ssl_security(self, url: str) -> float:
        """Evaluate SSL security (0-100)"""
        if not url:
            return 0.0
        
        if url.startswith("https://"):
            return 100.0
        elif url.startswith("http://"):
            return 0.0
        else:
            return 50.0  # Neutral for relative URLs
    
    def _evaluate_url_structure(self, url: str) -> float:
        """Evaluate URL structure (0-100)"""
        if not url:
            return 0.0
        
        score = 0.0
        
        # URL length
        url_length = len(url)
        if url_length <= 100:
            score += 30
        elif url_length <= 150:
            score += 20
        elif url_length <= 200:
            score += 10
        else:
            score += 5
        
        # Clean URL structure
        if "?" not in url and "#" not in url:
            score += 30
        elif "?" not in url:
            score += 20
        else:
            score += 10
        
        # Descriptive URL
        if url.count("/") <= 4:
            score += 20
        elif url.count("/") <= 6:
            score += 15
        else:
            score += 10
        
        # No excessive parameters
        if url.count("&") <= 2:
            score += 20
        elif url.count("&") <= 4:
            score += 15
        else:
            score += 10
        
        return min(100.0, score)
    
    def _evaluate_content_length(self, content: str) -> float:
        """Evaluate content length (0-100)"""
        if not content:
            return 0.0
        
        word_count = len(content.split())
        
        # Optimal content length varies by content type
        # For general content, 1000-2000 words is good
        if 1000 <= word_count <= 2000:
            return 100.0
        elif 500 <= word_count <= 3000:
            return 80.0
        elif 200 <= word_count <= 5000:
            return 60.0
        elif word_count >= 100:
            return 40.0
        else:
            return 20.0
    
    def _evaluate_content_quality(self, content: str) -> float:
        """Evaluate content quality (0-100)"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Content structure
        paragraphs = content.count("\n\n") + 1
        if paragraphs >= 5:
            score += 25
        elif paragraphs >= 3:
            score += 20
        elif paragraphs >= 1:
            score += 15
        else:
            score += 10
        
        # Sentence variety
        sentences = content.split(".")
        if len(sentences) >= 10:
            score += 25
        elif len(sentences) >= 5:
            score += 20
        elif len(sentences) >= 2:
            score += 15
        else:
            score += 10
        
        # Content uniqueness (basic check)
        unique_words = len(set(content.lower().split()))
        total_words = len(content.split())
        if total_words > 0:
            uniqueness_ratio = unique_words / total_words
            if uniqueness_ratio >= 0.7:
                score += 25
            elif uniqueness_ratio >= 0.5:
                score += 20
            else:
                score += 15
        
        # Readability indicators
        if any(word in content.lower() for word in ["because", "however", "therefore", "furthermore"]):
            score += 25
        else:
            score += 15
        
        return min(100.0, score)
    
    def _evaluate_readability(self, content: str) -> float:
        """Evaluate content readability (0-100)"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Average sentence length
        sentences = content.split(".")
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
            
            if avg_sentence_length <= 15:
                score += 40
            elif avg_sentence_length <= 20:
                score += 30
            elif avg_sentence_length <= 25:
                score += 20
            else:
                score += 10
        
        # Average word length
        words = content.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            
            if avg_word_length <= 5:
                score += 30
            elif avg_word_length <= 6:
                score += 25
            elif avg_word_length <= 7:
                score += 20
            else:
                score += 15
        
        # Paragraph length
        paragraphs = content.split("\n\n")
        if paragraphs:
            avg_paragraph_length = sum(len(p.split()) for p in paragraphs if p.strip()) / len([p for p in paragraphs if p.strip()])
            
            if avg_paragraph_length <= 50:
                score += 30
            elif avg_paragraph_length <= 100:
                score += 25
            elif avg_paragraph_length <= 150:
                score += 20
            else:
                score += 15
        
        return min(100.0, score)
    
    def _evaluate_content_freshness(self, last_updated: str) -> float:
        """Evaluate content freshness (0-100)"""
        if not last_updated:
            return 50.0  # Neutral score for missing data
        
        try:
            from datetime import datetime
            update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            current_date = datetime.now()
            
            days_old = (current_date - update_date).days
            
            if days_old <= 30:
                return 100.0
            elif days_old <= 90:
                return 80.0
            elif days_old <= 180:
                return 60.0
            elif days_old <= 365:
                return 40.0
            else:
                return 20.0
                
        except Exception:
            return 50.0  # Neutral score for parsing errors
    
    def _evaluate_engagement_signals(self, engagement_data: dict) -> float:
        """Evaluate engagement signals (0-100)"""
        if not engagement_data:
            return 50.0  # Neutral score for missing data
        
        score = 0.0
        
        # Social shares
        shares = engagement_data.get("social_shares", 0)
        if shares >= 100:
            score += 35
        elif shares >= 50:
            score += 25
        elif shares >= 10:
            score += 20
        elif shares >= 1:
            score += 15
        else:
            score += 10
        
        # Comments
        comments = engagement_data.get("comments", 0)
        if comments >= 20:
            score += 35
        elif comments >= 10:
            score += 25
        elif comments >= 5:
            score += 20
        elif comments >= 1:
            score += 15
        else:
            score += 10
        
        # Time on page
        time_on_page = engagement_data.get("time_on_page", 0)
        if time_on_page >= 300:  # 5 minutes
            score += 30
        elif time_on_page >= 180:  # 3 minutes
            score += 25
        elif time_on_page >= 60:  # 1 minute
            score += 20
        elif time_on_page >= 30:  # 30 seconds
            score += 15
        else:
            score += 10
        
        return min(100.0, score)
    
    def _evaluate_navigation(self, navigation_data: dict) -> float:
        """Evaluate navigation (0-100)"""
        if not navigation_data:
            return 50.0  # Neutral score for missing data
        
        score = 0.0
        
        # Breadcrumb navigation
        if navigation_data.get("breadcrumbs", False):
            score += 35
        else:
            score += 15
        
        # Site search
        if navigation_data.get("site_search", False):
            score += 35
        else:
            score += 15
        
        # Menu structure
        menu_items = navigation_data.get("menu_items", 0)
        if 5 <= menu_items <= 15:
            score += 30
        elif 3 <= menu_items <= 20:
            score += 25
        elif menu_items >= 1:
            score += 20
        else:
            score += 10
        
        return min(100.0, score)
    
    def _evaluate_accessibility(self, accessibility_data: dict) -> float:
        """Evaluate accessibility (0-100)"""
        if not accessibility_data:
            return 50.0  # Neutral score for missing data
        
        score = 0.0
        
        # ARIA labels
        if accessibility_data.get("aria_labels", False):
            score += 35
        else:
            score += 15
        
        # Keyboard navigation
        if accessibility_data.get("keyboard_navigation", False):
            score += 35
        else:
            score += 15
        
        # Color contrast
        if accessibility_data.get("color_contrast", False):
            score += 30
        else:
            score += 15
        
        return min(100.0, score)
    
    def _evaluate_keyword_difficulty(self, difficulty: int) -> float:
        """Evaluate keyword difficulty (0-100)"""
        if difficulty is None:
            return 50.0  # Neutral score for missing data
        
        # Lower difficulty is better for ranking
        if difficulty <= 20:
            return 100.0
        elif difficulty <= 40:
            return 80.0
        elif difficulty <= 60:
            return 60.0
        elif difficulty <= 80:
            return 40.0
        else:
            return 20.0
    
    def _evaluate_competition_level(self, competition_data: dict) -> float:
        """Evaluate competition level (0-100)"""
        if not competition_data:
            return 50.0  # Neutral score for missing data
        
        # Lower competition is better for ranking
        competition_score = competition_data.get("competition_level", "moderate")
        
        if competition_score == "low":
            return 100.0
        elif competition_score == "moderate":
            return 70.0
        elif competition_score == "high":
            return 40.0
        else:
            return 50.0
    
    def _evaluate_search_volume(self, volume: int) -> float:
        """Evaluate search volume (0-100)"""
        if volume is None or volume == 0:
            return 50.0  # Neutral score for missing data
        
        # Higher volume is generally better
        if volume >= 10000:
            return 100.0
        elif volume >= 5000:
            return 90.0
        elif volume >= 1000:
            return 80.0
        elif volume >= 500:
            return 70.0
        elif volume >= 100:
            return 60.0
        else:
            return 50.0
    
    def _evaluate_trend_direction(self, trend: str) -> float:
        """Evaluate trend direction (0-100)"""
        if not trend:
            return 50.0  # Neutral score for missing data
        
        if trend == "growing":
            return 100.0
        elif trend == "stable":
            return 70.0
        elif trend == "declining":
            return 30.0
        else:
            return 50.0
    
    def _generate_score_breakdown(self, scores: dict) -> dict:
        """Generate detailed score breakdown"""
        try:
            breakdown = {
                "category_breakdown": {},
                "strengths": [],
                "weaknesses": [],
                "improvement_areas": []
            }
            
            for category, score in scores.items():
                breakdown["category_breakdown"][category] = {
                    "score": score,
                    "grade": self._get_score_grade(score),
                    "weight": self.score_weights[category],
                    "weighted_score": score * self.score_weights[category]
                }
                
                # Identify strengths and weaknesses
                if score >= 80:
                    breakdown["strengths"].append(f"{category.replace('_', ' ').title()}: {score}/100")
                elif score <= 40:
                    breakdown["weaknesses"].append(f"{category.replace('_', ' ').title()}: {score}/100")
                else:
                    breakdown["improvement_areas"].append(f"{category.replace('_', ' ').title()}: {score}/100")
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error generating score breakdown: {str(e)}")
            return {"error": str(e)}
    
    def _generate_score_recommendations(self, scores: dict, analysis_data: dict) -> List[str]:
        """Generate actionable recommendations based on scores"""
        try:
            recommendations = []
            
            # On-page recommendations
            if scores.get("on_page", 0) < 70:
                recommendations.append("Optimize title tags and meta descriptions for better click-through rates")
                recommendations.append("Improve heading structure with proper H1-H6 hierarchy")
                recommendations.append("Optimize keyword density and internal linking strategy")
            
            # Technical recommendations
            if scores.get("technical", 0) < 70:
                recommendations.append("Improve page loading speed and Core Web Vitals")
                recommendations.append("Ensure mobile-friendliness and responsive design")
                recommendations.append("Implement SSL certificate and secure URL structure")
            
            # Content recommendations
            if scores.get("content", 0) < 70:
                recommendations.append("Increase content length and improve content quality")
                recommendations.append("Enhance readability with better sentence structure")
                recommendations.append("Update content regularly to maintain freshness")
            
            # UX recommendations
            if scores.get("user_experience", 0) < 70:
                recommendations.append("Improve user engagement and time on page")
                recommendations.append("Enhance navigation and site search functionality")
                recommendations.append("Implement accessibility features and ARIA labels")
            
            # Competitive recommendations
            if scores.get("competitive", 0) < 70:
                recommendations.append("Target lower-competition keywords for better ranking potential")
                recommendations.append("Focus on trending and growing search terms")
                recommendations.append("Improve competitive positioning through content gaps")
            
            # General recommendations
            if len(recommendations) < 3:
                recommendations.append("Maintain current optimization levels and monitor performance")
                recommendations.append("Focus on user experience and content quality improvements")
                recommendations.append("Track competitor performance and identify new opportunities")
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Focus on improving overall SEO performance"]
    
    def _identify_priority_actions(self, scores: dict) -> List[dict]:
        """Identify priority actions based on scores"""
        try:
            priorities = []
            
            # Sort categories by score (lowest first)
            sorted_categories = sorted(scores.items(), key=lambda x: x[1])
            
            for i, (category, score) in enumerate(sorted_categories[:3]):  # Top 3 priorities
                priority = {
                    "category": category,
                    "current_score": score,
                    "priority_level": i + 1,
                    "target_score": min(100, score + 20),  # Aim for 20-point improvement
                    "effort_required": self._estimate_effort_required(category, score),
                    "impact_potential": self._estimate_impact_potential(category)
                }
                priorities.append(priority)
            
            return priorities
            
        except Exception as e:
            logger.error(f"Error identifying priority actions: {str(e)}")
            return []
    
    def _estimate_effort_required(self, category: str, current_score: float) -> str:
        """Estimate effort required for improvement"""
        if current_score >= 80:
            return "low"
        elif current_score >= 60:
            return "medium"
        elif current_score >= 40:
            return "high"
        else:
            return "very_high"
    
    def _estimate_impact_potential(self, category: str) -> str:
        """Estimate potential impact of improvements"""
        impact_map = {
            "on_page": "high",
            "technical": "high",
            "content": "high",
            "user_experience": "medium",
            "competitive": "medium"
        }
        return impact_map.get(category, "medium")
    
    def _calculate_improvement_potential(self, scores: dict) -> dict:
        """Calculate improvement potential for each category"""
        try:
            improvement = {}
            
            for category, score in scores.items():
                current_score = score
                max_possible = 100
                improvement_potential = max_possible - current_score
                improvement_percentage = (improvement_potential / max_possible) * 100
                
                improvement[category] = {
                    "current_score": current_score,
                    "improvement_potential": round(improvement_potential, 1),
                    "improvement_percentage": round(improvement_percentage, 1),
                    "priority": "high" if improvement_percentage >= 40 else "medium" if improvement_percentage >= 20 else "low"
                }
            
            return improvement
            
        except Exception as e:
            logger.error(f"Error calculating improvement potential: {str(e)}")
            return {}
    
    def _generate_benchmark_comparison(self, overall_score: float) -> dict:
        """Generate benchmark comparison data"""
        try:
            benchmarks = {
                "excellent": 90,
                "good": 80,
                "average": 70,
                "below_average": 60,
                "poor": 50
            }
            
            # Find benchmark category
            benchmark_category = "poor"
            for category, threshold in benchmarks.items():
                if overall_score >= threshold:
                    benchmark_category = category
                    break
            
            # Calculate distance to next benchmark
            next_benchmark = None
            for category, threshold in sorted(benchmarks.items(), key=lambda x: x[1]):
                if threshold > overall_score:
                    next_benchmark = {"category": category, "score": threshold, "points_needed": threshold - overall_score}
                    break
            
            return {
                "current_benchmark": benchmark_category,
                "next_benchmark": next_benchmark,
                "industry_average": 65,  # Example industry average
                "competitor_range": "60-80"  # Example competitor range
            }
            
        except Exception as e:
            logger.error(f"Error generating benchmark comparison: {str(e)}")
            return {"error": str(e)}
    
    def _get_score_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 45:
            return "D+"
        elif score >= 40:
            return "D"
        else:
            return "F"


class SEOCacheManager:
    """
    Comprehensive caching system for SEO service with intelligent cache management
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
        
        # Cache configuration
        self.default_ttl = self.config.get("default_ttl", 3600)  # 1 hour
        self.max_cache_size = self.config.get("max_cache_size", 1000)  # Max items
        self.max_memory_mb = self.config.get("max_memory_mb", 100)  # Max memory usage
        self.cleanup_interval = self.config.get("cleanup_interval", 300)  # 5 minutes
        self.last_cleanup = time.time()
        
        # Cache policies
        self.eviction_policy = self.config.get("eviction_policy", "lru")  # lru, lfu, fifo
        self.compression_enabled = self.config.get("compression_enabled", True)
        self.persistent_storage = self.config.get("persistent_storage", False)
        
        # Initialize cache storage
        self._initialize_cache_storage()
    
    def _initialize_cache_storage(self):
        """Initialize cache storage based on configuration"""
        try:
            if self.persistent_storage:
                # Initialize persistent storage (file-based for now)
                self.storage_file = self.config.get("storage_file", "seo_cache.json")
                self._load_persistent_cache()
            else:
                self.storage_file = None
                
        except Exception as e:
            logger.warning(f"Could not initialize persistent storage: {str(e)}")
            self.persistent_storage = False
    
    def get(self, key: str, default=None):
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            if key not in self.cache:
                self.cache_stats["misses"] += 1
                return default
            
            cache_entry = self.cache[key]
            
            # Check if expired
            if self._is_expired(cache_entry):
                self.delete(key)
                self.cache_stats["misses"] += 1
                return default
            
            # Update access time for LRU
            if self.eviction_policy == "lru":
                cache_entry["last_accessed"] = time.time()
            
            # Update access count for LFU
            if self.eviction_policy == "lfu":
                cache_entry["access_count"] += 1
            
            self.cache_stats["hits"] += 1
            return cache_entry["value"]
            
        except Exception as e:
            logger.warning(f"Error getting from cache: {str(e)}")
            return default
    
    def set(self, key: str, value, ttl: int = None, tags: List[str] = None):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Optional tags for cache invalidation
        """
        try:
            # Check cache size limit
            if len(self.cache) >= self.max_cache_size:
                self._evict_entries()
            
            # Check memory limit
            if self._get_cache_memory_usage() > self.max_memory_mb:
                self._evict_entries()
            
            # Create cache entry
            cache_entry = {
                "value": value,
                "created_at": time.time(),
                "expires_at": time.time() + (ttl or self.default_ttl),
                "last_accessed": time.time(),
                "access_count": 1,
                "size": self._estimate_value_size(value),
                "tags": tags or []
            }
            
            self.cache[key] = cache_entry
            self.cache_stats["sets"] += 1
            
            # Periodic cleanup
            if time.time() - self.last_cleanup > self.cleanup_interval:
                self._cleanup_expired_entries()
            
        except Exception as e:
            logger.warning(f"Error setting cache: {str(e)}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                self.cache_stats["deletes"] += 1
                return True
            return False
            
        except Exception as e:
            logger.warning(f"Error deleting from cache: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if key not in self.cache:
                return False
            
            if self._is_expired(self.cache[key]):
                self.delete(key)
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking cache existence: {str(e)}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds"""
        try:
            if key not in self.cache:
                return -1
            
            cache_entry = self.cache[key]
            if self._is_expired(cache_entry):
                return -1
            
            return max(0, int(cache_entry["expires_at"] - time.time()))
            
        except Exception as e:
            logger.warning(f"Error getting TTL: {str(e)}")
            return -1
    
    def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for an existing key"""
        try:
            if key not in self.cache:
                return False
            
            self.cache[key]["expires_at"] = time.time() + ttl
            return True
            
        except Exception as e:
            logger.warning(f"Error setting TTL: {str(e)}")
            return False
    
    def get_multiple(self, keys: List[str]) -> dict:
        """Get multiple values from cache"""
        try:
            result = {}
            for key in keys:
                value = self.get(key)
                if value is not None:
                    result[key] = value
            return result
            
        except Exception as e:
            logger.warning(f"Error getting multiple from cache: {str(e)}")
            return {}
    
    def set_multiple(self, data: dict, ttl: int = None, tags: List[str] = None):
        """Set multiple values in cache"""
        try:
            for key, value in data.items():
                self.set(key, value, ttl, tags)
                
        except Exception as e:
            logger.warning(f"Error setting multiple in cache: {str(e)}")
    
    def delete_multiple(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        try:
            deleted_count = 0
            for key in keys:
                if self.delete(key):
                    deleted_count += 1
            return deleted_count
            
        except Exception as e:
            logger.warning(f"Error deleting multiple from cache: {str(e)}")
            return 0
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags"""
        try:
            invalidated_count = 0
            keys_to_delete = []
            
            for key, entry in self.cache.items():
                if any(tag in entry.get("tags", []) for tag in tags):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                if self.delete(key):
                    invalidated_count += 1
            
            return invalidated_count
            
        except Exception as e:
            logger.warning(f"Error invalidating by tags: {str(e)}")
            return 0
    
    def clear(self):
        """Clear all cache entries"""
        try:
            self.cache.clear()
            self.cache_stats["deletes"] += len(self.cache)
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            current_memory = self._get_cache_memory_usage()
            hit_rate = 0
            
            if self.cache_stats["hits"] + self.cache_stats["misses"] > 0:
                hit_rate = self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"])
            
            return {
                "cache_size": len(self.cache),
                "memory_usage_mb": round(current_memory, 2),
                "max_cache_size": self.max_cache_size,
                "max_memory_mb": self.max_memory_mb,
                "hit_rate": round(hit_rate, 3),
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "sets": self.cache_stats["sets"],
                "deletes": self.cache_stats["deletes"],
                "evictions": self.cache_stats["evictions"],
                "eviction_policy": self.eviction_policy,
                "compression_enabled": self.compression_enabled,
                "persistent_storage": self.persistent_storage
            }
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {str(e)}")
            return {}
    
    def get_keys(self, pattern: str = None) -> List[str]:
        """Get cache keys, optionally filtered by pattern"""
        try:
            if not pattern:
                return list(self.cache.keys())
            
            import re
            regex = re.compile(pattern.replace("*", ".*"))
            return [key for key in self.cache.keys() if regex.match(key)]
            
        except Exception as e:
            logger.warning(f"Error getting cache keys: {str(e)}")
            return []
    
    def get_memory_usage(self) -> float:
        """Get current cache memory usage in MB"""
        try:
            return self._get_cache_memory_usage()
            
        except Exception as e:
            logger.warning(f"Error getting memory usage: {str(e)}")
            return 0.0
    
    def optimize(self):
        """Optimize cache performance"""
        try:
            # Clean up expired entries
            self._cleanup_expired_entries()
            
            # Evict if needed
            if len(self.cache) > self.max_cache_size * 0.9:
                self._evict_entries()
            
            # Compress if enabled
            if self.compression_enabled:
                self._compress_cache()
            
            # Save to persistent storage if enabled
            if self.persistent_storage:
                self._save_persistent_cache()
                
        except Exception as e:
            logger.warning(f"Error optimizing cache: {str(e)}")
    
    def _is_expired(self, cache_entry: dict) -> bool:
        """Check if cache entry is expired"""
        return time.time() > cache_entry["expires_at"]
    
    def _estimate_value_size(self, value) -> int:
        """Estimate memory size of a value in bytes"""
        try:
            import sys
            return sys.getsizeof(value)
        except:
            return 100  # Default estimate
    
    def _get_cache_memory_usage(self) -> float:
        """Calculate total cache memory usage in MB"""
        try:
            total_bytes = sum(entry.get("size", 100) for entry in self.cache.values())
            return total_bytes / (1024 * 1024)  # Convert to MB
        except:
            return 0.0
    
    def _evict_entries(self):
        """Evict cache entries based on policy"""
        try:
            if not self.cache:
                return
            
            # Determine which entries to evict
            if self.eviction_policy == "lru":
                # Least Recently Used
                entries_to_evict = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]["last_accessed"]
                )
            elif self.eviction_policy == "lfu":
                # Least Frequently Used
                entries_to_evict = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]["access_count"]
                )
            else:
                # FIFO (First In, First Out)
                entries_to_evict = sorted(
                    self.cache.items(),
                    key=lambda x: x[1]["created_at"]
                )
            
            # Evict 20% of entries
            evict_count = max(1, len(entries_to_evict) // 5)
            
            for i in range(evict_count):
                if i < len(entries_to_evict):
                    key = entries_to_evict[i][0]
                    self.delete(key)
                    self.cache_stats["evictions"] += 1
                    
        except Exception as e:
            logger.warning(f"Error evicting cache entries: {str(e)}")
    
    def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        try:
            expired_keys = [
                key for key, entry in self.cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                self.delete(key)
            
            self.last_cleanup = time.time()
            
        except Exception as e:
            logger.warning(f"Error cleaning up expired entries: {str(e)}")
    
    def _compress_cache(self):
        """Compress cache entries to save memory"""
        try:
            if not self.compression_enabled:
                return
            
            # Simple compression: remove unnecessary metadata for old entries
            current_time = time.time()
            
            for key, entry in self.cache.items():
                # Remove detailed metadata for entries older than 1 hour
                if current_time - entry["created_at"] > 3600:
                    if "access_count" in entry and entry["access_count"] > 1:
                        entry["access_count"] = 1  # Reset to save memory
                    
                    # Remove tags for old entries
                    if "tags" in entry and len(entry["tags"]) > 0:
                        entry["tags"] = []
                        
        except Exception as e:
            logger.warning(f"Error compressing cache: {str(e)}")
    
    def _save_persistent_cache(self):
        """Save cache to persistent storage"""
        try:
            if not self.persistent_storage or not self.storage_file:
                return
            
            # Save essential cache data
            cache_data = {
                "timestamp": time.time(),
                "entries": {}
            }
            
            for key, entry in self.cache.items():
                if not self._is_expired(entry):
                    cache_data["entries"][key] = {
                        "value": entry["value"],
                        "expires_at": entry["expires_at"],
                        "tags": entry["tags"]
                    }
            
            import json
            with open(self.storage_file, 'w') as f:
                json.dump(cache_data, f, default=str)
                
        except Exception as e:
            logger.warning(f"Error saving persistent cache: {str(e)}")
    
    def _load_persistent_cache(self):
        """Load cache from persistent storage"""
        try:
            if not self.persistent_storage or not self.storage_file:
                return
            
            import json
            import os
            
            if not os.path.exists(self.storage_file):
                return
            
            with open(self.storage_file, 'r') as f:
                cache_data = json.load(f)
            
            # Load entries, checking expiration
            current_time = time.time()
            for key, entry_data in cache_data.get("entries", {}).items():
                if entry_data["expires_at"] > current_time:
                    self.set(
                        key,
                        entry_data["value"],
                        int(entry_data["expires_at"] - current_time),
                        entry_data.get("tags", [])
                    )
                    
        except Exception as e:
            logger.warning(f"Error loading persistent cache: {str(e)}")