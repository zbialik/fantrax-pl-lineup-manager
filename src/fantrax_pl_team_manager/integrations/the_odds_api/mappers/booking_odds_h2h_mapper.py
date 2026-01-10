from typing import Any, Dict, Mapping, List
from statistics import median
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead
from fantrax_pl_team_manager.integrations.the_odds_api.constants import BOOKING_ODDS_TEAM_NAME_MAP
import logging

logger = logging.getLogger(__name__)

class BookingOddsHeadToHeadMapper:
    def from_json(self, obj: Mapping[str, Any]) -> List[BookingOddsHeadToHead]:
        data = obj

        booking_odds_h2h_list: List[BookingOddsHeadToHead] = []

        for event in data:
            _home_team = event['home_team']
            _away_team = event['away_team']

            _home_team_outcomes = []
            _away_team_outcomes = []
            _draw_outcome = []
            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == _home_team:
                                _home_team_outcomes.append(float(outcome['price']))
                            elif outcome['name'] == _away_team:
                                _away_team_outcomes.append(float(outcome['price']))
                            elif outcome['name'] == 'Draw':
                                _draw_outcome.append(float(outcome['price']))
                            else:
                                logger.error(f"Unknown outcome for bookmaker '{bookmaker['title']}' and market '{market['key']}': {outcome['name']} does not match either '{_home_team}' or '{_away_team}' or 'Draw'")
                                continue
            # Get the median of the home team outcomes, away team outcomes, and draw outcome
            home_team_outcome = median(_home_team_outcomes) if _home_team_outcomes else None
            away_team_outcome = median(_away_team_outcomes) if _away_team_outcomes else None
            draw_outcome = median(_draw_outcome) if _draw_outcome else None
            
            booking_odds_h2h: BookingOddsHeadToHead = BookingOddsHeadToHead(
                home_team=BOOKING_ODDS_TEAM_NAME_MAP[_home_team],
                away_team=BOOKING_ODDS_TEAM_NAME_MAP[_away_team],
                home_team_booking_odds_outcome=home_team_outcome,
                away_team_booking_odds_outcome=away_team_outcome,
                draw_booking_odds_outcome=draw_outcome,
            )
            booking_odds_h2h_list.append(booking_odds_h2h)

        return booking_odds_h2h_list
