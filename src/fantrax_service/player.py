from datetime import datetime, timedelta
import json

class Player:
    def __init__(self, fantrax_player_row):
        print(fantrax_player_row)
        
        def clean_fantrax_data(fantrax_player_row):
            def fantrax_status():
                # init status object to False for everything
                status = {
                    'will_not_play': False,
                    'starting': False,
                    'benched': False,
                    'already_played': False
                }

                if fantrax_player_row["scorer"].get("disableLineupChange"):
                    status['already_played'] = fantrax_player_row["scorer"].get("disableLineupChange")
                
                for icon in fantrax_player_row["scorer"].get("icons"):
                    if icon["typeId"] in ["1", "2", "6", "30"]: # DtD, Out, IR, Knee
                        status["will_not_play"] = True
                    if icon["typeId"] == "12": # starting
                        status["starting"] = True
                    # TODO: identify typeId for benched
                    if icon["typeId"] == "????": # benched
                        status["benched"] = True
                return status

            d = {
                'scorerId': fantrax_player_row['scorer']['scorerId'],
                'name': fantrax_player_row['scorer']['name'],
                'team_name': fantrax_player_row['scorer']['teamName'],
                'fantrax_status': fantrax_status(),
                'rostered_starter': True if fantrax_player_row["statusId"] == "1" else False
            }

            return d
        
        # Store cleaned fantrax data
        self.fantrax = clean_fantrax_data(fantrax_player_row)
    
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
