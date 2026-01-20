from dataclasses import dataclass
import json
import logging
from typing import List, Optional
from fantrax_pl_team_manager.domain.constants import *

logger = logging.getLogger(__name__)

@dataclass
class BookingOddsHeadToHead:
    """Data class representing booking odds for a head to head match.
    
    Attributes:
    """
    home_team: str = None
    away_team: str = None
    home_team_booking_odds_outcome: float = None
    away_team_booking_odds_outcome: float = None
    draw_booking_odds_outcome: float = None


class BookingOddsHeadToHeadList (List[BookingOddsHeadToHead]):
    def __init__(self, iterable: Optional[List[BookingOddsHeadToHead]] = [], filename: str = None):
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
                super().__init__([BookingOddsHeadToHead(**d) for d in data])
        else:
            super().__init__(iterable)
