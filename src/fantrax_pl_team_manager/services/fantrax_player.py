import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.exceptions import FantraxException

# Position mapping constants
POSITION_MAP_BY_ID = {
    "704": "G",
    "703": "D",
    "702": "M",
    "701": "F"
}
POSITION_MAP_BY_SHORT_NAME = {v: k for k, v in POSITION_MAP_BY_ID.items()}

# Status icon mapping constants
STATUS_ICON_MAP_BY_ID = {
    "12": "starting",
    "34": "benched",
    "15": "out",
    "32": "expected-to-play",
    "30": "out-for-next-game",
    "1": "uncertain-gametime-decision",
    "6": "suspended"
}

# Roster status constants
ROSTER_STATUS_STARTER = "1"
ROSTER_STATUS_RESERVE = "2"

# Lineup requirement constants
MIN_STARTERS = 11
MIN_DEFENDERS = 3
MIN_MIDFIELDERS = 3
MIN_FORWARDS = 1
MAX_GOALKEEPERS = 1
MAX_DEFENDERS = 5
MAX_MIDFIELDERS = 5
MAX_FORWARDS = 3
MAX_RECENT_GAMEWEEKS = 5

# Status string constants
STATUS_BENCHED = "benched"
STATUS_SUSPENDED = "suspended"
STATUS_OUT = "out"
STATUS_OUT_FOR_NEXT_GAME = "out-for-next-game"
STATUS_STARTING = "starting"
STATUS_EXPECTED_TO_PLAY = "expected-to-play"
STATUS_UNCERTAIN_GAMETIME_DECISION = "uncertain-gametime-decision"

# Fantasy value calculation constants
DEFAULT_UPCOMING_GAME_COEFFICIENT_K = 0.7
DEFAULT_UPCOMING_GAME_COEFFICIENT_A = 1

logger = logging.getLogger(__name__)

@dataclass
class FantasyValue:
    """Data class representing a player's fantasy value.
    
    Attributes:
        value_for_gameweek: Fantasy value for the current gameweek
        value_for_future_gameweeks: Fantasy value for future gameweeks
    """
    value_for_gameweek: int = 0
    value_for_future_gameweeks: int = 0

