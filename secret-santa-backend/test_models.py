"""
Unit tests for data models.
"""
import unittest
from datetime import datetime
from models import Participant, Gift, GameState


class TestParticipant(unittest.TestCase):
    """Test cases for Participant model."""
    
    def test_participant_creation(self):
        """Test basic participant creation."""
        participant = Participant(1, "John Doe")
        
        self.assertEqual(participant.id, 1)
        self.assertEqual(participant.name, "John Doe")
        self.assertIsInstance(participant.registration_timestamp, str)
    
    def test_participant_with_timestamp(self):
        """Test participant creation with custom timestamp."""
        timestamp = "2023-12-01T10:00:00"
        participant = Participant(2, "Jane Smith", timestamp)
        
        self.assertEqual(participant.registration_timestamp, timestamp)
    
    def test_participant_to_dict(self):
        """Test participant serialization to dictionary."""
        participant = Participant(3, "Bob Johnson", "2023-12-01T10:00:00")
        data = participant.to_dict()
        
        expected = {
            "id": 3,
            "name": "Bob Johnson",
            "registration_timestamp": "2023-12-01T10:00:00"
        }
        self.assertEqual(data, expected)
    
    def test_participant_from_dict(self):
        """Test participant deserialization from dictionary."""
        data = {
            "id": 4,
            "name": "Alice Brown",
            "registration_timestamp": "2023-12-01T11:00:00"
        }
        participant = Participant.from_dict(data)
        
        self.assertEqual(participant.id, 4)
        self.assertEqual(participant.name, "Alice Brown")
        self.assertEqual(participant.registration_timestamp, "2023-12-01T11:00:00")
    
    def test_participant_repr(self):
        """Test participant string representation."""
        participant = Participant(5, "Charlie Wilson")
        repr_str = repr(participant)
        
        self.assertIn("Participant", repr_str)
        self.assertIn("id=5", repr_str)
        self.assertIn("Charlie Wilson", repr_str)


class TestGift(unittest.TestCase):
    """Test cases for Gift model."""
    
    def test_gift_creation(self):
        """Test basic gift creation."""
        gift = Gift("gift-1", "Chocolate Box")
        
        self.assertEqual(gift.id, "gift-1")
        self.assertEqual(gift.name, "Chocolate Box")
        self.assertEqual(gift.steal_count, 0)
        self.assertFalse(gift.is_locked)
        self.assertIsNone(gift.current_owner)
        self.assertEqual(gift.steal_history, [])
    
    def test_gift_creation_with_owner(self):
        """Test gift creation with initial owner."""
        gift = Gift("gift-2", "Coffee Mug", 10)
        
        self.assertEqual(gift.current_owner, 10)
    
    def test_gift_steal_first_time(self):
        """Test stealing a gift for the first time."""
        gift = Gift("gift-3", "Book")
        
        success = gift.steal_gift(5)
        
        self.assertTrue(success)
        self.assertEqual(gift.current_owner, 5)
        self.assertEqual(gift.steal_count, 1)
        self.assertFalse(gift.is_locked)
        self.assertEqual(gift.steal_history, [])
    
    def test_gift_steal_from_owner(self):
        """Test stealing a gift from another participant."""
        gift = Gift("gift-4", "Candle", 3)
        
        success = gift.steal_gift(7)
        
        self.assertTrue(success)
        self.assertEqual(gift.current_owner, 7)
        self.assertEqual(gift.steal_count, 1)
        self.assertEqual(gift.steal_history, [3])
    
    def test_gift_steal_multiple_times(self):
        """Test stealing a gift multiple times."""
        gift = Gift("gift-5", "Scarf", 1)
        
        # First steal
        gift.steal_gift(2)
        self.assertEqual(gift.steal_count, 1)
        self.assertFalse(gift.is_locked)
        
        # Second steal
        gift.steal_gift(3)
        self.assertEqual(gift.steal_count, 2)
        self.assertFalse(gift.is_locked)
        
        # Third steal - should lock the gift
        gift.steal_gift(4)
        self.assertEqual(gift.steal_count, 3)
        self.assertTrue(gift.is_locked)
        self.assertEqual(gift.current_owner, 4)
        self.assertEqual(gift.steal_history, [1, 2, 3])
    
    def test_gift_steal_when_locked(self):
        """Test attempting to steal a locked gift."""
        gift = Gift("gift-6", "Wallet")
        gift.is_locked = True
        
        success = gift.steal_gift(8)
        
        self.assertFalse(success)
        self.assertIsNone(gift.current_owner)
        self.assertEqual(gift.steal_count, 0)
    
    def test_gift_to_dict(self):
        """Test gift serialization to dictionary."""
        gift = Gift("gift-7", "Notebook", 5)
        gift.steal_count = 2
        gift.steal_history = [1, 3]
        
        data = gift.to_dict()
        
        expected = {
            "id": "gift-7",
            "name": "Notebook",
            "steal_count": 2,
            "is_locked": False,
            "current_owner": 5,
            "steal_history": [1, 3]
        }
        self.assertEqual(data, expected)
    
    def test_gift_from_dict(self):
        """Test gift deserialization from dictionary."""
        data = {
            "id": "gift-8",
            "name": "Tea Set",
            "steal_count": 1,
            "is_locked": False,
            "current_owner": 9,
            "steal_history": [2]
        }
        gift = Gift.from_dict(data)
        
        self.assertEqual(gift.id, "gift-8")
        self.assertEqual(gift.name, "Tea Set")
        self.assertEqual(gift.steal_count, 1)
        self.assertFalse(gift.is_locked)
        self.assertEqual(gift.current_owner, 9)
        self.assertEqual(gift.steal_history, [2])
    
    def test_gift_repr(self):
        """Test gift string representation."""
        gift = Gift("gift-9", "Plant Pot")
        gift.steal_count = 1
        gift.is_locked = False
        
        repr_str = repr(gift)
        
        self.assertIn("Gift", repr_str)
        self.assertIn("gift-9", repr_str)
        self.assertIn("Plant Pot", repr_str)
        self.assertIn("steals=1", repr_str)
        self.assertIn("locked=False", repr_str)


