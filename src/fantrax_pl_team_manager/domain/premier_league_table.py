import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set
logger = logging.getLogger(__name__)

@dataclass
class PremierLeagueTeamStats:
    """Data class representing the stats for a team in the Premier League table.
    
    Attributes:
        rank: Rank of the team
        stats: Dictionary of stats for the team
    """
    games_played: int = None
    wins: int = None
    losses: int = None
    ties_or_overtime_losses: int = None
    points: int = None
    goals_for: int = None
    goals_against: int = None
    goal_difference: int = None
    home_record: str = None
    away_record: str = None
    last_ten_record: str = None
    current_streak: str = None

@dataclass
class PremierLeagueTeam:
    """Data class representing a team in the Premier League table.
    
    Attributes:
        rank: Rank of the team
        stats: Dictionary of stats for the team
    """
    rank: int
    stats: PremierLeagueTeamStats = None

@dataclass
class PremierLeagueTable(Dict[str, PremierLeagueTeam]):
    """Data class representing the Premier League table.
    
    Attributes:
        rank: Rank of the team
        stats: Dictionary of stats for the team
    """
