"""Analytics service for player and team performance analysis."""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from fantrax_service.data.repositories import PlayerRepository, PlayerStatsRepository, RosterRepository
from fantrax_service.data.database import session_scope

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and performance reporting."""
    
    def __init__(
        self,
        player_repo: Optional[PlayerRepository] = None,
        player_stats_repo: Optional[PlayerStatsRepository] = None,
        roster_repo: Optional[RosterRepository] = None
    ):
        self.player_repo = player_repo or PlayerRepository()
        self.player_stats_repo = player_stats_repo or PlayerStatsRepository()
        self.roster_repo = roster_repo or RosterRepository(self.player_repo)
    
    def get_roster_performance_summary(self, player_ids: Optional[List[str]] = None) -> Dict[str, any]:
        """Get performance summary for roster players.
        
        Parameters:
            player_ids: Optional list of player IDs to include. If None, includes all roster players.
        
        Returns:
            Dictionary with performance summary metrics
        """
        logger.info("Generating roster performance summary")
        
        with session_scope() as session:
            if player_ids:
                players = self.roster_repo.get_roster_players(player_ids, session=session)
            else:
                players = self.player_repo.get_all_players(session=session)
            
            total_players = len(players)
            players_with_scores = [p for p in players if p.performance_score is not None]
            avg_performance = 0.0
            
            if players_with_scores:
                avg_performance = sum(
                    float(p.performance_score) for p in players_with_scores
                ) / len(players_with_scores)
            
            summary = {
                'total_players': total_players,
                'players_with_performance_data': len(players_with_scores),
                'average_performance_score': avg_performance,
                'players': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'position': p.position,
                        'performance_score': float(p.performance_score) if p.performance_score else None,
                        'transfer_value': float(p.transfer_value) if p.transfer_value else None,
                    }
                    for p in players
                ]
            }
            
            return summary
    
    def get_player_performance_trend(self, player_id: str, gameweeks: Optional[int] = None) -> Dict[str, any]:
        """Get performance trend for a specific player.
        
        Parameters:
            player_id: Player ID to analyze
            gameweeks: Number of recent gameweeks to include (None for all)
        
        Returns:
            Dictionary with performance trend data
        """
        with session_scope() as session:
            player = self.player_repo.get_player(player_id, session=session)
            
            if not player:
                raise ValueError(f"Player {player_id} not found")
            
            stats = self.player_stats_repo.get_player_stats(player_id, session=session)
            
            if gameweeks:
                stats = stats[:gameweeks]
            
            trend_data = {
                'player_id': player_id,
                'player_name': player.name,
                'stats_count': len(stats),
                'points_history': [
                    {
                        'gameweek': s.gameweek,
                        'points': float(s.points) if s.points else None,
                        'recorded_at': s.recorded_at.isoformat() if s.recorded_at else None,
                    }
                    for s in stats
                ],
                'average_points': self._calculate_average_points(stats),
            }
            
            return trend_data
    
    def _calculate_average_points(self, stats: List) -> Optional[float]:
        """Calculate average points from stats list."""
        points_list = [float(s.points) for s in stats if s.points is not None]
        if points_list:
            return sum(points_list) / len(points_list)
        return None
    
    def get_position_analysis(self, position: str) -> Dict[str, any]:
        """Get performance analysis for a specific position.
        
        Parameters:
            position: Position to analyze (G, D, M, F)
        
        Returns:
            Dictionary with position analysis
        """
        with session_scope() as session:
            all_players = self.player_repo.get_all_players(session=session)
            position_players = [p for p in all_players if p.position == position]
            
            players_with_scores = [p for p in position_players if p.performance_score is not None]
            
            avg_performance = 0.0
            if players_with_scores:
                avg_performance = sum(
                    float(p.performance_score) for p in players_with_scores
                ) / len(players_with_scores)
            
            analysis = {
                'position': position,
                'total_players': len(position_players),
                'players_with_data': len(players_with_scores),
                'average_performance_score': avg_performance,
                'top_players': sorted(
                    [
                        {
                            'id': p.id,
                            'name': p.name,
                            'performance_score': float(p.performance_score),
                        }
                        for p in players_with_scores
                    ],
                    key=lambda x: x['performance_score'],
                    reverse=True
                )[:10]  # Top 10
            }
            
            return analysis
    
    def generate_roster_report(self) -> Dict[str, any]:
        """Generate a comprehensive roster performance report.
        
        Returns:
            Dictionary with comprehensive roster analysis
        """
        logger.info("Generating comprehensive roster report")
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'roster_summary': self.get_roster_performance_summary(),
            'position_analysis': {
                'G': self.get_position_analysis('G'),
                'D': self.get_position_analysis('D'),
                'M': self.get_position_analysis('M'),
                'F': self.get_position_analysis('F'),
            },
            # TODO: Add more report sections (transfers, trends, recommendations)
        }
        
        return report

