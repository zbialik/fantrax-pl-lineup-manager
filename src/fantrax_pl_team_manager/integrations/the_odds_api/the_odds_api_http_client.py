import requests
from typing import Any, Mapping
import json
import logging

logger = logging.getLogger(__name__)

class TheOddsApiRequestsHTTPClient:
    """ The Odds API HTTP Client
    """
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._base_url = 'https://api.the-odds-api.com'

    def the_odds_api_request(self, path: str, params={}, headers={}) -> Mapping[str, Any]:
        # Add authentcation parameters to the request
        merged_params = params | {'api_key': self._api_key}
        # Make the request
        resp = requests.get(self._base_url + path, params=merged_params, headers=headers)
        logger.info(f"Remaining API requests: {resp.headers['x-requests-remaining']}")
        resp.raise_for_status()
        out = resp.json()
        # TODO: Remove this
        with open('TEST_odds_h2h.json', 'w') as f:
            json.dump(out, f, indent=2)
        return out
