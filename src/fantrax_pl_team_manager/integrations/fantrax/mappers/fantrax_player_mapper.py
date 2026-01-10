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
        player.gameweek_stats = self.get_player_recent_gameweek_stats(dto, player)
        player.fantasy_value = FantasyValue(value_for_gameweek=0, value_for_future_gameweeks=0)
        
        return player

    """Helper function to get player gameweek stats."""
    def get_player_recent_gameweek_stats(self, dto: Mapping[str, Any], player:FantasyPlayer) -> List[PlayerGameweekStats]:
        """Get player recent gameweek stats."""
        data = dto["responses"][0]["data"]
        player_recent_gameweek_stats: List[PlayerGameweekStats] = []

        """Parse overview tables (Recent Games) from data."""
        try:
            tables = data.get('sectionContent', {}).get('OVERVIEW', {}).get('tables', [])
            for table in tables:
                if table.get('caption') == 'Recent Games':
                    """Parse recent games table to extract team name and gameweek statistics."""
                    header_cells = table.get('header', {}).get('cells', [])
                    gameweek_rows = table.get('rows', [])
                    
                    if not gameweek_rows:
                        return
                    
                    header_names = [header['name'] for header in header_cells]
                    stat_header_name_to_index = {
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_DATE: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_DATE) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_DATE in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OPPONENT: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OPPONENT) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OPPONENT in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SCORE: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SCORE) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SCORE in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES in header_names else None,
                        FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS: header_names.index(FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS) if FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS in header_names else None,
                    }

                    for gameweek_row in gameweek_rows[:MAX_RECENT_GAMEWEEKS]:
                        if str(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OPPONENT]]['content']).startswith('@'):
                            home_or_away = 'away'
                        else:
                            home_or_away = 'home'
                        opponent = str(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OPPONENT]]['content']).lstrip('@')
                        player_recent_gameweek_stats.append(
                            PlayerGameweekStats(
                                date=str(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_DATE]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_DATE] is not None else None,
                                team=str(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_TEAM] is not None else None,
                                home_or_away=home_or_away,
                                opponent=opponent,
                                score=str(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SCORE]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SCORE] is not None else None,
                                games_started=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED] is not None else 0,
                                minutes_played=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED] is not None else 0,
                                goals=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS] is not None else 0,
                                assists=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS] is not None else 0,
                                points=float(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS] is not None else float(0),
                                shots=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS] is not None else 0,
                                shots_on_target=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET] is not None else 0,
                                fouls_committed=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED] is not None else 0,
                                fouls_suffered=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED] is not None else 0,
                                yellow_cards=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS] is not None else 0,
                                red_cards=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS] is not None else 0,
                                offsides=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES] is not None else 0,
                                penalty_kick_goals=int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS] is not None else 0,
                        ))
                    
                    return player_recent_gameweek_stats
            raise FantraxException(f"Recent Games table not found in data: {str(data)}")
        except Exception as e:
            logger.error(f"Error processing overview tables: {e}")
            raise FantraxException(f"Error processing overview tables: {e}")
