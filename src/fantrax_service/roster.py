from datetime import datetime, timedelta
import json
from typing import List, Dict
from fantrax_service.player import Player
import logging

logger = logging.getLogger(__name__)

class Roster:
    def __init__(self, data):
        # Safely handle different roster data structures
        try:
            status_totals = data.get("miscData", {}).get("statusTotals", [])
            
            # Set defaults
            self.active = 0
            self.reserve = 0
            self.max = 0
            self.injured = 0
            
            # Safely extract values based on available data
            if len(status_totals) > 0:
                self.active = status_totals[0].get("total", 0)
            if len(status_totals) > 1:
                self.reserve = status_totals[1].get("total", 0)
                self.max = status_totals[1].get("max", 0)
            if len(status_totals) > 2:
                self.injured = status_totals[2].get("total", 0)
                
        except Exception as e:
            # Fallback to safe defaults if data structure is unexpected
            logger.error(f"Unexpected roster data structure: {e}")
            self.active = 0
            self.reserve = 0
            self.max = 0
            self.injured = 0
        
        self.players: Dict[str, Player] = {}
        try:
            for table in data.get("tables", []):
                for row_item in table.get("rows", []):
                    if "scorer" in row_item:
                        player = Player(row_item)
                        player_id = player.fantrax['id']
                        self.players[player_id] = player
        except Exception as e:
            logger.error(f"Error processing roster rows: {e}")
            self.players = {}
    
    def __len__(self):
        """Return the number of players in the roster."""
        return len(self.players)
    
    def get_player(self, player_id: str) -> Player:
        """Get a player by their Fantrax ID."""
        return self.players.get(player_id)
    
    def __contains__(self, player_id: str) -> bool:
        """Check if a player ID exists in the roster."""
        return player_id in self.players
    
    def values(self):
        """Return a view of all players in the roster."""
        return self.players.values()
    
    def keys(self):
        """Return a view of all player IDs in the roster."""
        return self.players.keys()
    
    def items(self):
        """Return a view of all (player_id, player) pairs in the roster."""
        return self.players.items()

    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        return {
            'active': self.active,
            'reserve': self.reserve,
            'max': self.max,
            'injured': self.injured,
            'players': [player._to_dict() for player in self.players.values()]
        }
    
    def __str__(self):
        """Return JSON representation of roster data."""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def __repr__(self):
        """Return JSON representation of roster data."""
        return self.__str__()

    def get_starters_not_starting(self) -> List[Player]:
        # TODO: Implement logic to return only starters who are not starting (per domain rules)
        # Placeholder: currently returns all players
        
        return list(self.players.values())
