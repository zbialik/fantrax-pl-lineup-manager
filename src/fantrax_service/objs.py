from datetime import datetime, timedelta

class Player:
    """ Represents a single Player.

        Attributes:
            id (str): Player ID.
            name (str): Player Name.
            short_name (str): Player Short Name.
            team_name (str): Team Name.
            team_short_name (str): Team Short Name.
            pos_short_name (str): Player Positions.
            positions (List[Position]): Player Positions.

    """
    def __init__(self, api, data, transaction_type=None):
        self._api = api
        self.type = transaction_type
        self.id = data["scorerId"]
        self.name = data["name"]
        self.short_name = data["shortName"]
        self.team_name = data["teamName"]
        self.team_short_name = data["teamShortName"] if "teamShortName" in data else self.team_name
        self.pos_short_name = data["posShortNames"]
        self.positions = [self._api.positions[d] for d in data["posIdsNoFlex"]]
        self.all_positions = [self._api.positions[d] for d in data["posIds"]]
        self.injured = False
        self.suspended = False
        if "icons" in data:
            for icon in data["icons"]:
                if icon["typeId"] in ["1", "2", "6", "30"]: # DtD, Out, IR, Knee
                    self.injured = True
                elif icon["typeId"] == "6":
                    self.suspended = True


    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.type} {self.name}" if self.type else self.name


class Position:
    """ Represents a single Position.

        Attributes:
            id (str): Position ID.
            name (str): Position Name.
            short_name (str): Position Short Name.

    """
    def __init__(self, api, data):
        self._api = api
        self.id = data["id"]
        self.name = data["name"]
        self.short_name = data["shortName"]

    def __eq__(self, other):
        return (self.id, self.name, self.short_name) == (other.id, other.name, other.short_name)

class Team:
    """ Represents a single Team.

        Attributes:
            team_id (str): Team ID.
            name (str): Team Name.
            short (str): Team Short Name.

    """
    def __init__(self, api, team_id, name, short, logo):
        self._api = api
        self.team_id = team_id
        self.name = name
        self.short = short
        self.logo = logo

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.name


class Roster:
    def __init__(self, api, data, team_id):
        self._api = api
        self.team = self._api.team(team_id)
        
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
        
        self.rows = []
        try:
            for group in data.get("tables", []):
                for row in group.get("rows", []):
                    if "scorer" in row or row.get("statusId") == "1":
                        self.rows.append(Player(self._api, row))
        except Exception as e:
            print(f"Warning: Error processing roster rows: {e}")
            self.rows = []

    def get_player_by_name(self, player_name: str):
        """Find a player by name (case-insensitive partial match).
        
        Parameters:
            player_name (str): Player name to search for
            
        Returns:
            Player or None: The roster row containing the player, or None if not found
        """
        player_name_lower = player_name.lower()
        for row in self.rows:
            if row.player and player_name_lower in row.player.name.lower():
                return row
        return None

    def get_starters(self):
        """Get all players currently in starting positions.
        
        Returns:
            list: List of Player objects for starters
        """
        starters = []
        for row in self.rows:
            if row.player:
                if row.pos_id != "0":
                    starters.append(row)
        return starters

    def get_bench_players(self):
        """Get all players currently on the bench.
        
        Returns:
            list: List of Player objects for bench players
        """
        bench = []
        for row in self.rows:
            if row.player:
                if row.pos_id == "0":
                    bench.append(row)
        return bench

    def get_players_by_position(self, position_short_name: str):
        """Get all players at a specific position.
        
        Parameters:
            position_short_name (str): Position abbreviation (e.g., "F", "D", "G")
            
        Returns:
            list: List of Player objects for players at that position
        """
        return [row for row in self.rows if row.player and row.pos.short_name == position_short_name]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        rows = "\n".join([str(r) for r in self.rows])
        return f"{self.team} Roster\n{rows}"

class Player:
    def __init__(self, api, data):
        print(data)
        self._api = api

        if data["statusId"] == "1":
            self.pos_id = data["posId"]
            self.pos = self._api.positions[self.pos_id]
        elif data["statusId"] == "3":
            self.pos_id = "-1"
            self.pos = Position(self._api, {"id": "-1", "name": "Injured", "shortName": "IR"})
        else:
            self.pos_id = "0"
            self.pos = Position(self._api, {"id": "0", "name": "Reserve", "shortName": "Res"})

        self.player = None
        self.fppg = None
        if "scorer" in data:
            self.player = Player(self._api, data["scorer"])
            self.fppg = float(data["cells"][3]["content"])

        content = data["cells"][1]["content"]
        self.opponent = None
        self.time = None
        if content and content.endswith(("AM", "PM")):
            self.opponent, time_str = content.split("\u003cbr/\u003e")
            self.time = datetime.strptime(time_str.split(" ")[1], "%I:%M%p")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.player:
            return f"{self.pos.short_name}: {self.player}{f' vs {self.opponent}' if self.opponent else ''}"
        else:
            return f"{self.pos.short_name}: Empty"


