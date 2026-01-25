from datetime import datetime, timedelta
import os
import json
from dataclasses import asdict
import logging
from typing import Any
from zoneinfo import ZoneInfo
from fantrax_pl_team_manager.domain.fantasy_roster import FantasyRoster

logger = logging.getLogger(__name__)

def write_datatype_to_json(data: Any, data_dir: str = "data") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    os.makedirs(data_dir, exist_ok=True)
    
    if isinstance(data,list):
        if len(data) > 0:
            datatype = type(data[0]).__name__.lower()
            filename = os.path.join(data_dir, f"list_{datatype}_{timestamp}.json")
            with open(filename, 'w') as f:
                json.dump([asdict(d) for d in data], f, indent=2)
        else:
            logger.warning(f"No data to write to filesystem.")
            return
    else:
        datatype = type(data).__name__.lower()
        filename = os.path.join(data_dir, f"{datatype}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(asdict(data), f, indent=2)
    logger.info(f"Saved data to {filename}")

def match_time_within_window(current_datetime: datetime, target_match_datetime: datetime, update_lineup_interval: int) -> bool:
    """Check if the match is within the time window."""
    if target_match_datetime is None:
        logger.info(f"Target match datetime is None, returning False")
        return False
    # Match is within 1 hour of start time
    if current_datetime + timedelta(hours=1) <= target_match_datetime:
        logger.info(f"Match is not within 1 hour of start time, returning False")
        return False
    # Update lineup interval has not passed
    if current_datetime + timedelta(hours=1) - target_match_datetime > timedelta(seconds=update_lineup_interval):
        logger.info(f"Update lineup interval has passed, returning False")
        return False
    return True

def premier_league_match_within_time_window(roster:FantasyRoster, update_lineup_interval: int) -> bool:
    """Check if the premier league match is within the time window."""
    current_datetime = datetime.now(ZoneInfo("America/Los_Angeles")).replace(tzinfo=None)
    logger.info(f"Checking if any upcoming match is within the time window (current datetime: {current_datetime}, update lineup interval: {update_lineup_interval})")
    for p in roster:
        logger.info(f"{p.name} has upcoming game datetime: {p.upcoming_game_datetime}")
        if match_time_within_window(current_datetime, p.upcoming_game_datetime, update_lineup_interval):
            logger.info(f"Match for {p.name} is within time window constraints")
            return True
    return False
