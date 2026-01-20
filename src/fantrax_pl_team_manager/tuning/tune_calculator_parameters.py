import os
from typing import Any, List
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead, BookingOddsHeadToHeadList
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.integrations.fantrax.fantrax_http_client import FantraxRequestsHTTPClient
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_gameweek_stats_mapper import FantraxPlayerGameweekStatsMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_roster_mapper import FantraxRosterMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_mapper import FantraxPlayerMapper

from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_premier_league_table_mapper import FantraxPremierLeagueTableMapper
from fantrax_pl_team_manager.integrations.the_odds_api.mappers.booking_odds_h2h_mapper import BookingOddsHeadToHeadMapper
from fantrax_pl_team_manager.domain.fantasy_roster import FantasyRoster
from fantrax_pl_team_manager.domain.fantasy_roster_player import FantasyRosterPlayer
from fantrax_pl_team_manager.integrations.fantrax.endpoints.roster import get_roster
from fantrax_pl_team_manager.integrations.fantrax.endpoints.premier_league_table import get_premier_league_table
from fantrax_pl_team_manager.integrations.the_odds_api.endpoints.odds_h2h import get_odds_h2h
from fantrax_pl_team_manager.integrations.the_odds_api.the_odds_api_http_client import TheOddsApiRequestsHTTPClient

from fantrax_pl_team_manager.domain.utils import write_datatype_to_json
import json
import copy
import logging

from fantrax_pl_team_manager.services.lineup_optimizer import optimize_lineup

logger = logging.getLogger(__name__)


def actual_best_lineup_for_gameweek(roster:FantasyRoster, gameweek: int) -> FantasyRoster:
    """Get the actual best lineup for a given gameweek."""
    actual_best_roster = copy.deepcopy(roster)
    for player in actual_best_roster:
        player.disable_lineup_change = False
        player.fantasy_value.value_for_gameweek = player.gameweek_stats[-1*gameweek + 1].points
    roster.sort_players_by_gameweek_status_and_fantasy_value()
    for player in actual_best_roster:
        player.change_to_reserve()
    for player in actual_best_roster:
        vs = actual_best_roster.valid_substitutions([player], disable_min_position_counts_check=True)
        if vs[0]:
            player.change_to_starter()
        else:
            logger.info(f"Player {player.name} cannot be promoted to starter: {vs[1]} for gameweek {gameweek}")
    
    logger.info(f"Starting lineup optimized to for gameweek {gameweek}: ")
    print(json.dumps(actual_best_roster.starting_lineup_by_position_short_name(), indent=2))
    return actual_best_roster

def actual_best_lineup_total_points_for_gameweek(roster:FantasyRoster, gameweek: int) -> FantasyRoster:
    """Get the actual best lineup for a given gameweek."""
    actual_best_roster = actual_best_lineup_for_gameweek(roster, gameweek)
    total_points = 0
    for player in actual_best_roster:
        if player.rostered_starter:
            total_points += player.fantasy_value.value_for_gameweek
    logger.info(f"Total points for actual best lineup for gameweek {gameweek}: {total_points}")
    return total_points

def compare_actual_best_lineup_and_optimized_lineup(roster:FantasyRoster, gameweek: int, parameter_samples: List[Any] = []) -> float:
        total_points = actual_best_lineup_total_points_for_gameweek(roster, gameweek)


        for p in parameter_samples:
            _roster = copy.deepcopy(roster)
            optimize_lineup(_roster, premier_league_table, odds_h2h_data) # TODO: update optimize_lineup to accept parameter sample

if __name__ == "__main__":
    odds_api_key = os.getenv('THE_ODDS_API_KEY')
    league_id = 'o90qdw15mc719reh'
    team_id = 'jassfpe6mc719rep'

    fantrax_http_client = FantraxRequestsHTTPClient(cookie_path="deploy/fantraxloggedin.cookie")  
    player_mapper = FantraxPlayerMapper()
    player_gameweek_stats_mapper = FantraxPlayerGameweekStatsMapper()
    roster_mapper = FantraxRosterMapper()
    premier_league_table_mapper = FantraxPremierLeagueTableMapper()
    odds_h2h_mapper = BookingOddsHeadToHeadMapper()
    the_odds_api_http_client = TheOddsApiRequestsHTTPClient(api_key=odds_api_key)

    roster:FantasyRoster = get_roster(fantrax_http_client, roster_mapper, player_mapper, player_gameweek_stats_mapper, league_id, team_id)
    premier_league_table:PremierLeagueTable = get_premier_league_table(fantrax_http_client, premier_league_table_mapper)
    odds_h2h_data: BookingOddsHeadToHeadList = get_odds_h2h(the_odds_api_http_client, odds_h2h_mapper)
    write_datatype_to_json(odds_h2h_data)

    # # run comparison between actual best lineup and optimized lineup (using various parameter inputs) for each gameweek
    # for gameweek in range(10, len(roster[0].gameweek_stats)):
    #     roster:FantasyRoster = get_roster(fantrax_http_client, roster_mapper, player_mapper, player_gameweek_stats_mapper, league_id, team_id, period=gameweek)


        # total_points = actual_best_lineup_total_points_for_gameweek(roster, gameweek)
        # _roster = copy.deepcopy(roster)
        # optimize_lineup(_roster, premier_league_table, odds_h2h_data)
        # total_points = actual_best_lineup_total_points_for_gameweek(_roster, gameweek)
        # logger.info(f"Total points for optimized lineup for gameweek {gameweek}: {total_points}")
