import json
import inspect
import math
from datetime import datetime
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
from fantrax_pl_team_manager.domain.constants import *

logger = logging.getLogger(__name__)

@dataclass
class FantasyValue:
    """Data class representing a player's fantasy value.
    
    Attributes:
        value_for_gameweek: Fantasy value for the current gameweek
        value_for_future_gameweeks: Fantasy value for future gameweeks
    """
    value_for_gameweek: float = 0
    value_for_future_gameweeks: float = 0

class FantasyPlayer:
    """Represents a Fantrax player with their profile data and statistics.
    
    Attributes:
        id: Player ID
        name: Player name
        team_name: Name of the player's Premier League team
        icon_statuses: Set of parsed icon statuses
        highlight_stats: Dictionary of highlight statistics
        gameweek_stats: List of gameweek statistics
        upcoming_game_opponent: Name of the opponent in the upcoming game
        upcoming_game_home_or_away: Whether the upcoming game is 'home' or 'away'
    """

    def __init__(self,
        id:str, 
        name:str = None, 
        team_name:str = None, 
        icon_statuses: Set[str] = set(), 
        highlight_stats: Dict[str, Any] = {}, # TODO: change to PlayerHighlightStats
        gameweek_stats: List[PlayerGameweekStats] = [],
        upcoming_game_opponent: str = None, 
        upcoming_game_home_or_away: str = None, 
        upcoming_game_datetime: datetime = None,
        ):
            self.id = id
            self.name = name
            self.team_name = team_name
            self.icon_statuses = icon_statuses
            self.highlight_stats = highlight_stats
            self.gameweek_stats:List[PlayerGameweekStats] = gameweek_stats
            self.fantasy_value:FantasyValue = FantasyValue(value_for_gameweek=float(0.0), value_for_future_gameweeks=float(0.0))
            self.upcoming_game_opponent:str = upcoming_game_opponent
            self.upcoming_game_home_or_away:str = upcoming_game_home_or_away
            self.upcoming_game_datetime:datetime = upcoming_game_datetime
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
