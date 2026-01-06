import json
import inspect
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.domain.fantrax_player import FantraxPlayer
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.domain.constants import *

logger = logging.getLogger(__name__)

class FantraxRosterPlayer(FantraxPlayer):
    """Represents a player on a Fantrax roster with roster-specific attributes.
    
    Extends FantraxPlayer with roster-specific information like position and
    starting status within the team's roster.
    
    Attributes:
        rostered_status_id: Status ID indicating if player is starter ("1") or reserve ("2")
        rostered_position: Position short name for the player in the roster
        disable_lineup_change: Whether the player can have their lineup status changed
    """
    def __init__(self, 
        id:str, 
        name:str = None, 
        team_name:str = None, 
        icon_statuses: Set[str] = None, 
        highlight_stats: Dict[str, Any] = None, 
        recent_gameweeks_stats: Dict[str, Any] = None,
        upcoming_game_opponent: str = None, 
        upcoming_game_home_or_away: str = None, 
        premier_league_table: PremierLeagueTable = None,
        rostered_starter: bool = None,
        rostered_position:str = None, 
        disable_lineup_change:bool = False
        ):
            self.rostered_starter = rostered_starter
            self.rostered_position = rostered_position
            self.disable_lineup_change = disable_lineup_change

            super().__init__(id, name, team_name, icon_statuses, highlight_stats, recent_gameweeks_stats, upcoming_game_opponent, upcoming_game_home_or_away, premier_league_table)
    
    def change_to_starter(self) -> None:
        """Change the player to a starter."""
        self.rostered_starter = True
    
    def change_to_reserve(self) -> None:
        """Change the player to a reserve."""
        self.rostered_starter = False
    
    def swap_starting_status(self) -> None:
        """Swap the starting status of the player (starter <-> reserve)."""
        if self.rostered_starter:
            self.change_to_reserve()
        else:
            self.change_to_starter()