class FantraxPlayer:
    """Represents a Fantrax player with their profile data and statistics.
    
    Attributes:
        client: FantraxClient instance for API calls
        league_id: ID of the Fantrax league
        id: Player ID
        name: Player name
        team_name: Name of the player's Premier League team
        icons: List of status icons for the player
        icon_statuses: Set of parsed icon statuses
        highlight_stats: Dictionary of highlight statistics
        recent_gameweeks_stats: Dictionary of recent gameweek statistics
        fantasy_value: Fantasy value for the player
        upcoming_game_opponent: Name of the opponent in the upcoming game
        upcoming_game_home_or_away: Whether the upcoming game is 'home' or 'away'
        premier_league_team_stats: Dictionary of Premier League team statistics
    """
    def __init__(self, client: FantraxClient, league_id: str, player_id: str, premier_league_team_stats: Dict[str, Any] = None):
        self.client = client
        self.league_id = league_id
        self.id = player_id

        self.name = None
        self.team_name = None
        self.icons = None
        self.icon_statuses: Set[str] = None
        self.highlight_stats = {}
        self.recent_gameweeks_stats = {}
        self.fantasy_value = FantasyValue()
        self.upcoming_game_opponent = None
        self.upcoming_game_home_or_away = None
        self.premier_league_team_stats = premier_league_team_stats
        self.refresh_player_data() # used to set the above attributes
    
    def refresh_player_data(self):
        """Get the player info from Fantrax."""
        data = self.client.get_player_profile_data(self.league_id, self.id)

        self._parse_basic_info(data)
        self._parse_highlight_stats(data)
        self._parse_overview_tables(data)

        # Finally, set priority value for gameweek
        self._update_fantasy_value_for_gameweek()
    
    def _parse_basic_info(self, data: Dict[str, Any]) -> None:
        """Parse basic player information from data."""
        self.name = data['miscData'].get('name')
        self.icons = data['miscData'].get('icons', [])
        self.icon_statuses = set([
            STATUS_ICON_MAP_BY_ID.get(icon["typeId"])
            for icon in self.icons
            if icon.get("typeId") in STATUS_ICON_MAP_BY_ID
        ])
    
    def _parse_highlight_stats(self, data: Dict[str, Any]) -> None:
        """Parse highlight statistics from data."""
        highlight_stats_list = data['miscData'].get('highlightStats', [])
        for stat in highlight_stats_list:
            if 'shortName' not in stat or 'value' not in stat:
                continue
            
            value = stat['value']
            if isinstance(value, str) and value.endswith('%'):
                value = value.rstrip('%')
            
            try:
                decimal_value = Decimal(value)
                self.highlight_stats[stat['shortName']] = decimal_value / 100
            except (InvalidOperation, ValueError):
                # If conversion fails, use the original value
                self.highlight_stats[stat['shortName']] = value
    
    def _parse_overview_tables(self, data: Dict[str, Any]) -> None:
        """Parse overview tables (Upcoming Games, Recent Games) from data."""
        try:
            tables = data.get('sectionContent', {}).get('OVERVIEW', {}).get('tables', [])
            for table in tables:
                if table.get('caption') == 'Upcoming Games':
                    self._parse_upcoming_games_table(table)
                elif table.get('caption') == 'Recent Games':
                    self._parse_recent_games_table(table)
        except Exception as e:
            logger.error(f"Error processing overview tables: {e}")
            raise FantraxException(f"Error processing overview tables: {e}")
    
    def _parse_upcoming_games_table(self, table: Dict[str, Any]) -> None:
        """Parse upcoming games table to extract opponent and home/away status."""
        header_cells = table.get('header', {}).get('cells', [])
        rows = table.get('rows', [])
        
        if not rows:
            return
        
        for i, cell in enumerate(header_cells):
            if cell.get('key') == 'opp':
                opponent = rows[0]['cells'][i]['content']
                if isinstance(opponent, str) and opponent.startswith('@'):
                    opponent = opponent.lstrip('@')
                    self.upcoming_game_home_or_away = 'away'
                else:
                    self.upcoming_game_home_or_away = 'home'
                
                self.upcoming_game_opponent = opponent
                break
    
    def _parse_recent_games_table(self, table: Dict[str, Any]) -> None:
        """Parse recent games table to extract team name and gameweek statistics."""
        header_cells = table.get('header', {}).get('cells', [])
        rows = table.get('rows', [])
        
        if not rows:
            return
        
        for i, cell in enumerate(header_cells):
            stat_key = cell.get('name') or cell.get('key')
            if not stat_key:
                continue
            
            # Extract team name from Team column
            if stat_key.lower() == 'team':
                self.team_name = rows[0]['cells'][i].get('toolTip')
            
            # Initialize and populate recent gameweeks stats
            self.recent_gameweeks_stats[stat_key] = []
            
            for j in range(min(MAX_RECENT_GAMEWEEKS, len(rows))):
                gameweek_stat_value = rows[j]['cells'][i]['content']
                try:
                    decimal_value = Decimal(gameweek_stat_value)
                    self.recent_gameweeks_stats[stat_key].append(decimal_value)
                except (InvalidOperation, ValueError):
                    # If conversion fails, use the original value
                    self.recent_gameweeks_stats[stat_key].append(gameweek_stat_value)
    
    def _update_fantasy_value_for_gameweek(self) -> None:
        """Update the fantasy value for the gameweek based on recent performance and upcoming match difficulty."""
        # Initialize fantasy value using recent gameweeks stats
        fantasy_points = self.recent_gameweeks_stats.get('Fantasy Points', [])
        if fantasy_points:
            avg_fantasy_points = sum(fantasy_points) / len(fantasy_points)
            self.fantasy_value.value_for_gameweek += avg_fantasy_points

        # Update fantasy value based on difficulty of upcoming game
        upcoming_game_coefficient = self._calculate_upcoming_game_coefficient()
        self.fantasy_value.value_for_gameweek *= Decimal(upcoming_game_coefficient)
    
    def _calculate_upcoming_game_coefficient(
        self,
        k: float = DEFAULT_UPCOMING_GAME_COEFFICIENT_K,
        a: int = DEFAULT_UPCOMING_GAME_COEFFICIENT_A
    ) -> float:
        """Calculate coefficient for upcoming game difficulty.
        
        Uses a hyperbolic tangent function to adjust fantasy value based on the
        relative strength difference between the player's team and their opponent.
        
        Parameters:
            k: Scaling factor for the coefficient (default: 0.7)
            a: Scaling factor for rank difference (default: 1)
            
        Returns:
            float: Coefficient multiplier for fantasy value
            
        Raises:
            FantraxException: If team or opponent not found in Premier League stats
        """
        logger.debug(f"Calculating upcoming game coefficient for {self.team_name} vs {self.upcoming_game_opponent}")
        
        team_stats = self.premier_league_team_stats.get(self.team_name)
        opponent_stats = self.premier_league_team_stats.get(self.upcoming_game_opponent)
        
        if team_stats is None:
            error_msg = f"Team {self.team_name} not found in Premier League team stats"
            logger.error(error_msg)
            raise FantraxException(error_msg)
        
        if opponent_stats is None:
            error_msg = f"Opponent {self.upcoming_game_opponent} not found in Premier League team stats"
            logger.error(error_msg)
            raise FantraxException(error_msg)
        
        team_rank = team_stats.get('rank')
        opponent_rank = opponent_stats.get('rank')
        total_teams = len(self.premier_league_team_stats.keys())
        
        # Calculate coefficient using hyperbolic tangent function
        coefficient = 1 + k * math.tanh(a * (team_rank - opponent_rank) / (total_teams - 1))
        return coefficient

    @property
    def is_benched_or_suspended_or_out_in_gameweek(self) -> bool:
        """Check if player is benched, suspended, or out for the gameweek.
        
        Returns:
            bool: True if player has any of these statuses
        """
        check_statuses = {
            STATUS_BENCHED,
            STATUS_SUSPENDED,
            STATUS_OUT,
            STATUS_OUT_FOR_NEXT_GAME
        }
        return bool(check_statuses & self.icon_statuses)
    
    @property
    def is_uncertain_gametime_decision_in_gameweek(self) -> bool:
        """Check if player has an uncertain gametime decision status.
        
        Returns:
            bool: True if player has uncertain gametime decision status
        """
        return STATUS_UNCERTAIN_GAMETIME_DECISION in self.icon_statuses
    
    @property
    def is_starting_in_gameweek(self) -> bool:
        """Check if player is starting in the gameweek.
        
        Returns:
            bool: True if player has starting status
        """
        return STATUS_STARTING in self.icon_statuses
    
    @property
    def is_expected_to_play_in_gameweek(self) -> bool:
        """Check if player is expected to play in the gameweek.
        
        If no statuses are present, assumes player is expected to play.
        
        Returns:
            bool: True if player is expected to play or has no status
        """
        if not self.icon_statuses:
            # If no statuses, assume they are expected to play
            return True
        return STATUS_EXPECTED_TO_PLAY in self.icon_statuses
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert all attributes to a dictionary for JSON serialization.
        
        Returns:
            Dict[str, Any]: Dictionary containing all instance attributes and properties
        """
        data: Dict[str, Any] = {}

        # Regular instance attributes
        data.update(self.__dict__)

        # @property attributes
        for name, member in inspect.getmembers(type(self)):
            if isinstance(member, property):
                try:
                    data[name] = getattr(self, name)
                except Exception as e:
                    data[name] = f"<error: {e}>"

        return data
    
    def __str__(self):
        """Return JSON representation of all attributes."""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def __repr__(self):
        """Return JSON representation of all attributes."""
        return self.__str__()
