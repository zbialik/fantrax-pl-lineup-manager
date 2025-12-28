"""Prediction service for forecasting player performance."""
import logging
from typing import List, Dict, Optional

from fantrax_service.data.repositories import PlayerRepository, PlayerStatsRepository
from fantrax_service.data.database import session_scope

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for predicting future player performance."""
    
    def __init__(
        self,
        player_repo: Optional[PlayerRepository] = None,
        player_stats_repo: Optional[PlayerStatsRepository] = None
    ):
        self.player_repo = player_repo or PlayerRepository()
        self.player_stats_repo = player_stats_repo or PlayerStatsRepository()
    
    def predict_player_performance(self, player_id: str, gameweeks_ahead: int = 1) -> Dict[str, any]:
        """Predict a player's performance for upcoming gameweeks.
        
        Parameters:
            player_id: Player ID to predict
            gameweeks_ahead: Number of gameweeks to predict ahead
        
        Returns:
            Dictionary with performance predictions
        """
        logger.info(f"Predicting performance for player {player_id}, {gameweeks_ahead} gameweeks ahead")
        
        with session_scope() as session:
            player = self.player_repo.get_player(player_id, session=session)
            
            if not player:
                raise ValueError(f"Player {player_id} not found")
            
            # Get historical stats
            stats = self.player_stats_repo.get_player_stats(player_id, session=session)
            
            # TODO: Implement prediction algorithm
            # This could use:
            # - Historical performance trends
            # - Opponent difficulty
            # - Player form
            # - Machine learning models
            
            prediction = {
                'player_id': player_id,
                'player_name': player.name,
                'gameweeks_ahead': gameweeks_ahead,
                'predicted_points': self._simple_average_prediction(stats, gameweeks_ahead),
                'confidence': self._calculate_confidence(stats),
                'historical_data_points': len(stats),
                # TODO: Add more prediction metrics
            }
            
            return prediction
    
    def _simple_average_prediction(self, stats: List, gameweeks: int) -> Optional[float]:
        """Simple prediction based on average (placeholder for more sophisticated algorithm)."""
        if not stats:
            return None
        
        points_list = [float(s.points) for s in stats if s.points is not None]
        if not points_list:
            return None
        
        avg_points = sum(points_list) / len(points_list)
        return avg_points * gameweeks
    
    def _calculate_confidence(self, stats: List) -> float:
        """Calculate confidence score for prediction (0.0 to 1.0)."""
        if len(stats) < 3:
            return 0.3  # Low confidence with little data
        elif len(stats) < 10:
            return 0.6  # Medium confidence
        else:
            return 0.8  # Higher confidence with more data
    
    def predict_lineup_performance(self, player_ids: List[str], gameweek: int) -> Dict[str, any]:
        """Predict overall lineup performance for a given gameweek.
        
        Parameters:
            player_ids: List of player IDs in the lineup
            gameweek: Gameweek to predict for
        
        Returns:
            Dictionary with lineup prediction
        """
        logger.info(f"Predicting lineup performance for gameweek {gameweek}")
        
        total_predicted_points = 0.0
        player_predictions = []
        
        for player_id in player_ids:
            try:
                prediction = self.predict_player_performance(player_id, gameweeks_ahead=1)
                if prediction['predicted_points']:
                    total_predicted_points += prediction['predicted_points']
                player_predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Error predicting for player {player_id}: {e}")
                player_predictions.append({
                    'player_id': player_id,
                    'error': str(e)
                })
        
        lineup_prediction = {
            'gameweek': gameweek,
            'total_predicted_points': total_predicted_points,
            'player_count': len(player_ids),
            'player_predictions': player_predictions,
        }
        
        return lineup_prediction

