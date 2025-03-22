import re
import time
import random
import subprocess
import logging
from urllib.parse import urlparse
import requests
from typing import List, Dict, Optional, Tuple

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

class VPNManager:
    """Class for managing VPN connections and proxies."""
    
    def __init__(self):
        """Initialize the VPN manager."""
        # VPN providers configuration
        self.vpn_providers = {
            'pia': {
                'enabled': False,
                'connected': False,
                'regions': [],
                'current_region': None,
                'command': 'piactl'
            },
            'nordvpn': {
                'enabled': False,
                'connected': False,
                'regions': [],
                'current_region': None,
                'command': 'nordvpn'
            },
            'expressvpn': {
                'enabled': False,
                'connected': False,
                'regions': [],
                'current_region': None,
                'command': 'expressvpn'
            }
        }
        
        # Proxy settings
        self.proxies = []
        self.current_proxy = None
        self.current_vpn = None
        self.use_proxies = True
        
        # Country targeting
        self.target_countries = []  # e.g., ['US', 'UK', 'CA', 'AU']
    
    def load_proxies(self, proxy_file: str) -> None:
        """Load proxies from a file."""
        try:
            with open(proxy_file, 'r') as f:
                all_proxies = [line.strip() for line in f if line.strip()]
            
            # If target countries are specified, filter proxies that match those countries
            if self.target_countries and any('country:' in p.lower() for p in all_proxies):
                filtered_proxies = []
                for proxy in all_proxies:
                    # Check if the proxy has country information
                    proxy_lower = proxy.lower()
                    for country in self.target_countries:
                        country_lower = country.lower()
                        if f"country:{country_lower}" in proxy_lower or proxy_lower.startswith(f"{country_lower}:"):
                            filtered_proxies.append(proxy)
                            break
                
                if filtered_proxies:
                    self.proxies = filtered_proxies
                    activity_logger.info(f"Filtered proxies from {len(all_proxies)} to {len(filtered_proxies)} based on target countries")
                else:
                    self.proxies = all_proxies
                    activity_logger.warning("No proxies match the target countries. Using all available proxies.")
            else:
                self.proxies = all_proxies
            
            activity_logger.info(f"Loaded {len(self.proxies)} proxies from {proxy_file}")
        except Exception as e:
            error_logger.error(f"Failed to load proxies: {str(e)}")
    
    def filter_regions_by_country(self, provider: str, regions: List[str]) -> List[str]:
        """Filter VPN regions to only include target countries."""
        if not self.target_countries:
            return regions  # If no target countries set, return all regions
        
        filtered_regions = []
        for region in regions:
            # Different VPN providers format their regions differently
            region_lower = region.lower()
            for country in self.target_countries:
                country_lower = country.lower()
                if country_lower in region_lower:
                    filtered_regions.append(region)
                    break
        
        # If no regions match the target countries, log a warning
        if not filtered_regions:
            activity_logger.warning(f"No {provider} regions match the target countries. Using all available regions.")
            return regions
        
        activity_logger.info(f"Filtered {provider} regions from {len(regions)} to {len(filtered_regions)} based on target countries")
        return filtered_regions
    
    def load_vpn_regions(self, provider: str) -> None:
        """Load VPN regions for a specific provider."""
        if provider not in self.vpn_providers:
            error_logger.error(f"Unknown VPN provider: {provider}")
            return
        
        try:
            vpn_info = self.vpn_providers[provider]
            
            if provider == 'pia':
                # PIA VPN
                result = subprocess.run(["piactl", "get", "regions"], capture_output=True, text=True)
                if result.returncode == 0:
                    all_regions = [region.strip() for region in result.stdout.split('\n') if region.strip()]
                    vpn_info['regions'] = self.filter_regions_by_country(provider, all_regions)
                    activity_logger.info(f"Loaded {len(vpn_info['regions'])} PIA regions")
                else:
                    error_logger.error(f"Failed to get PIA regions: {result.stderr}")
            
            elif provider == 'nordvpn':
                # NordVPN (using their CLI tool)
                result = subprocess.run(["nordvpn", "countries"], capture_output=True, text=True)
                if result.returncode == 0:
                    all_countries = re.findall(r'- ([A-Za-z_\s]+)', result.stdout)
                    all_regions = [c.strip() for c in all_countries if c.strip()]
                    vpn_info['regions'] = self.filter_regions_by_country(provider, all_regions)
                    activity_logger.info(f"Loaded {len(vpn_info['regions'])} NordVPN countries")
                else:
                    error_logger.error(f"Failed to get NordVPN countries: {result.stderr}")
            
            elif provider == 'expressvpn':
                # ExpressVPN
                result = subprocess.run(["expressvpn", "list", "all"], capture_output=True, text=True)
                if result.returncode == 0:
                    locations = re.findall(r'([A-Z]{2})\s+-\s+([A-Za-z\s]+)', result.stdout)
                    all_regions = [f"{code} - {name.strip()}" for code, name in locations]
                    vpn_info['regions'] = self.filter_regions_by_country(provider, all_regions)
                    activity_logger.info(f"Loaded {len(vpn_info['regions'])} ExpressVPN locations")
                else:
                    error_logger.error(f"Failed to get ExpressVPN locations: {result.stderr}")
        
        except Exception as e:
            error_logger.error(f"Failed to load {provider} regions: {str(e)}")
    
    def enable_vpn(self, provider: str) -> bool:
        """Enable a specific VPN provider."""
        if provider in self.vpn_providers:
            self.vpn_providers[provider]['enabled'] = True
            activity_logger.info(f"Enabled {provider} VPN provider")
            return True
        return False
    
    def disable_vpn(self, provider: str) -> bool:
        """Disable a specific VPN provider."""
        if provider in self.vpn_providers:
            self.vpn_providers[provider]['enabled'] = False
            activity_logger.info(f"Disabled {provider} VPN provider")
            return True
        return False
    
    def connect_vpn(self, provider: str, region: str) -> bool:
        """Connect to VPN using a specific provider and region."""
        if provider not in self.vpn_providers:
            error_logger.error(f"Unknown VPN provider: {provider}")
            return False
        
        vpn_info = self.vpn_providers[provider]
        
        try:
            activity_logger.info(f"Connecting to {provider} region: {region}")
            
            # Disconnect any active VPNs first
            self.disconnect_all_vpns()
            time.sleep(2)
            
            if provider == 'pia':
                # PIA VPN
                result = subprocess.run(["piactl", "connect", region], capture_output=True, text=True)
            
            elif provider == 'nordvpn':
                # NordVPN
                result = subprocess.run(["nordvpn", "connect", region], capture_output=True, text=True)
            
            elif provider == 'expressvpn':
                # ExpressVPN - extract location code from the region string
                location_code = region.split(' - ')[0] if ' - ' in region else region
                result = subprocess.run(["expressvpn", "connect", location_code], capture_output=True, text=True)
            
            if result.returncode == 0:
                vpn_info['current_region'] = region
                vpn_info['connected'] = True
                self.current_vpn = provider
                activity_logger.info(f"Connected to {provider} region: {region}")
                return True
            else:
                error_logger.error(f"Failed to connect to {provider} region {region}: {result.stderr}")
                return False
        
        except Exception as e:
            error_logger.error(f"Error connecting to {provider}: {str(e)}")
            return False
    
    def disconnect_vpn(self, provider: str) -> bool:
        """Disconnect from a specific VPN provider."""
        if provider not in self.vpn_providers:
            error_logger.error(f"Unknown VPN provider: {provider}")
            return False
        
        vpn_info = self.vpn_providers[provider]
        
        if not vpn_info['connected']:
            return True
        
        try:
            if provider == 'pia':
                subprocess.run(["piactl", "disconnect"], check=True)
            elif provider == 'nordvpn':
                subprocess.run(["nordvpn", "disconnect"], check=True)
            elif provider == 'expressvpn':
                subprocess.run(["expressvpn", "disconnect"], check=True)
            
            vpn_info['connected'] = False
            vpn_info['current_region'] = None
            
            if self.current_vpn == provider:
                self.current_vpn = None
            
            activity_logger.info(f"Disconnected from {provider} VPN")
            return True
        
        except Exception as e:
            error_logger.error(f"Error disconnecting from {provider}: {str(e)}")
            return False
    
    def disconnect_all_vpns(self) -> bool:
        """Disconnect from all VPN providers."""
        success = True
        
        for provider in self.vpn_providers:
            if self.vpn_providers[provider]['connected']:
                provider_success = self.disconnect_vpn(provider)
                success = success and provider_success
        
        return success
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the loaded list."""
        if not self.proxies:
            error_logger.error("No proxies available")
            return None
        
        self.current_proxy = random.choice(self.proxies)
        activity_logger.info(f"Selected proxy: {self.current_proxy}")
        return self.current_proxy
    
    def get_random_vpn_region(self, provider: str) -> Optional[str]:
        """Get a random VPN region from a specific provider."""
        if provider not in self.vpn_providers:
            error_logger.error(f"Unknown VPN provider: {provider}")
            return None
        
        vpn_info = self.vpn_providers[provider]
        
        if not vpn_info['regions']:
            error_logger.error(f"No {provider} regions available")
            return None
        
        region = random.choice(vpn_info['regions'])
        activity_logger.info(f"Selected {provider} region: {region}")
        return region
    
    def get_random_vpn(self) -> Tuple[Optional[str], Optional[str]]:
        """Get a random VPN provider and region from enabled providers."""
        enabled_providers = [p for p in self.vpn_providers if self.vpn_providers[p]['enabled'] and self.vpn_providers[p]['regions']]
        
        if not enabled_providers:
            error_logger.error("No enabled VPN providers with regions available")
            return None, None
        
        provider = random.choice(enabled_providers)
        region = self.get_random_vpn_region(provider)
        
        return provider, region
    
    def get_current_ip(self) -> str:
        """Get the current public IP address."""
        try:
            response = requests.get("https://api.ipify.org", timeout=10)
            ip = response.text
            activity_logger.info(f"Current IP: {ip}")
            return ip
        except Exception as e:
            error_logger.error(f"Error getting current IP: {str(e)}")
            return "Unknown"
    
    def is_any_vpn_connected(self) -> bool:
        """Check if any VPN is currently connected."""
        return any(vpn_info['connected'] for vpn_info in self.vpn_providers.values())