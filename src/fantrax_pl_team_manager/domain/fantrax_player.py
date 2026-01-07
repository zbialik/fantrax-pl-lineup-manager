import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from decimal import Decimal, InvalidOperation
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.domain.constants import *

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
        id: Player ID
        name: Player name
        team_name: Name of the player's Premier League team
        icon_statuses: Set of parsed icon statuses
        highlight_stats: Dictionary of highlight statistics
        recent_gameweeks_stats: Dictionary of recent gameweek statistics
        fantasy_value: Fantasy value for the player
        upcoming_game_opponent: Name of the opponent in the upcoming game
        upcoming_game_home_or_away: Whether the upcoming game is 'home' or 'away'
        premier_league_table: Dictionary of Premier League team statistics
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
        premier_league_table: PremierLeagueTable = PremierLeagueTable()
        ):
            self.id = id
            self.name = name
            self.team_name = team_name
            self.icon_statuses = icon_statuses
            self.highlight_stats = highlight_stats
            self.gameweek_stats:List[PlayerGameweekStats] = gameweek_stats
            self.fantasy_value:FantasyValue = FantasyValue(value_for_gameweek=0, value_for_future_gameweeks=0)
            self.upcoming_game_opponent:str = upcoming_game_opponent
            self.upcoming_game_home_or_away:str = upcoming_game_home_or_away
            self.premier_league_table:PremierLeagueTable = premier_league_table
    
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
    

    def _update_fantasy_value_for_gameweek(self) -> None:
        """Update the fantasy value for the gameweek based on recent performance and upcoming match difficulty."""
        # Initialize fantasy value using recent gameweeks stats
        fantasy_points = [gameweek_stat.points for gameweek_stat in self.gameweek_stats]
        if fantasy_points:
            avg_fantasy_points = sum(fantasy_points) / len(fantasy_points)
            self.fantasy_value.value_for_gameweek += avg_fantasy_points

        # Update fantasy value based on difficulty of upcoming game
        upcoming_game_coefficient = self._calculate_upcoming_game_coefficient()
        self.fantasy_value.value_for_gameweek *= Decimal(upcoming_game_coefficient)
    
    def _calculate_upcoming_game_coefficient(
        self,
        k: float = DEFAULT_UPCOMING_GAME_COEFFICIENT_K,
        a: int = DEFAULT_UPCOMING_GAME_COEFFICIENT_A) -> float:
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
        
        team = self.premier_league_table.get(self.team_name)
        opponent = self.premier_league_table.get(self.upcoming_game_opponent)
        
        if team is None:
            error_msg = f"Team {self.team_name} not found in Premier League team stats"
            logger.error(error_msg)
            raise FantraxException(error_msg)
        
        if opponent is None:
            error_msg = f"Opponent {self.upcoming_game_opponent} not found in Premier League team stats"
            logger.error(error_msg)
            raise FantraxException(error_msg)
        
        team_rank = team.rank
        opponent_rank = opponent.rank
        total_teams = len(self.premier_league_table.keys())
        
        # Calculate coefficient using hyperbolic tangent function
        coefficient = 1 + k * math.tanh(a * (team_rank - opponent_rank) / (total_teams - 1))
        return coefficient

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
