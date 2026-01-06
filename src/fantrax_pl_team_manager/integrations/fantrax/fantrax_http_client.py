import requests
from typing import Any, Mapping

import logging
import os
import pickle
from pathlib import Path
from typing import Optional, Union, List, Dict
from requests import Session
from json.decoder import JSONDecodeError
from requests.exceptions import RequestException
from fantrax_pl_team_manager.exceptions import FantraxException, Unauthorized

logger = logging.getLogger(__name__)

class FantraxRequestsHTTPClient:
    """ Main Object Class

        Parameters:
            session (Optional[Session]): Use you're own Session object
            cookie_path (Optional[str]): Path to cookie file for authentication.
                                        If not provided, will check FANTRAX_COOKIE_FILE env var.
                                        Ignored if session is provided.

        Attributes:
            league_id (str): Fantrax League ID.
            teams (List[:class:`~Team`]): List of Teams in the League.
    """
    def __init__(self, cookie_path: str, session: requests.Session | None = None):
        # Create a new session and load cookies
        if session is None:
            self._session = Session()
        else:
            self._session = session
            
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
        else:
            self._load_cookies(cookie_path)

    def _load_cookies(self, cookie_path: str) -> None:
        """Load authentication cookies from a pickle file into the session.
        
        Parameters:
            cookie_path (str): Path to the cookie file
            
        Raises:
            FileNotFoundError: If cookie file doesn't exist
            FantraxException: If cookie loading fails
        """
        cookie_file = Path(cookie_path)
        
        if not cookie_file.exists():
            raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
        
        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    self._session.cookies.set(cookie["name"], cookie["value"])
            logger.debug(f"Loaded {len(cookies)} cookies from {cookie_path}")
        except Exception as e:
            raise FantraxException(f"Error loading cookie file {cookie_path}: {e}")

    def fantrax_request(self, payload, params={}, headers={}) -> Mapping[str, Any]:
        try:
            resp = self._session.post("https://www.fantrax.com/fxpa/req", params=params, json=payload, headers=headers)
            resp.raise_for_status()
            response_json = resp.json()
        except (RequestException, JSONDecodeError) as e:
            raise FantraxException(f"Failed to Connect to Fantrax: {e}\nData: {payload}")
        if resp.status_code >= 400:
            raise FantraxException(f"({resp.status_code} [{resp.reason}]) {response_json}")
        if "pageError" in response_json:
            if "code" in response_json["pageError"]:
                if response_json["pageError"]["code"] == "WARNING_NOT_LOGGED_IN":
                    raise Unauthorized("Unauthorized: Not Logged in")
            raise FantraxException(f"Error: {response_json}")
        return response_json
