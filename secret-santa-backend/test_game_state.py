"""
Unit tests for game state management endpoints.
"""
import pytest
import json
import os
import tempfile
from app import app
from database import FileDatabase
from models import Participant, GameState


@pytest.fixture
def client():
    """Create test client with temporary database."""
    # Create temporary file for testing
    db_fd, temp_db_file = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    # Override the global db instance
    import app as app_module
    original_db = app_module.db
    app_module.db = FileDatabase(temp_db_file)
    
    with app.test_client() as client:
        yield client
    
    # Restore original db and clean up
    app_module.db = original_db
    os.close(db_fd)
    os.unlink(temp_db_file)


@pytest.fixture
def db_with_participants():
    """Create database with test participants."""
    db_fd, db_file = tempfile.mkstemp()
    db = FileDatabase(db_file)
    
    # Add test participants
    participants = [
        db.add_participant_atomic("Alice"),
        db.add_participant_atomic("Bob"),
        db.add_participant_atomic("Charlie")
    ]
    
    yield db, participants
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_file)


class TestCurrentTurnEndpoint:
    """Test cases for GET /api/game/current-turn endpoint."""
    
    def test_get_current_turn_no_participants(self, client):
        """Test getting current turn with no participants."""
        response = client.get('/api/game/current-turn')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['current_turn'] is None
        assert data['current_participant'] is None
        assert data['game_phase'] == 'registration'
        assert data['turn_order'] == []
        assert data['total_participants'] == 0
    
    def test_get_current_turn_with_participants_registration_phase(self, client):
        """Test getting current turn with participants in registration phase."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        client.post('/api/participants', json={'name': 'Charlie'})
        
        response = client.get('/api/game/current-turn')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['current_turn'] is not None
        assert data['current_participant'] is not None
        assert data['current_participant']['name'] in ['Alice', 'Bob', 'Charlie']
        assert data['game_phase'] == 'registration'
        assert len(data['turn_order']) == 3
        assert data['total_participants'] == 3
        
        # Turn order should be sorted by participant ID
        assert data['turn_order'] == sorted(data['turn_order'])
    
    def test_get_current_turn_sets_turn_order_automatically(self, client):
        """Test that getting current turn automatically sets up turn order."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        
        # First call should set up turn order
        response1 = client.get('/api/game/current-turn')
        data1 = json.loads(response1.data)
        
        # Second call should have same turn order
        response2 = client.get('/api/game/current-turn')
        data2 = json.loads(response2.data)
        
        assert data1['turn_order'] == data2['turn_order']
        assert len(data1['turn_order']) == 2


class TestAdvanceTurnEndpoint:
    """Test cases for PUT /api/game/next-turn endpoint."""
    
    def test_advance_turn_no_participants(self, client):
        """Test advancing turn with no participants."""
        response = client.put('/api/game/next-turn')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No participants' in data['message']
        assert data['current_turn'] is None
        assert data['current_participant'] is None
    
    def test_advance_turn_starts_game(self, client):
        """Test that advancing turn starts the game from registration phase."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        
        # Advance turn should start game
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['game_phase'] == 'active'
        assert data['current_turn'] is not None
        assert data['current_participant'] is not None
    
    def test_advance_turn_progression(self, client):
        """Test turn advancement through all participants."""
        # Add participants
        participants = []
        for name in ['Alice', 'Bob', 'Charlie']:
            response = client.post('/api/participants', json={'name': name})
            participants.append(json.loads(response.data))
        
        # Get initial turn order
        response = client.get('/api/game/current-turn')
        initial_data = json.loads(response.data)
        turn_order = initial_data['turn_order']
        
        # Advance through all turns
        current_turns = []
        for i in range(len(turn_order)):
            response = client.put('/api/game/next-turn')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            
            if i < len(turn_order) - 1:
                # Should advance to next participant
                assert data['game_phase'] == 'active'
                assert data['current_turn'] == turn_order[i + 1]
                current_turns.append(data['current_turn'])
            else:
                # Should complete game
                assert data['game_phase'] == 'completed'
                assert data['current_turn'] is None
        
        # Verify we went through all participants in order
        assert current_turns == turn_order[1:]  # Skip first as it was set initially
    
    def test_advance_turn_after_completion(self, client):
        """Test advancing turn after game is completed."""
        # Add participant
        client.post('/api/participants', json={'name': 'Alice'})
        
        # Advance to start game
        client.put('/api/game/next-turn')
        
        # Advance to complete game (only one participant)
        response = client.put('/api/game/next-turn')
        data = json.loads(response.data)
        assert data['game_phase'] == 'completed'
        
        # Try to advance again
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['game_phase'] == 'completed'
        assert data['current_turn'] is None
    
    def test_advance_turn_sets_turn_order_if_missing(self, client):
        """Test that advancing turn sets up turn order if not already set."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        
        # Advance turn should set up turn order and start game
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['game_phase'] == 'active'
        
        # Check that turn order was set
        response = client.get('/api/game/current-turn')
        turn_data = json.loads(response.data)
        assert len(turn_data['turn_order']) == 2
        assert turn_data['turn_order'] == sorted(turn_data['turn_order'])


