"""
Keyword Clustering Algorithm Module
Implements semantic similarity and clustering algorithms for keyword analysis
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Configure logging
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK data: {e}")

class KeywordClusterer:
    """Advanced keyword clustering using semantic similarity and NLP techniques"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess_keyword(self, keyword: str) -> str:
        """Clean and normalize keyword text"""
        # Convert to lowercase
        keyword = keyword.lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        keyword = re.sub(r'[^\w\s-]', '', keyword)
        
        # Tokenize and lemmatize
        tokens = word_tokenize(keyword)
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        
        return ' '.join(tokens)
    
    def extract_keyword_features(self, keyword: str) -> Dict[str, Any]:
        """Extract linguistic features from keyword"""
        features = {
            'length': len(keyword),
            'word_count': len(keyword.split()),
            'has_numbers': bool(re.search(r'\d', keyword)),
            'has_brand': bool(re.search(r'\b(apple|google|microsoft|amazon|netflix)\b', keyword, re.IGNORECASE)),
            'is_question': keyword.strip().endswith('?'),
            'is_long_tail': len(keyword.split()) > 3,
            'has_location': bool(re.search(r'\b(usa|uk|canada|australia|new york|london|toronto)\b', keyword, re.IGNORECASE))
        }
        return features
    
    def calculate_semantic_similarity(self, keywords: List[str]) -> np.ndarray:
        """Calculate semantic similarity matrix using TF-IDF and cosine similarity"""
        try:
            # Preprocess keywords
            processed_keywords = [self.preprocess_keyword(kw) for kw in keywords]
            
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(processed_keywords)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            # Fallback to simple string similarity
            return self._fallback_similarity(keywords)
    
    def _fallback_similarity(self, keywords: List[str]) -> np.ndarray:
        """Fallback similarity calculation using Jaccard similarity"""
        n = len(keywords)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    similarity_matrix[i][j] = self._jaccard_similarity(keywords[i], keywords[j])
        
        return similarity_matrix
    
    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaccard similarity between two strings"""
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def cluster_keywords(self, keywords: List[str], 
                        search_volumes: List[int] = None,
                        difficulties: List[int] = None) -> List[Dict[str, Any]]:
        """Cluster keywords using DBSCAN algorithm"""
        if len(keywords) < 2:
            return [{'cluster_id': 0, 'keywords': keywords, 'centroid': keywords[0] if keywords else ''}]
        
        try:
            # Calculate similarity matrix
            similarity_matrix = self.calculate_semantic_similarity(keywords)
            
            # Convert similarity to distance (1 - similarity)
            distance_matrix = 1 - similarity_matrix
            
            # Apply DBSCAN clustering
            clustering = DBSCAN(
                eps=1 - self.similarity_threshold,
                min_samples=1,
                metric='precomputed'
            )
            
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Group keywords by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append({
                    'keyword': keywords[i],
                    'search_volume': search_volumes[i] if search_volumes else None,
                    'difficulty': difficulties[i] if difficulties else None
                })
            
            # Create cluster summaries
            cluster_results = []
            for cluster_id, cluster_keywords in clusters.items():
                # Find centroid (most representative keyword)
                centroid = self._find_centroid(cluster_keywords, similarity_matrix)
                
                # Calculate cluster metrics
                total_volume = sum(kw.get('search_volume', 0) or 0 for kw in cluster_keywords)
                avg_difficulty = np.mean([kw.get('difficulty', 0) or 0 for kw in cluster_keywords])
                
                cluster_results.append({
                    'cluster_id': int(cluster_id),
                    'keywords': cluster_keywords,
                    'centroid': centroid,
                    'size': len(cluster_keywords),
                    'total_search_volume': total_volume,
                    'average_difficulty': round(avg_difficulty, 2),
                    'cluster_score': self._calculate_cluster_score(cluster_keywords)
                })
            
            # Sort clusters by score
            cluster_results.sort(key=lambda x: x['cluster_score'], reverse=True)
            
            return cluster_results
            
        except Exception as e:
            logger.error(f"Error in keyword clustering: {e}")
            # Return single cluster with all keywords
            return [{
                'cluster_id': 0,
                'keywords': [{'keyword': kw, 'search_volume': None, 'difficulty': None} for kw in keywords],
                'centroid': keywords[0] if keywords else '',
                'size': len(keywords),
                'total_search_volume': 0,
                'average_difficulty': 0,
                'cluster_score': 0
            }]
    
    def _find_centroid(self, cluster_keywords: List[Dict], similarity_matrix: np.ndarray) -> str:
        """Find the most representative keyword in a cluster"""
        if not cluster_keywords:
            return ""
        
        # For simplicity, return the first keyword
        # In a more sophisticated implementation, you could find the keyword with highest average similarity
        return cluster_keywords[0]['keyword']
    
    def _calculate_cluster_score(self, cluster_keywords: List[Dict]) -> float:
        """Calculate overall score for a cluster based on volume and difficulty"""
        if not cluster_keywords:
            return 0.0
        
        # Calculate weighted score based on search volume and difficulty
        total_score = 0
        total_weight = 0
        
        for kw in cluster_keywords:
            volume = kw.get('search_volume', 0) or 0
            difficulty = kw.get('difficulty', 50) or 50
            
            # Higher volume = higher score, lower difficulty = higher score
            volume_score = min(volume / 1000, 1.0)  # Normalize to 0-1
            difficulty_score = 1.0 - (difficulty / 100)  # Invert difficulty
            
            # Weight by volume
            weight = volume if volume > 0 else 1
            score = (volume_score + difficulty_score) / 2
            
            total_score += score * weight
            total_weight += weight
        
        return round(total_score / total_weight, 3) if total_weight > 0 else 0.0
    
    def find_keyword_opportunities(self, clusters: List[Dict[str, Any]], 
                                 min_volume: int = 1000,
                                 max_difficulty: int = 70) -> List[Dict[str, Any]]:
        """Identify high-opportunity keywords from clusters"""
        opportunities = []
        
        for cluster in clusters:
            for kw in cluster['keywords']:
                volume = kw.get('search_volume', 0) or 0
                difficulty = kw.get('difficulty', 50) or 50
                
                # Check if keyword meets opportunity criteria
                if volume >= min_volume and difficulty <= max_difficulty:
                    opportunity_score = self._calculate_opportunity_score(volume, difficulty)
                    
                    opportunities.append({
                        'keyword': kw['keyword'],
                        'search_volume': volume,
                        'difficulty': difficulty,
                        'cluster_id': cluster['cluster_id'],
                        'cluster_size': cluster['size'],
                        'opportunity_score': opportunity_score,
                        'reasoning': self._explain_opportunity(volume, difficulty, cluster['size'])
                    })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return opportunities
    
    def _calculate_opportunity_score(self, volume: int, difficulty: int) -> float:
        """Calculate opportunity score (0-100) based on volume and difficulty"""
        # Volume score (0-50 points)
        volume_score = min(volume / 10000 * 50, 50)
        
        # Difficulty score (0-50 points) - lower difficulty = higher score
        difficulty_score = max(0, 50 - (difficulty / 100 * 50))
        
        return round(volume_score + difficulty_score, 1)
    
    def _explain_opportunity(self, volume: int, difficulty: int, cluster_size: int) -> str:
        """Generate human-readable explanation for opportunity score"""
        reasons = []
        
        if volume >= 5000:
            reasons.append("High search volume")
        elif volume >= 1000:
            reasons.append("Good search volume")
        
        if difficulty <= 30:
            reasons.append("Low competition")
        elif difficulty <= 50:
            reasons.append("Moderate competition")
        
        if cluster_size >= 5:
            reasons.append("Multiple related keywords")
        
        return "; ".join(reasons) if reasons else "Balanced volume and difficulty"
