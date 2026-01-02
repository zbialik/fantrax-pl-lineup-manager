import json
import inspect
from dataclasses import dataclass
import logging
from typing import List, Set
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.services.fantrax_player import FantraxPlayer
from fantrax_pl_team_manager.services.fantrax_player import POSITION_MAP_BY_ID, POSITION_MAP_BY_SHORT_NAME

logger = logging.getLogger(__name__)

class FantraxRosterPlayer(FantraxPlayer):
    def __init__(self, client: FantraxClient, league_id: str, fantrax_roster_manager_row):
        self.client = client
        
        self.id = fantrax_roster_manager_row['scorer']['scorerId']

        self.rostered_status_id = fantrax_roster_manager_row['statusId']
        self.rostered_position_id = fantrax_roster_manager_row['posId']

        # TODO: see if this can be acquired from generic player data retrieved in super class instead
        self.disable_lineup_change = fantrax_roster_manager_row["scorer"].get("disableLineupChange",False)

        super().__init__(client, league_id, self.id)
    
    @property
    def rostered_starter(self) -> bool:
        return True if self.rostered_status_id == "1" else False
    
    @property
    def rostered_position_short_name(self) -> str:
        return POSITION_MAP_BY_ID.get(self.rostered_position_id)
    
    def change_position_by_short_name(self, position_short_name: str):
        self.rostered_position_id = POSITION_MAP_BY_SHORT_NAME.get(position_short_name)
    
    def change_to_starter(self):
        """Change the player to a starter."""
        self.rostered_status_id = "1"
    
    def change_to_reserve(self):
        """Change the player to a reserve."""
        self.rostered_status_id = "2"
    
    def swap_starting_status(self):
        """Swap the starting status of the player."""
        if self.rostered_starter:
            self.change_to_reserve()
        else:
            self.change_to_starter()
