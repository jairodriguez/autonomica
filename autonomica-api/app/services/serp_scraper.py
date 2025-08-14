"""
SERP Scraping Service using Playwright

This module provides comprehensive SERP (Search Engine Results Page) scraping capabilities:
- Google search results scraping
- Featured snippet extraction
- People Also Ask (PAA) questions
- Related searches
- Top-ranking content analysis
- Anti-bot detection handling
- Structured data extraction
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import hashlib

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from bs4 import BeautifulSoup
import aiohttp

from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

@dataclass
class SERPResult:
    """Data structure for individual SERP result"""
    title: str
    url: str
    snippet: str
    position: int
    domain: str
    featured_snippet: bool = False
    rich_snippet: bool = False
    structured_data: Optional[Dict[str, Any]] = None

@dataclass
class SERPFeatures:
    """Data structure for SERP features"""
    featured_snippet: Optional[Dict[str, Any]] = None
    people_also_ask: List[str] = None
    related_searches: List[str] = None
    knowledge_panel: Optional[Dict[str, Any]] = None
    shopping_results: List[Dict[str, Any]] = None
    video_results: List[Dict[str, Any]] = None
    news_results: List[Dict[str, Any]] = None

@dataclass
class SERPData:
    """Complete SERP data structure"""
    keyword: str
    total_results: int
    results: List[SERPResult]
    features: SERPFeatures
    scraped_at: datetime
    search_url: str
    country: str
    language: str

class SERPScraper:
    """SERP scraping service using Playwright"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # User agent rotation for anti-bot detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        
        # Search engine configurations
        self.search_engines = {
            "google": {
                "base_url": "https://www.google.com",
                "search_path": "/search",
                "selectors": {
                    "results": "div.g",
                    "title": "h3",
                    "url": "a[href]",
                    "snippet": "div.VwiC3b",
                    "featured_snippet": "div.xpd",
                    "people_also_ask": "div.related-question-pair",
                    "related_searches": "div.brs_col a",
                    "knowledge_panel": "div.kp-wholepage"
                }
            },
            "bing": {
                "base_url": "https://www.bing.com",
                "search_path": "/search",
                "selectors": {
                    "results": "li.b_algo",
                    "title": "h2 a",
                    "url": "h2 a[href]",
                    "snippet": "div.b_caption p",
                    "featured_snippet": "div.b_attribution",
                    "people_also_ask": "div.b_rs",
                    "related_searches": "div.b_rs a",
                    "knowledge_panel": "div.b_attribution"
                }
            }
        }
        
        # Rate limiting and delays
        self.delays = {
            "page_load": 2,
            "scroll_pause": 1,
            "between_requests": 3
        }
        
        # Caching configuration
        self.cache_ttl = 3600 * 6  # 6 hours
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with anti-detection measures
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-zygote"
            ]
        )
        
        # Create context with stealth settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.user_agents[0],
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _get_cached_serp(self, keyword: str, country: str, search_engine: str = "google") -> Optional[SERPData]:
        """Retrieve cached SERP data"""
        cache_key = f"serp:{search_engine}:{country}:{hashlib.md5(keyword.encode()).hexdigest()}"
        
        try:
            cached = await self.redis_service.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Convert string dates back to datetime objects
                data["scraped_at"] = datetime.fromisoformat(data["scraped_at"])
                return SERPData(**data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached SERP data: {e}")
        
        return None
    
    async def _cache_serp_data(self, serp_data: SERPData, search_engine: str = "google") -> bool:
        """Cache SERP data"""
        cache_key = f"serp:{search_engine}:{serp_data.country}:{hashlib.md5(serp_data.keyword.encode()).hexdigest()}"
        
        try:
            # Convert datetime to string for JSON serialization
            data_dict = serp_data.__dict__.copy()
            data_dict["scraped_at"] = data_dict["scraped_at"].isoformat()
            
            await self.redis_service.set(
                cache_key,
                json.dumps(data_dict),
                expire=self.cache_ttl
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to cache SERP data: {e}")
            return False
    
    async def _rotate_user_agent(self, page: Page):
        """Rotate user agent to avoid detection"""
        import random
        user_agent = random.choice(self.user_agents)
        await page.set_extra_http_headers({"User-Agent": user_agent})
    
    async def _handle_anti_bot_detection(self, page: Page) -> bool:
        """Handle potential anti-bot detection"""
        try:
            # Check for common anti-bot indicators
            captcha_selectors = [
                "iframe[src*='recaptcha']",
                "div.g-recaptcha",
                "div#captcha",
                "form[action*='captcha']"
            ]
            
            for selector in captcha_selectors:
                if await page.query_selector(selector):
                    logger.warning("Captcha detected, waiting for manual intervention")
                    await asyncio.sleep(10)  # Wait for potential manual solving
                    return True
            
            # Check for suspicious activity warnings
            suspicious_text = await page.query_selector("text='unusual traffic'")
            if suspicious_text:
                logger.warning("Unusual traffic detected, implementing delays")
                await asyncio.sleep(30)
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Anti-bot detection check failed: {e}")
            return False
    
    async def _scroll_page(self, page: Page):
        """Scroll page to load dynamic content"""
        try:
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.delays["scroll_pause"])
            
            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(self.delays["scroll_pause"])
            
        except Exception as e:
            logger.warning(f"Page scrolling failed: {e}")
    
    async def _extract_google_results(self, page: Page, keyword: str) -> Tuple[List[SERPResult], SERPFeatures]:
        """Extract results from Google SERP"""
        results = []
        features = SERPFeatures()
        
        try:
            # Wait for results to load
            await page.wait_for_selector("div.g", timeout=10000)
            
            # Extract organic results
            result_elements = await page.query_selector_all("div.g")
            
            for i, element in enumerate(result_elements):
                try:
                    title_element = await element.query_selector("h3")
                    url_element = await element.query_selector("a[href]")
                    snippet_element = await element.query_selector("div.VwiC3b")
                    
                    if title_element and url_element:
                        title = await title_element.inner_text()
                        url = await url_element.get_attribute("href")
                        
                        # Filter out non-organic results
                        if url and not url.startswith(("javascript:", "#", "/search")):
                            snippet = ""
                            if snippet_element:
                                snippet = await snippet_element.inner_text()
                            
                            domain = urlparse(url).netloc
                            
                            result = SERPResult(
                                title=title.strip(),
                                url=url,
                                snippet=snippet.strip(),
                                position=i + 1,
                                domain=domain,
                                featured_snippet=False
                            )
                            results.append(result)
                
                except Exception as e:
                    logger.warning(f"Failed to extract result {i}: {e}")
                    continue
            
            # Extract featured snippet
            featured_snippet = await page.query_selector("div.xpd")
            if featured_snippet:
                try:
                    title = await featured_snippet.query_selector("h3")
                    snippet = await featured_snippet.query_selector("div.VwiC3b")
                    
                    if title and snippet:
                        features.featured_snippet = {
                            "title": await title.inner_text(),
                            "snippet": await snippet.inner_text()
                        }
                except Exception as e:
                    logger.warning(f"Failed to extract featured snippet: {e}")
            
            # Extract People Also Ask
            paa_elements = await page.query_selector_all("div.related-question-pair")
            for element in paa_elements:
                try:
                    question = await element.query_selector("div.q-box span")
                    if question:
                        features.people_also_ask.append(await question.inner_text())
                except Exception as e:
                    logger.warning(f"Failed to extract PAA question: {e}")
            
            # Extract related searches
            related_elements = await page.query_selector_all("div.brs_col a")
            for element in related_elements:
                try:
                    related_search = await element.inner_text()
                    features.related_searches.append(related_search.strip())
                except Exception as e:
                    logger.warning(f"Failed to extract related search: {e}")
            
            # Extract knowledge panel
            knowledge_panel = await page.query_selector("div.kp-wholepage")
            if knowledge_panel:
                try:
                    features.knowledge_panel = {
                        "exists": True,
                        "content": await knowledge_panel.inner_text()
                    }
                except Exception as e:
                    logger.warning(f"Failed to extract knowledge panel: {e}")
            
        except Exception as e:
            logger.error(f"Failed to extract Google results: {e}")
        
        return results, features
    
    async def _extract_bing_results(self, page: Page, keyword: str) -> Tuple[List[SERPResult], SERPFeatures]:
        """Extract results from Bing SERP"""
        results = []
        features = SERPFeatures()
        
        try:
            # Wait for results to load
            await page.wait_for_selector("li.b_algo", timeout=10000)
            
            # Extract organic results
            result_elements = await page.query_selector_all("li.b_algo")
            
            for i, element in enumerate(result_elements):
                try:
                    title_element = await element.query_selector("h2 a")
                    snippet_element = await element.query_selector("div.b_caption p")
                    
                    if title_element:
                        title = await title_element.inner_text()
                        url = await title_element.get_attribute("href")
                        
                        if url and not url.startswith(("javascript:", "#", "/search")):
                            snippet = ""
                            if snippet_element:
                                snippet = await snippet_element.inner_text()
                            
                            domain = urlparse(url).netloc
                            
                            result = SERPResult(
                                title=title.strip(),
                                url=url,
                                snippet=snippet.strip(),
                                position=i + 1,
                                domain=domain,
                                featured_snippet=False
                            )
                            results.append(result)
                
                except Exception as e:
                    logger.warning(f"Failed to extract Bing result {i}: {e}")
                    continue
            
            # Extract Bing-specific features
            # Note: Bing has different selectors and features than Google
            
        except Exception as e:
            logger.error(f"Failed to extract Bing results: {e}")
        
        return results, features
    
    async def scrape_serp(self, keyword: str, country: str = "us", 
                          search_engine: str = "google", max_results: int = 20) -> SERPData:
        """
        Scrape SERP data for a given keyword
        
        Args:
            keyword: Target keyword to search
            country: Country for localized results
            search_engine: Search engine to use (google, bing)
            max_results: Maximum number of results to extract
        
        Returns:
            Complete SERP data
        """
        # Check cache first
        cached_data = await self._get_cached_serp(keyword, country, search_engine)
        if cached_data:
            logger.info(f"Retrieved cached SERP data for '{keyword}'")
            return cached_data
        
        if search_engine not in self.search_engines:
            raise ValueError(f"Unsupported search engine: {search_engine}")
        
        engine_config = self.search_engines[search_engine]
        
        try:
            # Create new page
            page = await self.context.new_page()
            
            # Rotate user agent
            await self._rotate_user_agent(page)
            
            # Set viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Construct search URL
            search_params = {
                "q": keyword,
                "hl": "en",
                "gl": country,
                "num": max_results
            }
            
            search_url = f"{engine_config['base_url']}{engine_config['search_path']}?{self._build_query_string(search_params)}"
            
            logger.info(f"Scraping SERP for '{keyword}' from {search_url}")
            
            # Navigate to search page
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(self.delays["page_load"])
            
            # Handle anti-bot detection
            if await self._handle_anti_bot_detection(page):
                logger.info("Anti-bot measures applied, continuing...")
            
            # Scroll page to load dynamic content
            await self._scroll_page(page)
            
            # Extract results based on search engine
            if search_engine == "google":
                results, features = await self._extract_google_results(page, keyword)
            elif search_engine == "bing":
                results, features = await self._extract_bing_results(page, keyword)
            else:
                results, features = [], SERPFeatures()
            
            # Limit results
            results = results[:max_results]
            
            # Get total results count
            total_results = 0
            try:
                if search_engine == "google":
                    stats_element = await page.query_selector("div#result-stats")
                    if stats_element:
                        stats_text = await stats_element.inner_text()
                        # Extract number from "About X results" text
                        match = re.search(r"About\s+([\d,]+)\s+results", stats_text)
                        if match:
                            total_results = int(match.group(1).replace(",", ""))
                elif search_engine == "bing":
                    stats_element = await page.query_selector("span.sb_count")
                    if stats_element:
                        stats_text = await stats_element.inner_text()
                        # Extract number from "X results" text
                        match = re.search(r"([\d,]+)\s+results", stats_text)
                        if match:
                            total_results = int(match.group(1).replace(",", ""))
            except Exception as e:
                logger.warning(f"Failed to extract total results count: {e}")
            
            # Create SERP data object
            serp_data = SERPData(
                keyword=keyword,
                total_results=total_results,
                results=results,
                features=features,
                scraped_at=datetime.now(),
                search_url=search_url,
                country=country,
                language="en"
            )
            
            # Cache the data
            await self._cache_serp_data(serp_data, search_engine)
            
            logger.info(f"Successfully scraped {len(results)} results for '{keyword}'")
            
            return serp_data
            
        except Exception as e:
            logger.error(f"SERP scraping failed for '{keyword}': {e}")
            # Return minimal data on failure
            return SERPData(
                keyword=keyword,
                total_results=0,
                results=[],
                features=SERPFeatures(),
                scraped_at=datetime.now(),
                search_url="",
                country=country,
                language="en"
            )
        
        finally:
            if 'page' in locals():
                await page.close()
    
    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """Build URL query string from parameters"""
        return "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
    
    async def batch_scrape_keywords(self, keywords: List[str], country: str = "us",
                                   search_engine: str = "google", max_results: int = 20) -> Dict[str, SERPData]:
        """
        Scrape SERP data for multiple keywords
        
        Args:
            keywords: List of keywords to scrape
            country: Country for localized results
            search_engine: Search engine to use
            max_results: Maximum results per keyword
        
        Returns:
            Dictionary mapping keywords to SERP data
        """
        results = {}
        
        for i, keyword in enumerate(keywords):
            try:
                logger.info(f"Scraping keyword {i+1}/{len(keywords)}: '{keyword}'")
                
                serp_data = await self.scrape_serp(
                    keyword=keyword,
                    country=country,
                    search_engine=search_engine,
                    max_results=max_results
                )
                
                results[keyword] = serp_data
                
                # Add delay between requests
                if i < len(keywords) - 1:
                    await asyncio.sleep(self.delays["between_requests"])
                
            except Exception as e:
                logger.error(f"Failed to scrape keyword '{keyword}': {e}")
                # Add empty result for failed keywords
                results[keyword] = SERPData(
                    keyword=keyword,
                    total_results=0,
                    results=[],
                    features=SERPFeatures(),
                    scraped_at=datetime.now(),
                    search_url="",
                    country=country,
                    language="en"
                )
        
        return results
    
    async def get_competitor_domains(self, keyword: str, country: str = "us",
                                    search_engine: str = "google", top_n: int = 10) -> List[str]:
        """
        Extract competitor domains from SERP results
        
        Args:
            keyword: Target keyword
            country: Country for localized results
            search_engine: Search engine to use
            top_n: Number of top results to analyze
        
        Returns:
            List of competitor domains
        """
        try:
            serp_data = await self.scrape_serp(keyword, country, search_engine, top_n)
            
            # Extract unique domains from top results
            domains = []
            for result in serp_data.results[:top_n]:
                if result.domain not in domains:
                    domains.append(result.domain)
            
            return domains
            
        except Exception as e:
            logger.error(f"Failed to get competitor domains for '{keyword}': {e}")
            return []
    
    async def analyze_serp_features(self, keyword: str, country: str = "us",
                                   search_engine: str = "google") -> Dict[str, Any]:
        """
        Analyze SERP features for a keyword
        
        Args:
            keyword: Target keyword
            country: Country for localized results
            search_engine: Search engine to use
        
        Returns:
            Dictionary with SERP feature analysis
        """
        try:
            serp_data = await self.scrape_serp(keyword, country, search_engine)
            
            analysis = {
                "keyword": keyword,
                "total_results": serp_data.total_results,
                "has_featured_snippet": serp_data.features.featured_snippet is not None,
                "has_people_also_ask": len(serp_data.features.people_also_ask) > 0,
                "has_knowledge_panel": serp_data.features.knowledge_panel is not None,
                "people_also_ask_count": len(serp_data.features.people_also_ask),
                "related_searches_count": len(serp_data.features.related_searches),
                "top_domains": [result.domain for result in serp_data.results[:5]],
                "featured_snippet_text": serp_data.features.featured_snippet.get("snippet") if serp_data.features.featured_snippet else None,
                "people_also_ask_questions": serp_data.features.people_also_ask[:5],
                "related_searches": serp_data.features.related_searches[:5]
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze SERP features for '{keyword}': {e}")
            return {
                "keyword": keyword,
                "error": str(e)
            }