"""
Unit tests for file database operations.
"""
import unittest
import os
import tempfile
import json
import threading
import time
from unittest.mock import patch, mock_open
from database import FileDatabase, DatabaseError, ConcurrentAccessError
from models import Participant, Gift, GameState


class TestFileDatabase(unittest.TestCase):
    """Test cases for FileDatabase class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        # Remove the empty file so our database can initialize it properly
        os.unlink(self.temp_file.name)
        self.db = FileDatabase(self.temp_file.name, max_retries=3, retry_delay=0.01)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_database_initialization(self):
        """Test database initialization creates file with correct structure."""
        self.assertTrue(os.path.exists(self.temp_file.name))
        
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
        
        self.assertIn('participants', data)
        self.assertIn('gifts', data)
        self.assertIn('game_state', data)
        self.assertIn('metadata', data)
        self.assertEqual(data['participants'], [])
        self.assertEqual(data['gifts'], [])
    
    def test_read_all_data_empty(self):
        """Test reading data from empty database."""
        participants, gifts, game_state = self.db.read_all_data()
        
        self.assertEqual(len(participants), 0)
        self.assertEqual(len(gifts), 0)
        self.assertEqual(game_state.game_phase, "registration")
        self.assertIsNone(game_state.current_turn)
    
    def test_add_participant_atomic(self):
        """Test atomic participant addition."""
        participant = self.db.add_participant_atomic("John Doe")
        
        self.assertEqual(participant.name, "John Doe")
        self.assertGreaterEqual(participant.id, 1)
        self.assertLessEqual(participant.id, 100)
        self.assertIsInstance(participant.registration_timestamp, str)
        
        # Verify persistence
        participants, _, _ = self.db.read_all_data()
        self.assertEqual(len(participants), 1)
        self.assertEqual(participants[0].name, "John Doe")
        self.assertGreaterEqual(participants[0].id, 1)
        self.assertLessEqual(participants[0].id, 100)
    
    def test_add_multiple_participants(self):
        """Test adding multiple participants with unique numbers."""
        names = ["Alice", "Bob", "Charlie"]
        participants = []
        
        for name in names:
            participant = self.db.add_participant_atomic(name)
            participants.append(participant)
        
        # Check unique IDs
        ids = [p.id for p in participants]
        self.assertEqual(len(set(ids)), 3)  # All unique
        # Verify all IDs are in valid range
        for participant_id in ids:
            self.assertGreaterEqual(participant_id, 1)
            self.assertLessEqual(participant_id, 100)
        
        # Verify persistence
        stored_participants, _, _ = self.db.read_all_data()
        self.assertEqual(len(stored_participants), 3)
    
    def test_add_participant_empty_name(self):
        """Test adding participant with empty name raises error."""
        with self.assertRaises(DatabaseError) as context:
            self.db.add_participant_atomic("")
        
        self.assertIn("empty", str(context.exception))
        
        with self.assertRaises(DatabaseError):
            self.db.add_participant_atomic("   ")
    
    def test_add_participant_max_limit(self):
        """Test participant limit enforcement."""
        # Fill up to limit
        for i in range(100):
            self.db.add_participant_atomic(f"User{i}")
        
        # Try to add one more
        with self.assertRaises(DatabaseError) as context:
            self.db.add_participant_atomic("ExtraUser")
        
        self.assertIn("Maximum", str(context.exception))
    
    def test_get_participants(self):
        """Test getting all participants."""
        # Add some participants
        self.db.add_participant_atomic("Alice")
        self.db.add_participant_atomic("Bob")
        
        participants = self.db.get_participants()
        
        self.assertEqual(len(participants), 2)
        names = [p.name for p in participants]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
    
    def test_get_participant_count(self):
        """Test getting participant count."""
        self.assertEqual(self.db.get_participant_count(), 0)
        
        self.db.add_participant_atomic("Alice")
        self.assertEqual(self.db.get_participant_count(), 1)
        
        self.db.add_participant_atomic("Bob")
        self.assertEqual(self.db.get_participant_count(), 2)
    
    def test_add_gift(self):
        """Test adding a gift."""
        gift = self.db.add_gift("Chocolate Box")
        
        self.assertEqual(gift.name, "Chocolate Box")
        self.assertIsNotNone(gift.id)
        self.assertEqual(gift.steal_count, 0)
        self.assertFalse(gift.is_locked)
        
        # Verify persistence
        gifts = self.db.get_gifts()
        self.assertEqual(len(gifts), 1)
        self.assertEqual(gifts[0].name, "Chocolate Box")
    
    def test_add_gift_with_owner(self):
        """Test adding a gift with initial owner."""
        gift = self.db.add_gift("Coffee Mug", 5)
        
        self.assertEqual(gift.current_owner, 5)
        
        # Verify persistence
        gifts = self.db.get_gifts()
        self.assertEqual(gifts[0].current_owner, 5)
    
    def test_add_gift_empty_name(self):
        """Test adding gift with empty name raises error."""
        with self.assertRaises(DatabaseError):
            self.db.add_gift("")
        
        with self.assertRaises(DatabaseError):
            self.db.add_gift("   ")
    
    def test_steal_gift_atomic(self):
        """Test atomic gift stealing."""
        # Add a gift
        gift = self.db.add_gift("Book", 1)
        
        # Steal the gift
        success = self.db.steal_gift_atomic(gift.id, 2)
        
        self.assertTrue(success)
        
        # Verify changes
        gifts = self.db.get_gifts()
        stolen_gift = gifts[0]
        self.assertEqual(stolen_gift.current_owner, 2)
        self.assertEqual(stolen_gift.steal_count, 1)
        self.assertEqual(stolen_gift.steal_history, [1])
    
    def test_steal_gift_multiple_times(self):
        """Test stealing a gift multiple times until locked."""
        gift = self.db.add_gift("Scarf", 1)
        
        # First steal
        success = self.db.steal_gift_atomic(gift.id, 2)
        self.assertTrue(success)
        
        # Second steal
        success = self.db.steal_gift_atomic(gift.id, 3)
        self.assertTrue(success)
        
        # Third steal - should lock
        success = self.db.steal_gift_atomic(gift.id, 4)
        self.assertTrue(success)
        
        # Fourth steal - should fail
        success = self.db.steal_gift_atomic(gift.id, 5)
        self.assertFalse(success)
        
        # Verify final state
        gifts = self.db.get_gifts()
        final_gift = gifts[0]
        self.assertEqual(final_gift.steal_count, 3)
        self.assertTrue(final_gift.is_locked)
        self.assertEqual(final_gift.current_owner, 4)
    
    def test_steal_gift_not_found(self):
        """Test stealing non-existent gift raises error."""
        with self.assertRaises(DatabaseError) as context:
            self.db.steal_gift_atomic("nonexistent-id", 1)
        
        self.assertIn("not found", str(context.exception))
    
    def test_get_gifts(self):
        """Test getting all gifts."""
        self.db.add_gift("Gift 1")
        self.db.add_gift("Gift 2")
        
        gifts = self.db.get_gifts()
        
        self.assertEqual(len(gifts), 2)
        names = [g.name for g in gifts]
        self.assertIn("Gift 1", names)
        self.assertIn("Gift 2", names)
    
    def test_game_state_operations(self):
        """Test game state get and update operations."""
        # Get initial state
        game_state = self.db.get_game_state()
        self.assertEqual(game_state.game_phase, "registration")
        
        # Update state
        game_state.game_phase = "active"
        game_state.current_turn = 5
        game_state.turn_order = [5, 3, 1]
        
        self.db.update_game_state(game_state)
        
        # Verify persistence
        updated_state = self.db.get_game_state()
        self.assertEqual(updated_state.game_phase, "active")
        self.assertEqual(updated_state.current_turn, 5)
        self.assertEqual(updated_state.turn_order, [5, 3, 1])
    
    def test_write_all_data(self):
        """Test writing all data at once."""
        # Create test data
        participants = [
            Participant(1, "Alice"),
            Participant(2, "Bob")
        ]
        gifts = [
            Gift("gift-1", "Book"),
            Gift("gift-2", "Mug")
        ]
        game_state = GameState()
        game_state.game_phase = "active"
        
        # Write data
        self.db.write_all_data(participants, gifts, game_state)
        
        # Read back and verify
        read_participants, read_gifts, read_game_state = self.db.read_all_data()
        
        self.assertEqual(len(read_participants), 2)
        self.assertEqual(len(read_gifts), 2)
        self.assertEqual(read_game_state.game_phase, "active")
    
    def test_concurrent_participant_addition(self):
        """Test concurrent participant addition doesn't create duplicates."""
        # Add participants sequentially to test unique ID assignment
        participants = []
        for i in range(5):
            participant = self.db.add_participant_atomic(f"User_{i}")
            participants.append(participant)
        
        # Verify all IDs are unique
        ids = [p.id for p in participants]
        self.assertEqual(len(set(ids)), 5)  # All unique
        # Verify all IDs are in valid range
        for participant_id in ids:
            self.assertGreaterEqual(participant_id, 1)
            self.assertLessEqual(participant_id, 100)
        
        # Verify in database
        stored_participants = self.db.get_participants()
        self.assertEqual(len(stored_participants), 5)
    
    def test_retry_mechanism(self):
        """Test retry mechanism for failed operations."""
        # Create database with very short retry delay
        db = FileDatabase(self.temp_file.name, max_retries=3, retry_delay=0.001)
        
        # Mock file operations to fail first few times
        original_open = open
        call_count = 0
        
        def mock_file_open(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise OSError("Simulated file error")
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_file_open):
            # This should succeed on the 3rd attempt
            participant = db.add_participant_atomic("Test User")
            self.assertEqual(participant.name, "Test User")
        
        self.assertGreaterEqual(call_count, 3)  # Should have retried at least 3 times
    
    def test_retry_exhaustion(self):
        """Test behavior when all retries are exhausted."""
        db = FileDatabase(self.temp_file.name, max_retries=2, retry_delay=0.001)
        
        # Mock to always fail
        with patch('builtins.open', side_effect=OSError("Persistent error")):
            with self.assertRaises(ConcurrentAccessError) as context:
                db.add_participant_atomic("Test User")
            
            self.assertIn("failed after 2 attempts", str(context.exception))
    
    def test_update_gift_name_atomic(self):
        """Test atomic gift name update."""
        # Add a gift
        gift = self.db.add_gift("Original Name")
        
        # Update the gift name
        updated_gift = self.db.update_gift_name_atomic(gift.id, "Updated Name")
        
        self.assertEqual(updated_gift.name, "Updated Name")
        self.assertEqual(updated_gift.id, gift.id)
        
        # Verify persistence
        gifts = self.db.get_gifts()
        self.assertEqual(len(gifts), 1)
        self.assertEqual(gifts[0].name, "Updated Name")
    
    def test_update_gift_name_preserves_metadata(self):
        """Test that updating gift name preserves all metadata."""
        # Add a gift with owner
        gift = self.db.add_gift("Test Gift", 5)
        
        # Steal it a couple times
        self.db.steal_gift_atomic(gift.id, 10)
        self.db.steal_gift_atomic(gift.id, 15)
        
        # Get current state before update
        gifts_before = self.db.get_gifts()
        gift_before = gifts_before[0]
        
        # Update the name
        updated_gift = self.db.update_gift_name_atomic(gift.id, "New Name")
        
        # Verify all metadata is preserved
        self.assertEqual(updated_gift.name, "New Name")
        self.assertEqual(updated_gift.steal_count, gift_before.steal_count)
        self.assertEqual(updated_gift.is_locked, gift_before.is_locked)
        self.assertEqual(updated_gift.current_owner, gift_before.current_owner)
        self.assertEqual(updated_gift.steal_history, gift_before.steal_history)
        
        # Verify persistence
        gifts = self.db.get_gifts()
        persisted_gift = gifts[0]
        self.assertEqual(persisted_gift.name, "New Name")
        self.assertEqual(persisted_gift.steal_count, 2)
        self.assertEqual(persisted_gift.current_owner, 15)
        self.assertEqual(persisted_gift.steal_history, [5, 10])
    
    def test_update_gift_name_locked_gift(self):
        """Test updating name of a locked gift preserves locked status."""
        # Add a gift and lock it by stealing 3 times
        gift = self.db.add_gift("Locked Gift", 1)
        self.db.steal_gift_atomic(gift.id, 2)
        self.db.steal_gift_atomic(gift.id, 3)
        self.db.steal_gift_atomic(gift.id, 4)
        
        # Verify it's locked
        gifts = self.db.get_gifts()
        self.assertTrue(gifts[0].is_locked)
        
        # Update the name
        updated_gift = self.db.update_gift_name_atomic(gift.id, "Still Locked")
        
        # Verify it's still locked
        self.assertEqual(updated_gift.name, "Still Locked")
        self.assertTrue(updated_gift.is_locked)
        self.assertEqual(updated_gift.steal_count, 3)
    
    def test_update_gift_name_not_found(self):
        """Test updating non-existent gift raises error."""
        with self.assertRaises(DatabaseError) as context:
            self.db.update_gift_name_atomic("nonexistent-id", "New Name")
        
        self.assertIn("not found", str(context.exception))
    
    def test_update_gift_name_empty(self):
        """Test updating gift with empty name raises error."""
        gift = self.db.add_gift("Original")
        
        with self.assertRaises(DatabaseError) as context:
            self.db.update_gift_name_atomic(gift.id, "")
        
        self.assertIn("empty", str(context.exception))
    
    def test_update_gift_name_whitespace_only(self):
        """Test updating gift with whitespace-only name raises error."""
        gift = self.db.add_gift("Original")
        
        with self.assertRaises(DatabaseError) as context:
            self.db.update_gift_name_atomic(gift.id, "   ")
        
        self.assertIn("empty", str(context.exception))
    
    def test_update_gift_name_strips_whitespace(self):
        """Test that gift name update strips leading/trailing whitespace."""
        gift = self.db.add_gift("Original")
        
        updated_gift = self.db.update_gift_name_atomic(gift.id, "  Trimmed Name  ")
        
        self.assertEqual(updated_gift.name, "Trimmed Name")


