from datetime import datetime, timedelta
import json
from typing import List
from collections.abc import MutableSequence
from fantrax_service.player import Player

class Roster(MutableSequence):
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
            print(f"Warning: Unexpected roster data structure: {e}")
            self.active = 0
            self.reserve = 0
            self.max = 0
            self.injured = 0
        
        self.players: List[Player] = []
        try:
            for table in data.get("tables", []):
                for row_item in table.get("rows", []):
                    if "scorer" in row_item:
                        self.players.append(Player(row_item))
        except Exception as e:
            print(f"Warning: Error processing roster rows: {e}")
            self.players = []

    # Required abstract methods for MutableSequence
    def __getitem__(self, index):
        return self.players[index]
    
    def __setitem__(self, index, value):
        self.players[index] = value
    
    def __delitem__(self, index):
        del self.players[index]
    
    def __len__(self):
        return len(self.players)
    
    def insert(self, index, value):
        self.players.insert(index, value)

    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        return {
            'active': self.active,
            'reserve': self.reserve,
            'max': self.max,
            'injured': self.injured,
            'players': [player._to_dict() for player in self.players]
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
        
        return self.players
