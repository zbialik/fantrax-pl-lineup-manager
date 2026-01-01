import sys
import os
import asyncio
import logging

from fantrax_pl_team_manager.clients.fantraxclient import FantraxClient
from fantrax_pl_team_manager.services.gameweek_manager import GameweekManager

import argparse

if __name__ == "__main__":
    # Configure logging to output to stdout
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--init-cookie-auth", action="store_true", default=False, required=False)
    parser.add_argument("--cookie-path", type=str, default="deploy/fantraxloggedin.cookie", required=False)
    parser.add_argument("--fantrax-username", type=str, default=os.getenv('FANTRAX_USERNAME'), required=False)
    parser.add_argument("--fantrax-password", type=str, default=os.getenv('FANTRAX_PASSWORD'), required=False)
    parser.add_argument("--update-lineup-interval", type=int, default=600, required=False)
    parser.add_argument("--run-once", action="store_true", default=False, required=False)
    args = parser.parse_args()
    
    client = FantraxClient(
        league_id=args.league_id,
        init_cookie_auth=args.init_cookie_auth,
        cookie_path=args.cookie_path, 
        fantrax_username=args.fantrax_username, 
        fantrax_password=args.fantrax_password
    )
    gameweek_manager = GameweekManager(
        client=client, 
        team_id=args.team_id, 
        update_lineup_interval=args.update_lineup_interval, 
        run_once=args.run_once
    )
    try:
        asyncio.run(gameweek_manager.run())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)


docker run -dit --name fantrax-pl-team-manager -e LEAGUE_ID=o90qdw15mc719reh -e TEAM_ID=jassfpe6mc719rep -e FANTRAX_USERNAME=${FANTRAX_USERNAME} -e FANTRAX_PASSWORD=${FANTRAX_PASSWORD} --entrypoint python zach17/fantrax-pl-team-manager:latest -m fantrax_pl_team_manager --update-lineup-interval 5 --init-cookie-auth