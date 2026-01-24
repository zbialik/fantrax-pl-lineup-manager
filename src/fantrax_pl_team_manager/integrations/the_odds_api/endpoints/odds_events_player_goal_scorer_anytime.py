from typing import List, Set
from fantrax_pl_team_manager.domain.booking_odds_event_player_goal_scorer_anytime import BookingOddsEventPlayerGoalScorerAnytimeList
from fantrax_pl_team_manager.integrations.the_odds_api.constants import BOOKING_ODDS_TEAM_NAME_MAP
from fantrax_pl_team_manager.integrations.the_odds_api.protocols import HttpClient, Mapper
import logging

logger = logging.getLogger(__name__)

def get_odds_events_player_goal_scorer_anytime(the_odds_api_http_client: HttpClient, mapper: Mapper[BookingOddsEventPlayerGoalScorerAnytimeList], matches_to_include: Set[List[str]]) -> BookingOddsEventPlayerGoalScorerAnytimeList:
    """Get the odds for a events player goal scorer anytime markets.

    Returns:
        BookingOddsEventPlayerGoalScorerAnytimeList: Booking odds for a event player goal scorer anytime market
    """
    events = the_odds_api_http_client.the_odds_api_request('/v4/sports/soccer_epl/events', params={
        'dateFormat': 'iso',
    })

    event_ids_to_get_market_for = set[str]()
    for event in events:
        domain_home_team=BOOKING_ODDS_TEAM_NAME_MAP[event['home_team']]
        domain_away_team=BOOKING_ODDS_TEAM_NAME_MAP[event['away_team']]
        if tuple([domain_home_team, domain_away_team]) in matches_to_include:
            event_ids_to_get_market_for.add(event['id'])
    
    out: BookingOddsEventPlayerGoalScorerAnytimeList = BookingOddsEventPlayerGoalScorerAnytimeList()
    for event_id in event_ids_to_get_market_for:
        obj = the_odds_api_http_client.the_odds_api_request(f"/v4/sports/soccer_epl/events/{event_id}/odds", params={
            'regions': 'us',
            'markets': 'player_goal_scorer_anytime',
            'oddsFormat': 'decimal',
            'dateFormat': 'iso',
        })
        out.extend(mapper.from_json(obj)) # extend the list with the new data
    return out
