import logging
from typing import List, Optional

from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead
from fantrax_pl_team_manager.domain.constants import *
from fantrax_pl_team_manager.domain.fantasy_player import FantasyPlayer
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.exceptions import FantraxException
import math

logger = logging.getLogger(__name__)

def calculate_fantasy_value_for_gameweek(player: FantasyPlayer, player_gameweek_stats: List[PlayerGameweekStats], premier_league_table: PremierLeagueTable, odds_h2h_data_for_upcoming_game: Optional[BookingOddsHeadToHead]) -> float:
    """Calculate the fantasy value of a player.
    
    Args:
        player: The player to calculate the fantasy value of.
        premier_league_table: Premier League table.
        odds_h2h_data_for_upcoming_game: Booking odds data for the upcoming game.
        
    Returns:
        The fantasy value of the player.
    """
    fantasy_value_for_gameweek: float = 0.0
    
    # Initialize fantasy value using recent gameweeks stats
    fantasy_points = [gameweek_stat.points for gameweek_stat in player_gameweek_stats]
    if fantasy_points:
        avg_fantasy_points = sum(fantasy_points) / len(fantasy_points)
        fantasy_value_for_gameweek += avg_fantasy_points

    # Update fantasy value based on booking odds
    if odds_h2h_data_for_upcoming_game:
        logger.info(f"Head-to-head booking odds data available for {player.team_name} vs {player.upcoming_game_opponent}, using for fixture difficulty coefficient")
        booking_odds_coefficient = _calc_fixture_difficulty_coefficient_with_booking_odds(player, odds_h2h_data_for_upcoming_game)
        fantasy_value_for_gameweek *= float(booking_odds_coefficient)
    else:
        logger.info(f"No head-to-head booking odds data available for {player.team_name} vs {player.upcoming_game_opponent}, using league standings for fixture difficulty coefficient")
        # Update fantasy value based on difficulty of upcoming game
        upcoming_game_coefficient = _calc_fixture_difficulty_coefficient_with_league_standings(player, premier_league_table)
        fantasy_value_for_gameweek *= float(upcoming_game_coefficient)
    
    return fantasy_value_for_gameweek

def _calc_fixture_difficulty_coefficient_with_league_standings(
    player: FantasyPlayer,
    premier_league_table: PremierLeagueTable,
    k: float = 0.8,
    a: float = 0.4) -> float:
    """Calculate coefficient for upcoming game difficulty.
    
    Uses a hyperbolic tangent function to adjust fantasy value based on the
    relative strength difference between the player's team and their opponent.
    
    Parameters:
        player: The player whose fantasy value is being calculated.
        premier_league_table: Premier League table.
        k: Scaling factor for the coefficient (default: 0.7)
        a: Scaling factor for rank difference (default: 1)
        
    Returns:
        float: Coefficient multiplier for fantasy value
        
    Raises:
        FantraxException: If team or opponent not found in Premier League stats
    """
    logger.debug(f"Calculating upcoming game coefficient for {player.team_name} vs {player.upcoming_game_opponent}")
    
    team = premier_league_table.get(player.team_name)
    opponent = premier_league_table.get(player.upcoming_game_opponent)
    
    if team is None:
        error_msg = f"Team {player.team_name} not found in Premier League team stats"
        logger.error(error_msg)
        raise FantraxException(error_msg)
    
    if opponent is None:
        error_msg = f"Opponent {player.upcoming_game_opponent} not found in Premier League team stats"
        logger.error(error_msg)
        raise FantraxException(error_msg)
    
    team_rank = team.rank
    opponent_rank = opponent.rank
    total_teams = len(premier_league_table.keys())
    
    # Calculate coefficient using hyperbolic tangent function
    def coefficient_calculation(team_rank, opponent_rank, total_teams, _k=k, _a=a):
        return 1 + _k * math.tanh(_a * (team_rank - opponent_rank) / (total_teams - 1))
    coefficient = coefficient_calculation(team_rank, opponent_rank, total_teams, k)
    logger.debug(f"Fixture difficulty coefficient range (from league standing): [{coefficient_calculation(1,total_teams,total_teams,k,a)},{coefficient_calculation(total_teams,1,total_teams,k,a)}]")
    
    return coefficient

def _calc_fixture_difficulty_coefficient_with_booking_odds(
    player: FantasyPlayer,
    odds_h2h_data: BookingOddsHeadToHead,
    k: float = 0.3) -> float:
    """Calculate coefficient based on booking odds for the upcoming game.
    
    Teams with higher booking odds may play more aggressively, which can lead to
    more defensive actions (tackles, interceptions) that score fantasy points.
    However, actual bookings result in negative fantasy points. This coefficient
    balances these factors.
    
    Parameters:
        player: The player whose fantasy value is being calculated.
        odds_h2h_data: Booking odds data for the upcoming game.
        k: Scaling factor for the booking odds coefficient (default: 0.15)
        
    Returns:
        float: Coefficient multiplier for fantasy value based on booking odds
    """
    if odds_h2h_data is None:
        return 1.0
    
    # Determine if player's team is home or away
    # First check if team name matches directly, then use home_or_away as fallback
    if odds_h2h_data.home_team == player.team_name:
        is_home = True
    elif odds_h2h_data.away_team == player.team_name:
        is_home = False
    elif player.upcoming_game_home_or_away and player.upcoming_game_home_or_away.lower() == 'home':
        is_home = True
    else:
        # Default to away if we can't determine
        is_home = False
        logger.warning(f"Could not determine home/away status for {player.team_name} in booking odds data. Defaulting to away.")
    
    # Get the appropriate booking odds for the player's team
    if is_home:
        player_team_booking_odds = odds_h2h_data.home_team_booking_odds_outcome
        opponent_team_booking_odds = odds_h2h_data.away_team_booking_odds_outcome
    else:
        player_team_booking_odds = odds_h2h_data.away_team_booking_odds_outcome
        opponent_team_booking_odds = odds_h2h_data.home_team_booking_odds_outcome
    
    # If booking odds are not available, return neutral coefficient
    if player_team_booking_odds is None or opponent_team_booking_odds is None:
        logger.debug(f"Booking odds not available for {player.team_name} vs {player.upcoming_game_opponent}")
        return 1.0
    
    # Calculate relative booking probability
    # Higher odds for player's team indicates more aggressive play (potential for more tackles/interceptions)
    # But also higher risk of actual bookings (negative points)
    # Use a normalized difference to create a coefficient
    total_booking_odds = player_team_booking_odds + opponent_team_booking_odds + (odds_h2h_data.draw_booking_odds_outcome or 0)
    
    if total_booking_odds == 0:
        return 1.0
    
    # Calculate the probability that player's team gets more bookings
    player_team_booking_probability = player_team_booking_odds / total_booking_odds
    
    # Create a coefficient that slightly boosts fantasy value when booking odds are higher
    # (more aggressive play = more defensive actions), but not too much (actual bookings are negative)
    def coefficient_calculation(player_team_booking_probability, _k=k):
        return 1 + _k * (player_team_booking_probability - 0.5) * 2
    coefficient = coefficient_calculation(player_team_booking_probability, k)
    logger.debug(f"Booking odds coefficient range: [{coefficient_calculation(0,k)},{coefficient_calculation(1,k)}]")
    logger.debug(f"Booking odds coefficient for {player.team_name}: {coefficient:.3f} (player team booking odds: {player_team_booking_odds:.2f}, prob: {player_team_booking_probability:.3f})")
    
    return coefficient