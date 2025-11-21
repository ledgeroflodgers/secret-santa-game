"""
Tests for the gift unlock functionality in the Secret Santa backend.
"""

import pytest
import json
import tempfile
import os
from app import app, db


class TestGiftResetFunctionality:
    """Test the gift reset functionality."""
    
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
    
    def test_reset_gift_not_needed(self, client):
        """Test resetting a gift that doesn't need resetting."""
        # Add a gift
        response = client.post('/api/gifts', json={'name': 'iPhone'})
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Try to reset it (should succeed but indicate it wasn't needed)
        response = client.put(f'/api/gifts/{gift_id}/reset-steals', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert "already has 0 steals" in data['message']
        assert data['gift']['is_locked'] == False
        assert data['gift']['steal_count'] == 0
    
    def test_reset_gift_steals_not_found(self, client):
        """Test resetting steals for a non-existent gift."""
        response = client.put('/api/gifts/nonexistent/reset-steals', json={})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error_code'] == "NOT_FOUND"
    
    def test_reset_gift_steals_success(self, client):
        """Test resetting a gift's steal count."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        client.post('/api/participants', json={'name': 'Charlie'})
        
        # Get participant IDs
        response = client.get('/api/participants')
        participants = json.loads(response.data)['participants']
        participant_ids = [p['id'] for p in participants]
        
        # Add a gift
        response = client.post('/api/gifts', json={'name': 'iPhone', 'owner_id': participant_ids[0]})
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Steal the gift twice
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[1]})
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[2]})
        
        # Verify gift has 2 steals
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        gift = next(g for g in gifts if g['id'] == gift_id)
        assert gift['steal_count'] == 2
        assert gift['is_locked'] == False
        
        # Reset the gift's steal count
        response = client.put(f'/api/gifts/{gift_id}/reset-steals', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert "reset to 0 and unlocked" in data['message']
        assert data['gift']['steal_count'] == 0
        assert data['gift']['is_locked'] == False
    
    def test_reset_locked_gift_steals(self, client):
        """Test resetting a locked gift's steal count."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        client.post('/api/participants', json={'name': 'Charlie'})
        client.post('/api/participants', json={'name': 'David'})
        
        # Get participant IDs
        response = client.get('/api/participants')
        participants = json.loads(response.data)['participants']
        participant_ids = [p['id'] for p in participants]
        
        # Add a gift
        response = client.post('/api/gifts', json={'name': 'iPhone', 'owner_id': participant_ids[0]})
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Steal the gift 3 times to lock it
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[1]})
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[2]})
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[3]})
        
        # Verify gift is locked
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        locked_gift = next(g for g in gifts if g['id'] == gift_id)
        assert locked_gift['is_locked'] == True
        assert locked_gift['steal_count'] == 3
        
        # Reset the gift's steal count
        response = client.put(f'/api/gifts/{gift_id}/reset-steals', json={})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert "reset to 0 and unlocked" in data['message']
        assert data['gift']['steal_count'] == 0
        assert data['gift']['is_locked'] == False
    
    def test_reset_then_steal_again(self, client):
        """Test that reset gifts can be stolen again properly."""
        # Add participants
        client.post('/api/participants', json={'name': 'Alice'})
        client.post('/api/participants', json={'name': 'Bob'})
        client.post('/api/participants', json={'name': 'Charlie'})
        client.post('/api/participants', json={'name': 'David'})
        client.post('/api/participants', json={'name': 'Eve'})
        
        # Get participant IDs
        response = client.get('/api/participants')
        participants = json.loads(response.data)['participants']
        participant_ids = [p['id'] for p in participants]
        
        # Add a gift
        response = client.post('/api/gifts', json={'name': 'iPhone', 'owner_id': participant_ids[0]})
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Steal the gift 3 times to lock it
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[1]})
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[2]})
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[3]})
        
        # Verify gift is locked
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        locked_gift = next(g for g in gifts if g['id'] == gift_id)
        assert locked_gift['is_locked'] == True
        assert locked_gift['steal_count'] == 3
        
        # Reset the gift
        response = client.put(f'/api/gifts/{gift_id}/reset-steals', json={})
        assert response.status_code == 200
        
        # Verify gift is reset
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        reset_gift = next(g for g in gifts if g['id'] == gift_id)
        assert reset_gift['is_locked'] == False
        assert reset_gift['steal_count'] == 0
        
        # Try to steal it again (should work now)
        response = client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[4]})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['gift']['current_owner'] == participant_ids[4]
        assert data['gift']['steal_count'] == 1  # Should start from 1 again
        assert data['gift']['is_locked'] == False  # Should not be locked yet
        
        # Steal it two more times to verify it can reach 3 steals again
        client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[0]})
        response = client.put(f'/api/gifts/{gift_id}/steal', json={'new_owner_id': participant_ids[1]})
        
        # Should be locked again after 3 steals
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 3
        assert data['gift']['is_locked'] == True
    

    
    def test_invalid_gift_id_reset(self, client):
        """Test resetting with invalid gift ID."""
        response = client.put('/api/gifts/invalid-id/reset-steals', json={})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error_code'] == "NOT_FOUND"


if __name__ == '__main__':
    pytest.main([__file__])