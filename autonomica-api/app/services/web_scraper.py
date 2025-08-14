"""
Web Scraping Module for SEO Research and Content Analysis.

This module provides comprehensive web scraping capabilities using Playwright:
- SERP analysis and featured snippet extraction
- Content structure analysis
- Anti-bot detection handling
- Structured data extraction
- Content quality assessment
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from datetime import datetime

from loguru import logger


@dataclass
class SERPFeature:
    """Represents a SERP feature found in search results."""
    feature_type: str  # featured_snippet, people_also_ask, related_searches, etc.
    content: str
    position: int
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    position: int
    domain: str
    featured_snippet: bool = False
    rich_snippet: bool = False
    structured_data: Optional[Dict[str, Any]] = None


@dataclass
class SERPData:
    """Complete SERP analysis data."""
    query: str
    total_results: int
    search_time: float
    results: List[SearchResult]
    features: List[SERPFeature]
    related_searches: List[str]
    people_also_ask: List[str]
    timestamp: datetime
    user_agent: str


class WebScraper:
    """
    Advanced web scraper using Playwright for SEO research.
    
    Features:
    - SERP analysis with feature detection
    - Content extraction and analysis
    - Anti-bot detection handling
    - Structured data extraction
    - Rate limiting and rotation
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize web scraper.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        
        # User agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        # Rate limiting
        self.min_delay = 2.0  # Minimum delay between requests
        self.max_delay = 5.0   # Maximum delay between requests
        self.last_request_time = 0
        
        logger.info("Web scraper initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _setup_browser(self):
        """Set up Playwright browser and context."""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create context with custom user agent
            user_agent = self._get_random_user_agent()
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set extra headers
            await self.page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Set timeout
            self.page.set_default_timeout(self.timeout)
            
            logger.info("Browser setup completed successfully")
            
        except ImportError:
            logger.error("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            raise
    
    async def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the rotation."""
        import random
        return random.choice(self.user_agents)
    
    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            delay = self.min_delay - time_since_last
            await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
    
    async def scrape_google_serp(self, query: str, country: str = "us", language: str = "en") -> SERPData:
        """
        Scrape Google search results page.
        
        Args:
            query: Search query
            country: Country code for localized results
            language: Language code
            
        Returns:
            SERPData object with comprehensive analysis
        """
        await self._rate_limit()
        
        start_time = time.time()
        
        # Construct Google search URL
        search_url = self._build_google_search_url(query, country, language)
        
        try:
            logger.info(f"Scraping Google SERP for query: {query}")
            
            # Navigate to search page
            await self.page.goto(search_url, wait_until='networkidle')
            
            # Wait for results to load
            await self.page.wait_for_selector('#search', timeout=10000)
            
            # Extract search results
            results = await self._extract_search_results()
            
            # Extract SERP features
            features = await self._extract_serp_features()
            
            # Extract related searches
            related_searches = await self._extract_related_searches()
            
            # Extract people also ask
            people_also_ask = await self._extract_people_also_ask()
            
            # Get total results count
            total_results = await self._extract_total_results()
            
            search_time = time.time() - start_time
            
            serp_data = SERPData(
                query=query,
                total_results=total_results,
                search_time=search_time,
                results=results,
                features=features,
                related_searches=related_searches,
                people_also_ask=people_also_ask,
                timestamp=datetime.now(),
                user_agent=self._get_random_user_agent()
            )
            
            logger.info(f"SERP scraping completed in {search_time:.2f}s")
            return serp_data
            
        except Exception as e:
            logger.error(f"Failed to scrape Google SERP: {e}")
            raise
    
    def _build_google_search_url(self, query: str, country: str, language: str) -> str:
        """Build Google search URL with parameters."""
        base_url = "https://www.google.com/search"
        params = {
            'q': query,
            'hl': language,
            'gl': country,
            'num': '10',  # Number of results
            'safe': 'off',
            'source': 'hp'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def _extract_search_results(self) -> List[SearchResult]:
        """Extract search results from the page."""
        results = []
        
        try:
            # Find all search result containers
            result_elements = await self.page.query_selector_all('#search .g')
            
            for i, element in enumerate(result_elements):
                try:
                    # Extract title
                    title_element = await element.query_selector('h3')
                    title = await title_element.text_content() if title_element else "No title"
                    
                    # Extract URL
                    link_element = await element.query_selector('a')
                    url = await link_element.get_attribute('href') if link_element else ""
                    
                    # Clean URL
                    if url and url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    # Extract snippet
                    snippet_element = await element.query_selector('.VwiC3b')
                    snippet = await snippet_element.text_content() if snippet_element else "No snippet"
                    
                    # Extract domain
                    domain = urlparse(url).netloc if url else ""
                    
                    # Check if it's a featured snippet
                    featured_snippet = await element.query_selector('.ULSxyf') is not None
                    
                    # Check for rich snippets
                    rich_snippet = await element.query_selector('[data-ved]') is not None
                    
                    # Extract structured data if available
                    structured_data = await self._extract_structured_data(element)
                    
                    result = SearchResult(
                        title=title.strip(),
                        url=url,
                        snippet=snippet.strip(),
                        position=i + 1,
                        domain=domain,
                        featured_snippet=featured_snippet,
                        rich_snippet=rich_snippet,
                        structured_data=structured_data
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract result {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to extract search results: {e}")
        
        return results
    
    async def _extract_serp_features(self) -> List[SERPFeature]:
        """Extract SERP features like featured snippets, knowledge panels, etc."""
        features = []
        
        try:
            # Featured snippet
            featured_snippet = await self.page.query_selector('.ULSxyf')
            if featured_snippet:
                content = await featured_snippet.text_content()
                features.append(SERPFeature(
                    feature_type="featured_snippet",
                    content=content.strip() if content else "",
                    position=1
                ))
            
            # Knowledge panel
            knowledge_panel = await self.page.query_selector('[data-ved]')
            if knowledge_panel:
                content = await knowledge_panel.text_content()
                features.append(SERPFeature(
                    feature_type="knowledge_panel",
                    content=content.strip() if content else "",
                    position=2
                ))
            
            # Local pack
            local_pack = await self.page.query_selector('[data-ved][data-ved]')
            if local_pack:
                content = await local_pack.text_content()
                features.append(SERPFeature(
                    feature_type="local_pack",
                    content=content.strip() if content else "",
                    position=3
                ))
            
            # Shopping results
            shopping_results = await self.page.query_selector('[data-ved][data-ved][data-ved]')
            if shopping_results:
                content = await shopping_results.text_content()
                features.append(SERPFeature(
                    feature_type="shopping_results",
                    content=content.strip() if content else "",
                    position=4
                ))
            
        except Exception as e:
            logger.error(f"Failed to extract SERP features: {e}")
        
        return features
    
    async def _extract_related_searches(self) -> List[str]:
        """Extract related searches from the bottom of the page."""
        related_searches = []
        
        try:
            # Look for related searches section
            related_section = await self.page.query_selector('#bres')
            if related_section:
                search_links = await related_section.query_selector_all('a')
                for link in search_links:
                    text = await link.text_content()
                    if text:
                        related_searches.append(text.strip())
            
            # Also check for "Searches related to" section
            related_text = await self.page.query_selector('p:has-text("Searches related to")')
            if related_text:
                parent = await related_text.query_selector('xpath=..')
                if parent:
                    links = await parent.query_selector_all('a')
                    for link in links:
                        text = await link.text_content()
                        if text:
                            related_searches.append(text.strip())
            
        except Exception as e:
            logger.error(f"Failed to extract related searches: {e}")
        
        return list(set(related_searches))  # Remove duplicates
    
    async def _extract_people_also_ask(self) -> List[str]:
        """Extract 'People also ask' questions."""
        questions = []
        
        try:
            # Look for people also ask section
            paa_section = await self.page.query_selector('[jsname="NpkX8b"]')
            if paa_section:
                question_elements = await paa_section.query_selector_all('[jsname="8bqA6e"]')
                for element in question_elements:
                    question_text = await element.text_content()
                    if question_text:
                        questions.append(question_text.strip())
            
        except Exception as e:
            logger.error(f"Failed to extract people also ask: {e}")
        
        return questions
    
    async def _extract_total_results(self) -> int:
        """Extract total number of search results."""
        try:
            # Look for result stats
            stats_element = await self.page.query_selector('#result-stats')
            if stats_element:
                stats_text = await stats_element.text_content()
                if stats_text:
                    # Extract number from text like "About 1,000,000,000 results"
                    match = re.search(r'About\s+([\d,]+)', stats_text)
                    if match:
                        return int(match.group(1).replace(',', ''))
            
            return len(await self.page.query_selector_all('#search .g'))
            
        except Exception as e:
            logger.error(f"Failed to extract total results: {e}")
            return 0
    
    async def _extract_structured_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract structured data from a search result element."""
        try:
            # Look for JSON-LD structured data
            script_elements = await element.query_selector_all('script[type="application/ld+json"]')
            for script in script_elements:
                content = await script.text_content()
                if content:
                    try:
                        data = json.loads(content)
                        return data
                    except json.JSONDecodeError:
                        continue
            
            # Look for microdata
            microdata = await element.query_selector('[itemtype]')
            if microdata:
                itemtype = await microdata.get_attribute('itemtype')
                return {"itemtype": itemtype}
            
        except Exception as e:
            logger.debug(f"Failed to extract structured data: {e}")
        
        return None
    
    async def scrape_website_content(self, url: str, extract_text: bool = True) -> Dict[str, Any]:
        """
        Scrape content from a specific website.
        
        Args:
            url: URL to scrape
            extract_text: Whether to extract text content
            
        Returns:
            Dictionary with scraped content and metadata
        """
        await self._rate_limit()
        
        try:
            logger.info(f"Scraping website: {url}")
            
            # Navigate to the page
            await self.page.goto(url, wait_until='networkidle')
            
            # Wait for content to load
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Extract page metadata
            metadata = await self._extract_page_metadata()
            
            # Extract text content if requested
            content = {}
            if extract_text:
                content = await self._extract_page_content()
            
            # Extract structured data
            structured_data = await self._extract_page_structured_data()
            
            # Extract links
            links = await self._extract_page_links()
            
            result = {
                "url": url,
                "metadata": metadata,
                "content": content,
                "structured_data": structured_data,
                "links": links,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Website scraping completed: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to scrape website {url}: {e}")
            raise
    
    async def _extract_page_metadata(self) -> Dict[str, Any]:
        """Extract page metadata."""
        metadata = {}
        
        try:
            # Title
            title = await self.page.title()
            metadata["title"] = title
            
            # Meta description
            meta_desc = await self.page.query_selector('meta[name="description"]')
            if meta_desc:
                metadata["description"] = await meta_desc.get_attribute('content')
            
            # Meta keywords
            meta_keywords = await self.page.query_selector('meta[name="keywords"]')
            if meta_keywords:
                metadata["keywords"] = await meta_keywords.get_attribute('content')
            
            # Canonical URL
            canonical = await self.page.query_selector('link[rel="canonical"]')
            if canonical:
                metadata["canonical"] = await canonical.get_attribute('href')
            
            # Open Graph tags
            og_tags = await self.page.query_selector_all('meta[property^="og:"]')
            for tag in og_tags:
                property_name = await tag.get_attribute('property')
                content = await tag.get_attribute('content')
                if property_name and content:
                    metadata[property_name] = content
            
            # Twitter Card tags
            twitter_tags = await self.page.query_selector_all('meta[name^="twitter:"]')
            for tag in twitter_tags:
                name = await tag.get_attribute('name')
                content = await tag.get_attribute('content')
                if name and content:
                    metadata[name] = content
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
        
        return metadata
    
    async def _extract_page_content(self) -> Dict[str, Any]:
        """Extract page content."""
        content = {}
        
        try:
            # Main content
            main_content = await self.page.query_selector('main, [role="main"], .main, #main, #content')
            if main_content:
                content["main"] = await main_content.text_content()
            
            # Headings
            headings = await self.page.query_selector_all('h1, h2, h3, h4, h5, h6')
            content["headings"] = []
            for heading in headings:
                text = await heading.text_content()
                tag_name = await heading.evaluate('el => el.tagName.toLowerCase()')
                content["headings"].append({
                    "level": tag_name,
                    "text": text.strip() if text else ""
                })
            
            # Paragraphs
            paragraphs = await self.page.query_selector_all('p')
            content["paragraphs"] = []
            for p in paragraphs:
                text = await p.text_content()
                if text and len(text.strip()) > 50:  # Only meaningful paragraphs
                    content["paragraphs"].append(text.strip())
            
            # Lists
            lists = await self.page.query_selector_all('ul, ol')
            content["lists"] = []
            for lst in lists:
                items = await lst.query_selector_all('li')
                list_items = []
                for item in items:
                    text = await item.text_content()
                    if text:
                        list_items.append(text.strip())
                if list_items:
                    content["lists"].append(list_items)
            
        except Exception as e:
            logger.error(f"Failed to extract content: {e}")
        
        return content
    
    async def _extract_page_structured_data(self) -> List[Dict[str, Any]]:
        """Extract structured data from the page."""
        structured_data = []
        
        try:
            # JSON-LD structured data
            script_elements = await self.page.query_selector_all('script[type="application/ld+json"]')
            for script in script_elements:
                content = await script.text_content()
                if content:
                    try:
                        data = json.loads(content)
                        structured_data.append({
                            "type": "json-ld",
                            "data": data
                        })
                    except json.JSONDecodeError:
                        continue
            
            # Microdata
            microdata_elements = await self.page.query_selector_all('[itemtype]')
            for element in microdata_elements:
                itemtype = await element.get_attribute('itemtype')
                itemprops = await element.query_selector_all('[itemprop]')
                props = {}
                for prop in itemprops:
                    name = await prop.get_attribute('itemprop')
                    content = await prop.get_attribute('content') or await prop.text_content()
                    if name and content:
                        props[name] = content.strip()
                
                if props:
                    structured_data.append({
                        "type": "microdata",
                        "itemtype": itemtype,
                        "properties": props
                    })
            
        except Exception as e:
            logger.error(f"Failed to extract structured data: {e}")
        
        return structured_data
    
    async def _extract_page_links(self) -> List[Dict[str, str]]:
        """Extract links from the page."""
        links = []
        
        try:
            link_elements = await self.page.query_selector_all('a[href]')
            for link in link_elements:
                href = await link.get_attribute('href')
                text = await link.text_content()
                
                if href and not href.startswith('#'):
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(self.page.url, href)
                    
                    # Compare domains to determine if link is external
                    current_domain = urlparse(self.page.url).netloc
                    link_domain = urlparse(absolute_url).netloc
                    is_external = current_domain != link_domain
                    
                    links.append({
                        "url": absolute_url,
                        "text": text.strip() if text else "",
                        "external": is_external
                    })
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
        
        return links
    
    async def get_page_screenshot(self, url: str, output_path: str = None) -> str:
        """
        Take a screenshot of a webpage.
        
        Args:
            url: URL to screenshot
            output_path: Path to save screenshot (optional)
            
        Returns:
            Path to saved screenshot
        """
        try:
            await self.page.goto(url, wait_until='networkidle')
            await self.page.wait_for_load_state('domcontentloaded')
            
            if not output_path:
                output_path = f"screenshot_{int(time.time())}.png"
            
            await self.page.screenshot(path=output_path, full_page=True)
            logger.info(f"Screenshot saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise


# Example usage and testing
async def test_web_scraper():
    """Test the web scraper functionality."""
    try:
        async with WebScraper(headless=True) as scraper:
            # Test Google SERP scraping
            serp_data = await scraper.scrape_google_serp("digital marketing")
            print(f"Scraped SERP for 'digital marketing'")
            print(f"Total results: {serp_data.total_results}")
            print(f"Search time: {serp_data.search_time:.2f}s")
            print(f"Results found: {len(serp_data.results)}")
            print(f"Features found: {len(serp_data.features)}")
            
            # Test website content scraping
            if serp_data.results:
                first_result = serp_data.results[0]
                content = await scraper.scrape_website_content(first_result.url)
                print(f"Scraped content from: {first_result.url}")
                print(f"Title: {content['metadata'].get('title', 'N/A')}")
                print(f"Description: {content['metadata'].get('description', 'N/A')[:100]}...")
                
    except Exception as e:
        logger.error(f"Web scraper test failed: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_web_scraper())