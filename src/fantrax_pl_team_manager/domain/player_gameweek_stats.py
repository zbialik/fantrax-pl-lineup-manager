import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
from decimal import Decimal, InvalidOperation
from datetime import datetime
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.domain.constants import *

logger = logging.getLogger(__name__)

@dataclass
class PlayerGameweekStats:
    """Data class representing a player's gameweek stats.
    
    Attributes:
    """
    date: str = None
    team: str = None
    home_or_away: str = None
    opponent: str = None
    score: str = None
    games_started: int = None
    minutes_played: int = None
    goals: int = None
    assists: int = None
    points: Decimal = None
    shots: int = None
    shots_on_target: int = None
    fouls_committed: int = None
    fouls_suffered: int = None
    yellow_cards: int = None
    red_cards: int = None
    offsides: int = None
    penalty_kick_goals: int = None