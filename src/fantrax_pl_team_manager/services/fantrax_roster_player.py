import json
import inspect
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.services.fantrax_player import (
    FantraxPlayer,
    POSITION_MAP_BY_ID,
    POSITION_MAP_BY_SHORT_NAME,
    ROSTER_STATUS_STARTER,
    ROSTER_STATUS_RESERVE
)

logger = logging.getLogger(__name__)

class FantraxRosterPlayer(FantraxPlayer):
    """Represents a player on a Fantrax roster with roster-specific attributes.
    
    Extends FantraxPlayer with roster-specific information like position and
    starting status within the team's roster.
    
    Attributes:
        rostered_status_id: Status ID indicating if player is starter ("1") or reserve ("2")
        rostered_position_id: Position ID for the player in the roster
        disable_lineup_change: Whether the player can have their lineup status changed
    """
    def __init__(self, client: FantraxClient, league_id: str, fantrax_roster_manager_row, premier_league_team_stats: Dict[str, Any]):
        self.client = client
        
        self.id = fantrax_roster_manager_row['scorer']['scorerId']

        self.rostered_status_id = fantrax_roster_manager_row['statusId']
        self.rostered_position_id = fantrax_roster_manager_row['posId']

        # TODO: see if this can be acquired from generic player data retrieved in super class instead
        self.disable_lineup_change = fantrax_roster_manager_row["scorer"].get("disableLineupChange",False)

        super().__init__(client, league_id, self.id, premier_league_team_stats)
    
    @property
    def rostered_starter(self) -> bool:
        return self.rostered_status_id == ROSTER_STATUS_STARTER
    
    @property
    def rostered_position_short_name(self) -> str:
        return POSITION_MAP_BY_ID.get(self.rostered_position_id)
    
    def change_position_by_short_name(self, position_short_name: str) -> None:
        """Change the player's position in the roster by short name.
        
        Parameters:
            position_short_name: Position short name (G, D, M, or F)
        """
        self.rostered_position_id = POSITION_MAP_BY_SHORT_NAME.get(position_short_name)
    
    def change_to_starter(self) -> None:
        """Change the player to a starter."""
        self.rostered_status_id = ROSTER_STATUS_STARTER
    
    def change_to_reserve(self) -> None:
        """Change the player to a reserve."""
        self.rostered_status_id = ROSTER_STATUS_RESERVE
    
    def swap_starting_status(self) -> None:
        """Swap the starting status of the player (starter <-> reserve)."""
        if self.rostered_starter:
            self.change_to_reserve()
        else:
            self.change_to_starter()
