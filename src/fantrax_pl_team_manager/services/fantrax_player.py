import json
import inspect
from dataclasses import dataclass
from typing import List, Set

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

@dataclass
class FantasyValue:
    value_for_gameweek: int = 0
    value_for_future_gameweeks: int = 0

class FantraxPlayer:
    def __init__(self, fantrax_player_row):
        self.name = fantrax_player_row['scorer']['name']
        self.team_name = fantrax_player_row['scorer']['teamName']
        self.id = fantrax_player_row['scorer']['scorerId']
        self.rostered_status_id = fantrax_player_row['statusId']
        self.rostered_position_id = fantrax_player_row['posId']
        self.disable_lineup_change = fantrax_player_row["scorer"].get("disableLineupChange",False)
        self.icons = fantrax_player_row["scorer"].get("icons",[])
        self.icon_statuses: Set[str] = set([STATUS_ICON_MAP_BY_ID.get(icon["typeId"]) for icon in self.icons if icon["typeId"] in STATUS_ICON_MAP_BY_ID])

        self.fantasy_value = FantasyValue()
        self.update_value_for_gameweek()

    @property
    def rostered_starter(self) -> bool:
        return True if self.rostered_status_id == "1" else False
    
    @property
    def rostered_position_short_name(self) -> str:
        return POSITION_MAP_BY_ID.get(self.rostered_position_id)
    
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

    def update_value_for_gameweek(self):
        """Update the value for the gameweek."""
        # VALUE: Prefer 'starting' > 'expected-to-play' > others
        if self.is_starting_in_gameweek:
            self.fantasy_value.value_for_gameweek += 3
        elif self.is_expected_to_play_in_gameweek:
            self.fantasy_value.value_for_gameweek += 2
        elif self.is_uncertain_gametime_decision_in_gameweek:
            self.fantasy_value.value_for_gameweek += 1
    
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
