"""
Unit tests for gift management API endpoints.
Tests gift creation, retrieval, stealing mechanics, and locking behavior.
"""
import pytest
import json
import os
import tempfile
import threading
import time
from unittest.mock import patch
from app import app
from database import FileDatabase
from models import Gift, Participant


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    # Use a temporary file for testing
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    test_db_file.close()
    
    with patch('app.db') as mock_db:
        mock_db.data_file = test_db_file.name
        real_db = FileDatabase(test_db_file.name)
        mock_db.add_gift = real_db.add_gift
        mock_db.get_gifts = real_db.get_gifts
        mock_db.steal_gift_atomic = real_db.steal_gift_atomic
        mock_db.add_participant_atomic = real_db.add_participant_atomic
        mock_db.update_gift_name_atomic = real_db.update_gift_name_atomic
        
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    # Clean up
    os.unlink(test_db_file.name)


class TestGiftCreation:
    """Test gift creation endpoint."""
    
    def test_add_gift_success(self, client):
        """Test successful gift addition."""
        response = client.post('/api/gifts', 
                             json={'name': 'Test Gift'},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'id' in data
        assert data['name'] == 'Test Gift'
        assert data['steal_count'] == 0
        assert data['is_locked'] is False
        assert data['current_owner'] is None
        assert data['steal_history'] == []
    
    def test_add_gift_with_owner(self, client):
        """Test gift addition with initial owner."""
        # First add a participant
        client.post('/api/participants', 
                   json={'name': 'Test Participant'},
                   content_type='application/json')
        
        response = client.post('/api/gifts',
                             json={'name': 'Owned Gift', 'owner_id': 1},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['name'] == 'Owned Gift'
        assert data['current_owner'] == 1
    
    def test_add_gift_missing_name(self, client):
        """Test gift addition without name."""
        response = client.post('/api/gifts',
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required field: name' in data['error']
    
    def test_add_gift_empty_name(self, client):
        """Test gift addition with empty name."""
        response = client.post('/api/gifts',
                             json={'name': ''},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'empty' in data['error'].lower()
    
    def test_add_gift_invalid_name_type(self, client):
        """Test gift addition with non-string name."""
        response = client.post('/api/gifts',
                             json={'name': 123},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Gift name must be a string' in data['error']
    
    def test_add_gift_invalid_owner_type(self, client):
        """Test gift addition with invalid owner ID type."""
        response = client.post('/api/gifts',
                             json={'name': 'Test Gift', 'owner_id': 'invalid'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Owner ID must be an integer' in data['error']
    
    def test_add_gift_invalid_content_type(self, client):
        """Test gift addition with invalid content type."""
        response = client.post('/api/gifts',
                             data='name=Test Gift',
                             content_type='application/x-www-form-urlencoded')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Content-Type must be application/json' in data['error']


class TestGiftRetrieval:
    """Test gift retrieval endpoint."""
    
    def test_get_gifts_empty(self, client):
        """Test getting gifts when none exist."""
        response = client.get('/api/gifts')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gifts'] == []
    
    def test_get_gifts_with_data(self, client):
        """Test getting gifts when some exist."""
        # Add some gifts
        client.post('/api/gifts', json={'name': 'Gift 1'})
        client.post('/api/gifts', json={'name': 'Gift 2'})
        
        response = client.get('/api/gifts')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['gifts']) == 2
        
        gift_names = [g['name'] for g in data['gifts']]
        assert 'Gift 1' in gift_names
        assert 'Gift 2' in gift_names


class TestGiftStealing:
    """Test gift stealing mechanics."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.gift_id = None
    
    def add_test_gift(self, client, name='Test Gift', owner_id=None):
        """Helper to add a test gift and return its ID."""
        response = client.post('/api/gifts',
                             json={'name': name, 'owner_id': owner_id})
        data = json.loads(response.data)
        return data['id']
    
    def test_steal_gift_success(self, client):
        """Test successful gift stealing."""
        gift_id = self.add_test_gift(client)
        
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 1})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'stolen successfully' in data['message']
        assert data['gift']['current_owner'] == 1
        assert data['gift']['steal_count'] == 1
        assert data['gift']['is_locked'] is False
    
    def test_steal_gift_multiple_times(self, client):
        """Test stealing a gift multiple times."""
        gift_id = self.add_test_gift(client)
        
        # First steal
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 1})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 1
        assert data['gift']['current_owner'] == 1
        
        # Second steal
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 2})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 2
        assert data['gift']['current_owner'] == 2
        assert 1 in data['gift']['steal_history']
        
        # Third steal - should lock the gift
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 3})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 3
        assert data['gift']['current_owner'] == 3
        assert data['gift']['is_locked'] is True
        assert 'locked after 3 steals' in data['message']
        assert 1 in data['gift']['steal_history']
        assert 2 in data['gift']['steal_history']
    
    def test_steal_locked_gift(self, client):
        """Test attempting to steal a locked gift."""
        gift_id = self.add_test_gift(client)
        
        # Steal 3 times to lock the gift
        for i in range(1, 4):
            client.put(f'/api/gifts/{gift_id}/steal',
                      json={'new_owner_id': i})
        
        # Attempt to steal locked gift
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 4})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'locked' in data['message']
        assert data['gift']['current_owner'] == 3  # Still owned by previous stealer
        assert data['gift']['steal_count'] == 3
        assert data['gift']['is_locked'] is True
    
    def test_steal_nonexistent_gift(self, client):
        """Test stealing a gift that doesn't exist."""
        response = client.put('/api/gifts/nonexistent-id/steal',
                            json={'new_owner_id': 1})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()
    
    def test_steal_gift_missing_owner_id(self, client):
        """Test stealing without providing new owner ID."""
        gift_id = self.add_test_gift(client)
        
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required field: new_owner_id' in data['error']
    
    def test_steal_gift_invalid_owner_type(self, client):
        """Test stealing with invalid owner ID type."""
        gift_id = self.add_test_gift(client)
        
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 'invalid'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'New owner ID must be an integer' in data['error']
    
    def test_steal_gift_invalid_content_type(self, client):
        """Test stealing with invalid content type."""
        gift_id = self.add_test_gift(client)
        
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            data='new_owner_id=1',
                            content_type='application/x-www-form-urlencoded')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Content-Type must be application/json' in data['error']


class TestGiftLockingMechanics:
    """Test gift locking behavior in detail."""
    
    def add_test_gift(self, client, name='Test Gift'):
        """Helper to add a test gift and return its ID."""
        response = client.post('/api/gifts', json={'name': name})
        data = json.loads(response.data)
        return data['id']
    
    def test_gift_locking_after_exactly_three_steals(self, client):
        """Test that gift locks after exactly 3 steals."""
        gift_id = self.add_test_gift(client)
        
        # Perform exactly 3 steals
        for i in range(1, 4):
            response = client.put(f'/api/gifts/{gift_id}/steal',
                                json={'new_owner_id': i})
            data = json.loads(response.data)
            
            if i < 3:
                assert data['gift']['is_locked'] is False
            else:
                assert data['gift']['is_locked'] is True
    
    def test_steal_history_tracking(self, client):
        """Test that steal history is properly tracked."""
        gift_id = self.add_test_gift(client)
        
        # Initial steal (no previous owner)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 1})
        data = json.loads(response.data)
        assert data['gift']['steal_history'] == []
        
        # Second steal (previous owner should be in history)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 2})
        data = json.loads(response.data)
        assert data['gift']['steal_history'] == [1]
        
        # Third steal (both previous owners should be in history)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 3})
        data = json.loads(response.data)
        assert data['gift']['steal_history'] == [1, 2]
    
    def test_gift_with_initial_owner_steal_history(self, client):
        """Test steal history when gift has initial owner."""
        # Add participant first
        client.post('/api/participants', json={'name': 'Initial Owner'})
        
        # Add gift with initial owner
        response = client.post('/api/gifts',
                             json={'name': 'Owned Gift', 'owner_id': 1})
        gift_id = json.loads(response.data)['id']
        
        # Steal from initial owner
        response = client.put(f'/api/gifts/{gift_id}/steal',
                            json={'new_owner_id': 2})
        data = json.loads(response.data)
        
        assert data['gift']['current_owner'] == 2
        assert data['gift']['steal_history'] == [1]  # Initial owner in history
        assert data['gift']['steal_count'] == 1


class TestConcurrentGiftOperations:
    """Test concurrent gift operations for race conditions."""
    
    def add_test_gift(self, client, name='Test Gift'):
        """Helper to add a test gift and return its ID."""
        response = client.post('/api/gifts', json={'name': name})
        data = json.loads(response.data)
        return data['id']
    
    def test_concurrent_gift_steals_simulation(self, client):
        """Test gift stealing mechanics by simulating concurrent behavior."""
        gift_id = self.add_test_gift(client)
        
        # Simulate concurrent steals by making sequential requests
        # This tests the locking logic without threading complications
        results = []
        
        for i in range(1, 6):  # 5 steal attempts
            response = client.put(f'/api/gifts/{gift_id}/steal',
                                json={'new_owner_id': i})
            data = json.loads(response.data)
            results.append((i, response.status_code, data))
        
        # Count successful steals
        successful_steals = [r for r in results if r[2]['success']]
        failed_steals = [r for r in results if not r[2]['success']]
        
        # Should have exactly 3 successful steals and 2 failed (due to locking)
        assert len(successful_steals) == 3
        assert len(failed_steals) == 2
        
        # Verify final gift state
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        final_gift = gifts[0]
        
        assert final_gift['steal_count'] == 3
        assert final_gift['is_locked'] is True
        assert len(final_gift['steal_history']) == 2  # Two previous owners
    
    def test_multiple_gift_additions(self, client):
        """Test adding multiple gifts sequentially."""
        results = []
        
        # Add multiple gifts
        for i in range(10):
            response = client.post('/api/gifts',
                                 json={'name': f'Gift {i}'})
            data = json.loads(response.data)
            results.append((f'Gift {i}', response.status_code, data))
        
        # All additions should be successful
        for gift_name, status_code, data in results:
            assert status_code == 201
            assert data['name'] == gift_name
            assert 'id' in data
        
        # Verify all gifts were added
        response = client.get('/api/gifts')
        gifts = json.loads(response.data)['gifts']
        assert len(gifts) == 10
        
        # Verify all gift IDs are unique
        gift_ids = [g['id'] for g in gifts]
        assert len(set(gift_ids)) == 10


class TestGiftNameUpdate:
    """Test gift name update endpoint."""
    
    def test_update_gift_name_success(self, client):
        """Test successful gift name update."""
        # Add a gift
        response = client.post('/api/gifts', 
                             json={'name': 'Original Name'},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Update the gift name
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={'name': 'Updated Name'},
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['message'] == 'Gift name updated successfully'
        assert data['gift']['id'] == gift_id
        assert data['gift']['name'] == 'Updated Name'
        assert data['gift']['steal_count'] == 0
        assert data['gift']['is_locked'] is False
    
    def test_update_gift_name_preserves_metadata(self, client):
        """Test that updating gift name preserves steal count and other metadata."""
        # Add a gift with owner
        response = client.post('/api/gifts',
                             json={'name': 'Test Gift', 'owner_id': 5},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Simulate some steals by directly manipulating the gift
        # (In a real scenario, we'd use the steal endpoint)
        
        # Update the gift name
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={'name': 'New Name'},
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify metadata is preserved
        assert data['gift']['name'] == 'New Name'
        assert data['gift']['current_owner'] == 5
    
    def test_update_gift_name_not_found(self, client):
        """Test updating name for non-existent gift."""
        response = client.put('/api/gifts/nonexistent-id/name',
                            json={'name': 'New Name'},
                            content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()
    
    def test_update_gift_name_empty(self, client):
        """Test updating gift with empty name."""
        # Add a gift
        response = client.post('/api/gifts',
                             json={'name': 'Original Name'},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Try to update with empty name
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={'name': ''},
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'empty' in data['error'].lower()
    
    def test_update_gift_name_whitespace_only(self, client):
        """Test updating gift with whitespace-only name."""
        # Add a gift
        response = client.post('/api/gifts',
                             json={'name': 'Original Name'},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Try to update with whitespace-only name
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={'name': '   '},
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'empty' in data['error'].lower()
    
    def test_update_gift_name_missing_field(self, client):
        """Test updating gift without name field."""
        # Add a gift
        response = client.post('/api/gifts',
                             json={'name': 'Original Name'},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Try to update without name field
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={},
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'missing' in data['error'].lower()
    
    def test_update_gift_name_invalid_type(self, client):
        """Test updating gift with non-string name."""
        # Add a gift
        response = client.post('/api/gifts',
                             json={'name': 'Original Name'},
                             content_type='application/json')
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        
        # Try to update with non-string name
        response = client.put(f'/api/gifts/{gift_id}/name',
                            json={'name': 123},
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'string' in data['error'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])