import logging
import os
import pickle
from pathlib import Path
from typing import Optional, Union, List, Dict
from requests import Session
from json.decoder import JSONDecodeError
from requests.exceptions import RequestException
from fantrax_service.exceptions import FantraxException, Unauthorized
from fantrax_service.objs import Team, Position, Roster

logger = logging.getLogger(__name__)

class FantraxService:
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
    def __init__(self, league_id: str, team_id: str, cookie_path: str):
        self.league_id = league_id
        self.team_id = team_id
        # Create a new session and load cookies
        self._session = Session()
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
        else:
            self._load_cookies(cookie_path)
        
        self._teams = None
        self._positions = None

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

    @property
    def teams(self) -> List[Team]:
        if self._teams is None:
            response = self._request("getFantasyTeams")
            self._teams = []
            for data in response["fantasyTeams"]:
                self._teams.append(Team(self, data["id"], data["name"], data["shortName"], data["logoUrl256"]))
        return self._teams

    @property
    def positions(self) -> Dict[str, Position]:
        if self._positions is None:
            self._positions = {k: Position(self, v) for k, v in self._request("getRefObject", type="Position")["allObjs"].items()}
        return self._positions

    def team(self, team_id: str) -> Team:
        """ :class:`~Team` Object for the given Team ID.

            Parameters:
                team_id (str): Team ID.

            Returns:
                :class:`~Team`

            Raises:
                :class:`FantraxException`: When an Invalid Team ID is provided.
        """
        for team in self.teams:
            if team.team_id == team_id:
                return team
        raise FantraxException(f"Team ID: {team_id} not found")

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

    def roster_info(self):
        return Roster(self, self._request("getTeamRosterInfo", teamId=self.team_id), self.team_id)

        
    def make_lineup_changes(self, changes: dict, apply_to_future_periods: bool = True) -> bool:
        """Make lineup changes for a team.
        
        Parameters:
            team_id (str): The team ID to make changes for
            changes (dict): Dictionary mapping player IDs to new positions/status
                          Format: {"player_id": {"posId": "position_id", "stId": "status_id"}}
            apply_to_future_periods (bool): Whether to apply changes to future periods
        
        Returns:
            bool: True if changes were successful
            
        Raises:
            FantraxException: If the lineup change fails
        """
        # First, get current roster to build the complete fieldMap
        roster = self.roster_info()
        current_field_map = {}
        
        # Build current field map from existing roster
        for row in roster.rows:
            if row.player:
                current_field_map[row.player.id] = {
                    "posId": row.pos_id,
                    "stId": "1" if row.pos_id != "0" else "2"  # 1=starter, 2=bench
                }
        
        # Apply the requested changes
        for player_id, new_config in changes.items():
            if player_id in current_field_map:
                current_field_map[player_id].update(new_config)
        
        # Phase 1: Confirm changes
        confirm_data = {
            "rosterLimitPeriod": 2,  # This appears to be a constant from your example
            "fantasyTeamId": self.team_id,
            "daily": False,
            "adminMode": False,
            "confirm": True,
            "applyToFuturePeriods": apply_to_future_periods,
            "fieldMap": current_field_map
        }
        
        try:
            self._api._request("confirmOrExecuteTeamRosterChanges", **confirm_data)
        except FantraxException as e:
            raise FantraxException(f"Failed to confirm lineup changes: {e}")
        
        # Phase 2: Execute changes
        execute_data = {
            "rosterLimitPeriod": 2,
            "fantasyTeamId": self.team_id,
            "daily": False,
            "adminMode": False,
            "confirm": False,
            "applyToFuturePeriods": apply_to_future_periods,
            "fieldMap": current_field_map
        }
        
        try:
            self._api._request("confirmOrExecuteTeamRosterChanges", **execute_data)
        except FantraxException as e:
            raise FantraxException(f"Failed to execute lineup changes: {e}")
        
        return True

    def swap_players(self, player1_id: str, player2_id: str) -> bool:
        """Swap two players between starter and bench positions.
        
        Parameters:
            player1_id (str): First player ID
            player2_id (str): Second player ID
            
        Returns:
            bool: True if swap was successful
        """
        roster = self.roster_info()
        
        # Find current status of both players
        player1_status = None
        player2_status = None
        
        for row in roster.rows:
            if row.player:
                if row.player.id == player1_id:
                    player1_status = "1" if row.pos_id != "0" else "2"
                elif row.player.id == player2_id:
                    player2_status = "1" if row.pos_id != "0" else "2"
        
        if player1_status is None or player2_status is None:
            raise FantraxException("One or both players not found on roster")
        
        # Swap their statuses
        changes = {
            player1_id: {"stId": player2_status},
            player2_id: {"stId": player1_status}
        }
        
        return self.make_lineup_changes(changes)

    def move_to_starters(self, player_ids: list) -> bool:
        """Move specified players to starter positions.
        
        Parameters:
            team_id (str): The team ID
            player_ids (list): List of player IDs to move to starters
            
        Returns:
            bool: True if moves were successful
        """
        changes = {player_id: {"stId": "1"} for player_id in player_ids}
        return self.make_lineup_changes(changes)

    def move_to_bench(self, player_ids: list) -> bool:
        """Move specified players to bench positions.
        
        Parameters:
            team_id (str): The team ID
            player_ids (list): List of player IDs to move to bench
            
        Returns:
            bool: True if moves were successful
        """
        changes = {player_id: {"stId": "2"} for player_id in player_ids}
        return self.make_lineup_changes(changes)
