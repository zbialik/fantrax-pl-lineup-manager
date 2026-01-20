from typing import List, Optional
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.domain.fantasy_roster import FantasyRoster
from fantrax_pl_team_manager.services.fantasy_value_calculator import calculate_fantasy_value_for_gameweek
import logging
import json

logger = logging.getLogger(__name__)

def optimize_lineup(roster: FantasyRoster, premier_league_table: PremierLeagueTable, odds_h2h_data: List[BookingOddsHeadToHead] = []):
    """Optimize the lineup for the current roster."""

    logger.info(f"Starting optimize_lineup() for current roster")
    
    # Calculate the fantasy value for each player for the current gameweek
    logger.info(f"Calculating fantasy value for each player for the current gameweek")
    for player in roster:
        odds_h2h_data_for_upcoming_game: Optional[BookingOddsHeadToHead] = None
        if odds_h2h_data:
            for o in odds_h2h_data:
                if (o.home_team == player.upcoming_game_opponent and o.away_team == player.team_name) or (o.away_team == player.upcoming_game_opponent and o.home_team == player.team_name):
                    odds_h2h_data_for_upcoming_game = o
                    break
        fantasy_value_for_gameweek = calculate_fantasy_value_for_gameweek(player, player.gameweek_stats, premier_league_table, odds_h2h_data_for_upcoming_game)
        player.fantasy_value.value_for_gameweek = fantasy_value_for_gameweek
    
    # Sort the players by gameweek status and fantasy value for gameweek
    logger.info(f"Sorting players by gameweek status and fantasy value for gameweek")
    roster.sort_players_by_gameweek_status_and_fantasy_value()
    
    # Reset all players as reserves unless they are locked from lineup changes
    logger.info(f"Resetting all players as reserves unless they are locked from lineup changes")
    for player in roster:
        if not player.disable_lineup_change:
            player.change_to_reserve()
    
    # Iterate through players and promote to starter unless they are an invalid substitution
    logger.info(f"Iterating through players to promote to starter unless they are an invalid substitution")
    for player in roster:
        if player.disable_lineup_change:
            logger.info(f"Player {player.name} is locked from lineup changes, skipping")
        else:
            vs = roster.valid_substitutions([player], disable_min_position_counts_check=True)
            if vs[0]:
                logger.info(f"Promoting {player.name} to starter")
                player.change_to_starter()
            else:
                logger.info(f"Player {player.name} cannot be promoted to starter: {vs[1]}")
    
    logger.info(f"Starting lineup optimized to: ")
    print(json.dumps(roster.starting_lineup_by_position_short_name(), indent=2))
