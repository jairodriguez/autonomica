"""
SEO Score Calculation Module

This module provides comprehensive SEO scoring capabilities:
- On-page SEO scoring
- Technical SEO assessment
- Content quality evaluation
- User experience scoring
- Mobile optimization scoring
- Page speed assessment
- Security and trust scoring
- Overall SEO score calculation
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
from urllib.parse import urlparse
import aiohttp

from app.services.redis_service import RedisService
from app.services.seo_service import SEOService
from app.services.serp_scraper import SERPScraper

logger = logging.getLogger(__name__)

@dataclass
class SEOScore:
    """Individual SEO score component"""
    category: str
    score: float
    max_score: float
    percentage: float
    details: List[str]
    recommendations: List[str]
    weight: float

@dataclass
class PageSEOScore:
    """Complete page SEO score"""
    url: str
    overall_score: float
    grade: str
    scores: Dict[str, SEOScore]
    total_score: float
    max_possible_score: float
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    analyzed_at: datetime

@dataclass
class ContentAnalysis:
    """Content quality analysis"""
    word_count: int
    readability_score: float
    keyword_density: Dict[str, float]
    heading_structure: Dict[str, int]
    image_count: int
    internal_links: int
    external_links: int
    content_quality_score: float

@dataclass
class TechnicalAnalysis:
    """Technical SEO analysis"""
    page_load_time: Optional[float]
    mobile_friendly: bool
    ssl_secure: bool
    robots_txt: bool
    sitemap: bool
    structured_data: bool
    technical_score: float

class SEOScorer:
    """Comprehensive SEO scoring service"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.seo_service = SEOService()
        self.serp_scraper = SERPScraper()
        
        # Scoring weights for different categories
        self.score_weights = {
            "on_page": 0.25,
            "technical": 0.20,
            "content": 0.20,
            "user_experience": 0.15,
            "mobile": 0.10,
            "security": 0.10
        }
        
        # Scoring criteria and thresholds
        self.scoring_criteria = {
            "on_page": {
                "title_length": {"min": 30, "max": 60, "score": 10},
                "meta_description": {"min": 120, "max": 160, "score": 10},
                "heading_structure": {"h1_count": 1, "score": 10},
                "keyword_optimization": {"density_min": 0.5, "density_max": 2.5, "score": 15},
                "url_structure": {"score": 10},
                "internal_linking": {"score": 10}
            },
            "technical": {
                "page_speed": {"fast": 3, "medium": 2, "slow": 1, "score": 20},
                "mobile_friendly": {"score": 15},
                "ssl_secure": {"score": 10},
                "robots_txt": {"score": 5},
                "sitemap": {"score": 5},
                "structured_data": {"score": 10}
            },
            "content": {
                "word_count": {"min": 300, "score": 15},
                "readability": {"min": 60, "score": 15},
                "keyword_density": {"score": 10},
                "heading_structure": {"score": 10},
                "image_optimization": {"score": 10}
            },
            "user_experience": {
                "navigation": {"score": 15},
                "content_organization": {"score": 15},
                "call_to_action": {"score": 10},
                "social_proof": {"score": 10}
            },
            "mobile": {
                "responsive_design": {"score": 20},
                "touch_friendly": {"score": 15},
                "mobile_speed": {"score": 15}
            },
            "security": {
                "ssl_certificate": {"score": 20},
                "security_headers": {"score": 15},
                "privacy_policy": {"score": 10}
            }
        }
        
        # Grade thresholds
        self.grade_thresholds = {
            "A+": 95,
            "A": 90,
            "A-": 85,
            "B+": 80,
            "B": 75,
            "B-": 70,
            "C+": 65,
            "C": 60,
            "C-": 55,
            "D+": 50,
            "D": 45,
            "D-": 40,
            "F": 0
        }
        
        # Caching configuration
        self.cache_ttl = 3600 * 6  # 6 hours
    
    async def _get_cached_score(self, url: str) -> Optional[PageSEOScore]:
        """Retrieve cached SEO score from Redis"""
        cache_key = f"seo_score:{hashlib.md5(url.encode()).hexdigest()}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Convert string dates back to datetime objects
                data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"])
                return PageSEOScore(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached SEO score: {e}")
        
        return None
    
    async def _cache_score(self, url: str, score: PageSEOScore) -> bool:
        """Cache SEO score in Redis"""
        cache_key = f"seo_score:{hashlib.md5(url.encode()).hexdigest()}"
        
        try:
            # Convert datetime objects to strings for JSON serialization
            data_dict = score.__dict__.copy()
            data_dict["analyzed_at"] = data_dict["analyzed_at"].isoformat()
            
            await self.redis_service.set(
                cache_key,
                json.dumps(data_dict, default=str),
                expire=self.cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache SEO score: {e}")
            return False
    
    async def _analyze_on_page_seo(self, url: str, html_content: str, 
                                  target_keywords: List[str]) -> SEOScore:
        """Analyze on-page SEO factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # Title analysis
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                title_length = len(title)
                
                if 30 <= title_length <= 60:
                    score += 10
                    details.append(f"Title length optimal: {title_length} characters")
                elif title_length < 30:
                    score += 5
                    details.append(f"Title too short: {title_length} characters")
                    recommendations.append("Increase title length to 30-60 characters")
                else:
                    score += 5
                    details.append(f"Title too long: {title_length} characters")
                    recommendations.append("Reduce title length to 30-60 characters")
                
                # Check keyword in title
                title_lower = title.lower()
                if any(keyword.lower() in title_lower for keyword in target_keywords):
                    score += 5
                    details.append("Target keyword found in title")
                else:
                    recommendations.append("Include target keyword in title")
                
                max_score += 15
            else:
                details.append("No title tag found")
                recommendations.append("Add a title tag")
                max_score += 15
            
            # Meta description analysis
            meta_desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
            if meta_desc_match:
                meta_desc = meta_desc_match.group(1).strip()
                meta_length = len(meta_desc)
                
                if 120 <= meta_length <= 160:
                    score += 10
                    details.append(f"Meta description optimal: {meta_length} characters")
                elif meta_length < 120:
                    score += 5
                    details.append(f"Meta description too short: {meta_length} characters")
                    recommendations.append("Increase meta description to 120-160 characters")
                else:
                    score += 5
                    details.append(f"Meta description too long: {meta_length} characters")
                    recommendations.append("Reduce meta description to 120-160 characters")
                
                max_score += 10
            else:
                details.append("No meta description found")
                recommendations.append("Add a meta description")
                max_score += 10
            
            # Heading structure analysis
            h1_count = len(re.findall(r'<h1[^>]*>', html_content, re.IGNORECASE))
            h2_count = len(re.findall(r'<h2[^>]*>', html_content, re.IGNORECASE))
            
            if h1_count == 1:
                score += 10
                details.append("Proper H1 structure: 1 H1 tag found")
            elif h1_count == 0:
                details.append("No H1 tag found")
                recommendations.append("Add exactly one H1 tag")
            else:
                details.append(f"Multiple H1 tags found: {h1_count}")
                recommendations.append("Use only one H1 tag per page")
            
            if h2_count > 0:
                score += 5
                details.append(f"Good heading hierarchy: {h2_count} H2 tags found")
            else:
                recommendations.append("Add H2 tags for better content structure")
            
            max_score += 15
            
            # URL structure analysis
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            if len(path) <= 3 or path == "/":
                score += 10
                details.append("Clean URL structure")
            elif len(path) <= 50:
                score += 7
                details.append("Acceptable URL length")
            else:
                score += 3
                details.append("URL could be shorter")
                recommendations.append("Consider shortening URL for better user experience")
            
            max_score += 10
            
            # Internal linking analysis
            internal_links = len(re.findall(r'href=["\']/[^"\']*["\']', html_content))
            if internal_links >= 3:
                score += 10
                details.append(f"Good internal linking: {internal_links} internal links")
            elif internal_links > 0:
                score += 5
                details.append(f"Some internal linking: {internal_links} internal links")
                recommendations.append("Add more internal links for better site structure")
            else:
                details.append("No internal links found")
                recommendations.append("Add internal links to related content")
            
            max_score += 10
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="on_page",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["on_page"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze on-page SEO: {e}")
            return SEOScore(
                category="on_page",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check page content and try again"],
                weight=self.score_weights["on_page"]
            )
    
    async def _analyze_technical_seo(self, url: str, html_content: str) -> SEOScore:
        """Analyze technical SEO factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # SSL security check
            if url.startswith("https://"):
                score += 20
                details.append("SSL certificate active (HTTPS)")
            else:
                details.append("No SSL certificate (HTTP)")
                recommendations.append("Implement SSL certificate for security")
            max_score += 20
            
            # Mobile friendliness check (basic)
            viewport_match = re.search(r'<meta[^>]*name=["\']viewport["\']', html_content, re.IGNORECASE)
            if viewport_match:
                score += 15
                details.append("Viewport meta tag found")
            else:
                details.append("No viewport meta tag")
                recommendations.append("Add viewport meta tag for mobile optimization")
            max_score += 15
            
            # Robots.txt check
            try:
                robots_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt"
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url) as response:
                        if response.status == 200:
                            score += 5
                            details.append("Robots.txt file found")
                        else:
                            details.append("Robots.txt file not found")
                            recommendations.append("Create robots.txt file")
            except Exception:
                details.append("Could not check robots.txt")
                recommendations.append("Verify robots.txt file exists")
            max_score += 5
            
            # Sitemap check
            try:
                sitemap_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/sitemap.xml"
                async with aiohttp.ClientSession() as session:
                    async with session.get(sitemap_url) as response:
                        if response.status == 200:
                            score += 5
                            details.append("XML sitemap found")
                        else:
                            details.append("XML sitemap not found")
                            recommendations.append("Create XML sitemap")
            except Exception:
                details.append("Could not check sitemap")
                recommendations.append("Verify XML sitemap exists")
            max_score += 5
            
            # Structured data check
            structured_data = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>', html_content, re.IGNORECASE)
            if structured_data:
                score += 10
                details.append("Structured data found")
            else:
                details.append("No structured data found")
                recommendations.append("Implement structured data for better search results")
            max_score += 10
            
            # Page load time simulation (basic)
            # In a real implementation, you would use tools like PageSpeed Insights
            score += 10  # Placeholder score
            details.append("Page load time analysis (simulated)")
            max_score += 10
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="technical",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["technical"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze technical SEO: {e}")
            return SEOScore(
                category="technical",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check technical configuration and try again"],
                weight=self.score_weights["technical"]
            )
    
    async def _analyze_content_quality(self, html_content: str, target_keywords: List[str]) -> SEOScore:
        """Analyze content quality factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # Extract text content (remove HTML tags)
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Word count analysis
            word_count = len(text_content.split())
            if word_count >= 300:
                score += 15
                details.append(f"Good content length: {word_count} words")
            elif word_count >= 150:
                score += 10
                details.append(f"Acceptable content length: {word_count} words")
                recommendations.append("Consider adding more content for better SEO")
            else:
                score += 5
                details.append(f"Content too short: {word_count} words")
                recommendations.append("Add more content (aim for 300+ words)")
            max_score += 15
            
            # Readability analysis (basic Flesch-Kincaid simulation)
            sentences = len(re.split(r'[.!?]+', text_content))
            avg_sentence_length = word_count / sentences if sentences > 0 else 0
            
            if avg_sentence_length <= 20:
                score += 15
                details.append("Good readability: short sentences")
            elif avg_sentence_length <= 25:
                score += 10
                details.append("Acceptable readability")
                recommendations.append("Consider shortening some sentences")
            else:
                score += 5
                details.append("Complex readability: long sentences")
                recommendations.append("Break down long sentences for better readability")
            max_score += 15
            
            # Keyword density analysis
            if target_keywords:
                total_keyword_occurrences = 0
                for keyword in target_keywords:
                    keyword_lower = keyword.lower()
                    occurrences = text_content.lower().count(keyword_lower)
                    total_keyword_occurrences += occurrences
                
                if word_count > 0:
                    keyword_density = (total_keyword_occurrences / word_count) * 100
                    
                    if 0.5 <= keyword_density <= 2.5:
                        score += 10
                        details.append(f"Optimal keyword density: {keyword_density:.2f}%")
                    elif keyword_density < 0.5:
                        score += 5
                        details.append(f"Low keyword density: {keyword_density:.2f}%")
                        recommendations.append("Increase target keyword usage naturally")
                    else:
                        score += 3
                        details.append(f"High keyword density: {keyword_density:.2f}%")
                        recommendations.append("Reduce keyword stuffing for better user experience")
                else:
                    score += 5
                    details.append("No content to analyze for keywords")
            else:
                score += 5
                details.append("No target keywords specified")
            max_score += 10
            
            # Heading structure analysis
            heading_tags = re.findall(r'<h[1-6][^>]*>', html_content, re.IGNORECASE)
            if len(heading_tags) >= 3:
                score += 10
                details.append(f"Good heading structure: {len(heading_tags)} heading tags")
            elif len(heading_tags) > 0:
                score += 5
                details.append(f"Basic heading structure: {len(heading_tags)} heading tags")
                recommendations.append("Add more headings for better content organization")
            else:
                details.append("No heading tags found")
                recommendations.append("Add heading tags for content structure")
            max_score += 10
            
            # Image optimization check
            images = re.findall(r'<img[^>]*>', html_content, re.IGNORECASE)
            if images:
                alt_tags = sum(1 for img in images if 'alt=' in img.lower())
                if alt_tags == len(images):
                    score += 10
                    details.append("All images have alt tags")
                else:
                    score += 5
                    details.append(f"Some images missing alt tags: {alt_tags}/{len(images)}")
                    recommendations.append("Add alt tags to all images")
            else:
                score += 5
                details.append("No images found")
            max_score += 10
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="content",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["content"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze content quality: {e}")
            return SEOScore(
                category="content",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check content and try again"],
                weight=self.score_weights["content"]
            )
    
    async def _analyze_user_experience(self, html_content: str) -> SEOScore:
        """Analyze user experience factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # Navigation analysis
            navigation_links = re.findall(r'<nav[^>]*>.*?</nav>', html_content, re.IGNORECASE | re.DOTALL)
            if navigation_links:
                score += 15
                details.append("Navigation menu found")
            else:
                details.append("No navigation menu found")
                recommendations.append("Add navigation menu for better user experience")
            max_score += 15
            
            # Content organization
            sections = re.findall(r'<section[^>]*>|<article[^>]*>|<div[^>]*class=["\'][^"\']*content[^"\']*["\']', html_content, re.IGNORECASE)
            if sections:
                score += 15
                details.append("Content well organized with semantic elements")
            else:
                score += 5
                details.append("Basic content organization")
                recommendations.append("Use semantic HTML elements for better structure")
            max_score += 15
            
            # Call to action analysis
            cta_patterns = [
                r'<button[^>]*>.*?(buy|shop|order|subscribe|download|sign up|get started|learn more).*?</button>',
                r'<a[^>]*>.*?(buy|shop|order|subscribe|download|sign up|get started|learn more).*?</a>'
            ]
            
            cta_found = False
            for pattern in cta_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    cta_found = True
                    break
            
            if cta_found:
                score += 10
                details.append("Call to action elements found")
            else:
                details.append("No clear call to action found")
                recommendations.append("Add clear call to action buttons/links")
            max_score += 10
            
            # Social proof elements
            social_proof_patterns = [
                r'<div[^>]*class=["\'][^"\']*(testimonial|review|rating|social|trust)[^"\']*["\']',
                r'<span[^>]*class=["\'][^"\']*(star|rating)[^"\']*["\']'
            ]
            
            social_proof_found = False
            for pattern in social_proof_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    social_proof_found = True
                    break
            
            if social_proof_found:
                score += 10
                details.append("Social proof elements found")
            else:
                score += 5
                details.append("Limited social proof elements")
                recommendations.append("Add testimonials, reviews, or trust indicators")
            max_score += 10
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="user_experience",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["user_experience"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze user experience: {e}")
            return SEOScore(
                category="user_experience",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check user experience elements and try again"],
                weight=self.score_weights["user_experience"]
            )
    
    async def _analyze_mobile_optimization(self, html_content: str) -> SEOScore:
        """Analyze mobile optimization factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # Responsive design check
            viewport_meta = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
            if viewport_meta:
                viewport_content = viewport_meta.group(1)
                if 'width=device-width' in viewport_content:
                    score += 20
                    details.append("Responsive viewport meta tag found")
                else:
                    score += 10
                    details.append("Viewport meta tag found but not responsive")
                    recommendations.append("Update viewport meta tag for responsive design")
            else:
                details.append("No viewport meta tag found")
                recommendations.append("Add responsive viewport meta tag")
            max_score += 20
            
            # Touch-friendly elements
            touch_elements = re.findall(r'<button[^>]*>|<a[^>]*>|<input[^>]*>', html_content, re.IGNORECASE)
            if len(touch_elements) > 0:
                score += 15
                details.append(f"Touch-friendly elements found: {len(touch_elements)}")
            else:
                details.append("No interactive elements found")
                recommendations.append("Add touch-friendly buttons and links")
            max_score += 15
            
            # Mobile-specific CSS
            mobile_css = re.search(r'<link[^>]*media=["\'](?:only screen and \(max-width|max-width)[^"\']*["\']', html_content, re.IGNORECASE)
            if mobile_css:
                score += 15
                details.append("Mobile-specific CSS found")
            else:
                score += 5
                details.append("No mobile-specific CSS detected")
                recommendations.append("Consider adding mobile-specific stylesheets")
            max_score += 15
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="mobile",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["mobile"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze mobile optimization: {e}")
            return SEOScore(
                category="mobile",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check mobile optimization and try again"],
                weight=self.score_weights["mobile"]
            )
    
    async def _analyze_security(self, url: str) -> SEOScore:
        """Analyze security factors"""
        try:
            details = []
            recommendations = []
            score = 0
            max_score = 0
            
            # SSL certificate check
            if url.startswith("https://"):
                score += 20
                details.append("SSL certificate active (HTTPS)")
            else:
                details.append("No SSL certificate (HTTP)")
                recommendations.append("Implement SSL certificate for security")
            max_score += 20
            
            # Security headers check (basic)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        headers = response.headers
                        
                        # Check for common security headers
                        security_headers = {
                            'X-Frame-Options': 'Clickjacking protection',
                            'X-Content-Type-Options': 'MIME type sniffing protection',
                            'X-XSS-Protection': 'XSS protection',
                            'Strict-Transport-Security': 'HSTS enabled'
                        }
                        
                        for header, description in security_headers.items():
                            if header in headers:
                                score += 5
                                details.append(f"{description}: {header} found")
                            else:
                                details.append(f"{description}: {header} not found")
                                recommendations.append(f"Add {header} security header")
                            max_score += 5
                        
            except Exception as e:
                details.append(f"Could not check security headers: {e}")
                max_score += 20
            
            # Privacy policy check
            try:
                privacy_urls = [
                    f"{urlparse(url).scheme}://{urlparse(url).netloc}/privacy",
                    f"{urlparse(url).scheme}://{urlparse(url).netloc}/privacy-policy",
                    f"{urlparse(url).scheme}://{urlparse(url).netloc}/privacy-policy.html"
                ]
                
                privacy_found = False
                for privacy_url in privacy_urls:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(privacy_url) as response:
                                if response.status == 200:
                                    privacy_found = True
                                    break
                    except Exception:
                        continue
                
                if privacy_found:
                    score += 10
                    details.append("Privacy policy page found")
                else:
                    details.append("Privacy policy page not found")
                    recommendations.append("Create privacy policy page")
                max_score += 10
                
            except Exception as e:
                details.append(f"Could not check privacy policy: {e}")
                max_score += 10
            
            # Calculate percentage
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            return SEOScore(
                category="security",
                score=score,
                max_score=max_score,
                percentage=round(percentage, 2),
                details=details,
                recommendations=recommendations,
                weight=self.score_weights["security"]
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze security: {e}")
            return SEOScore(
                category="security",
                score=0,
                max_score=0,
                percentage=0,
                details=["Analysis failed"],
                recommendations=["Check security configuration and try again"],
                weight=self.score_weights["security"]
            )
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade based on percentage"""
        for grade, threshold in self.grade_thresholds.items():
            if percentage >= threshold:
                return grade
        return "F"
    
    async def calculate_seo_score(self, url: str, target_keywords: List[str] = None) -> PageSEOScore:
        """
        Calculate comprehensive SEO score for a web page
        
        Args:
            url: URL of the page to analyze
            target_keywords: List of target keywords for optimization
        
        Returns:
            Complete SEO score analysis
        """
        # Check cache first
        cached_score = await self._get_cached_score(url)
        if cached_score:
            logger.info(f"Retrieved cached SEO score for {url}")
            return cached_score
        
        try:
            logger.info(f"Calculating SEO score for {url}")
            
            # Fetch page content
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch page: HTTP {response.status}")
                    
                    html_content = await response.text()
            
            # Analyze all SEO factors
            on_page_score = await self._analyze_on_page_seo(url, html_content, target_keywords or [])
            technical_score = await self._analyze_technical_seo(url, html_content)
            content_score = await self._analyze_content_quality(html_content, target_keywords or [])
            ux_score = await self._analyze_user_experience(html_content)
            mobile_score = await self._analyze_mobile_optimization(html_content)
            security_score = await self._analyze_security(url)
            
            # Compile all scores
            all_scores = {
                "on_page": on_page_score,
                "technical": technical_score,
                "content": content_score,
                "user_experience": ux_score,
                "mobile": mobile_score,
                "security": security_score
            }
            
            # Calculate weighted overall score
            total_score = 0
            max_possible_score = 0
            
            for score_obj in all_scores.values():
                weighted_score = score_obj.score * score_obj.weight
                weighted_max = score_obj.max_score * score_obj.weight
                
                total_score += weighted_score
                max_possible_score += weighted_max
            
            overall_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
            
            # Generate overall recommendations
            all_recommendations = []
            critical_issues = []
            warnings = []
            
            for score_obj in all_scores.values():
                if score_obj.percentage < 50:
                    critical_issues.extend(score_obj.recommendations)
                elif score_obj.percentage < 70:
                    warnings.extend(score_obj.recommendations)
                
                all_recommendations.extend(score_obj.recommendations)
            
            # Remove duplicates and limit recommendations
            all_recommendations = list(set(all_recommendations))[:10]
            critical_issues = list(set(critical_issues))[:5]
            warnings = list(set(warnings))[:5]
            
            # Create final score object
            page_score = PageSEOScore(
                url=url,
                overall_score=round(overall_percentage, 2),
                grade=self._calculate_grade(overall_percentage),
                scores=all_scores,
                total_score=round(total_score, 2),
                max_possible_score=round(max_possible_score, 2),
                critical_issues=critical_issues,
                warnings=warnings,
                recommendations=all_recommendations,
                analyzed_at=datetime.now()
            )
            
            # Cache the result
            await self._cache_score(url, page_score)
            
            logger.info(f"SEO score calculated: {overall_percentage:.2f}% ({page_score.grade})")
            
            return page_score
            
        except Exception as e:
            logger.error(f"Failed to calculate SEO score for {url}: {e}")
            # Return minimal score on failure
            return PageSEOScore(
                url=url,
                overall_score=0.0,
                grade="F",
                scores={},
                total_score=0.0,
                max_possible_score=0.0,
                critical_issues=["Analysis failed"],
                warnings=[],
                recommendations=["Check URL accessibility and try again"],
                analyzed_at=datetime.now()
            )
    
    async def compare_seo_scores(self, urls: List[str], target_keywords: List[str] = None) -> Dict[str, PageSEOScore]:
        """
        Compare SEO scores across multiple URLs
        
        Args:
            urls: List of URLs to analyze
            target_keywords: List of target keywords for optimization
        
        Returns:
            Dictionary mapping URLs to SEO scores
        """
        try:
            comparison_results = {}
            
            for url in urls:
                try:
                    score = await self.calculate_seo_score(url, target_keywords)
                    comparison_results[url] = score
                except Exception as e:
                    logger.warning(f"Failed to analyze {url}: {e}")
                    # Add failed result
                    comparison_results[url] = PageSEOScore(
                        url=url,
                        overall_score=0.0,
                        grade="F",
                        scores={},
                        total_score=0.0,
                        max_possible_score=0.0,
                        critical_issues=["Analysis failed"],
                        warnings=[],
                        recommendations=["Check URL and try again"],
                        analyzed_at=datetime.now()
                    )
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Failed to compare SEO scores: {e}")
            return {}
    
    async def export_seo_score(self, page_score: PageSEOScore, format: str = "json") -> str:
        """
        Export SEO score in various formats
        
        Args:
            page_score: SEO score to export
            format: Export format (json, csv)
        
        Returns:
            Exported data as string
        """
        try:
            if format.lower() == "json":
                # Convert to serializable format
                data_dict = page_score.__dict__.copy()
                data_dict["analyzed_at"] = data_dict["analyzed_at"].isoformat()
                
                return json.dumps(data_dict, indent=2, default=str)
                
            elif format.lower() == "csv":
                # Create CSV with key metrics
                csv_lines = [
                    "url,overall_score,grade,total_score,max_possible_score,critical_issues,warnings,recommendations"
                ]
                
                critical_issues_str = "; ".join(page_score.critical_issues)
                warnings_str = "; ".join(page_score.warnings)
                recommendations_str = "; ".join(page_score.recommendations)
                
                csv_lines.append(
                    f"{page_score.url},{page_score.overall_score},{page_score.grade},"
                    f"{page_score.total_score},{page_score.max_possible_score},"
                    f"\"{critical_issues_str}\",\"{warnings_str}\",\"{recommendations_str}\""
                )
                
                return "\n".join(csv_lines)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export SEO score: {e}")
            return json.dumps({"error": str(e)})