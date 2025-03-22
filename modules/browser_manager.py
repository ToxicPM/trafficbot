import random
import string
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from fake_useragent import UserAgent

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

class BehaviorProfile:
    """Class to define various browsing behavior profiles."""
    def __init__(self):
        # Visit duration (in seconds)
        self.min_visit_duration = 60  # Default: 1 minute minimum
        self.max_visit_duration = 180  # Default: 3 minutes maximum
        
        # Page interaction settings
        self.scroll_depth = 70  # Default: scroll to 70% of page depth
        self.click_probability = 0.6  # Default: 60% chance to click internal links
        self.max_subpage_visits = 3  # Default: visit up to 3 subpages
        self.form_interaction_probability = 0.3  # Default: 30% chance to interact with forms
        
        # Device emulation
        self.device_types = {
            "desktop": 0.6,  # 60% desktop
            "mobile": 0.3,   # 30% mobile
            "tablet": 0.1    # 10% tablet
        }
        
        # Bounce rate settings
        self.bounce_rate = 0.15  # Default: 15% bounce rate (very low)
        
        # Referrer settings
        self.referrer_types = {
            "search": 0.40,    # Search engines
            "social": 0.25,    # Social media
            "direct": 0.20,    # Direct traffic
            "referral": 0.15   # Referral from other sites
        }
        
        # Search engine distribution
        self.search_engines = {
            "google": 0.75,
            "bing": 0.15,
            "yahoo": 0.05,
            "duckduckgo": 0.05
        }
        
        # Social media distribution
        self.social_sources = {
            "facebook": 0.35,
            "twitter": 0.25,
            "instagram": 0.15,
            "linkedin": 0.10,
            "pinterest": 0.10,
            "reddit": 0.05
        }
        
        # AdSense settings
        self.adsense_safe = True
    
    def get_visit_duration(self) -> tuple:
        """Get the min and max visit duration in seconds."""
        return (self.min_visit_duration, self.max_visit_duration)
    
    def get_random_device(self) -> str:
        """Get a random device type based on distribution."""
        return random.choices(
            list(self.device_types.keys()),
            weights=list(self.device_types.values()),
            k=1
        )[0]
    
    def get_random_referrer(self) -> str:
        """Get a random referrer type based on distribution."""
        ref_type = random.choices(
            list(self.referrer_types.keys()),
            weights=list(self.referrer_types.values()),
            k=1
        )[0]
        
        if ref_type == "search":
            search_engine = random.choices(
                list(self.search_engines.keys()),
                weights=list(self.search_engines.values()),
                k=1
            )[0]
            return f"search_{search_engine}"
        elif ref_type == "social":
            social_site = random.choices(
                list(self.social_sources.keys()),
                weights=list(self.social_sources.values()),
                k=1
            )[0]
            return f"social_{social_site}"
        else:
            return ref_type
    
    def should_bounce(self) -> bool:
        """Determine if this visit should bounce based on bounce rate."""
        return random.random() < self.bounce_rate
    
    def get_subpage_count(self) -> int:
        """Get random number of subpages to visit."""
        if self.should_bounce():
            return 0
        else:
            # Weight towards lower numbers but allow up to max_subpage_visits
            weights = [max(1, self.max_subpage_visits - i) for i in range(self.max_subpage_visits)]
            return random.choices(range(1, self.max_subpage_visits + 1), weights=weights, k=1)[0]

class BrowserManager:
    """Class for managing browser instances and their behavior."""
    def __init__(self, vpn_manager, captcha_solver):
        """Initialize the browser manager with VPN manager and CAPTCHA solver."""
        self.vpn_manager = vpn_manager
        self.captcha_solver = captcha_solver
        self.user_agent = UserAgent()
        
        # Initialize behavior profile
        self.behavior_profile = BehaviorProfile()
    
    def get_driver(self, use_proxy: bool = False, device_type: str = None) -> Optional[webdriver.Chrome]:
        """Create and configure a Chrome WebDriver with appropriate settings.
        
        Args:
            use_proxy: Whether to use the currently selected proxy
            device_type: The device type to emulate (desktop, mobile, tablet)
            
        Returns:
            Configured Chrome WebDriver or None if creation failed
        """
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Use random user agent appropriate for the device type
            random_ua = self._get_user_agent_for_device(device_type)
            options.add_argument(f"user-agent={random_ua}")
            
            # Add proxy if requested
            if use_proxy and self.vpn_manager.current_proxy:
                proxy_without_auth = self._extract_proxy_address(self.vpn_manager.current_proxy)
                if proxy_without_auth:
                    options.add_argument(f'--proxy-server={proxy_without_auth}')
            
            # Device-specific settings
            if device_type == "mobile":
                mobile_emulation = {
                    "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
                    "userAgent": random_ua
                }
                options.add_experimental_option("mobileEmulation", mobile_emulation)
            elif device_type == "tablet":
                tablet_emulation = {
                    "deviceMetrics": {"width": 768, "height": 1024, "pixelRatio": 2.0},
                    "userAgent": random_ua
                }
                options.add_