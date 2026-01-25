import unittest
from datetime import datetime, timedelta
from fantrax_pl_team_manager.domain.utils import match_time_within_window


class TestMatchTimeWithinWindow(unittest.TestCase):
    """Test cases for match_time_within_window function."""
    def test_within_window_at_interval_starts(self):
        """Test that True is returned when match is within the time window."""
        update_lineup_interval = 600
        current_datetime = datetime(2026, 1, 31, 6, 0, 0) # at the start of the first 10 minute inverval
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        result1 = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        current_datetime = datetime(2026, 1, 31, 6, 0, 0) + timedelta(seconds=update_lineup_interval) # at the start of the second 10 minute inverval
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        result2 = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertFalse(result1, 
                       "Should return False when current time is at the start of the first 10 minute inverval and within 1 hour of match window")
        self.assertTrue(result2, 
                       "Should return True when current time is at the start of the second 10 minute inverval and within 1 hour of match window")
    
    def test_within_window_after_interval_start_returns_true(self):
        """Test that True is returned when match is within the time window."""
        current_datetime = datetime(2026, 1, 31, 6, 0, 1) # 1 second after first 10 minute inverval starts
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        update_lineup_interval = 600
        
        result = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertTrue(result, 
                       "Should return True when current time is just after the update lineup interval and within 1 hour of match window")
    
    def test_within_window_before_interval_end_returns_true(self):
        """Test that True is returned when match is within the time window."""
        current_datetime = datetime(2026, 1, 31, 6, 9, 59) # 1 second before next 10 minute inverval starts
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        update_lineup_interval = 600
        
        result = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertTrue(result, 
                       "Should return True when current time is just before the next update lineup interval and within 1 hour of match window")
    
    def test_within_window_after_interval_end_returns_false(self):
        """Test that True is returned when match is within the time window."""
        current_datetime = datetime(2026, 1, 31, 6, 10, 0, 1)
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        update_lineup_interval = 600
        
        result = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertFalse(result, 
                       "Should return False when current time is just after the update lineup interval and within 1 hour of match window")
    
    def test_interval_exceeded_returns_false(self):
        """Test that False is returned when update_lineup_interval has been exceeded."""
        current_datetime = datetime(2026, 1, 31, 6, 11, 0)
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        update_lineup_interval = 600
        
        result = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertFalse(result,
                        "Should return False when more than 10 minutes (600 seconds) have passed since match start")
    
    def test_after_match_start_returns_false(self):
        """Test that False is returned when current time is after match start."""
        current_datetime = datetime(2026, 1, 31, 7, 1, 0)
        target_match_datetime = datetime(2026, 1, 31, 7, 0, 0)
        update_lineup_interval = 600
        
        result = match_time_within_window(current_datetime, target_match_datetime, update_lineup_interval)
        
        self.assertFalse(result,
                        "Should return False when current time is after match start time")
