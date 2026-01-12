from typing import Any, Dict, Mapping, List
from datetime import datetime
from fantrax_pl_team_manager.domain.fantasy_player import FantasyPlayer, FantasyValue
from fantrax_pl_team_manager.exceptions import FantraxException

from fantrax_pl_team_manager.domain.constants import *
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
import logging

logger = logging.getLogger(__name__)


class FantraxPlayerGameweekStatsMapper:
    """Mapper for Fantrax player gameweek stats."""
    def from_json(self, dto: Mapping[str, Any]) -> List[PlayerGameweekStats]:
        """Get player recent gameweek stats."""
        def _safe_int(value: Any, default: int = 0) -> int:
            """Safely convert value to int, handling empty strings and None."""
            if value is None or value == '':
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        def _safe_float(value: Any, default: float = 0.0) -> float:
            """Safely convert value to float, handling empty strings and None."""
            if value is None or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        data = dto["responses"][0]["data"]
        player_recent_gameweek_stats: List[PlayerGameweekStats] = []

        """Parse overview tables (Recent Games) from data."""
        try:
            tables = data.get('sectionContent', {}).get('GAME_LOG_FANTASY', {}).get('tables', [])
            for table in tables:
                if table.get('caption') == 'Game Log (Fantasy)':
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

                    # for gameweek_row in gameweek_rows[:MAX_RECENT_GAMEWEEKS]:
                    for gameweek_row in gameweek_rows:
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
                                games_started=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GAMES_STARTED] is not None else 0,
                                minutes_played=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_MINUTES_PLAYED] is not None else 0,
                                goals=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_GOALS] is not None else 0,
                                assists=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_ASSISTS] is not None else 0,
                                points=_safe_float(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_POINTS] is not None else 0.0,
                                shots=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS] is not None else 0,
                                shots_on_target=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_SHOTS_ON_TARGET] is not None else 0,
                                fouls_committed=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_COMMITTED] is not None else 0,
                                fouls_suffered=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_FOULS_SUFFERED] is not None else 0,
                                yellow_cards=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_YELLOW_CARDS] is not None else 0,
                                red_cards=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_RED_CARDS] is not None else 0,
                                offsides=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_OFFSIDES] is not None else 0,
                                penalty_kick_goals=_safe_int(gameweek_row['cells'][stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS]]['content']) if stat_header_name_to_index[FANTRAX_PLAYER_RECENT_GAMES_TABLE_HEADER_NAME_PENALTY_KICK_GOALS] is not None else 0,
                        ))
                    
                    return player_recent_gameweek_stats
            raise FantraxException(f"Recent Games table not found in data: {str(data)}")
        except Exception as e:
            logger.error(f"Error processing overview tables: {e}")
            raise FantraxException(f"Error processing overview tables: {e}")
