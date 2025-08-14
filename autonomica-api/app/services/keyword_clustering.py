"""
Keyword Clustering Algorithm for SEO Research and Content Strategy.

This module provides advanced keyword clustering capabilities:
- Semantic similarity using OpenAI embeddings
- Hierarchical clustering algorithms
- Intent-based grouping
- Topic modeling and clustering
- Keyword opportunity scoring
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import time

from loguru import logger

# Try to import required libraries, provide fallbacks if not available
try:
    from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation, NMF
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Some clustering methods will be disabled.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Embedding generation will be disabled.")


@dataclass
class KeywordCluster:
    """Represents a cluster of related keywords."""
    cluster_id: str
    name: str
    keywords: List[str]
    centroid: Optional[List[float]] = None
    intent: Optional[str] = None
    topic: Optional[str] = None
    volume_sum: int = 0
    avg_difficulty: float = 0.0
    avg_cpc: float = 0.0
    opportunity_score: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class KeywordData:
    """Enhanced keyword data for clustering."""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
    keyword_difficulty: Optional[int] = None
    intent: Optional[str] = None
    topic: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class KeywordClusteringEngine:
    """
    Advanced keyword clustering engine with multiple algorithms.
    
    Features:
    - Semantic similarity clustering using embeddings
    - Hierarchical clustering with customizable distance metrics
    - Intent-based grouping
    - Topic modeling and LDA clustering
    - Keyword opportunity scoring
    - Caching and optimization
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 embedding_model: str = "text-embedding-ada-002",
                 cache_enabled: bool = True):
        """
        Initialize the clustering engine.
        
        Args:
            openai_api_key: OpenAI API key for embeddings
            embedding_model: OpenAI embedding model to use
            cache_enabled: Enable embedding caching
        """
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.cache_enabled = cache_enabled
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE and openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Embedding cache
        self.embedding_cache = {}
        
        # Clustering parameters
        self.default_similarity_threshold = 0.85
        self.default_min_cluster_size = 2
        self.default_max_clusters = 50
        
        # Intent patterns for classification
        self.intent_patterns = {
            "informational": [
                "what", "how", "why", "when", "where", "guide", "tutorial", "learn",
                "tips", "examples", "definition", "meaning", "explanation"
            ],
            "navigational": [
                "login", "sign in", "account", "dashboard", "homepage", "contact",
                "about", "support", "help", "faq"
            ],
            "commercial": [
                "buy", "purchase", "order", "shop", "store", "price", "cost",
                "discount", "deal", "offer", "sale", "best", "top", "review"
            ],
            "transactional": [
                "download", "install", "sign up", "register", "subscribe",
                "book", "reserve", "schedule", "appointment"
            ]
        }
        
        logger.info("Keyword clustering engine initialized")
    
    async def generate_embeddings(self, keywords: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Generate embeddings for a list of keywords.
        
        Args:
            keywords: List of keywords to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available. Please provide an API key.")
        
        embeddings = []
        uncached_keywords = []
        uncached_indices = []
        
        # Check cache first
        if use_cache and self.cache_enabled:
            for i, keyword in enumerate(keywords):
                cache_key = self._get_cache_key(keyword)
                if cache_key in self.embedding_cache:
                    embeddings.append(self.embedding_cache[cache_key])
                else:
                    uncached_keywords.append(keyword)
                    uncached_indices.append(i)
        else:
            uncached_keywords = keywords
            uncached_indices = list(range(len(keywords)))
        
        # Generate embeddings for uncached keywords
        if uncached_keywords:
            try:
                logger.info(f"Generating embeddings for {len(uncached_keywords)} keywords")
                
                # Batch process keywords (OpenAI allows up to 2048 inputs per request)
                batch_size = 100
                all_batch_embeddings = []
                
                for i in range(0, len(uncached_keywords), batch_size):
                    batch = uncached_keywords[i:i + batch_size]
                    
                    response = await asyncio.to_thread(
                        self.openai_client.embeddings.create,
                        input=batch,
                        model=self.embedding_model
                    )
                    
                    batch_embeddings = [data.embedding for data in response.data]
                    all_batch_embeddings.extend(batch_embeddings)
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
                # Cache new embeddings
                if use_cache and self.cache_enabled:
                    for keyword, embedding in zip(uncached_keywords, all_batch_embeddings):
                        cache_key = self._get_cache_key(keyword)
                        self.embedding_cache[cache_key] = embedding
                
                # Insert embeddings at correct positions
                for i, embedding in zip(uncached_indices, all_batch_embeddings):
                    embeddings.insert(i, embedding)
                
                logger.info("Embedding generation completed successfully")
                
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
                raise
        
        return embeddings
    
    def _get_cache_key(self, keyword: str) -> str:
        """Generate cache key for a keyword."""
        return hashlib.md5(f"{keyword}_{self.embedding_model}".encode()).hexdigest()
    
    def classify_intent(self, keyword: str) -> str:
        """
        Classify keyword intent based on patterns.
        
        Args:
            keyword: Keyword to classify
            
        Returns:
            Intent classification (informational, navigational, commercial, transactional)
        """
        keyword_lower = keyword.lower()
        
        # Count matches for each intent type
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in keyword_lower)
            intent_scores[intent] = score
        
        # Return intent with highest score, default to informational
        if any(intent_scores.values()):
            return max(intent_scores, key=intent_scores.get)
        else:
            return "informational"
    
    def classify_topic(self, keywords: List[str]) -> str:
        """
        Classify topic based on keyword frequency analysis.
        
        Args:
            keywords: List of keywords in the cluster
            
        Returns:
            Topic classification
        """
        if not keywords:
            return "general"
        
        # Simple topic classification based on common words
        word_freq = {}
        for keyword in keywords:
            words = keyword.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return most common word as topic
        if word_freq:
            return max(word_freq, key=word_freq.get)
        else:
            return "general"
    
    async def cluster_by_similarity(self, 
                                  keywords: List[str], 
                                  similarity_threshold: float = None,
                                  min_cluster_size: int = None) -> List[KeywordCluster]:
        """
        Cluster keywords by semantic similarity.
        
        Args:
            keywords: List of keywords to cluster
            similarity_threshold: Minimum similarity for clustering
            min_cluster_size: Minimum size for a valid cluster
            
        Returns:
            List of KeywordCluster objects
        """
        similarity_threshold = similarity_threshold or self.default_similarity_threshold
        min_cluster_size = min_cluster_size or self.default_min_cluster_size
        
        if len(keywords) < 2:
            return [KeywordCluster(
                cluster_id="single",
                name="Single Keywords",
                keywords=keywords
            )]
        
        # Generate embeddings
        embeddings = await self.generate_embeddings(keywords)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Apply clustering algorithm
        clusters = self._apply_similarity_clustering(
            keywords, embeddings, similarity_matrix, similarity_threshold, min_cluster_size
        )
        
        return clusters
    
    def _apply_similarity_clustering(self, 
                                   keywords: List[str], 
                                   embeddings: List[List[float]], 
                                   similarity_matrix: np.ndarray,
                                   threshold: float,
                                   min_size: int) -> List[KeywordCluster]:
        """Apply similarity-based clustering algorithm."""
        clusters = []
        used_indices = set()
        
        # Find clusters based on similarity threshold
        for i in range(len(keywords)):
            if i in used_indices:
                continue
            
            # Find all keywords similar to this one
            similar_indices = [i]
            for j in range(i + 1, len(keywords)):
                if j not in used_indices and similarity_matrix[i][j] >= threshold:
                    similar_indices.append(j)
            
            # Create cluster if it meets minimum size
            if len(similar_indices) >= min_size:
                cluster_keywords = [keywords[idx] for idx in similar_indices]
                cluster_embeddings = [embeddings[idx] for idx in similar_indices]
                
                # Calculate centroid
                centroid = np.mean(cluster_embeddings, axis=0).tolist()
                
                # Classify intent and topic
                intent = self.classify_intent(cluster_keywords[0])
                topic = self.classify_topic(cluster_keywords)
                
                cluster = KeywordCluster(
                    cluster_id=f"cluster_{len(clusters)}",
                    name=f"{topic.title()} {intent.title()} Cluster",
                    keywords=cluster_keywords,
                    centroid=centroid,
                    intent=intent,
                    topic=topic
                )
                
                clusters.append(cluster)
                used_indices.update(similar_indices)
        
        # Handle remaining unclustered keywords
        remaining_indices = set(range(len(keywords))) - used_indices
        if remaining_indices:
            remaining_keywords = [keywords[idx] for idx in remaining_indices]
            remaining_cluster = KeywordCluster(
                cluster_id="unclustered",
                name="Unclustered Keywords",
                keywords=remaining_keywords
            )
            clusters.append(remaining_cluster)
        
        return clusters
    
    async def cluster_by_hierarchical(self, 
                                    keywords: List[str], 
                                    n_clusters: int = None,
                                    distance_threshold: float = None) -> List[KeywordCluster]:
        """
        Cluster keywords using hierarchical clustering.
        
        Args:
            keywords: List of keywords to cluster
            n_clusters: Number of clusters to create
            distance_threshold: Distance threshold for clustering
            
        Returns:
            List of KeywordCluster objects
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for hierarchical clustering")
        
        if len(keywords) < 2:
            return [KeywordCluster(
                cluster_id="single",
                name="Single Keywords",
                keywords=keywords
            )]
        
        # Generate embeddings
        embeddings = await self.generate_embeddings(keywords)
        
        # Apply hierarchical clustering
        if distance_threshold:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=distance_threshold,
                linkage='ward'
            )
        else:
            n_clusters = n_clusters or min(len(keywords) // 2, self.default_max_clusters)
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward'
            )
        
        cluster_labels = clustering.fit_predict(embeddings)
        
        # Create clusters from labels
        clusters = []
        unique_labels = set(cluster_labels)
        
        for label in unique_labels:
            cluster_indices = [i for i, l in enumerate(cluster_labels) if l == label]
            cluster_keywords = [keywords[i] for i in cluster_indices]
            cluster_embeddings = [embeddings[i] for i in cluster_indices]
            
            # Calculate centroid
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            
            # Classify intent and topic
            intent = self.classify_intent(cluster_keywords[0])
            topic = self.classify_topic(cluster_keywords)
            
            cluster = KeywordCluster(
                cluster_id=f"hierarchical_{label}",
                name=f"{topic.title()} {intent.title()} Cluster",
                keywords=cluster_keywords,
                centroid=centroid,
                intent=intent,
                topic=topic
            )
            
            clusters.append(cluster)
        
        return clusters
    
    async def cluster_by_topic_modeling(self, 
                                      keywords: List[str], 
                                      n_topics: int = None) -> List[KeywordCluster]:
        """
        Cluster keywords using topic modeling (LDA).
        
        Args:
            keywords: List of keywords to cluster
            n_topics: Number of topics to extract
            
        Returns:
            List of KeywordCluster objects
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for topic modeling")
        
        if len(keywords) < 2:
            return [KeywordCluster(
                cluster_id="single",
                name="Single Keywords",
                keywords=keywords
            )]
        
        # Prepare text for topic modeling
        n_topics = n_topics or min(len(keywords) // 3, 10)
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(keywords)
            
            # Apply LDA
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=100
            )
            
            topic_distributions = lda.fit_transform(tfidf_matrix)
            
            # Assign keywords to topics based on highest probability
            topic_assignments = np.argmax(topic_distributions, axis=1)
            
            # Create clusters from topic assignments
            clusters = []
            unique_topics = set(topic_assignments)
            
            for topic_id in unique_topics:
                topic_indices = [i for i, t in enumerate(topic_assignments) if t == topic_id]
                topic_keywords = [keywords[i] for i in topic_indices]
                
                # Get topic keywords from LDA model
                feature_names = vectorizer.get_feature_names_out()
                top_words = []
                top_word_indices = lda.components_[topic_id].argsort()[-5:][::-1]
                for idx in top_word_indices:
                    if idx < len(feature_names):
                        top_words.append(feature_names[idx])
                
                topic_name = " ".join(top_words[:3])
                
                cluster = KeywordCluster(
                    cluster_id=f"topic_{topic_id}",
                    name=f"Topic: {topic_name}",
                    keywords=topic_keywords,
                    topic=topic_name
                )
                
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.warning(f"Topic modeling failed, falling back to similarity clustering: {e}")
            return await self.cluster_by_similarity(keywords)
    
    def calculate_opportunity_score(self, 
                                  search_volume: int, 
                                  keyword_difficulty: int, 
                                  cpc: float,
                                  competition: float) -> float:
        """
        Calculate keyword opportunity score.
        
        Args:
            search_volume: Monthly search volume
            keyword_difficulty: Keyword difficulty (0-100)
            cpc: Cost per click
            competition: Competition level (0-1)
            
        Returns:
            Opportunity score (0-100)
        """
        # Normalize values
        volume_score = min(search_volume / 10000, 1.0) * 100  # Cap at 10k searches
        difficulty_score = (100 - keyword_difficulty) / 100 * 100  # Lower difficulty = higher score
        cpc_score = min(cpc / 5.0, 1.0) * 100  # Cap at $5 CPC
        competition_score = (1 - competition) * 100  # Lower competition = higher score
        
        # Weighted average
        weights = [0.3, 0.3, 0.2, 0.2]  # Volume, Difficulty, CPC, Competition
        opportunity_score = (
            volume_score * weights[0] +
            difficulty_score * weights[1] +
            cpc_score * weights[2] +
            competition_score * weights[3]
        )
        
        return round(opportunity_score, 2)
    
    def enhance_clusters_with_metrics(self, 
                                    clusters: List[KeywordCluster], 
                                    keyword_metrics: Dict[str, Dict[str, Any]]) -> List[KeywordCluster]:
        """
        Enhance clusters with keyword metrics and opportunity scores.
        
        Args:
            clusters: List of KeywordCluster objects
            keyword_metrics: Dictionary mapping keywords to their metrics
            
        Returns:
            Enhanced KeywordCluster objects
        """
        for cluster in clusters:
            cluster_metrics = {
                'volumes': [],
                'difficulties': [],
                'cpcs': [],
                'competitions': []
            }
            
            for keyword in cluster.keywords:
                if keyword in keyword_metrics:
                    metrics = keyword_metrics[keyword]
                    
                    if 'search_volume' in metrics:
                        cluster_metrics['volumes'].append(metrics['search_volume'])
                    if 'keyword_difficulty' in metrics:
                        cluster_metrics['difficulties'].append(metrics['keyword_difficulty'])
                    if 'cpc' in metrics:
                        cluster_metrics['cpcs'].append(metrics['cpc'])
                    if 'competition' in metrics:
                        cluster_metrics['competitions'].append(metrics['competition'])
            
            # Calculate averages
            if cluster_metrics['volumes']:
                cluster.volume_sum = sum(cluster_metrics['volumes'])
                cluster.avg_difficulty = np.mean(cluster_metrics['difficulties']) if cluster_metrics['difficulties'] else 0
                cluster.avg_cpc = np.mean(cluster_metrics['cpcs']) if cluster_metrics['cpcs'] else 0
                
                # Calculate opportunity score for the cluster
                avg_competition = np.mean(cluster_metrics['competitions']) if cluster_metrics['competitions'] else 0.5
                cluster.opportunity_score = self.calculate_opportunity_score(
                    cluster.volume_sum,
                    int(cluster.avg_difficulty),
                    cluster.avg_cpc,
                    avg_competition
                )
        
        return clusters
    
    def get_cluster_recommendations(self, 
                                  clusters: List[KeywordCluster], 
                                  max_recommendations: int = 10) -> List[KeywordCluster]:
        """
        Get top cluster recommendations based on opportunity score.
        
        Args:
            clusters: List of KeywordCluster objects
            max_recommendations: Maximum number of recommendations
            
        Returns:
            Top clusters sorted by opportunity score
        """
        # Filter clusters with metrics
        scored_clusters = [c for c in clusters if c.opportunity_score > 0]
        
        # Sort by opportunity score (descending)
        scored_clusters.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return scored_clusters[:max_recommendations]
    
    def export_clusters_to_json(self, clusters: List[KeywordCluster], filepath: str = None) -> str:
        """
        Export clusters to JSON format.
        
        Args:
            clusters: List of KeywordCluster objects
            filepath: Path to save JSON file (optional)
            
        Returns:
            JSON string or filepath
        """
        # Convert clusters to serializable format
        export_data = []
        for cluster in clusters:
            cluster_data = {
                'cluster_id': cluster.cluster_id,
                'name': cluster.name,
                'keywords': cluster.keywords,
                'intent': cluster.intent,
                'topic': cluster.topic,
                'volume_sum': cluster.volume_sum,
                'avg_difficulty': cluster.avg_difficulty,
                'avg_cpc': cluster.avg_cpc,
                'opportunity_score': cluster.opportunity_score,
                'created_at': cluster.created_at.isoformat() if cluster.created_at else None
            }
            export_data.append(cluster_data)
        
        json_string = json.dumps(export_data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_string)
            return filepath
        else:
            return json_string


# Example usage and testing
async def test_keyword_clustering():
    """Test the keyword clustering functionality."""
    # Sample keywords for testing
    sample_keywords = [
        "digital marketing strategies",
        "social media marketing tips",
        "content marketing guide",
        "email marketing best practices",
        "SEO optimization techniques",
        "PPC advertising strategies",
        "marketing automation tools",
        "lead generation methods",
        "customer acquisition strategies",
        "brand awareness campaigns"
    ]
    
    try:
        # Initialize clustering engine
        engine = KeywordClusteringEngine()
        
        print("Testing keyword clustering engine...")
        
        # Test intent classification
        print("\nIntent Classification:")
        for keyword in sample_keywords[:5]:
            intent = engine.classify_intent(keyword)
            print(f"  {keyword} -> {intent}")
        
        # Test topic classification
        print("\nTopic Classification:")
        topic = engine.classify_topic(sample_keywords)
        print(f"  Overall topic: {topic}")
        
        # Note: Full clustering test requires OpenAI API key
        print("\nNote: Full clustering test requires OpenAI API key")
        print("The clustering engine is ready for use!")
        
    except Exception as e:
        logger.error(f"Keyword clustering test failed: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_keyword_clustering())