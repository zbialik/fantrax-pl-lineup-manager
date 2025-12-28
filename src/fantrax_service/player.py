from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

POSITION_MAP = {
    "704": "G",
    "703": "D",
    "702": "M",
    "701": "F"
}

class Player:
    def __init__(self, fantrax_player_row):        
        def game_week_status():
            if fantrax_player_row["scorer"].get("disableLineupChange"):
                return 'locked'
            for icon in fantrax_player_row["scorer"].get("icons", []):
                # Set game status
                if icon["typeId"] == "12": # starting
                    return 'starting'
                elif icon["typeId"] == "34": # on the bench but not starting
                    return 'benched'
                elif icon["typeId"] in ["15"]: # not rostered for game
                    return 'out'
                elif icon["typeId"] == "32": # expected to play in upcoming/current game
                    return 'expected-to-play'
            return None

        def general_status():
            for icon in fantrax_player_row["scorer"].get("icons", []):
                if icon["typeId"] == "30":
                    return 'out-for-next-game'
                elif icon["typeId"] == "1":
                    return 'uncertain-gametime-decision'
                elif icon["typeId"] == "6":
                    return 'suspended'
            return None

        # Store cleaned fantrax data
        self.fantrax = {
            'id': fantrax_player_row['scorer']['scorerId'],
            'name': fantrax_player_row['scorer']['name'],
            'team_name': fantrax_player_row['scorer'].get('teamName'),
            'gameweek_status': game_week_status(),
            'general_status': general_status(),
            'rostered_starter': True if fantrax_player_row.get("statusId") == "1" else False,
            'rostered_position_id': fantrax_player_row.get('posId', ''),
            'rostered_position_short_name': POSITION_MAP.get(fantrax_player_row.get('posId', ''))
        }
        
        # Enriched data attributes (can be populated from repository)
        self._enriched_data: Optional[Dict[str, Any]] = None
    
    def load_enriched_data(self, enriched_data: Dict[str, Any]):
        """Load enriched data from repository into the player object.
        
        This method allows enriching the player with database-stored data
        like performance scores and transfer values while maintaining
        backward compatibility with the fantrax dict structure.
        """
        self._enriched_data = enriched_data
    
    @property
    def performance_score(self) -> Optional[float]:
        """Get the player's performance score from enriched data."""
        if self._enriched_data and 'performance_score' in self._enriched_data:
            return self._enriched_data['performance_score']
        return None
    
    @property
    def transfer_value(self) -> Optional[float]:
        """Get the player's transfer value from enriched data."""
        if self._enriched_data and 'transfer_value' in self._enriched_data:
            return self._enriched_data['transfer_value']
        return None
    
    @property
    def rostered_position(self) -> Optional[str]:
        """Get the rostered position (short name) for convenience."""
        return self.fantrax.get('rostered_position_short_name')
    
    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes that start with underscore (except we'll include enriched data)
            if key.startswith('_') and key != '_enriched_data':
                continue
            # Try to serialize the value
            try:
                # If it's already a dict, list, or basic type, use it directly
                if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    result[key] = value
                # If it's a datetime, convert to ISO format string
                elif isinstance(value, (datetime, timedelta)):
                    result[key] = str(value)
                # For other objects, try to convert to string
                else:
                    result[key] = str(value)
            except Exception:
                result[key] = str(value)
        
        # Include enriched properties if available
        if self.performance_score is not None:
            result['performance_score'] = self.performance_score
        if self.transfer_value is not None:
            result['transfer_value'] = self.transfer_value
            
        return result
    
    def __str__(self):
        """Return JSON representation of all attributes."""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def __repr__(self):
        """Return JSON representation of all attributes."""
        return self.__str__()
