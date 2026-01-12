from typing import Any, Dict, Mapping, List
from datetime import datetime
from fantrax_pl_team_manager.domain.fantasy_player import FantasyPlayer, FantasyValue
from fantrax_pl_team_manager.exceptions import FantraxException

from fantrax_pl_team_manager.domain.constants import *
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
import logging

logger = logging.getLogger(__name__)


class FantraxPlayerMapper:
    """Mapper for Fantrax player data."""
    def from_json(self, dto: Mapping[str, Any], player_id:int) -> FantasyPlayer:
        def _parse_basic_info(player:FantasyPlayer, data: Dict[str, Any]) -> None:
            """Parse basic player information from data."""
            player.name = data['miscData'].get('name')
            player.icon_statuses = set([
                STATUS_ICON_MAP_BY_ID.get(icon["typeId"])
                for icon in data['miscData'].get('icons', [])
                if icon.get("typeId") in STATUS_ICON_MAP_BY_ID
            ])
        
        def _parse_highlight_stats(player:FantasyPlayer, data: Dict[str, Any]) -> None:
            """Parse highlight statistics from data."""
            highlight_stats_list = data['miscData'].get('highlightStats', [])
            for stat in highlight_stats_list:
                if 'shortName' not in stat or 'value' not in stat:
                    continue
                
                value = stat['value']
                if isinstance(value, str) and value.endswith('%'):
                    value = value.rstrip('%')
                
                try:
                    float_value = float(value)
                    player.highlight_stats[stat['shortName']] = float_value / 100
                except (ValueError):
                    # If conversion fails, use the original value
                    player.highlight_stats[stat['shortName']] = value
        
        def _parse_overview_tables(player:FantasyPlayer, data: Dict[str, Any]) -> None:
            """Parse overview tables (Upcoming Games, Recent Games) from data."""
            try:
                tables = data.get('sectionContent', {}).get('OVERVIEW', {}).get('tables', [])
                for table in tables:
                    if table.get('caption') == 'Upcoming Games':
                        _parse_upcoming_games_table(player, table)
                    elif table.get('caption') == 'Recent Games':
                        _parse_player_team_name(player, table)
            except Exception as e:
                logger.error(f"Error processing overview tables: {e}")
                raise FantraxException(f"Error processing overview tables: {e}")
        
        def _parse_upcoming_games_table(player:FantasyPlayer, table: Dict[str, Any]) -> None:
            """Parse upcoming games table to extract opponent and home/away status."""
            header_cells = table.get('header', {}).get('cells', [])
            rows = table.get('rows', [])
            
            if not rows:
                return
            
            for i, cell in enumerate(header_cells):
                if cell.get('key') == 'date':
                    date_string = rows[0]['cells'][i]['content'] # format: Sun Jan 4, 7:00AM
                    # Determine the year: use current year, but if the date would be in the past, use next year
                    current_year = datetime.now().year
                    date_with_year = f"{date_string} {current_year}"
                    parsed_date = datetime.strptime(date_with_year, "%a %b %d, %I:%M%p %Y")
                    # If the parsed date is in the past, assume it's next year
                    if parsed_date < datetime.now():
                        date_with_year = f"{date_string} {current_year + 1}"
                        parsed_date = datetime.strptime(date_with_year, "%a %b %d, %I:%M%p %Y")
                    player.upcoming_game_datetime = parsed_date
                elif cell.get('key') == 'opp':
                    opponent = rows[0]['cells'][i]['content']
                    if isinstance(opponent, str) and opponent.startswith('@'):
                        opponent = opponent.lstrip('@')
                        player.upcoming_game_home_or_away = 'away'
                    else:
                        player.upcoming_game_home_or_away = 'home'
                    
                    player.upcoming_game_opponent = opponent
                    break
        
        # TODO: replace with helper function mapping miscData.teamName to appropriate team name used in recent games table
        def _parse_player_team_name(player:FantasyPlayer, table: Dict[str, Any]) -> None:
            """Parse recent games table to extract team name and gameweek statistics."""
            header_cells = table.get('header', {}).get('cells', [])
            rows = table.get('rows', [])
            
            if not rows:
                return
            
            for i, cell in enumerate(header_cells):
                stat_key = cell.get('name') or cell.get('key')
                if not stat_key:
                    continue
                
                # Extract team name from Team column
                if stat_key.lower() == FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM.lower():
                    player.team_name = rows[0]['cells'][i].get('toolTip')
                    break
        
        # Adjust keys to whatever Fantrax returns.
        data = dto["responses"][0]["data"]
        player = FantasyPlayer(id=player_id)
        _parse_basic_info(player, data)
        _parse_highlight_stats(player, data)
        _parse_overview_tables(player, data)
        player.gameweek_stats = [] # set to empty list for now
        player.fantasy_value = FantasyValue(value_for_gameweek=0, value_for_future_gameweeks=0)
        
        return player
