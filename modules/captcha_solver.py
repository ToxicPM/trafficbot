import logging
import re
from typing import Optional
from selenium import webdriver
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from anticaptchaofficial.recaptchav3proxyless import recaptchaV3Proxyless
from anticaptchaofficial.imagecaptcha import imagecaptcha

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

class CaptchaSolver:
    """Class for solving various types of CAPTCHAs using AntiCaptcha service."""
    
    def __init__(self, api_key: str):
        """Initialize with AntiCaptcha API key.
        
        Args:
            api_key: AntiCaptcha API key
        """
        self.api_key = api_key
        self.verbose = False  # Set to True for detailed logs from AntiCaptcha
    
    def solve_recaptcha_v2(self, site_key: str, url: str) -> Optional[str]:
        """Solve reCAPTCHA v2 using AntiCaptcha.
        
        Args:
            site_key: The site key for the reCAPTCHA
            url: The URL of the page containing the reCAPTCHA
            
        Returns:
            Solution string or None if failed
        """
        try:
            activity_logger.info(f"Attempting to solve reCAPTCHA v2 on {url}")
            
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1 if self.verbose else 0)
            solver.set_key(self.api_key)
            solver.set_website_url(url)
            solver.set_website_key(site_key)
            
            g_response = solver.solve_and_return_solution()
            if g_response != 0:
                activity_logger.info(f"Successfully solved reCAPTCHA v2")
                return g_response
            else:
                error_logger.error(f"Failed to solve reCAPTCHA v2: {solver.error_code}")
                return None
        except Exception as e:
            error_logger.error(f"Error solving reCAPTCHA v2: {str(e)}")
            return None
    
    def solve_recaptcha_v3(self, site_key: str, url: str, action: str = "verify", min_score: float = 0.7) -> Optional[str]:
        """Solve reCAPTCHA v3 using AntiCaptcha.
        
        Args:
            site_key: The site key for the reCAPTCHA
            url: The URL of the page containing the reCAPTCHA
            action: The action value for reCAPTCHA v3
            min_score: Minimum score threshold
            
        Returns:
            Solution string or None if failed
        """
        try:
            activity_logger.info(f"Attempting to solve reCAPTCHA v3 on {url}")
            
            solver = recaptchaV3Proxyless()
            solver.set_verbose(1 if self.verbose else 0)
            solver.set_key(self.api_key)
            solver.set_website_url(url)
            solver.set_website_key(site_key)
            solver.set_action(action)
            solver.set_min_score(min_score)
            
            g_response = solver.solve_and_return_solution()
            if g_response != 0:
                activity_logger.info(f"Successfully solved reCAPTCHA v3")
                return g_response
            else:
                error_logger.error(f"Failed to solve reCAPTCHA v3: {solver.error_code}")
                return None
        except Exception as e:
            error_logger.error(f"Error solving reCAPTCHA v3: {str(e)}")
            return None
    
    def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """Solve a regular image CAPTCHA using AntiCaptcha.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Solution text or None if failed
        """
        try:
            activity_logger.info(f"Attempting to solve image CAPTCHA from {image_path}")
            
            solver = imagecaptcha()
            solver.set_verbose(1 if self.verbose else 0)
            solver.set_key(self.api_key)
            
            result = solver.solve_and_return_solution(image_path)
            if result != 0:
                activity_logger.info(f"Successfully solved image CAPTCHA: {result}")
                return result
            else:
                error_logger.error(f"Failed to solve image CAPTCHA: {solver.error_code}")
                return None
        except Exception as e:
            error_logger.error(f"Error solving image CAPTCHA: {str(e)}")
            return None
    
    def detect_and_solve_captcha(self, driver: webdriver.Chrome) -> bool:
        """Detect and solve any CAPTCHA on the current page.
        
        Args:
            driver: Selenium WebDriver instance with page loaded
            
        Returns:
            True if CAPTCHA was detected and solved, False otherwise
        """
        try:
            page_source = driver.page_source.lower()
            current_url = driver.current_url
            
            # Check for reCAPTCHA v2
            if "recaptcha" in page_source or "g-recaptcha" in page_source:
                activity_logger.info("reCAPTCHA detected")
                
                # Extract site key
                site_key_match = re.search(r'data-sitekey="([^"]+)"', driver.page_source)
                if site_key_match:
                    site_key = site_key_match.group(1)
                    solution = self.solve_recaptcha_v2(site_key, current_url)
                    
                    if solution:
                        # Inject the solution
                        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";')
                        
                        # Try to find and submit the form containing the CAPTCHA
                        try:
                            captcha_form = driver.find_element_by_css_selector("form:has(div.g-recaptcha)") or \
                                        driver.find_element_by_id("captcha-form") or \
                                        driver.find_element_by_css_selector("form")
                            
                            if captcha_form:
                                captcha_form.submit()
                                activity_logger.info("CAPTCHA form submitted")
                                return True
                        except:
                            activity_logger.info("Could not find or submit CAPTCHA form")
            
            # Check for "unusual traffic" or "suspicious activity" messages
            elif "unusual traffic" in page_source or "suspicious activity" in page_source:
                activity_logger.info("Unusual traffic detection page encountered")
                
                # Look for any visible forms or buttons to continue
                try:
                    continue_button = driver.find_element_by_xpath("//button[contains(text(), 'Continue') or contains(text(), 'Verify') or contains(text(), 'I am human')]")
                    continue_button.click()
                    activity_logger.info("Clicked continue button on unusual traffic page")
                    return True
                except:
                    activity_logger.info("No continue button found on unusual traffic page")
            
            return False
            
        except Exception as e:
            error_logger.error(f"Error detecting or solving CAPTCHA: {str(e)}")
            return False