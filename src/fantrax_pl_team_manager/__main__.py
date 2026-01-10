import sys
import os
import asyncio
import logging
from fantrax_pl_team_manager.domain.fantasy_roster import FantasyRoster
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.integrations.fantrax.fantrax_http_client import FantraxRequestsHTTPClient
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_mapper import FantraxPlayerMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_roster_mapper import FantraxRosterMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_premier_league_table_mapper import FantraxPremierLeagueTableMapper
from fantrax_pl_team_manager.integrations.fantrax.endpoints.roster import get_roster, update_roster
from fantrax_pl_team_manager.integrations.fantrax.endpoints.premier_league_table import get_premier_league_table
from fantrax_pl_team_manager.services.lineup_optimizer import optimize_lineup
from fantrax_pl_team_manager.integrations.the_odds_api.endpoints.odds_h2h import get_odds_h2h
from fantrax_pl_team_manager.integrations.the_odds_api.mappers.booking_odds_h2h_mapper import BookingOddsHeadToHeadMapper
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead
from fantrax_pl_team_manager.integrations.the_odds_api.the_odds_api_http_client import TheOddsApiRequestsHTTPClient
from typing import List
import argparse
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def premier_league_match_within_time_window(roster:FantasyRoster, update_lineup_interval: int) -> bool:
    """Check if the premier league match is within the time window."""
    for p in roster:
        if p.upcoming_game_datetime is not None and (
            # Match is within 1 hour of start time
            datetime.now() + timedelta(hours=1) > p.upcoming_game_datetime) and (
            # Update lineup interval has not passed
            datetime.now() + timedelta(hours=1) - p.upcoming_game_datetime <= timedelta(seconds=update_lineup_interval)):
            return True
    return False

async def main(
    fantrax_http_client: FantraxRequestsHTTPClient, 
    the_odds_api_http_client: TheOddsApiRequestsHTTPClient, 
    player_mapper: FantraxPlayerMapper, 
    roster_mapper: FantraxRosterMapper, 
    premier_league_table_mapper: FantraxPremierLeagueTableMapper, 
    odds_h2h_mapper: BookingOddsHeadToHeadMapper,
    league_id: str, 
    team_id: str, 
    update_lineup_interval: int, 
    run_once: bool = False
) -> None:
    """Run the roster manager."""
    _running = True
    logger.info("Fantrax Premier League Team Manager running")
    
    roster:FantasyRoster = get_roster(fantrax_http_client, roster_mapper, player_mapper, league_id, team_id)
    odds_h2h_data: List[BookingOddsHeadToHead] = get_odds_h2h(the_odds_api_http_client, odds_h2h_mapper) # always refresh odds data on restart
    premier_league_table:PremierLeagueTable = get_premier_league_table(fantrax_http_client, premier_league_table_mapper)
    _roster_limit_period: int = roster.roster_limit_period

    if run_once:
        logger.info("Running once, optimizing lineup")
        await asyncio.to_thread(optimize_lineup, roster, premier_league_table, odds_h2h_data)
        await asyncio.to_thread(update_roster, fantrax_http_client, league_id, team_id, roster)
        return
    
    while _running:
        try:
            # Check if premier league match is within reasonable time window to refresh odds data
            if premier_league_match_within_time_window(roster, update_lineup_interval):
                logger.info(f"An upcoming match is within time window to refresh booking odds data, doing so now...")
                odds_h2h_data: List[BookingOddsHeadToHead] = get_odds_h2h(the_odds_api_http_client, odds_h2h_mapper)
            else:
                logger.info(f"No upcoming match is within time window to refresh booking odds data, skipping...")
            
            await asyncio.to_thread(optimize_lineup, roster, premier_league_table, odds_h2h_data)
            await asyncio.to_thread(update_roster, fantrax_http_client, league_id, team_id, roster)
            
            roster = get_roster(fantrax_http_client, roster_mapper, player_mapper, league_id, team_id)
            premier_league_table:PremierLeagueTable = get_premier_league_table(fantrax_http_client, premier_league_table_mapper)
        except Exception as e:
            logger.error(f"Error during lineup optimization: {e}", exc_info=True)
        
        await asyncio.sleep(update_lineup_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--cookie-path", type=str, default="deploy/fantraxloggedin.cookie", required=False)
    parser.add_argument("--odds-api-key", type=str, default=os.getenv('THE_ODDS_API_KEY'), required=False)
    parser.add_argument("--update-lineup-interval", type=int, default=600, required=False)
    parser.add_argument("--run-once", action="store_true", default=False, required=False)
    parser.add_argument("--log-level", type=str, default="info", required=False)
    args = parser.parse_args()

    # Configure logging to output to stdout
    if args.log_level == "debug":
        log_level = logging.DEBUG
    elif args.log_level == "info":
        log_level = logging.INFO
    elif args.log_level == "warning":
        log_level = logging.WARNING
    elif args.log_level == "error":
        log_level = logging.ERROR
    else:
        log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    fantrax_http_client = FantraxRequestsHTTPClient(cookie_path=args.cookie_path)
    the_odds_api_http_client = TheOddsApiRequestsHTTPClient(api_key=args.odds_api_key)
    player_mapper = FantraxPlayerMapper()
    roster_mapper = FantraxRosterMapper()
    premier_league_table_mapper = FantraxPremierLeagueTableMapper()
    odds_h2h_mapper = BookingOddsHeadToHeadMapper()
    try:
        asyncio.run(main(fantrax_http_client, the_odds_api_http_client, player_mapper, roster_mapper, premier_league_table_mapper, odds_h2h_mapper, args.league_id, args.team_id, args.update_lineup_interval, run_once=args.run_once))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)