class TestDatabaseConcurrency(unittest.TestCase):
    """Test cases for database concurrency handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        # Remove the empty file so our database can initialize it properly
        os.unlink(self.temp_file.name)
        self.db = FileDatabase(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_concurrent_gift_stealing(self):
        """Test gift stealing mechanics with sequential operations."""
        # Add a gift
        gift = self.db.add_gift("Popular Gift", 1)
        
        # Test sequential stealing to verify locking mechanism
        # First steal
        success1 = self.db.steal_gift_atomic(gift.id, 2)
        self.assertTrue(success1)
        
        # Second steal
        success2 = self.db.steal_gift_atomic(gift.id, 3)
        self.assertTrue(success2)
        
        # Third steal - should lock the gift
        success3 = self.db.steal_gift_atomic(gift.id, 4)
        self.assertTrue(success3)
        
        # Fourth steal - should fail because gift is locked
        success4 = self.db.steal_gift_atomic(gift.id, 5)
        self.assertFalse(success4)
        
        # Verify final gift state
        gifts = self.db.get_gifts()
        final_gift = gifts[0]
        self.assertEqual(final_gift.steal_count, 3)
        self.assertTrue(final_gift.is_locked)
        self.assertEqual(final_gift.current_owner, 4)


if __name__ == '__main__':
    unittest.main()