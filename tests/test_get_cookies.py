import os
import pickle
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.fantrax_pl_team_manager.clients.get_cookies import fantrax_login_and_save_cookies


class TestFantraxLoginAndSaveCookies(unittest.TestCase):
    """Test cases for fantrax_login_and_save_cookies function."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test cookie files
        self.test_dir = tempfile.mkdtemp()
        self.test_cookie_path = os.path.join(self.test_dir, "test_cookies.cookie")
        
        # Create a mock WebDriver
        self.mock_driver = MagicMock()
        
        # Mock WebDriverWait
        self.mock_wait = MagicMock()
        
        # Mock element objects
        self.mock_username_input = MagicMock()
        self.mock_password_input = MagicMock()
        self.mock_submit_button = MagicMock()
        self.mock_submit_button.is_displayed.return_value = True
        self.mock_submit_button.is_enabled.return_value = True
        
        # Set up default mock behaviors
        self.mock_driver.current_url = "https://www.fantrax.com/login"
        self.mock_driver.get_cookies.return_value = [
            {"name": "session_id", "value": "test_session_123"},
            {"name": "auth_token", "value": "test_auth_token"}
        ]
        self.mock_driver.execute_script.return_value = None
        self.mock_driver.page_source = "<html></html>"
        
        # Mock WebDriverWait to return our mock_wait
        self.patcher_wait = patch(
            'src.fantrax_pl_team_manager.clients.get_cookies.WebDriverWait',
            return_value=self.mock_wait
        )
        self.patcher_wait.start()
        
        # Mock time.sleep to avoid actual delays
        self.patcher_sleep = patch('src.fantrax_pl_team_manager.clients.get_cookies.time.sleep')
        self.patcher_sleep.start()

    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        self.patcher_wait.stop()
        self.patcher_sleep.stop()
        
        # Clean up test files
        if os.path.exists(self.test_cookie_path):
            os.remove(self.test_cookie_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_creates_cookie_file_at_specified_path(self):
        """Test that fantrax_login_and_save_cookies creates a file at cookie_path."""
        # Track call count for wait.until calls
        call_count = [0]
        
        def wait_until_side_effect(func_or_condition):
            """Handle different types of wait.until calls."""
            call_count[0] += 1
            
            if call_count[0] == 1:
                # First call: page ready state check (lambda function)
                # The lambda calls: d.execute_script("return document.readyState") == "complete"
                if callable(func_or_condition):
                    # Mock execute_script to return "complete"
                    self.mock_driver.execute_script.return_value = "complete"
                    result = func_or_condition(self.mock_driver)
                    return result
                return True
            elif call_count[0] == 2:
                # Second call: username field clickable (EC.element_to_be_clickable)
                # wait.until should return the element when the condition is satisfied
                return self.mock_username_input
            elif call_count[0] == 3:
                # Third call: password field clickable (EC.element_to_be_clickable)
                return self.mock_password_input
            elif call_count[0] == 4:
                # Fourth call: redirect check (lambda function)
                # The lambda checks: "/login" not in (d.current_url or "").lower()
                self.mock_driver.current_url = "https://www.fantrax.com/dashboard"
                if callable(func_or_condition):
                    return func_or_condition(self.mock_driver)
                return True
            return True
        
        self.mock_wait.until.side_effect = wait_until_side_effect
        
        # Mock finding elements - return empty list so it uses the EC.element_to_be_clickable path
        self.mock_driver.find_elements.return_value = []
        self.mock_driver.find_element.return_value = self.mock_submit_button
        
        # Mock EC.element_to_be_clickable - it returns a condition object
        # The condition object is callable and when called with driver, returns the element
        with patch('src.fantrax_pl_team_manager.clients.get_cookies.EC.element_to_be_clickable') as mock_clickable:
            # Create mock conditions that return elements when called
            def create_mock_condition(element):
                condition = MagicMock()
                condition.__call__ = lambda driver: element
                return condition
            
            mock_clickable.side_effect = [
                create_mock_condition(self.mock_username_input),  # Username field condition
                create_mock_condition(self.mock_password_input),  # Password field condition
            ]
            
            # Execute the function
            cookies = fantrax_login_and_save_cookies(
                driver=self.mock_driver,
                username="test_user",
                password="test_password",
                cookie_path=self.test_cookie_path,
                timeout_s=30
            )
        
        # Verify the file was created
        self.assertTrue(
            os.path.exists(self.test_cookie_path),
            f"Cookie file should be created at {self.test_cookie_path}"
        )
        
        # Verify the file contains valid pickle data
        with open(self.test_cookie_path, "rb") as f:
            loaded_cookies = pickle.load(f)
        
        self.assertIsInstance(loaded_cookies, list)
        self.assertEqual(len(loaded_cookies), 2)
        self.assertEqual(loaded_cookies[0]["name"], "session_id")
        self.assertEqual(loaded_cookies[1]["name"], "auth_token")
        
        # Verify the function returned the cookies
        self.assertEqual(len(cookies), 2)
        self.assertEqual(cookies, self.mock_driver.get_cookies.return_value)


if __name__ == '__main__':
    unittest.main()

