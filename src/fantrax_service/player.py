from datetime import datetime, timedelta
import json

class Player:
    def __init__(self, fantrax_player_row):        
        def game_week_status():
            if fantrax_player_row["scorer"].get("disableLineupChange"):
                return 'locked'
            for icon in fantrax_player_row["scorer"].get("icons"):
                # Set game status
                if icon["typeId"] == "12": # starting
                    return 'starting'
                elif icon["typeId"] == "34": # on the bench but not starting
                    return 'benched'
                elif icon["typeId"] in ["15"]: # not rostered for game
                    return 'out'
                elif icon["typeId"] == "32": # expected to play in upcoming/current game
                    return 'expected-to-play'
                else:
                    return None

        def general_status():
            for icon in fantrax_player_row["scorer"].get("icons"):
                if icon["typeId"] == "30":
                    return 'out-for-next-game'
                elif icon["typeId"] == "1":
                    return 'uncertain-gametime-decision'
                elif icon["typeId"] == "6":
                    return 'suspended'
                else:
                    return None
 
        # Store cleaned fantrax data
        self.fantrax = {
            'id': fantrax_player_row['scorer']['scorerId'],
            'name': fantrax_player_row['scorer']['name'],
            'team_name': fantrax_player_row['scorer']['teamName'],
            'gameweek_status': game_week_status(),
            'general_status': general_status(),
            'rostered_starter': True if fantrax_player_row["statusId"] == "1" else False
        }
    
    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes that start with underscore
            if key.startswith('_'):
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
        return result
    
    def __str__(self):
        """Return JSON representation of all attributes."""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def __repr__(self):
        """Return JSON representation of all attributes."""
        return self.__str__()
