from typing import Set
import unittest
from unittest.mock import Mock
from fantrax_pl_team_manager.domain.fantrax_roster import FantraxRoster
from fantrax_pl_team_manager.domain.fantrax_player import FantasyValue
from fantrax_pl_team_manager.domain.fantrax_roster_player import FantraxRosterPlayer


class TestFantraxRoster(unittest.TestCase):
    """Test cases for sort_players_by_gameweek_status_and_fantasy_value method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_team_id = "test_team_id"
        self.mock_team_name = "Test Team"
        self.roster_limit_period = 1
        
        # Create a roster instance (we'll override players)
        self.roster = FantraxRoster(
            team_id=self.mock_team_id,
            team_name=self.mock_team_name,
            roster_limit_period=self.roster_limit_period
        )
    
    def _create_mock_player(self, name:str, icon_statuses:Set[str], fantasy_value:FantasyValue):
        """Helper method to create a mock player."""
        player = Mock(spec=FantraxRosterPlayer)
        player.name = name
        player.fantasy_value = fantasy_value
        player.icon_statuses = icon_statuses
        
        # Set status properties based on icon_statuses
        # These properties are computed from icon_statuses in the actual class
        player.is_starting_in_gameweek = 'starting' in icon_statuses
        player.is_expected_to_play_in_gameweek = 'expected-to-play' in icon_statuses or not icon_statuses
        player.is_uncertain_gametime_decision_in_gameweek = 'uncertain-gametime-decision' in icon_statuses
        player.is_benched_or_suspended_or_out_in_gameweek = bool(
            {'benched', 'suspended', 'out', 'out-for-next-game'} & icon_statuses
        )
        
        return player
    
    def test_sort_players_set_1_mixed_statuses(self):
        """Test sorting with mixed statuses and varying fantasy values."""
        # Create mock players with different statuses and fantasy values
        players = [
            self._create_mock_player("status=benched, fantasy_value=10", {'benched'}, FantasyValue(value_for_gameweek=10)),
            self._create_mock_player("status=out, fantasy_value=50", {'out'}, FantasyValue(value_for_gameweek=50)), 
            self._create_mock_player("status=uncertain-gametime-decision, fantasy_value=20", {'uncertain-gametime-decision'}, FantasyValue(value_for_gameweek=20)),
            self._create_mock_player("status=expected-to-play, fantasy_value=40", {'expected-to-play'}, FantasyValue(value_for_gameweek=40)),
            self._create_mock_player("status=suspended, fantasy_value=15", {'suspended'}, FantasyValue(value_for_gameweek=15)),
            self._create_mock_player("status=starting, fantasy_value=30", {'starting'}, FantasyValue(value_for_gameweek=30)), 
        ]
        
        self.roster[:] = players
        self.roster.sort_players_by_gameweek_status_and_fantasy_value()
        
        # Expected order:
        # 1. Starting/Expected (sorted by value desc)
        # 2. Uncertain (sorted by value desc)
        # 3. Benched/Suspended/Out (sorted by value desc)
        expected_order = [
            "status=expected-to-play, fantasy_value=40", 
            "status=starting, fantasy_value=30", 
            "status=uncertain-gametime-decision, fantasy_value=20", 
            "status=out, fantasy_value=50", 
            "status=suspended, fantasy_value=15", 
            "status=benched, fantasy_value=10"
        ]
        actual_order = [player.name for player in self.roster]
        
        self.assertEqual(actual_order, expected_order, 
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify groups are correctly separated
        # First 2 should be starting/expected
        for i in range(2):
            self.assertTrue(
                self.roster[i].is_starting_in_gameweek or 
                self.roster[i].is_expected_to_play_in_gameweek,
                f"Player {i} should be starting or expected to play"
            )
        
        # Player at index 2 should be uncertain
        self.assertTrue(
            self.roster[2].is_uncertain_gametime_decision_in_gameweek,
            "Player at index 2 should be uncertain"
        )
        
        # Last 3 should be benched/suspended/out
        for i in range(3, 6):
            self.assertTrue(
                self.roster[i].is_benched_or_suspended_or_out_in_gameweek,
                f"Player {i} should be benched, suspended, or out"
            )
    
    def test_sort_players_set_2_same_status_different_values(self):
        """Test sorting when players have the same status but different fantasy values."""
        # All players are starting, but with different values
        players = [
            self._create_mock_player("status=starting, fantasy_value=5", {'starting'}, FantasyValue(value_for_gameweek=5)),
            self._create_mock_player("status=starting, fantasy_value=100", {'starting'}, FantasyValue(value_for_gameweek=100)),
            self._create_mock_player("status=starting, fantasy_value=50", {'starting'}, FantasyValue(value_for_gameweek=50)),
        ]
        
        self.roster[:] = players
        self.roster.sort_players_by_gameweek_status_and_fantasy_value()
        
        # Should be sorted by value descending within the same status group
        expected_order = [
            "status=starting, fantasy_value=100",
            "status=starting, fantasy_value=50",
            "status=starting, fantasy_value=5",
        ]
        actual_order = [player.name for player in self.roster]
        
        self.assertEqual(actual_order, expected_order,
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify values are in descending order
        values = [player.fantasy_value.value_for_gameweek for player in self.roster]
        self.assertEqual(values, [100, 50, 5], "Values should be in descending order")
    
    def test_sort_players_set_3_all_categories_with_ties(self):
        """Test sorting with all categories represented and some tied fantasy values."""
        # Create players in all categories with some tied values
        players = [
            self._create_mock_player("status=out, fantasy_value=25", {'out'}, FantasyValue(value_for_gameweek=25)),
            self._create_mock_player("status=starting, fantasy_value=75", {'starting'}, FantasyValue(value_for_gameweek=75)),
            self._create_mock_player("status=uncertain-gametime-decision, fantasy_value=50", {'uncertain-gametime-decision'}, FantasyValue(value_for_gameweek=50)),
            self._create_mock_player("status=expected-to-play, fantasy_value=75", {'expected-to-play'}, FantasyValue(value_for_gameweek=75)),
            self._create_mock_player("status=benched, fantasy_value=30", {'benched'}, FantasyValue(value_for_gameweek=30)),
            self._create_mock_player("status=starting, fantasy_value=80", {'starting'}, FantasyValue(value_for_gameweek=80)),
            self._create_mock_player("status=uncertain-gametime-decision, fantasy_value=45", {'uncertain-gametime-decision'}, FantasyValue(value_for_gameweek=45)),
            self._create_mock_player("status=out, fantasy_value=20", {'out'}, FantasyValue(value_for_gameweek=20)),
        ]
        
        self.roster[:] = players
        self.roster.sort_players_by_gameweek_status_and_fantasy_value()
        
        expected_order = [
            "status=starting, fantasy_value=80",
            "status=starting, fantasy_value=75",
            "status=expected-to-play, fantasy_value=75",
            "status=uncertain-gametime-decision, fantasy_value=50",
            "status=uncertain-gametime-decision, fantasy_value=45",
            "status=benched, fantasy_value=30",
            "status=out, fantasy_value=25",
            "status=out, fantasy_value=20",
        ]
        actual_order = [player.name for player in self.roster]
        
        self.assertEqual(actual_order, expected_order,
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify group boundaries
        # First 3 should be starting/expected
        for i in range(3):
            self.assertTrue(
                self.roster[i].is_starting_in_gameweek or 
                self.roster[i].is_expected_to_play_in_gameweek,
                f"Player {i} should be starting or expected to play"
            )
        
        # Next 2 should be uncertain
        for i in range(3, 5):
            self.assertTrue(
                self.roster[i].is_uncertain_gametime_decision_in_gameweek,
                f"Player {i} should be uncertain"
            )
        
        # Last 3 should be benched/suspended/out
        for i in range(5, 8):
            self.assertTrue(
                self.roster[i].is_benched_or_suspended_or_out_in_gameweek,
                f"Player {i} should be benched, suspended, or out"
            )
        
        # Verify descending order within each group
        starting_expected_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster[:3]
        ]
        self.assertEqual(starting_expected_values, [80, 75, 75],
                        "Starting/Expected group should be sorted descending")
        
        uncertain_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster[3:5]
        ]
        self.assertEqual(uncertain_values, [50, 45],
                        "Uncertain group should be sorted descending")
        
        benched_out_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster[5:8]
        ]
        self.assertEqual(benched_out_values, [30, 25, 20],
                        "Benched/Out group should be sorted descending")

