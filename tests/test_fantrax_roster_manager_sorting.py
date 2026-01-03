from typing import Set
import unittest
from unittest.mock import Mock, MagicMock
from fantrax_pl_team_manager.services.fantrax_roster_manager import FantraxRosterManager
from fantrax_pl_team_manager.services.fantrax_player import FantasyValue
from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.services.fantrax_roster_player import FantraxRosterPlayer


class TestFantraxRosterManagerSorting(unittest.TestCase):
    """Test cases for sort_players_by_gameweek_status_and_fantasy_value method."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock client
        self.mock_client = Mock()
        self.mock_league_id = "test_league_id"
        self.mock_team_id = "test_team_id"
        self.update_interval = 600
        self.run_once = False
        
        # Mock the get_roster_data method to return minimal data for initialization
        self.mock_client.get_roster_data.return_value = {
            "fantasyTeams": [
                {"id": self.mock_team_id, "name": "Test Team"}
            ],
            "tables": []
        }
        
        # Create a mock roster manager (we'll override players)
        self.roster_manager = FantraxRosterManager(
            self.mock_client,
            self.mock_league_id,
            self.mock_team_id,
            self.update_interval,
            self.run_once
        )
    
    def _create_mock_player(self, name:str, icon_statuses:Set[str], fantasy_value:FantasyValue):
        """Helper method to create a mock player.
        """

        player = Mock(spec=FantraxRosterPlayer)
        player.name = name
        player.fantasy_value = fantasy_value
        player.icon_statuses = icon_statuses
        
        # # Set status properties based on status_type
        # if status_type == 'starting':
        #     player.is_starting_in_gameweek = True
        #     player.is_expected_to_play_in_gameweek = False
        #     player.is_uncertain_gametime_decision_in_gameweek = False
        #     player.is_benched_or_suspended_or_out_in_gameweek = False
        # elif status_type == 'expected':
        #     player.is_starting_in_gameweek = False
        #     player.is_expected_to_play_in_gameweek = True
        #     player.is_uncertain_gametime_decision_in_gameweek = False
        #     player.is_benched_or_suspended_or_out_in_gameweek = False
        # elif status_type == 'uncertain':
        #     player.is_starting_in_gameweek = False
        #     player.is_expected_to_play_in_gameweek = False
        #     player.is_uncertain_gametime_decision_in_gameweek = True
        #     player.is_benched_or_suspended_or_out_in_gameweek = False
        # elif status_type in ['benched', 'suspended', 'out']:
        #     player.is_starting_in_gameweek = False
        #     player.is_expected_to_play_in_gameweek = False
        #     player.is_uncertain_gametime_decision_in_gameweek = False
        #     player.is_benched_or_suspended_or_out_in_gameweek = True
        # else:
        #     raise ValueError(f"Unknown status_type: {status_type}")
        
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
        
        self.roster_manager.players = players
        self.roster_manager.sort_players_by_gameweek_status_and_fantasy_value()
        
        # Expected order:
        # 1. Starting/Expected (sorted by value desc)
        # 2. Uncertain (sorted by value desc)
        # 3. Benched/Suspended/Out (sorted by value desc)
        expected_order = [
            "status=out, fantasy_value=50", 
            "status=expected-to-play, fantasy_value=40", 
            "status=starting, fantasy_value=30", 
            "status=uncertain-gametime-decision, fantasy_value=20", 
            "status=suspended, fantasy_value=15", 
            "status=benched, fantasy_value=10"
        ]
        actual_order = [player.name for player in self.roster_manager.players]
        
        self.assertEqual(actual_order, expected_order, 
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify groups are correctly separated
        # First 3 should be starting/expected
        for i in range(3):
            self.assertTrue(
                self.roster_manager.players[i].is_starting_in_gameweek or 
                self.roster_manager.players[i].is_expected_to_play_in_gameweek,
                f"Player {i} should be starting or expected to play"
            )
        
        # Player at index 3 should be uncertain
        self.assertTrue(
            self.roster_manager.players[3].is_uncertain_gametime_decision_in_gameweek,
            "Player at index 3 should be uncertain"
        )
        
        # Last 2 should be benched/suspended/out
        for i in range(4, 6):
            self.assertTrue(
                self.roster_manager.players[i].is_benched_or_suspended_or_out_in_gameweek,
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
        
        self.roster_manager.players = players
        self.roster_manager.sort_players_by_gameweek_status_and_fantasy_value()
        
        # Should be sorted by value descending within the same status group
        expected_order = [
            "status=starting, fantasy_value=100",
            "status=starting, fantasy_value=50",
            "status=starting, fantasy_value=5",
        ]
        actual_order = [player.name for player in self.roster_manager.players]
        
        self.assertEqual(actual_order, expected_order,
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify values are in descending order
        values = [player.fantasy_value.value_for_gameweek for player in self.roster_manager.players]
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
        
        self.roster_manager.players = players
        self.roster_manager.sort_players_by_gameweek_status_and_fantasy_value()
        
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
        actual_order = [player.name for player in self.roster_manager.players]
        
        self.assertEqual(actual_order, expected_order,
                        f"Expected order: {expected_order}, but got: {actual_order}")
        
        # Verify group boundaries
        # First 3 should be starting/expected
        for i in range(3):
            self.assertTrue(
                self.roster_manager.players[i].is_starting_in_gameweek or 
                self.roster_manager.players[i].is_expected_to_play_in_gameweek,
                f"Player {i} should be starting or expected to play"
            )
        
        # Next 2 should be uncertain
        for i in range(3, 5):
            self.assertTrue(
                self.roster_manager.players[i].is_uncertain_gametime_decision_in_gameweek,
                f"Player {i} should be uncertain"
            )
        
        # Last 3 should be benched/suspended/out
        for i in range(5, 8):
            self.assertTrue(
                self.roster_manager.players[i].is_benched_or_suspended_or_out_in_gameweek,
                f"Player {i} should be benched, suspended, or out"
            )
        
        # Verify descending order within each group
        starting_expected_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster_manager.players[:3]
        ]
        self.assertEqual(starting_expected_values, [80, 75, 75],
                        "Starting/Expected group should be sorted descending")
        
        uncertain_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster_manager.players[3:5]
        ]
        self.assertEqual(uncertain_values, [50, 45],
                        "Uncertain group should be sorted descending")
        
        benched_out_values = [
            p.fantasy_value.value_for_gameweek 
            for p in self.roster_manager.players[5:8]
        ]
        self.assertEqual(benched_out_values, [30, 25, 20],
                        "Benched/Out group should be sorted descending")

