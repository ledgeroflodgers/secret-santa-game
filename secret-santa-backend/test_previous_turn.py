"""
Tests for the previous turn functionality in the Secret Santa backend.
"""

import pytest
import json
import tempfile
import os
from app import app, db


class TestPreviousTurnFunctionality:
    """Test the previous turn functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database."""
        app.config['TESTING'] = True
        
        # Create temporary file for testing
        temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
        os.close(temp_fd)
        
        # Store original data file path
        original_data_file = db.data_file
        
        # Initialize database with temp file
        db.data_file = temp_path
        db._ensure_data_file_exists()
        
        with app.test_client() as client:
            yield client
        
        # Restore original data file
        db.data_file = original_data_file
        
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_previous_turn_no_participants(self, client):
        """Test previous turn with no participants."""
        response = client.put('/api/game/previous-turn', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "NO_PARTICIPANTS"
    
    def test_previous_turn_game_not_started(self, client):
        """Test previous turn when game hasn't started."""
        # Add a participant but don't start the game
        client.post('/api/participants', json={'name': 'Alice'})
        
        response = client.put('/api/game/previous-turn', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "GAME_NOT_STARTED"
    
    def test_previous_turn_at_first_turn(self, client):
        """Test previous turn when already at first turn."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        
        # Start game by advancing turn (stays at first participant)
        client.put('/api/game/next-turn', json={})
        
        # Try to go back from first turn
        response = client.put('/api/game/previous-turn', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
        assert "Already at the first turn" in data['message']
    
    def test_previous_turn_success(self, client):
        """Test successful previous turn operation."""
        # Add participants
        response_alice = client.post('/api/participants', json={'name': 'Alice'})
        alice_data = json.loads(response_alice.data)
        print(f"Alice ID: {alice_data['id']}")
        
        response_bob = client.post('/api/participants', json={'name': 'Bob'})
        bob_data = json.loads(response_bob.data)
        print(f"Bob ID: {bob_data['id']}")
        
        response_charlie = client.post('/api/participants', json={'name': 'Charlie'})
        charlie_data = json.loads(response_charlie.data)
        print(f"Charlie ID: {charlie_data['id']}")
        
        # Check turn order
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        print(f"Turn order: {data['turn_order']}")
        
        # Get the turn order to understand the sequence
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        turn_order = data['turn_order']
        
        # Map IDs to names
        id_to_name = {alice_data['id']: 'Alice', bob_data['id']: 'Bob', charlie_data['id']: 'Charlie'}
        first_participant = id_to_name[turn_order[0]]
        second_participant = id_to_name[turn_order[1]]
        
        # Start game and advance a few turns
        response1 = client.put('/api/game/next-turn', json={})  # First participant
        data1 = json.loads(response1.data)
        assert data1['current_participant']['name'] == first_participant
        
        response2 = client.put('/api/game/next-turn', json={})  # Second participant
        data2 = json.loads(response2.data)
        assert data2['current_participant']['name'] == second_participant
        
        # Go back to previous turn
        response = client.put('/api/game/previous-turn', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert "Went back to previous turn" in data['message']
        assert data['current_participant']['name'] == first_participant
        assert data['game_phase'] == 'active'
    
    def test_previous_turn_from_completed_game(self, client):
        """Test going back from completed game state."""
        # Add participants
        response_alice = client.post('/api/participants', json={'name': 'Alice'})
        alice_data = json.loads(response_alice.data)
        response_bob = client.post('/api/participants', json={'name': 'Bob'})
        bob_data = json.loads(response_bob.data)
        
        # Get turn order
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        turn_order = data['turn_order']
        id_to_name = {alice_data['id']: 'Alice', bob_data['id']: 'Bob'}
        last_participant = id_to_name[turn_order[-1]]
        
        # Complete the game
        client.put('/api/game/next-turn', json={})  # First participant
        client.put('/api/game/next-turn', json={})  # Second participant
        client.put('/api/game/next-turn', json={})  # Game completed
        
        # Verify game is completed
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        assert data['game_phase'] == 'completed'
        assert data['current_turn'] is None
        
        # Go back from completed state
        response = client.put('/api/game/previous-turn', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['current_participant']['name'] == last_participant  # Last participant
        assert data['game_phase'] == 'active'  # Game should be active again
    
    def test_previous_turn_multiple_times(self, client):
        """Test going back multiple turns."""
        # Add participants
        response_alice = client.post('/api/participants', json={'name': 'Alice'})
        alice_data = json.loads(response_alice.data)
        response_bob = client.post('/api/participants', json={'name': 'Bob'})
        bob_data = json.loads(response_bob.data)
        response_charlie = client.post('/api/participants', json={'name': 'Charlie'})
        charlie_data = json.loads(response_charlie.data)
        
        # Get turn order
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        turn_order = data['turn_order']
        id_to_name = {alice_data['id']: 'Alice', bob_data['id']: 'Bob', charlie_data['id']: 'Charlie'}
        first_participant = id_to_name[turn_order[0]]
        second_participant = id_to_name[turn_order[1]]
        third_participant = id_to_name[turn_order[2]]
        
        # Advance through all turns
        client.put('/api/game/next-turn', json={})  # First
        client.put('/api/game/next-turn', json={})  # Second
        client.put('/api/game/next-turn', json={})  # Third
        
        # Go back twice
        response1 = client.put('/api/game/previous-turn', json={})
        data1 = json.loads(response1.data)
        assert data1['current_participant']['name'] == second_participant
        
        response2 = client.put('/api/game/previous-turn', json={})
        data2 = json.loads(response2.data)
        assert data2['current_participant']['name'] == first_participant
        
        # Try to go back again (should fail - already at first)
        response3 = client.put('/api/game/previous-turn', json={})
        data3 = json.loads(response3.data)
        assert data3['success'] == False
        assert "Already at the first turn" in data3['message']
    
    def test_next_and_previous_turn_cycle(self, client):
        """Test cycling between next and previous turns."""
        # Add participants
        response_alice = client.post('/api/participants', json={'name': 'Alice'})
        alice_data = json.loads(response_alice.data)
        response_bob = client.post('/api/participants', json={'name': 'Bob'})
        bob_data = json.loads(response_bob.data)
        
        # Get turn order
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        turn_order = data['turn_order']
        id_to_name = {alice_data['id']: 'Alice', bob_data['id']: 'Bob'}
        first_participant = id_to_name[turn_order[0]]
        second_participant = id_to_name[turn_order[1]]
        
        # Start game
        client.put('/api/game/next-turn', json={})  # First participant
        
        # Go to next turn
        response = client.put('/api/game/next-turn', json={})
        data = json.loads(response.data)
        assert data['current_participant']['name'] == second_participant
        
        # Go back
        response = client.put('/api/game/previous-turn', json={})
        data = json.loads(response.data)
        assert data['current_participant']['name'] == first_participant
        
        # Go forward again
        response = client.put('/api/game/next-turn', json={})
        data = json.loads(response.data)
        assert data['current_participant']['name'] == second_participant


if __name__ == '__main__':
    pytest.main([__file__])