class TestGameState(unittest.TestCase):
    """Test cases for GameState model."""
    
    def test_game_state_creation(self):
        """Test basic game state creation."""
        game_state = GameState()
        
        self.assertIsNone(game_state.current_turn)
        self.assertEqual(game_state.turn_order, [])
        self.assertEqual(game_state.game_phase, "registration")
    
    def test_set_turn_order(self):
        """Test setting turn order."""
        game_state = GameState()
        participants = [1, 3, 5, 2]
        
        game_state.set_turn_order(participants)
        
        self.assertEqual(game_state.turn_order, [1, 3, 5, 2])
        self.assertEqual(game_state.current_turn, 1)
    
    def test_set_turn_order_empty(self):
        """Test setting empty turn order."""
        game_state = GameState()
        
        game_state.set_turn_order([])
        
        self.assertEqual(game_state.turn_order, [])
        self.assertIsNone(game_state.current_turn)
    
    def test_next_turn(self):
        """Test advancing to next turn."""
        game_state = GameState()
        game_state.set_turn_order([1, 2, 3])
        
        # First advance
        next_player = game_state.next_turn()
        self.assertEqual(next_player, 2)
        self.assertEqual(game_state.current_turn, 2)
        
        # Second advance
        next_player = game_state.next_turn()
        self.assertEqual(next_player, 3)
        self.assertEqual(game_state.current_turn, 3)
        
        # Final advance - game should complete
        next_player = game_state.next_turn()
        self.assertIsNone(next_player)
        self.assertIsNone(game_state.current_turn)
        self.assertEqual(game_state.game_phase, "completed")
    
    def test_next_turn_no_order(self):
        """Test next turn with no turn order set."""
        game_state = GameState()
        
        next_player = game_state.next_turn()
        
        self.assertIsNone(next_player)
    
    def test_next_turn_invalid_current(self):
        """Test next turn with invalid current turn."""
        game_state = GameState()
        game_state.turn_order = [1, 2, 3]
        game_state.current_turn = 5  # Not in turn order
        
        next_player = game_state.next_turn()
        
        self.assertEqual(next_player, 1)  # Should reset to first
        self.assertEqual(game_state.current_turn, 1)
    
    def test_start_game(self):
        """Test starting the game."""
        game_state = GameState()
        game_state.set_turn_order([5, 3, 1])
        
        game_state.start_game()
        
        self.assertEqual(game_state.game_phase, "active")
        self.assertEqual(game_state.current_turn, 5)
    
    def test_start_game_no_participants(self):
        """Test starting game with no participants."""
        game_state = GameState()
        
        game_state.start_game()
        
        self.assertEqual(game_state.game_phase, "active")
        self.assertIsNone(game_state.current_turn)
    
    def test_game_state_to_dict(self):
        """Test game state serialization to dictionary."""
        game_state = GameState()
        game_state.current_turn = 3
        game_state.turn_order = [3, 1, 4]
        game_state.game_phase = "active"
        
        data = game_state.to_dict()
        
        expected = {
            "current_turn": 3,
            "turn_order": [3, 1, 4],
            "game_phase": "active"
        }
        self.assertEqual(data, expected)
    
    def test_game_state_from_dict(self):
        """Test game state deserialization from dictionary."""
        data = {
            "current_turn": 7,
            "turn_order": [7, 2, 9],
            "game_phase": "active"
        }
        game_state = GameState.from_dict(data)
        
        self.assertEqual(game_state.current_turn, 7)
        self.assertEqual(game_state.turn_order, [7, 2, 9])
        self.assertEqual(game_state.game_phase, "active")
    
    def test_game_state_from_dict_defaults(self):
        """Test game state deserialization with missing fields."""
        data = {}
        game_state = GameState.from_dict(data)
        
        self.assertIsNone(game_state.current_turn)
        self.assertEqual(game_state.turn_order, [])
        self.assertEqual(game_state.game_phase, "registration")
    
    def test_game_state_repr(self):
        """Test game state string representation."""
        game_state = GameState()
        game_state.game_phase = "active"
        game_state.current_turn = 5
        game_state.turn_order = [5, 2, 8]
        
        repr_str = repr(game_state)
        
        self.assertIn("GameState", repr_str)
        self.assertIn("phase='active'", repr_str)
        self.assertIn("current_turn=5", repr_str)
        self.assertIn("participants=3", repr_str)


if __name__ == '__main__':
    unittest.main()