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

class FantraxClient:
    """ Main Object Class

        Parameters:
            league_id (str): Fantrax League ID.
            session (Optional[Session]): Use you're own Session object
            cookie_path (Optional[str]): Path to cookie file for authentication.
                                        If not provided, will check FANTRAX_COOKIE_FILE env var.
                                        Ignored if session is provided.

        Attributes:
            league_id (str): Fantrax League ID.
            teams (List[:class:`~Team`]): List of Teams in the League.
    """
    def __init__(self, league_id: str, cookie_path: str):
        self.league_id = league_id
        # Create a new session and load cookies
        self._session = Session()
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
        else:
            self._load_cookies(cookie_path)
        
        self._teams = None

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

    def _request(self, method, **kwargs):
        data = {"leagueId": self.league_id}
        for key, value in kwargs.items():
            data[key] = value
        json_data = {"msgs": [{"method": method, "data": data}]}
        logger.debug(f"Request JSON: {json_data}")

        try:
            response = self._session.post("https://www.fantrax.com/fxpa/req", params={"leagueId": self.league_id}, json=json_data)
            response_json = response.json()
        except (RequestException, JSONDecodeError) as e:
            raise FantraxException(f"Failed to Connect to {method}: {e}\nData: {data}")
        logger.debug(f"Response ({response.status_code} [{response.reason}]) {response_json}")
        if response.status_code >= 400:
            raise FantraxException(f"({response.status_code} [{response.reason}]) {response_json}")
        if "pageError" in response_json:
            if "code" in response_json["pageError"]:
                if response_json["pageError"]["code"] == "WARNING_NOT_LOGGED_IN":
                    raise Unauthorized("Unauthorized: Not Logged in")
            raise FantraxException(f"Error: {response_json}")
        return response_json["responses"][0]["data"]

