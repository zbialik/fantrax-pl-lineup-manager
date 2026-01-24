from dataclasses import dataclass
import json
import logging
from typing import List, Optional
from fantrax_pl_team_manager.domain.constants import *

logger = logging.getLogger(__name__)

@dataclass
class BookingOddsEventPlayerGoalScorerAnytime:
    """Data class representing booking odds for an event market.
    
    Attributes:
    """
    player_name: str = None
    outcome_price: float = None


class BookingOddsEventPlayerGoalScorerAnytimeList (List[BookingOddsEventPlayerGoalScorerAnytime]):
    def __init__(self, iterable: Optional[List[BookingOddsEventPlayerGoalScorerAnytime]] = [], filename: str = None):
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
                super().__init__([BookingOddsEventPlayerGoalScorerAnytime(**d) for d in data])
        else:
            super().__init__(iterable)
