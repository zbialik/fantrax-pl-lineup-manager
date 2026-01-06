from typing import Any, Dict, Mapping, List
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable, PremierLeagueTeam, PremierLeagueTeamStats

from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *

class FantraxPremierLeagueTableMapper:
    def from_json(self, obj: Mapping[str, Any]) -> PremierLeagueTable:


        def _parse_team_stats(team_stats:PremierLeagueTeamStats, team_row: Dict[str, Any], headers: List[Dict[str, Any]]) -> None:
            header_names = [header['name'] for header in headers]
            stat_header_name_to_index = {
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GAMES_PLAYED: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GAMES_PLAYED),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_WINS: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_WINS),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LOSSES: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LOSSES),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_TIES_OR_OVERTIME_LOSS: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_TIES_OR_OVERTIME_LOSS),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_POINTS: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_POINTS),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_FOR: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_FOR),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_AGAINST: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_AGAINST),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOAL_DIFFERENCE: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOAL_DIFFERENCE),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_HOME_RECORD: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_HOME_RECORD),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_AWAY_RECORD: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_AWAY_RECORD),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LAST_TEN_RECORD: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LAST_TEN_RECORD),
                FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_CURRENT_STREAK: header_names.index(FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_CURRENT_STREAK),
            }
            
            team_stats.games_played = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GAMES_PLAYED]]
            team_stats.wins = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_WINS]]
            team_stats.losses = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LOSSES]]
            team_stats.ties_or_overtime_losses = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_TIES_OR_OVERTIME_LOSS]]
            team_stats.points = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_POINTS]]
            team_stats.goals_for = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_FOR]]
            team_stats.goals_against = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOALS_AGAINST]]
            team_stats.goal_difference = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_GOAL_DIFFERENCE]]
            team_stats.home_record = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_HOME_RECORD]]
            team_stats.away_record = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_AWAY_RECORD]]
            team_stats.last_ten_record = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_LAST_TEN_RECORD]]
            team_stats.current_streak = team_row['stats'][stat_header_name_to_index[FANTRAX_PREMIERE_LEAGUE_TABLE_HEADER_NAME_CURRENT_STREAK]]

        data = obj["responses"][0]["data"]

        team_name_lookup = {team.get("id"): team.get("name") for team in data["miscData"]['teams']}

        _premier_league_table:PremierLeagueTable = PremierLeagueTable()
        for row in data['tables'][0]['rows']:
            _team_name = team_name_lookup.get(row['teamId'])
            _premier_league_table_team: PremierLeagueTeam = PremierLeagueTeam(
                rank=row['rank']
            )
            _premier_league_team_stats: PremierLeagueTeamStats = PremierLeagueTeamStats()

            _parse_team_stats(_premier_league_team_stats, row, data['miscData']['headers'])
            _premier_league_table_team.stats = _premier_league_team_stats
            _premier_league_table[_team_name] = _premier_league_table_team
        
        return _premier_league_table
