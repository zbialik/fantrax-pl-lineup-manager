import json
import inspect
from dataclasses import dataclass
import logging
from typing import List, Set
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.exceptions import FantraxException

POSITION_MAP_BY_ID = {
    "704": "G",
    "703": "D",
    "702": "M",
    "701": "F"
}
POSITION_MAP_BY_SHORT_NAME = {v: k for k, v in POSITION_MAP_BY_ID.items()}

STATUS_ICON_MAP_BY_ID = {
    "12": "starting",
    "34": "benched",
    "15": "out",
    "32": "expected-to-play",
    "30": "out-for-next-game",
    "1": "uncertain-gametime-decision",
    "6": "suspended"
}

logger = logging.getLogger(__name__)

@dataclass
class FantasyValue:
    value_for_gameweek: int = 0
    value_for_future_gameweeks: int = 0

class FantraxPlayer:
    def __init__(self, client: FantraxClient, league_id: str, player_id: str):
        self.client = client
        self.league_id = league_id
        self.id = player_id

        self.name = None
        self.team_name = None
        self.icons = None
        self.icon_statuses: Set[str] = None
        self.highlight_stats = {}
        self.recent_gameweeks_stats = {}
        self.fantasy_value = FantasyValue()

        self.refresh_player_data() # used to set the above attributes
    
    def refresh_player_data(self):
        """Get the player info from Fantrax.
        
        Returns:
            FantraxPlayer: The player
        """

        data = self.client.get_player_profile_data(self.league_id, self.id)

        self.name = data['miscData'].get('name')
        self.team_name = data['miscData'].get('teamName')
        self.icons = data['miscData'].get('icons',[])
        self.icon_statuses = set[str | None]([STATUS_ICON_MAP_BY_ID.get(icon["typeId"]) for icon in self.icons if icon["typeId"] in STATUS_ICON_MAP_BY_ID])
        
        _highlight_stats_list = data['miscData'].get('highlightStats',[])
        for stat in _highlight_stats_list:
            if 'shortName' in stat and 'value' in stat:
                value = stat['value']
                if isinstance(value, str) and value.endswith('%'):
                    # Remove '%' and convert to Decimal divided by 100
                    value = value.rstrip('%')
                try:
                    # Validate that numeric_value can be converted to Decimal
                    decimal_value = Decimal(value)
                    self.highlight_stats[stat['shortName']] = decimal_value / 100
                except (InvalidOperation, ValueError):
                    # If conversion fails, use the original value
                    self.highlight_stats[stat['shortName']] = value
        
        try:
            for table in data['sectionContent']['OVERVIEW']['tables']:
                if table['caption'] == 'Recent Games':
                    i = 0
                    while i < len(table['header']['cells']):
                        if 'name' in table['header']['cells'][i]:
                            stat_key = table['header']['cells'][i]['name']
                        else:
                            stat_key = table['header']['cells'][i]['key']
                        
                        self.recent_gameweeks_stats[stat_key] = [] # init empty

                        # get most recent 5 gameweeks stats (or less if not enough)
                        j = 0
                        while j < 5 and j < len(table['rows']):
                            gameweek_stat_value = table['rows'][j]['cells'][i]['content']
                            try:
                                # Validate that numeric_value can be converted to Decimal
                                decimal_gameweek_stat_value = Decimal(gameweek_stat_value)
                                self.recent_gameweeks_stats[stat_key].append(decimal_gameweek_stat_value) # append stat to list
                            except (InvalidOperation, ValueError):
                                # If conversion fails, use the original value
                                self.recent_gameweeks_stats[stat_key].append(gameweek_stat_value)
                            j += 1
                        i += 1
        except Exception as e:
            logger.error(f"Error processing recent trend stats: {e}")
            raise FantraxException(f"Error processing recent trend stats: {e}")

        # Finally, set priority value for gameweek
        self._update_fantasy_value_for_gameweek()
    
    def _update_fantasy_value_for_gameweek(self):
        """Update the fantasy value for the gameweek."""
        self.fantasy_value.value_for_gameweek += sum(self.recent_gameweeks_stats['Fantasy Points']) / len(self.recent_gameweeks_stats['Fantasy Points'])

    @property
    def is_benched_or_suspended_or_out_in_gameweek(self) -> bool:
        check_statuses = set(['benched', 'suspended', 'out', 'out-for-next-game'])
        return bool(check_statuses & self.icon_statuses)
    
    @property
    def is_uncertain_gametime_decision_in_gameweek(self) -> bool:
        check_statuses = set(['uncertain-gametime-decision'])
        return bool(check_statuses & self.icon_statuses)
    
    @property
    def is_starting_in_gameweek(self) -> bool:
        check_statuses = set(['starting'])
        return bool(check_statuses & self.icon_statuses)
    
    @property
    def is_expected_to_play_in_gameweek(self) -> bool:
        if not self.icon_statuses: # if no statuses, assume they are expected to play
            return True
        check_statuses = set(['expected-to-play'])
        return bool(check_statuses & self.icon_statuses)
    
    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        data = {}

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
