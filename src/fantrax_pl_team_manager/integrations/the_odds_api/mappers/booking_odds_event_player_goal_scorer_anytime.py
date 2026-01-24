from typing import Any, Mapping
from statistics import median
from fantrax_pl_team_manager.domain.booking_odds_event_player_goal_scorer_anytime import BookingOddsEventPlayerGoalScorerAnytimeList, BookingOddsEventPlayerGoalScorerAnytime
import logging

logger = logging.getLogger(__name__)

class BookingOddsEventPlayerGoalScorerAnytimeMapper:
    def from_json(self, obj: Mapping[str, Any]) -> BookingOddsEventPlayerGoalScorerAnytimeList:
        data = obj
        out = BookingOddsEventPlayerGoalScorerAnytimeList()
        
        _outcomes = {} # key is player name, value is list of prices
        for bookmaker in data['bookmakers']:
            for market in bookmaker['markets']:
                if market['key'] == 'player_goal_scorer_anytime':
                    for outcome in market['outcomes']:
                        if outcome['name'] == 'Yes':
                            if outcome['description'] not in _outcomes:
                                _outcomes[outcome['description']] = []
                            _outcomes[outcome['description']].append(float(outcome['price']))
        
        for player_name, prices in _outcomes.items():
            out.append(BookingOddsEventPlayerGoalScorerAnytime(
                player_name=player_name,
                outcome_price=median(prices) # use median price from all bookmakers for this player
            ))
        return out
