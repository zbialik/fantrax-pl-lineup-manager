from dataclasses import dataclass
import logging
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
