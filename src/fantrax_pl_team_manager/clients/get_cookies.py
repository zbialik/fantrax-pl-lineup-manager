import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


def create_chrome_driver(headless: bool = True, service: Optional[Service] = None) -> WebDriver:
    """
    Create a Chrome WebDriver instance with proper configuration for automation.
    
    Args:
        headless: If True, run browser in headless mode (default: True)
        service: Optional ChromeDriver Service instance. If not provided and
                 webdriver_manager is available, it will be auto-configured.
    
    Returns:
        Configured WebDriver instance
    """
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")  # Use new headless mode
    
    # Common options for automation
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Set a realistic user agent to avoid bot detection
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Window size (even in headless, useful for rendering)
    options.add_argument("--window-size=1920,1080")
    
    # If service not provided and webdriver_manager is available, use it
    if service is None and WEBDRIVER_MANAGER_AVAILABLE:
        service = Service(ChromeDriverManager().install())
    
    return webdriver.Chrome(service=service, options=options)


def fantrax_login_and_save_cookies(
    debug_mode: bool,
    username: str,
    password: str,
    cookie_path: str = "fantraxloggedin.cookie",
    timeout_s: int = 45,
) -> List[Dict[str, Any]]:
    """
    Fully automated Fantrax login:
      - Navigates to https://www.fantrax.com/login
      - Enters credentials
      - Submits
      - Waits until URL is no longer /login
      - Saves cookies to cookie_path (JSON)

    Returns the cookie list from driver.get_cookies().
    Raises RuntimeError on timeout / login failure.
    """
    driver: WebDriver = create_chrome_driver(headless=not debug_mode)
    try:
        wait = WebDriverWait(driver, timeout_s)

        login_url = "https://www.fantrax.com/login"
        logger.info(f"Navigating to {login_url}")
        driver.get(login_url)

        # Give page a moment to load
        logger.info("Waiting for page to be ready...")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(2)  # Additional wait for dynamic content
        
        logger.info(f"Current URL: {driver.current_url}")
        logger.info("Looking for login form fields...")
        
        # Try to find username field with multiple strategies
        # Fantrax uses Angular Material with IDs like mat-input-0, mat-input-1
        user_input = None
        username_selectors = [
            "input#mat-input-0",  # Angular Material first input (username)
            "input[name='username']",
            "input#username", 
            "input[type='email']",
            "input[autocomplete='username']",
            "input[placeholder*='username']",
            "input[placeholder*='email']",
            "input[placeholder*='Email']",
            "input[placeholder*='Username']"
        ]
        
        for selector in username_selectors:
            try:
                logger.info(f"Trying username selector: {selector}")
                # Use shorter timeout for each attempt
                element_wait = WebDriverWait(driver, 5)
                user_input = element_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Found username field with selector: {selector}")
                break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if user_input is None:
            # Fallback: try to find first text input (for Angular Material)
            logger.info("Standard selectors failed, trying fallback: first text input")
            all_text_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if all_text_inputs:
                user_input = all_text_inputs[0]
                logger.info("Found username field using fallback (first text input)")
            else:
                # Try to find any input field and log page source for debugging
                logger.error("Could not find username field. Searching for all input fields...")
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                logger.error(f"Found {len(all_inputs)} input elements on page")
                for inp in all_inputs[:5]:  # Log first 5 inputs
                    try:
                        logger.error(f"  Input: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}, placeholder={inp.get_attribute('placeholder')}")
                    except:
                        pass
                logger.error("Page source snippet (first 2000 chars):")
                logger.error(driver.page_source[:2000])
                raise RuntimeError("Could not locate username input field on login page")
        
        # Try to find password field
        # Fantrax uses Angular Material with IDs like mat-input-0, mat-input-1
        pass_input = None
        password_selectors = [
            "input#mat-input-1",  # Angular Material second input (password)
            "input[name='password']",
            "input#password",
            "input[type='password']",
            "input[autocomplete='current-password']"
        ]
        
        for selector in password_selectors:
            try:
                logger.info(f"Trying password selector: {selector}")
                # Use shorter timeout for each attempt
                element_wait = WebDriverWait(driver, 5)
                pass_input = element_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Found password field with selector: {selector}")
                break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if pass_input is None:
            # Fallback: try to find first password input (for Angular Material)
            logger.info("Standard selectors failed, trying fallback: first password input")
            all_password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            if all_password_inputs:
                pass_input = all_password_inputs[0]
                logger.info("Found password field using fallback (first password input)")
            else:
                logger.error("Could not find password field. Searching for password inputs...")
                logger.error(f"Found {len(all_password_inputs)} password input elements")
                raise RuntimeError("Could not locate password input field on login page")
        
        # Fill creds - scroll into view and interact
        logger.info("Filling in credentials...")
        driver.execute_script("arguments[0].scrollIntoView(true);", user_input)
        time.sleep(0.5)
        user_input.clear()
        user_input.send_keys(username)
        logger.info("Username filled")
        
        driver.execute_script("arguments[0].scrollIntoView(true);", pass_input)
        time.sleep(0.5)
        pass_input.clear()
        pass_input.send_keys(password)
        logger.info("Password filled")

        # Submit: prefer clicking a submit button; otherwise hit ENTER
        logger.info("Attempting to submit form...")
        clicked = False
        submit_selectors = ["button[type='submit']", "input[type='submit']", "button.btn-primary", "button.login"]
        
        for sel in submit_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed() and btn.is_enabled():
                    logger.info(f"Found submit button with selector: {sel}")
                    btn.click()
                    clicked = True
                    break
            except Exception as e:
                logger.debug(f"Submit selector {sel} failed: {e}")
                continue

        if not clicked:
            logger.info("No submit button found, sending ENTER key")
            pass_input.send_keys(Keys.ENTER)
        
        time.sleep(2)  # Wait a moment for submission to process
        
        # Wait until we're no longer on the login page.
        logger.info("Waiting for redirect after login...")
        logger.info(f"Current URL before wait: {driver.current_url}")
        try:
            wait.until(lambda d: "/login" not in (d.current_url or "").lower())
            logger.info(f"Login successful! Redirected to: {driver.current_url}")
        except Exception as e:
            logger.error(f"Timeout waiting for redirect. Current URL: {driver.current_url}")
            # Optional: detect likely "bad password" message on page
            src = (driver.page_source or "").lower()
            if any(s in src for s in ["invalid", "incorrect", "unable to log in", "login failed", "wrong password"]):
                raise RuntimeError("Fantrax login failed: credentials rejected (page indicates invalid login).")
            # Save page source for debugging
            debug_file = Path(cookie_path).parent / "login_debug.html"
            debug_file.write_text(driver.page_source, encoding="utf-8")
            logger.error(f"Saved page source to {debug_file} for debugging")
            raise RuntimeError(f"Timed out waiting for Fantrax login redirect away from /login. Page saved to {debug_file} for inspection.")

        # Save cookies as pickle (binary format) to match FantraxClient._load_cookies expectations
        cookies = driver.get_cookies() or []
        cookie_file = Path(cookie_path)
        with open(cookie_file, "wb") as f:
            pickle.dump(cookies, f)
        logger.info(f"Saved {len(cookies)} cookies to {cookie_file.absolute()}")
        return cookies
    finally:
        driver.quit()
