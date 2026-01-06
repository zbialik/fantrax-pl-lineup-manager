import sys
import os
import asyncio
import logging
from fantrax_pl_team_manager.domain.fantrax_roster import FantraxRoster
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.integrations.fantrax.fantrax_http_client import FantraxRequestsHTTPClient
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_mapper import FantraxPlayerMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_roster_mapper import FantraxRosterMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_premier_league_table_mapper import FantraxPremierLeagueTableMapper
from fantrax_pl_team_manager.integrations.fantrax.endpoints.players import get_player
from fantrax_pl_team_manager.integrations.fantrax.endpoints.roster import get_roster, update_roster
from fantrax_pl_team_manager.integrations.fantrax.endpoints.premier_league_table import get_premier_league_table

import argparse

logger = logging.getLogger(__name__)

async def main(
    http: FantraxRequestsHTTPClient, 
    player_mapper: FantraxPlayerMapper, 
    roster_mapper: FantraxRosterMapper, 
    premier_league_table_mapper: FantraxPremierLeagueTableMapper, 
    league_id: str, 
    team_id: str, 
    update_lineup_interval: int, 
    run_once: bool = False
) -> None:
    """Run the roster manager."""
    _running = True
    logger.info("Fantrax Premier League Team Manager running")
    
    roster:FantraxRoster = get_roster(http, roster_mapper, premier_league_table_mapper, player_mapper, league_id, team_id)
    
    if run_once:
        logger.info("Running once, optimizing lineup")
        await asyncio.to_thread(roster.optimize_lineup)
        await asyncio.to_thread(update_roster, http, league_id, team_id, roster)
        return
    
    while _running:
        try:
            await asyncio.to_thread(roster.optimize_lineup)
            await asyncio.to_thread(update_roster, http, league_id, team_id, roster)
        except Exception as e:
            logger.error(f"Error during lineup optimization: {e}", exc_info=True)
        
        await asyncio.sleep(update_lineup_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--cookie-path", type=str, default="deploy/fantraxloggedin.cookie", required=False)
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
    
    http = FantraxRequestsHTTPClient(cookie_path=args.cookie_path)
    player_mapper = FantraxPlayerMapper()
    roster_mapper = FantraxRosterMapper()
    premier_league_table_mapper = FantraxPremierLeagueTableMapper()
    
    try:
        asyncio.run(main(http, player_mapper, roster_mapper, premier_league_table_mapper, args.league_id, args.team_id, args.update_lineup_interval, run_once=args.run_once))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)