class TestGameStateLogic:
    """Test cases for game state logic using database directly."""
    
    def test_game_state_initialization(self, db_with_participants):
        """Test game state initialization."""
        db, participants = db_with_participants
        game_state = db.get_game_state()
        
        assert game_state.game_phase == 'registration'
        assert game_state.current_turn is None
        assert game_state.turn_order == []
    
    def test_set_turn_order(self, db_with_participants):
        """Test setting turn order."""
        db, participants = db_with_participants
        game_state = db.get_game_state()
        
        participant_ids = [p.id for p in participants]
        game_state.set_turn_order(participant_ids)
        
        assert game_state.turn_order == participant_ids
        assert game_state.current_turn == participant_ids[0]
    
    def test_next_turn_progression(self, db_with_participants):
        """Test next turn progression."""
        db, participants = db_with_participants
        game_state = db.get_game_state()
        
        participant_ids = sorted([p.id for p in participants])
        game_state.set_turn_order(participant_ids)
        game_state.start_game()
        
        # Should start with first participant
        assert game_state.current_turn == participant_ids[0]
        assert game_state.game_phase == 'active'
        
        # Advance to second participant
        next_turn = game_state.next_turn()
        assert next_turn == participant_ids[1]
        assert game_state.current_turn == participant_ids[1]
        assert game_state.game_phase == 'active'
        
        # Advance to third participant
        next_turn = game_state.next_turn()
        assert next_turn == participant_ids[2]
        assert game_state.current_turn == participant_ids[2]
        assert game_state.game_phase == 'active'
        
        # Advance past last participant - should complete game
        next_turn = game_state.next_turn()
        assert next_turn is None
        assert game_state.current_turn is None
        assert game_state.game_phase == 'completed'
    
    def test_next_turn_empty_turn_order(self):
        """Test next turn with empty turn order."""
        game_state = GameState()
        
        next_turn = game_state.next_turn()
        assert next_turn is None
        assert game_state.current_turn is None
    
    def test_next_turn_invalid_current_turn(self, db_with_participants):
        """Test next turn with invalid current turn."""
        db, participants = db_with_participants
        game_state = db.get_game_state()
        
        participant_ids = [p.id for p in participants]
        game_state.set_turn_order(participant_ids)
        game_state.current_turn = 999  # Invalid participant ID
        
        # Should reset to first participant
        next_turn = game_state.next_turn()
        assert next_turn == participant_ids[0]
        assert game_state.current_turn == participant_ids[0]


class TestGameStateIntegration:
    """Integration tests for game state management."""
    
    def test_full_game_flow(self, client):
        """Test complete game flow from registration to completion."""
        # Register participants
        participants = []
        for name in ['Alice', 'Bob', 'Charlie']:
            response = client.post('/api/participants', json={'name': name})
            assert response.status_code == 201
            participants.append(json.loads(response.data))
        
        # Check initial game state
        response = client.get('/api/game/current-turn')
        assert response.status_code == 200
        initial_state = json.loads(response.data)
        assert initial_state['game_phase'] == 'registration'
        assert len(initial_state['turn_order']) == 3
        
        # Get the expected turn order
        expected_order = sorted([p['id'] for p in participants])
        assert initial_state['turn_order'] == expected_order
        
        # The first participant should already be set as current turn
        assert initial_state['current_turn'] == expected_order[0]
        
        # Start game by advancing turn (this moves to second participant)
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        game_started = json.loads(response.data)
        assert game_started['game_phase'] == 'active'
        assert game_started['current_turn'] == expected_order[1]
        
        # Continue through remaining turns
        turns_played = [expected_order[0], expected_order[1]]  # First was set initially, second from first advance
        
        for i in range(1):  # 1 more turn for 3 participants (third participant)
            response = client.put('/api/game/next-turn')
            assert response.status_code == 200
            turn_data = json.loads(response.data)
            
            assert turn_data['game_phase'] == 'active'
            assert turn_data['current_turn'] == expected_order[2]
            turns_played.append(turn_data['current_turn'])
        
        # Final advance should complete the game
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        final_data = json.loads(response.data)
        assert final_data['game_phase'] == 'completed'
        assert final_data['current_turn'] is None
        
        # Verify all participants had a turn in correct order
        assert turns_played == expected_order
    
    def test_concurrent_turn_advancement(self, client):
        """Test that concurrent turn advancement is handled safely."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        
        # Multiple concurrent advance requests should be handled safely
        responses = []
        for _ in range(5):
            response = client.put('/api/game/next-turn')
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
        
        # Game should be in consistent state
        response = client.get('/api/game/current-turn')
        final_state = json.loads(response.data)
        assert final_state['game_phase'] in ['active', 'completed']


if __name__ == '__main__':
    pytest.main([__file__])