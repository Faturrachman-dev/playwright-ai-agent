from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time
import random
import os
import json
import re
from urllib.parse import urlparse
from datetime import datetime

# Configure logging for this module (or rely on global config if main_playwright.py sets it up)
logger = logging.getLogger(__name__) # Use a module-specific logger

COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def generate_screenshot_filename(url):
    """Generate unique filename for screenshot based on URL and timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Sanitize URL to create a safe filename part
    url_part = re.sub(r'[^\w\-_.]', '_', urlparse(url).netloc + urlparse(url).path)[:75] # Increased length
    url_part = url_part.strip('_').strip('.').strip('-')
    return f"screenshot_{timestamp}_{url_part}.png"

def load_playwright_cookies(context, cookies_path):
    """Loads cookies from a JSON file (Selenium format) into a Playwright context."""
    logger.info(f"Attempting to load cookies from: {cookies_path}")
    try:
        if not os.path.exists(cookies_path):
            logger.warning(f"Cookies file not found: {cookies_path}. Proceeding without loaded cookies.")
            return
            
        with open(cookies_path, 'r') as f:
            selenium_cookies = json.load(f)
            
        if not isinstance(selenium_cookies, list):
            logger.error("Invalid cookies format in file. Expected a list of cookies.")
            return

        playwright_cookies = []
        for sc in selenium_cookies:
            if not sc.get('name') or sc.get('value') is None:
                logger.warning(f"Skipping cookie with missing name or value: {sc.get('name', 'N/A')}")
                continue

            samesite_value = sc.get('sameSite')
            valid_samesite_for_playwright = 'Lax' # Default

            if isinstance(samesite_value, str):
                samesite_lower = samesite_value.lower()
                if samesite_lower == 'strict': valid_samesite_for_playwright = 'Strict'
                elif samesite_lower == 'lax': valid_samesite_for_playwright = 'Lax'
                elif samesite_lower == 'none': valid_samesite_for_playwright = 'None'
            elif samesite_value is None:
                if sc.get('secure', False):
                    valid_samesite_for_playwright = 'None' 
                else:
                    valid_samesite_for_playwright = 'Lax' 
                    logger.warning(f"Cookie '{sc.get('name')}' has sameSite=null and is not Secure. Defaulting sameSite to Lax.")

            pc = {
                'name': sc['name'],
                'value': sc['value'],
                'domain': sc.get('domain'),
                'path': sc.get('path', '/'),
                'httpOnly': sc.get('httpOnly', False),
                'secure': sc.get('secure', False),
                'sameSite': valid_samesite_for_playwright
            }
            if sc.get('expirationDate') is not None:
                pc['expires'] = float(sc['expirationDate'])
            
            if pc['domain'] and pc['domain'].startswith('.'):
                pc['domain'] = pc['domain'][1:]

            playwright_cookies.append(pc)

        if playwright_cookies:
            context.add_cookies(playwright_cookies)
            logger.info(f"Successfully loaded {len(playwright_cookies)} cookies into Playwright context.")
        else:
            logger.info("No valid cookies found to load after conversion.")

    except Exception as e:
        logger.error(f"Error loading cookies for Playwright: {e}", exc_info=True)

def take_playwright_screenshot(context_to_use, url: str, output_path: str, headless: bool = True, timeout_ms: int = 60000):
    """
    Navigates to a URL using a given Playwright context and takes a full-page screenshot.
    Returns True on success, False on failure.
    Assumes browser and context are managed externally and passed in.
    """
    page = None
    logger.info(f"Attempting to capture screenshot for {url} with Playwright.")
    try:
        page = context_to_use.new_page()
        
        logger.info(f"Navigating to {url}...")
        page.goto(url, timeout=timeout_ms, wait_until='domcontentloaded')
        logger.info(f"Navigated to {url}.")

        # Attempt to click the cookie consent button
        try:
            cookie_button_selector = "button:has-text('Accept all cookies'), button:has-text('Accept'), [aria-label*='Accept'], [id*='cookie-accept']"
            logger.info(f"Attempting to click cookie consent button with selectors: {cookie_button_selector}")
            page.locator(cookie_button_selector).first.click(timeout=5000)
            logger.info("Clicked a cookie consent button (or attempted to).")
            page.wait_for_timeout(1500) # Wait for banner to disappear/page to adjust
        except PlaywrightTimeoutError:
            logger.warning(f"Cookie consent button not found or timed out for {url}. Continuing...")
        except Exception as e_cookie_click:
            logger.warning(f"Could not click cookie consent button (or it wasn't found): {e_cookie_click} for {url}")

        # Get page dimensions for logging
        try:
            dimensions = page.evaluate("() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight })")
            logger.info(f"Playwright - Page dimensions for {url}: Width={dimensions['width']}, Height={dimensions['height']}")
        except Exception as e_dim:
            logger.warning(f"Could not get page dimensions for {url}: {e_dim}")

        logger.info(f"Taking screenshot and saving to {output_path}")
        page.screenshot(path=output_path, full_page=True, timeout=120000) # 120s timeout for screenshot
        logger.info(f"Screenshot successful with Playwright for {url} saved to {output_path}.")
        return True
    except PlaywrightTimeoutError as e_timeout:
        logger.error(f"Playwright timed out for {url}: {e_timeout}", exc_info=True)
        error_screenshot_path = os.path.join(os.path.dirname(output_path), f"error_{os.path.basename(output_path)}")
        try:
            if page and not page.is_closed(): page.screenshot(path=error_screenshot_path, full_page=True)
            logger.info(f"Saved error page screenshot to {error_screenshot_path} due to timeout.")
        except Exception as e_screen:
            logger.error(f"Could not take error screenshot on timeout: {e_screen}")
        return False
    except Exception as e:
        logger.error(f"An error occurred with Playwright for {url}: {e}", exc_info=True)
        error_screenshot_path = os.path.join(os.path.dirname(output_path), f"error_{os.path.basename(output_path)}")
        try:
            if page and not page.is_closed(): page.screenshot(path=error_screenshot_path, full_page=True)
            logger.info(f"Saved error page screenshot to {error_screenshot_path} due to error.")
        except Exception as e_screen:
            logger.error(f"Could not take error screenshot on error: {e_screen}")
        return False
    finally:
        if page and not page.is_closed():
            page.close()
            logger.info(f"Closed page for {url}.") 