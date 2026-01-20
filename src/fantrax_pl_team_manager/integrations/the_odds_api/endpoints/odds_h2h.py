from typing import List
from fantrax_pl_team_manager.integrations.the_odds_api.protocols import HttpClient, Mapper
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead, BookingOddsHeadToHeadList
import logging

logger = logging.getLogger(__name__)

def get_odds_h2h(http: HttpClient, mapper: Mapper[BookingOddsHeadToHeadList]) -> BookingOddsHeadToHeadList:
    """Get the odds for a head to head match.

    Returns:
        BookingOddsHeadToHeadList: Booking odds for a head to head match
    """
    obj = http.the_odds_api_request('/v4/sports/soccer_epl/odds', params={
        'regions': 'us',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso',
    })
    return mapper.from_json(obj)
