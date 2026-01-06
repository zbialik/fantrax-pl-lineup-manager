from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Mapping
from fantrax_pl_team_manager.domain.fantrax_player import FantraxPlayer, FantasyValue
from fantrax_pl_team_manager.exceptions import FantraxException

from fantrax_pl_team_manager.domain.constants import *
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *

import logging

logger = logging.getLogger(__name__)

class FantraxPlayerMapper:
    """Mapper for Fantrax player data."""
    def from_json(self, dto: Mapping[str, Any], player_id:int) -> FantraxPlayer:
        data = dto["responses"][0]["data"]
        
        def _parse_basic_info(player:FantraxPlayer, data: Dict[str, Any]) -> None:
            """Parse basic player information from data."""
            player.name = data['miscData'].get('name')
            player.icon_statuses = set([
                STATUS_ICON_MAP_BY_ID.get(icon["typeId"])
                for icon in data['miscData'].get('icons', [])
                if icon.get("typeId") in STATUS_ICON_MAP_BY_ID
            ])
        
        def _parse_highlight_stats(player:FantraxPlayer, data: Dict[str, Any]) -> None:
            """Parse highlight statistics from data."""
            highlight_stats_list = data['miscData'].get('highlightStats', [])
            for stat in highlight_stats_list:
                if 'shortName' not in stat or 'value' not in stat:
                    continue
                
                value = stat['value']
                if isinstance(value, str) and value.endswith('%'):
                    value = value.rstrip('%')
                
                try:
                    decimal_value = Decimal(value)
                    player.highlight_stats[stat['shortName']] = decimal_value / 100
                except (InvalidOperation, ValueError):
                    # If conversion fails, use the original value
                    player.highlight_stats[stat['shortName']] = value
        
        def _parse_overview_tables(player:FantraxPlayer, data: Dict[str, Any]) -> None:
            """Parse overview tables (Upcoming Games, Recent Games) from data."""
            try:
                tables = data.get('sectionContent', {}).get('OVERVIEW', {}).get('tables', [])
                for table in tables:
                    if table.get('caption') == 'Upcoming Games':
                        _parse_upcoming_games_table(player, table)
                    elif table.get('caption') == 'Recent Games':
                        _parse_recent_games_table(player, table)
            except Exception as e:
                logger.error(f"Error processing overview tables: {e}")
                raise FantraxException(f"Error processing overview tables: {e}")
        
        def _parse_upcoming_games_table(player:FantraxPlayer, table: Dict[str, Any]) -> None:
            """Parse upcoming games table to extract opponent and home/away status."""
            header_cells = table.get('header', {}).get('cells', [])
            rows = table.get('rows', [])
            
            if not rows:
                return
            
            for i, cell in enumerate(header_cells):
                if cell.get('key') == 'opp':
                    opponent = rows[0]['cells'][i]['content']
                    if isinstance(opponent, str) and opponent.startswith('@'):
                        opponent = opponent.lstrip('@')
                        player.upcoming_game_home_or_away = 'away'
                    else:
                        player.upcoming_game_home_or_away = 'home'
                    
                    player.upcoming_game_opponent = opponent
                    break
        
        def _parse_recent_games_table(player:FantraxPlayer, table: Dict[str, Any]) -> None:
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
                if stat_key.lower() == 'team':
                    player.team_name = rows[0]['cells'][i].get('toolTip')
                
                # Initialize and populate recent gameweeks stats
                player.recent_gameweeks_stats[stat_key] = []
                
                for j in range(min(MAX_RECENT_GAMEWEEKS, len(rows))):
                    gameweek_stat_value = rows[j]['cells'][i]['content']
                    try:
                        decimal_value = Decimal(gameweek_stat_value)
                        player.recent_gameweeks_stats[stat_key].append(decimal_value)
                    except (InvalidOperation, ValueError):
                        # If conversion fails, use the original value
                        player.recent_gameweeks_stats[stat_key].append(gameweek_stat_value)
        

        # Adjust keys to whatever Fantrax returns.
        data = dto["responses"][0]["data"]
        player = FantraxPlayer(id=player_id)
        _parse_basic_info(player, data)
        _parse_highlight_stats(player, data)
        _parse_overview_tables(player, data)
        player.fantasy_value = FantasyValue(value_for_gameweek=0, value_for_future_gameweeks=0)
        
        return player
