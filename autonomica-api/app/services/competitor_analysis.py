"""
Competitor Analysis Module
Analyzes competitor domains, content structure, and ranking patterns
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json
from urllib.parse import urlparse, urljoin
import hashlib

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

class CompetitorAnalyzer:
    """Analyzes competitor domains and content for SEO insights"""
    
    def __init__(self, max_concurrent_requests: int = 5, request_timeout: int = 30):
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.request_timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_competitors(self, domain: str, 
                                competitor_domains: List[str],
                                analysis_depth: str = "basic") -> Dict[str, Any]:
        """Analyze competitor domains and provide insights"""
        try:
            logger.info(f"Starting competitor analysis for {domain} against {len(competitor_domains)} competitors")
            
            # Basic competitor analysis
            basic_analysis = await self._analyze_basic_metrics(domain, competitor_domains)
            
            if analysis_depth == "basic":
                return basic_analysis
            
            # Deep competitor analysis
            deep_analysis = await self._analyze_deep_metrics(domain, competitor_domains)
            
            # Combine results
            analysis_result = {
                **basic_analysis,
                "deep_analysis": deep_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_depth": analysis_depth
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_basic_metrics(self, domain: str, competitor_domains: List[str]) -> Dict[str, Any]:
        """Analyze basic competitor metrics"""
        try:
            # Analyze each competitor
            competitor_analyses = []
            
            for comp_domain in competitor_domains[:10]:  # Limit to top 10
                try:
                    comp_analysis = await self._analyze_single_competitor(comp_domain)
                    competitor_analyses.append(comp_analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze competitor {comp_domain}: {e}")
                    continue
            
            # Calculate competitive landscape metrics
            landscape_metrics = self._calculate_landscape_metrics(domain, competitor_analyses)
            
            return {
                "domain": domain,
                "competitors_analyzed": len(competitor_analyses),
                "competitor_analyses": competitor_analyses,
                "landscape_metrics": landscape_metrics,
                "analysis_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error in basic metrics analysis: {e}")
            return {"error": str(e), "analysis_status": "failed"}
    
    async def _analyze_single_competitor(self, domain: str) -> Dict[str, Any]:
        """Analyze a single competitor domain"""
        try:
            # Basic domain information
            domain_info = {
                "domain": domain,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Check domain accessibility
            accessibility = await self._check_domain_accessibility(domain)
            domain_info.update(accessibility)
            
            if not accessibility.get("accessible", False):
                return domain_info
            
            # Get basic page information
            page_info = await self._get_page_information(domain)
            domain_info.update(page_info)
            
            # Analyze content structure
            content_analysis = await self._analyze_content_structure(domain)
            domain_info["content_analysis"] = content_analysis
            
            # Analyze technical SEO
            technical_seo = await self._analyze_technical_seo(domain)
            domain_info["technical_seo"] = technical_seo
            
            return domain_info
            
        except Exception as e:
            logger.error(f"Error analyzing competitor {domain}: {e}")
            return {
                "domain": domain,
                "error": str(e),
                "analysis_status": "failed"
            }
    
    async def _check_domain_accessibility(self, domain: str) -> Dict[str, Any]:
        """Check if domain is accessible and responsive"""
        try:
            # Ensure domain has protocol
            if not domain.startswith(('http://', 'https://')):
                domain = f"https://{domain}"
            
            async with self.session.get(domain, allow_redirects=True) as response:
                return {
                    "accessible": True,
                    "status_code": response.status,
                    "final_url": str(response.url),
                    "response_time": response.headers.get("X-Response-Time", "unknown"),
                    "server": response.headers.get("Server", "unknown"),
                    "content_type": response.headers.get("Content-Type", "unknown")
                }
                
        except Exception as e:
            logger.warning(f"Domain {domain} not accessible: {e}")
            return {
                "accessible": False,
                "error": str(e)
            }
    
    async def _get_page_information(self, domain: str) -> Dict[str, Any]:
        """Get basic page information"""
        try:
            async with self.session.get(domain) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract basic page info
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                meta_description = soup.find('meta', attrs={'name': 'description'})
                description = meta_description.get('content', '') if meta_description else ""
                
                h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
                h2_tags = [h2.get_text().strip() for h2 in soup.find_all('h2')]
                
                # Count content elements
                paragraphs = len(soup.find_all('p'))
                images = len(soup.find_all('img'))
                links = len(soup.find_all('a'))
                
                return {
                    "page_info": {
                        "title": title_text,
                        "meta_description": description,
                        "h1_count": len(h1_tags),
                        "h2_count": len(h2_tags),
                        "paragraphs": paragraphs,
                        "images": images,
                        "links": links,
                        "content_length": len(html)
                    },
                    "headings": {
                        "h1": h1_tags[:5],  # Limit to first 5
                        "h2": h2_tags[:10]  # Limit to first 10
                    }
                }
                
        except Exception as e:
            logger.warning(f"Failed to get page information for {domain}: {e}")
            return {
                "page_info": {},
                "headings": {"h1": [], "h2": []}
            }
    
    async def _analyze_content_structure(self, domain: str) -> Dict[str, Any]:
        """Analyze content structure and patterns"""
        try:
            async with self.session.get(domain) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Analyze content structure
                content_analysis = {
                    "content_type": self._detect_content_type(soup),
                    "content_patterns": self._identify_content_patterns(soup),
                    "engagement_elements": self._identify_engagement_elements(soup),
                    "content_quality_indicators": self._assess_content_quality(soup)
                }
                
                return content_analysis
                
        except Exception as e:
            logger.warning(f"Failed to analyze content structure for {domain}: {e}")
            return {}
    
    def _detect_content_type(self, soup: BeautifulSoup) -> str:
        """Detect the type of content on the page"""
        # Check for common content type indicators
        if soup.find('article'):
            return "article"
        elif soup.find('form'):
            return "form"
        elif soup.find('table'):
            return "data_table"
        elif soup.find('video'):
            return "video"
        elif soup.find('img', {'alt': re.compile(r'.+')}):
            return "image_gallery"
        else:
            return "general"
    
    def _identify_content_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Identify common content patterns"""
        patterns = {
            "has_sidebar": bool(soup.find('aside') or soup.find(class_=re.compile(r'sidebar|nav|menu'))),
            "has_footer": bool(soup.find('footer')),
            "has_header": bool(soup.find('header')),
            "has_navigation": bool(soup.find('nav')),
            "has_search": bool(soup.find('input', {'type': 'search'}) or soup.find('form', {'action': re.compile(r'search')})),
            "has_social_links": bool(soup.find('a', href=re.compile(r'facebook|twitter|linkedin|instagram'))),
            "has_cta_buttons": bool(soup.find('button') or soup.find('a', class_=re.compile(r'btn|button|cta'))),
            "has_testimonials": bool(soup.find(text=re.compile(r'testimonial|review|rating'))),
            "has_faq": bool(soup.find(text=re.compile(r'faq|question|answer'))),
            "has_related_content": bool(soup.find(class_=re.compile(r'related|similar|recommended')))
        }
        
        return patterns
    
    def _identify_engagement_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Identify elements that increase user engagement"""
        engagement = {
            "has_videos": bool(soup.find('video') or soup.find('iframe', src=re.compile(r'youtube|vimeo'))),
            "has_images": bool(soup.find('img')),
            "has_interactive_elements": bool(soup.find('canvas') or soup.find('svg')),
            "has_forms": bool(soup.find('form')),
            "has_comments": bool(soup.find(class_=re.compile(r'comment|review'))),
            "has_ratings": bool(soup.find(class_=re.compile(r'rating|star'))),
            "has_sharing": bool(soup.find(class_=re.compile(r'share|social'))),
            "has_progress_bars": bool(soup.find(class_=re.compile(r'progress|meter'))),
            "has_tooltips": bool(soup.find(title=True) or soup.find(class_=re.compile(r'tooltip|popup')))
        }
        
        return engagement
    
    def _assess_content_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Assess content quality indicators"""
        # Count content elements
        text_content = soup.get_text()
        words = len(text_content.split())
        
        # Check for content quality indicators
        quality_indicators = {
            "word_count": words,
            "has_structured_data": bool(soup.find(attrs={'itemtype': True})),
            "has_schema_markup": bool(soup.find(attrs={'itemtype': True})),
            "has_meta_tags": bool(soup.find('meta', attrs={'name': 'description'})),
            "has_canonical": bool(soup.find('link', attrs={'rel': 'canonical'})),
            "has_alt_text": bool(soup.find('img', {'alt': True})),
            "has_internal_links": len([a for a in soup.find_all('a') if a.get('href', '').startswith('/')]),
            "has_external_links": len([a for a in soup.find_all('a') if a.get('href', '').startswith('http') and not a.get('href', '').startswith('/')]),
            "content_density": round(words / max(len(soup.find_all('p')), 1), 2)
        }
        
        return quality_indicators
    
    async def _analyze_technical_seo(self, domain: str) -> Dict[str, Any]:
        """Analyze technical SEO aspects"""
        try:
            async with self.session.get(domain) as response:
                headers = response.headers
                
                technical_seo = {
                    "http_status": response.status,
                    "https_enabled": str(response.url).startswith('https'),
                    "mobile_friendly": self._check_mobile_friendliness(headers),
                    "compression_enabled": self._check_compression(headers),
                    "caching_enabled": self._check_caching(headers),
                    "security_headers": self._check_security_headers(headers),
                    "performance_indicators": self._check_performance_indicators(headers)
                }
                
                return technical_seo
                
        except Exception as e:
            logger.warning(f"Failed to analyze technical SEO for {domain}: {e}")
            return {}
    
    def _check_mobile_friendliness(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check mobile-friendliness indicators"""
        viewport_meta = headers.get('X-Viewport-Meta', '')
        
        return {
            "has_viewport_meta": bool(viewport_meta),
            "viewport_content": viewport_meta,
            "mobile_optimized": "width=device-width" in viewport_meta.lower()
        }
    
    def _check_compression(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check compression settings"""
        content_encoding = headers.get('Content-Encoding', '')
        
        return {
            "compression_enabled": bool(content_encoding),
            "compression_type": content_encoding,
            "gzip_enabled": 'gzip' in content_encoding.lower(),
            "brotli_enabled": 'br' in content_encoding.lower()
        }
    
    def _check_caching(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check caching settings"""
        cache_control = headers.get('Cache-Control', '')
        expires = headers.get('Expires', '')
        
        return {
            "cache_control": cache_control,
            "expires": expires,
            "caching_enabled": bool(cache_control or expires),
            "max_age": self._extract_max_age(cache_control)
        }
    
    def _extract_max_age(self, cache_control: str) -> Optional[int]:
        """Extract max-age from Cache-Control header"""
        match = re.search(r'max-age=(\d+)', cache_control)
        return int(match.group(1)) if match else None
    
    def _check_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check security headers"""
        return {
            "x_frame_options": headers.get('X-Frame-Options', ''),
            "x_content_type_options": headers.get('X-Content-Type-Options', ''),
            "x_xss_protection": headers.get('X-XSS-Protection', ''),
            "strict_transport_security": headers.get('Strict-Transport-Security', ''),
            "content_security_policy": headers.get('Content-Security-Policy', ''),
            "referrer_policy": headers.get('Referrer-Policy', '')
        }
    
    def _check_performance_indicators(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Check performance-related headers"""
        return {
            "keep_alive": headers.get('Connection', '') == 'keep-alive',
            "transfer_encoding": headers.get('Transfer-Encoding', ''),
            "content_length": headers.get('Content-Length', ''),
            "server_timing": headers.get('Server-Timing', '')
        }
    
    def _calculate_landscape_metrics(self, domain: str, competitor_analyses: List[Dict]) -> Dict[str, Any]:
        """Calculate competitive landscape metrics"""
        if not competitor_analyses:
            return {}
        
        try:
            # Calculate averages across competitors
            total_competitors = len(competitor_analyses)
            
            # Content metrics
            avg_word_count = sum(
                comp.get('content_analysis', {}).get('content_quality_indicators', {}).get('word_count', 0)
                for comp in competitor_analyses
            ) / total_competitors
            
            # Technical metrics
            https_enabled_count = sum(
                1 for comp in competitor_analyses
                if comp.get('technical_seo', {}).get('https_enabled', False)
            )
            
            mobile_friendly_count = sum(
                1 for comp in competitor_analyses
                if comp.get('technical_seo', {}).get('mobile_friendly', {}).get('mobile_optimized', False)
            )
            
            # Engagement metrics
            engagement_elements = {}
            for comp in competitor_analyses:
                elements = comp.get('content_analysis', {}).get('engagement_elements', {})
                for key, value in elements.items():
                    if key not in engagement_elements:
                        engagement_elements[key] = 0
                    if value:
                        engagement_elements[key] += 1
            
            # Calculate percentages
            engagement_percentages = {
                key: round((value / total_competitors) * 100, 2)
                for key, value in engagement_elements.items()
            }
            
            return {
                "total_competitors": total_competitors,
                "average_word_count": round(avg_word_count, 0),
                "https_adoption_rate": round((https_enabled_count / total_competitors) * 100, 2),
                "mobile_optimization_rate": round((mobile_friendly_count / total_competitors) * 100, 2),
                "engagement_element_adoption": engagement_percentages,
                "competitive_gaps": self._identify_competitive_gaps(domain, competitor_analyses)
            }
            
        except Exception as e:
            logger.error(f"Error calculating landscape metrics: {e}")
            return {}
    
    def _identify_competitive_gaps(self, domain: str, competitor_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Identify gaps where competitors outperform the target domain"""
        gaps = []
        
        # This would require comparing against the target domain's metrics
        # For now, return common competitive advantages
        
        common_advantages = [
            "High-quality content with 1000+ words",
            "Mobile-optimized design",
            "Fast loading times",
            "Comprehensive internal linking",
            "Rich media content (videos, infographics)",
            "User-generated content (reviews, comments)",
            "Advanced schema markup",
            "Social proof elements"
        ]
        
        for advantage in common_advantages:
            gaps.append({
                "gap_type": "content_quality",
                "description": advantage,
                "priority": "medium",
                "estimated_effort": "2-4 weeks"
            })
        
        return gaps
    
    async def _analyze_deep_metrics(self, domain: str, competitor_domains: List[str]) -> Dict[str, Any]:
        """Perform deep competitor analysis using Playwright"""
        try:
            # This would use Playwright for deeper analysis
            # For now, return a placeholder
            return {
                "deep_analysis_status": "not_implemented",
                "note": "Deep analysis requires Playwright integration for JavaScript rendering and user interaction testing"
            }
            
        except Exception as e:
            logger.error(f"Error in deep metrics analysis: {e}")
            return {"error": str(e)}
