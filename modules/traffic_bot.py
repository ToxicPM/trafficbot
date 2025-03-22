import os
import time
import random
import string
import logging
import threading
import queue
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

class TrafficBot:
    """Main class for traffic generation bot."""
    
    def __init__(self, vpn_manager, browser_manager, scheduler):
        """Initialize the traffic bot with required components.
        
        Args:
            vpn_manager: VPN manager for IP rotation
            browser_manager: Browser manager for web automation
            scheduler: Traffic scheduler for timing
        """
        self.vpn_manager = vpn_manager
        self.browser_manager = browser_manager
        self.scheduler = scheduler
        
        # Bot settings
        self.keywords = []
        self.urls = []
        self.running = False
        self.paused = False
        self.worker_threads = []
        self.task_queue = queue.Queue()
        self.custom_tracking_urls = {}  # Map original URLs to tracking URLs
        
        # Statistics
        self.stats = {
            "visits": 0,
            "successful_visits": 0,
            "failed_visits": 0,
            "captchas_solved": 0,
            "start_time": None,
            "last_visit": None,
            "vpn_switches": 0,
            "proxy_switches": 0,
            "adsense_impressions": 0,
            "social_traffic": 0,
            "search_traffic": 0,
            "direct_traffic": 0,
            "referral_traffic": 0,
            "mobile_visits": 0,
            "desktop_visits": 0,
            "tablet_visits": 0
        }
    
    def load_keywords(self, keyword_file: str) -> None:
        """Load keywords from a file."""
        try:
            with open(keyword_file, 'r') as f:
                self.keywords = [line.strip() for line in f if line.strip()]
            activity_logger.info(f"Loaded {len(self.keywords)} keywords from {keyword_file}")
        except Exception as e:
            error_logger.error(f"Failed to load keywords: {str(e)}")
    
    def load_urls(self, url_file: str) -> None:
        """Load URLs from a file."""
        try:
            with open(url_file, 'r') as f:
                self.urls = [line.strip() for line in f if line.strip()]
            activity_logger.info(f"Loaded {len(self.urls)} URLs from {url_file}")
        except Exception as e:
            error_logger.error(f"Failed to load URLs: {str(e)}")
    
    def add_keyword(self, keyword: str) -> None:
        """Add a single keyword to the list."""
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
            activity_logger.info(f"Added keyword: {keyword}")
    
    def add_url(self, url: str) -> None:
        """Add a single URL to the list."""
        if url and url not in self.urls:
            self.urls.append(url)
            activity_logger.info(f"Added URL: {url}")
    
    def check_schedule(self) -> bool:
        """Check if we should generate traffic based on the scheduler."""
        if not self.scheduler.should_generate_traffic():
            activity_logger.info("Skipping traffic generation due to scheduling constraints")
            return False
        return True
    
    def search_google(self, keyword: str) -> List[str]:
        """Search Google for a keyword and return the results."""
        # Check if we should proceed based on scheduling
        if not self.check_schedule():
            return []
        
        results = []
        try:
            # Decide if we should use VPN or proxy
            use_vpn = False
            use_proxy = False
            
            # Randomly choose between VPN and proxy based on availability
            use_vpn_providers = [p for p in self.vpn_manager.vpn_providers 
                               if self.vpn_manager.vpn_providers[p]['enabled'] and 
                                  self.vpn_manager.vpn_providers[p]['regions']]
            
            if use_vpn_providers and random.random() > 0.5:
                # Use a VPN
                provider, region = self.vpn_manager.get_random_vpn()
                if provider and region:
                    self.vpn_manager.connect_vpn(provider, region)
                    use_vpn = True
                    self.stats["vpn_switches"] += 1
            
            if not use_vpn and self.vpn_manager.proxies and self.vpn_manager.use_proxies:
                # Use a proxy
                self.vpn_manager.get_random_proxy()
                use_proxy = True
                self.stats["proxy_switches"] += 1
            
            # Get driver with the proper configuration
            driver = self.browser_manager.get_driver(use_proxy=use_proxy)
            if not driver:
                return results
            
            # Search Google
            search_url = f"https://www.google.com/search?q={keyword.replace(' ', '+')}"
            activity_logger.info(f"Searching Google for: {keyword}")
            driver.get(search_url)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Check for CAPTCHA
            if "unusual traffic" in driver.page_source.lower() or "recaptcha" in driver.page_source.lower():
                activity_logger.info("CAPTCHA detected, attempting to solve...")
                solved = self.browser_manager.captcha_solver.detect_and_solve_captcha(driver)
                if solved:
                    self.stats["captchas_solved"] += 1
                    time.sleep(random.uniform(2, 4))
            
            # Extract search results
            try:
                links = driver.find_elements(By.CSS_SELECTOR, "div.g a")
            except:
                links = []
                
            if not links:
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, "a[jsname]")
                except:
                    links = []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "google.com" not in href:
                        results.append(href)
                except:
                    continue
            
            activity_logger.info(f"Found {len(results)} search results for: {keyword}")
            self.browser_manager.close_driver(driver)
            
            # Record the visit in scheduler
            self.scheduler.record_visit()
        
        except Exception as e:
            error_logger.error(f"Error searching Google for '{keyword}': {str(e)}")
            if 'driver' in locals():
                self.browser_manager.close_driver(driver)
        finally:
            # Disconnect VPN if using
            if use_vpn:
                self.vpn_manager.disconnect_all_vpns()
        
        return results
    
    def add_tracking_url(self, original_url: str, tracking_url: str) -> None:
        """Add a custom tracking URL that will be used instead of the original."""
        self.custom_tracking_urls[original_url] = tracking_url
        activity_logger.info(f"Added tracking URL: {tracking_url} for {original_url}")
    
    def get_tracking_url(self, url: str) -> str:
        """Get the tracking URL for a given original URL if it exists."""
        return self.custom_tracking_urls.get(url, url)
    
    def visit_url(self, url: str) -> bool:
        """Visit a URL and simulate human behavior."""
        # Check if we should proceed based on scheduling
        if not self.check_schedule():
            return False
        
        # Check if we have a custom tracking URL for this URL
        tracking_url = self.get_tracking_url(url)
        if tracking_url != url:
            activity_logger.info(f"Using tracking URL: {tracking_url} instead of {url}")
            url = tracking_url
        
        self.stats["visits"] += 1
        self.stats["last_visit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Decide if we should use VPN or proxy
            use_vpn = False
            use_proxy = False
            
            # Randomly choose between VPN and proxy based on availability
            use_vpn_providers = [p for p in self.vpn_manager.vpn_providers 
                               if self.vpn_manager.vpn_providers[p]['enabled'] and 
                                  self.vpn_manager.vpn_providers[p]['regions']]
            
            if use_vpn_providers and random.random() > 0.5:
                # Use a VPN
                provider, region = self.vpn_manager.get_random_vpn()
                if provider and region:
                    self.vpn_manager.connect_vpn(provider, region)
                    use_vpn = True
                    self.stats["vpn_switches"] += 1
            
            if not use_vpn and self.vpn_manager.proxies and self.vpn_manager.use_proxies:
                # Use a proxy
                self.vpn_manager.get_random_proxy()
                use_proxy = True
                self.stats["proxy_switches"] += 1
            
            # Select a device type based on behavior profile
            device_type = self.browser_manager.behavior_profile.get_random_device()
            
            # Update device type stats
            if device_type == "desktop":
                self.stats["desktop_visits"] += 1
            elif device_type == "mobile":
                self.stats["mobile_visits"] += 1
            elif device_type == "tablet":
                self.stats["tablet_visits"] += 1
            
            # Get driver with the proper configuration
            driver = self.browser_manager.get_driver(use_proxy=use_proxy, device_type=device_type)
            if not driver:
                self.stats["failed_visits"] += 1
                return False
            
            # Track referrer type
            referrer_type = self.browser_manager.behavior_profile.get_random_referrer()
            if referrer_type.startswith("search_"):
                self.stats["search_traffic"] += 1
            elif referrer_type.startswith("social_"):
                self.stats["social_traffic"] += 1
            elif referrer_type == "direct":
                self.stats["direct_traffic"] += 1
            elif referrer_type == "referral":
                self.stats["referral_traffic"] += 1
            
            # Visit the URL
            activity_logger.info(f"Visiting URL: {url} with device type: {device_type}")
            driver.get(url)
            
            # Check if the page loaded properly
            if driver.title == "":
                error_logger.error(f"Failed to load page: {url}")
                self.browser_manager.close_driver(driver)
                self.stats["failed_visits"] += 1
                return False
            
            # Check for CAPTCHA
            if "unusual traffic" in driver.page_source.lower() or "recaptcha" in driver.page_source.lower():
                activity_logger.info("CAPTCHA detected, attempting to solve...")
                solved = self.browser_manager.captcha_solver.detect_and_solve_captcha(driver)
                if solved:
                    self.stats["captchas_solved"] += 1
                    time.sleep(random.uniform(2, 4))
            
            # Get visit duration from behavior profile
            min_duration, max_duration = self.browser_manager.behavior_profile.get_visit_duration()
            visit_duration = random.uniform(min_duration, max_duration)
            activity_logger.info(f"Planning to stay on site for {visit_duration:.1f} seconds")
            
            # Determine if this should be a bounce or full visit
            should_bounce = self.browser_manager.behavior_profile.should_bounce()
            
            if should_bounce:
                # Simulate a bounce - short visit with minimal interaction
                activity_logger.info("Simulating bounce visit")
                time.sleep(random.uniform(3, 8))
                
                # Minimal scroll
                scroll_amount = random.randint(100, 300)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1, 3))
                
                self.browser_manager.close_driver(driver)
                self.stats["successful_visits"] += 1
                
                # Record the visit in scheduler
                self.scheduler.record_visit()
                
                return True
            
            # Get number of subpages to visit
            subpage_count = self.browser_manager.behavior_profile.get_subpage_count()
            activity_logger.info(f"Planning to visit {subpage_count} subpage(s)")
            
            # Track visited URLs to avoid loops
            visited_urls = {url}
            current_url = url
            
            # Calculate time budget for main page and subpages
            if subpage_count > 0:
                main_page_time = visit_duration * 0.4  # Spend 40% on main page
                subpage_time = visit_duration * 0.6 / subpage_count  # Distribute rest to subpages
            else:
                main_page_time = visit_duration
                subpage_time = 0
            
            # Main page interaction
            self._interact_with_page(driver, main_page_time)
            
            # Subpage navigation
            for i in range(subpage_count):
                # Find links that we can click (internal and not visited yet)
                internal_links = self._find_internal_links(driver, current_url, visited_urls)
                
                if not internal_links:
                    activity_logger.info("No more internal links to visit")
                    break
                
                # Select a random link
                link_to_click = random.choice(internal_links)
                
                try:
                    href = link_to_click.get_attribute("href")
                    activity_logger.info(f"Navigating to subpage ({i+1}/{subpage_count}): {href}")
                    
                    # Record the current URL
                    current_url = href
                    visited_urls.add(href)
                    
                    # Click the link
                    link_to_click.click()
                    time.sleep(random.uniform(2, 4))
                    
                    # Interact with the subpage
                    self._interact_with_page(driver, subpage_time)
                    
                except Exception as e:
                    error_logger.error(f"Error navigating to subpage: {str(e)}")
                    continue
            
            # End the visit
            self.browser_manager.close_driver(driver)
            self.stats["successful_visits"] += 1
            activity_logger.info(f"Successfully completed visit to: {url}")
            
            # Record the visit in scheduler
            self.scheduler.record_visit()
            
            return True
            
        except Exception as e:
            error_logger.error(f"Error visiting '{url}': {str(e)}")
            if 'driver' in locals():
                self.browser_manager.close_driver(driver)
            self.stats["failed_visits"] += 1
            return False
        finally:
            # Disconnect VPN if using
            if use_vpn:
                self.vpn_manager.disconnect_all_vpns()
    
    def _avoid_adsense_clicks(self, driver: webdriver.Chrome) -> None:
        """Identify AdSense ads and avoid clicking on them."""
        try:
            # Common AdSense selectors
            ad_selectors = [
                "ins.adsbygoogle", 
                "iframe[id^='google_ads']",
                "div[id^='div-gpt-ad']",
                "div[class*='advert']",
                "div[class*='ad-container']"
            ]
            
            # Find all ad elements
            ad_elements = []
            for selector in ad_selectors:
                ad_elements.extend(driver.find_elements(By.CSS_SELECTOR, selector))
            
            if ad_elements:
                activity_logger.info(f"Found {len(ad_elements)} potential ads on page")
                self.stats["adsense_impressions"] += 1
                
                # Inject JS to create invisible barriers around ads to prevent accidental clicks
                for i, ad in enumerate(ad_elements):
                    try:
                        driver.execute_script("""
                            var ad = arguments[0];
                            var rect = ad.getBoundingClientRect();
                            var barrier = document.createElement('div');
                            barrier.style.position = 'absolute';
                            barrier.style.top = (rect.top - 10) + 'px';
                            barrier.style.left = (rect.left - 10) + 'px';
                            barrier.style.width = (rect.width + 20) + 'px';
                            barrier.style.height = (rect.height + 20) + 'px';
                            barrier.style.zIndex = '9999';
                            barrier.style.background = 'transparent';
                            barrier.style.pointerEvents = 'none';
                            barrier.setAttribute('data-ad-barrier', 'true');
                            document.body.appendChild(barrier);
                        """, ad)
                    except Exception:
                        continue
        
        except Exception as e:
            activity_logger.info(f"Error avoiding AdSense: {str(e)}")
    
    def _interact_with_page(self, driver: webdriver.Chrome, duration: float) -> None:
        """Simulate realistic user interaction with a page for the specified duration."""
        start_time = time.time()
        end_time = start_time + duration
        
        # Handle AdSense safely if enabled
        if hasattr(self.browser_manager.behavior_profile, 'adsense_safe') and self.browser_manager.behavior_profile.adsense_safe:
            self._avoid_adsense_clicks(driver)
        
        # Calculate number of interactions based on duration
        num_interactions = max(2, int(duration / 10))
        
        # Define possible interactions with their weights
        interactions = [
            ("scroll", 0.6),
            ("mouse_move", 0.2),
            ("click_nowhere", 0.1),
            ("form_interact", 0.1)
        ]
        
        for _ in range(num_interactions):
            # Stop if we've exceeded the duration
            if time.time() >= end_time:
                break
            
            # Select a random interaction
            interaction = random.choices(
                [i[0] for i in interactions],
                weights=[i[1] for i in interactions],
                k=1
            )[0]
            
            # Perform the interaction
            if interaction == "scroll":
                # Scroll down or up with varying speeds
                direction = random.choice(["down", "up"])
                speed = random.randint(100, 800)
                
                if direction == "down":
                    driver.execute_script(f"window.scrollBy(0, {speed});")
                else:
                    driver.execute_script(f"window.scrollBy(0, -{speed});")
            
            elif interaction == "mouse_move":
                # Simulate mouse movement (doesn't actually move in headless, but adds JS events)
                try:
                    x = random.randint(0, driver.execute_script("return window.innerWidth;"))
                    y = random.randint(0, driver.execute_script("return window.innerHeight;"))
                    
                    driver.execute_script(
                        f"var e = new MouseEvent('mousemove', {{'view': window, 'bubbles': true, "
                        f"'cancelable': true, 'clientX': {x}, 'clientY': {y}}}); "
                        f"document.dispatchEvent(e);"
                    )
                except Exception as e:
                    activity_logger.info(f"Mouse move error: {str(e)}")
            
            elif interaction == "click_nowhere":
                # Random click on page (not on a specific element)
                try:
                    x = random.randint(0, driver.execute_script("return window.innerWidth;"))
                    y = random.randint(0, driver.execute_script("return window.innerHeight;"))
                    
                    driver.execute_script(
                        f"var e = new MouseEvent('click', {{'view': window, 'bubbles': true, "
                        f"'cancelable': true, 'clientX': {x}, 'clientY': {y}}}); "
                        f"document.elementFromPoint({x}, {y}).dispatchEvent(e);"
                    )
                except Exception as e:
                    activity_logger.info(f"Click nowhere error: {str(e)}")
            
            elif interaction == "form_interact" and random.random() < self.browser_manager.behavior_profile.form_interaction_probability:
                # Interact with forms if any exist
                try:
                    forms = driver.find_elements(By.TAG_NAME, "form")
                    if forms:
                        form = random.choice(forms)
                        inputs = form.find_elements(By.TAG_NAME, "input")
                        
                        text_inputs = []
                        for input_elem in inputs:
                            input_type = input_elem.get_attribute("type")
                            if input_type in ["text", "email", "search"]:
                                text_inputs.append(input_elem)
                        
                        if text_inputs:
                            input_elem = random.choice(text_inputs)
                            # Just focus the field without submitting
                            input_elem.click()
                            # Type something random but don't submit
                            random_text = "".join(random.choice(string.ascii_lowercase) for _ in range(5))
                            input_elem.send_keys(random_text)
                except Exception as e:
                    activity_logger.info(f"Form interact error: {str(e)}")
            
            # Pause between interactions
            time.sleep(random.uniform(1, 5))
        
        # Ensure we've spent the full duration
        remaining_time = max(0, end_time - time.time())
        if remaining_time > 0:
            time.sleep(remaining_time)
    
    def _find_internal_links(self, driver: webdriver.Chrome, current_url: str, visited_urls: set) -> list:
        """Find internal links that haven't been visited yet."""
        try:
            # Parse the domain from the current URL
            parsed_url = urlparse(current_url)
            base_domain = parsed_url.netloc
            
            # Find all links
            links = driver.find_elements(By.TAG_NAME, "a")
            internal_links = []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    
                    # Skip if no href or not http(s)
                    if not href or not href.startswith(("http://", "https://")):
                        continue
                    
                    # Parse the link URL
                    parsed_link = urlparse(href)
                    link_domain = parsed_link.netloc
                    
                    # Check if it's an internal link and not visited yet
                    if link_domain == base_domain and href not in visited_urls:
                        internal_links.append(link)
                except Exception:
                    continue
            
            return internal_links
        except Exception as e:
            activity_logger.info(f"Error finding internal links: {str(e)}")
            return []
    
    def worker(self) -> None:
        """Worker thread to process tasks from the queue."""
        while self.running and not self.paused:
            try:
                task = self.task_queue.get(timeout=1)
                if task["type"] == "search":
                    results = self.search_google(task["keyword"])
                    # Queue the results to visit
                    for url in results[:3]:  # Limit to top 3 results
                        self.task_queue.put({
                            "type": "visit",
                            "url": url
                        })
                elif task["type"] == "visit":
                    self.visit_url(task["url"])
                self.task_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                error_logger.error(f"Error in worker thread: {str(e)}")
    
    def start(self, num_workers: int = 3) -> None:
        """Start the traffic bot with specified number of worker threads."""
        if self.running:
            return
        
        self.running = True
        self.paused = False
        self.stats["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create and start worker threads
        for _ in range(num_workers):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
        
        activity_logger.info(f"Started traffic bot with {num_workers} workers")
        
        # Queue initial tasks
        self._queue_tasks()
    
    def pause(self) -> None:
        """Pause the traffic bot without stopping threads."""
        if not self.running or self.paused:
            return
        
        self.paused = True
        activity_logger.info("Paused traffic bot")
    
    def resume(self) -> None:
        """Resume the traffic bot after pausing."""
        if not self.running or not self.paused:
            return
        
        self.paused = False
        activity_logger.info("Resumed traffic bot")
    
    def _queue_tasks(self) -> None:
        """Queue tasks from keywords and URLs."""
        # Queue direct URL visits
        for url in self.urls:
            self.task_queue.put({
                "type": "visit",
                "url": url
            })
        
        # Queue keyword searches
        for keyword in self.keywords:
            self.task_queue.put({
                "type": "search",
                "keyword": keyword
            })
    
    def stop(self) -> None:
        """Stop the traffic bot."""
        if not self.running:
            return
        
        self.running = False
        self.paused = False
        
        # Wait for threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=2)
        
        self.worker_threads = []
        activity_logger.info("Stopped traffic bot")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        # Combine bot stats with scheduler stats
        combined_stats = self.stats.copy()
        combined_stats.update({"scheduler": self.scheduler.get_stats()})
        return combined_stats