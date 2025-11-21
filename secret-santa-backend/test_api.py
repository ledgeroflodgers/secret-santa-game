"""
Unit tests for participant registration API endpoints.
Tests focus on race conditions and concurrent access scenarios.
"""
import pytest
import json
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from app import app
from database import FileDatabase, DatabaseError, ConcurrentAccessError
from models import Participant


class TestParticipantRegistrationAPI:
    """Test cases for participant registration API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database."""
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        # Patch the database to use temporary file
        with patch('app.db') as mock_db:
            mock_db.data_file = self.temp_file.name
            real_db = FileDatabase(self.temp_file.name)
            mock_db.add_participant_atomic = real_db.add_participant_atomic
            mock_db.get_participants = real_db.get_participants
            mock_db.get_participant_count = real_db.get_participant_count
            
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client
        
        # Cleanup
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_register_participant_success(self, client):
        """Test successful participant registration."""
        response = client.post('/api/participants', 
                             json={'name': 'John Doe'},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'id' in data
        assert data['name'] == 'John Doe'
        assert 'registration_timestamp' in data
        assert 1 <= data['id'] <= 100
    
    def test_register_participant_missing_name(self, client):
        """Test registration with missing name field."""
        response = client.post('/api/participants', 
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'name' in data['error'].lower()
    
    def test_register_participant_empty_name(self, client):
        """Test registration with empty name."""
        response = client.post('/api/participants', 
                             json={'name': ''},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'empty' in data['error'].lower()
    
    def test_register_participant_whitespace_name(self, client):
        """Test registration with whitespace-only name."""
        response = client.post('/api/participants', 
                             json={'name': '   '},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_participant_invalid_content_type(self, client):
        """Test registration with invalid content type."""
        response = client.post('/api/participants', 
                             data='name=John',
                             content_type='application/x-www-form-urlencoded')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Content-Type' in data['error']
    
    def test_register_participant_non_string_name(self, client):
        """Test registration with non-string name."""
        response = client.post('/api/participants', 
                             json={'name': 123},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'string' in data['error'].lower()
    
    def test_get_participants_empty(self, client):
        """Test getting participants when none are registered."""
        response = client.get('/api/participants')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'participants' in data
        assert data['participants'] == []
    
    def test_get_participants_with_data(self, client):
        """Test getting participants after registration."""
        # Register a participant first
        client.post('/api/participants', 
                   json={'name': 'Alice'},
                   content_type='application/json')
        
        response = client.get('/api/participants')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'participants' in data
        assert len(data['participants']) == 1
        assert data['participants'][0]['name'] == 'Alice'
    
    def test_get_participant_count_empty(self, client):
        """Test getting participant count when none are registered."""
        response = client.get('/api/participants/count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert data['max_participants'] == 100
    
    def test_get_participant_count_with_data(self, client):
        """Test getting participant count after registrations."""
        # Register multiple participants
        for i in range(3):
            client.post('/api/participants', 
                       json={'name': f'User{i}'},
                       content_type='application/json')
        
        response = client.get('/api/participants/count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 3
        assert data['max_participants'] == 100
    
    def test_participants_sorted_by_id(self, client):
        """Test that participants are returned sorted by ID."""
        names = ['Charlie', 'Alice', 'Bob']
        
        # Register participants
        for name in names:
            client.post('/api/participants', 
                       json={'name': name},
                       content_type='application/json')
        
        response = client.get('/api/participants')
        data = json.loads(response.data)
        
        # Check that IDs are in ascending order
        ids = [p['id'] for p in data['participants']]
        assert ids == sorted(ids)


class TestConcurrentRegistration:
    """Test cases for concurrent participant registration scenarios."""
    
    @pytest.fixture
    def temp_db_file(self):
        """Create temporary database file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        yield temp_file.name
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_concurrent_registration_unique_numbers(self, temp_db_file):
        """Test that concurrent registrations get unique participant numbers."""
        db = FileDatabase(temp_db_file)
        num_threads = 10
        results = []
        errors = []
        
        def register_participant(name):
            try:
                participant = db.add_participant_atomic(f"User_{name}")
                return participant.id
            except Exception as e:
                errors.append(str(e))
                return None
        
        # Run concurrent registrations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(register_participant, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)
        
        # Verify all registrations succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads
        
        # Verify all numbers are unique
        assert len(set(results)) == len(results), f"Duplicate numbers found: {results}"
        
        # Verify all numbers are in valid range
        for num in results:
            assert 1 <= num <= 100
    
    def test_concurrent_registration_race_condition_simulation(self, temp_db_file):
        """Test registration under simulated race conditions."""
        db = FileDatabase(temp_db_file)
        num_threads = 20
        successful_registrations = []
        failed_registrations = []
        
        def register_with_delay(thread_id):
            try:
                # Add small random delay to increase chance of race conditions
                time.sleep(0.001 * (thread_id % 3))
                participant = db.add_participant_atomic(f"RaceUser_{thread_id}")
                successful_registrations.append(participant.id)
                return True
            except Exception as e:
                failed_registrations.append(str(e))
                return False
        
        # Run concurrent registrations
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=register_with_delay, args=(i,))
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(successful_registrations) == num_threads, f"Expected {num_threads} successful registrations, got {len(successful_registrations)}"
        assert len(failed_registrations) == 0, f"Unexpected failures: {failed_registrations}"
        
        # Verify unique numbers
        assert len(set(successful_registrations)) == len(successful_registrations)
    
    def test_registration_limit_enforcement(self, temp_db_file):
        """Test that registration limit is properly enforced under concurrent access."""
        db = FileDatabase(temp_db_file)
        
        # Pre-register 98 participants to approach the limit
        for i in range(98):
            db.add_participant_atomic(f"PreUser_{i}")
        
        # Now try to register 5 more participants concurrently (only 2 should succeed)
        num_threads = 5
        successful_registrations = []
        failed_registrations = []
        
        def register_participant(thread_id):
            try:
                participant = db.add_participant_atomic(f"LimitUser_{thread_id}")
                successful_registrations.append(participant.id)
                return True
            except DatabaseError as e:
                if "maximum" in str(e).lower() or "limit" in str(e).lower():
                    failed_registrations.append("limit_reached")
                else:
                    failed_registrations.append(str(e))
                return False
        
        # Run concurrent registrations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(register_participant, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                future.result()
        
        # Verify exactly 2 succeeded and 3 failed due to limit
        assert len(successful_registrations) == 2, f"Expected 2 successful registrations, got {len(successful_registrations)}"
        assert len(failed_registrations) == 3, f"Expected 3 failed registrations, got {len(failed_registrations)}"
        assert all(failure == "limit_reached" for failure in failed_registrations)
        
        # Verify total count is exactly 100
        total_count = db.get_participant_count()
        assert total_count == 100
    
    def test_file_corruption_recovery(self, temp_db_file):
        """Test recovery from file corruption during concurrent access."""
        db = FileDatabase(temp_db_file, max_retries=3, retry_delay=0.01)
        
        # Register a few participants normally first
        for i in range(3):
            db.add_participant_atomic(f"NormalUser_{i}")
        
        # Simulate file corruption by writing invalid JSON
        with open(temp_db_file, 'w') as f:
            f.write('{"invalid": json content')
        
        # The next registration should handle the corruption and reinitialize
        try:
            participant = db.add_participant_atomic("RecoveryUser")
            # If we get here, the database recovered
            assert participant.name == "RecoveryUser"
        except Exception as e:
            # The database should attempt recovery, but might still fail
            # This is acceptable behavior for severe corruption
            error_msg = str(e).lower()
            assert "json" in error_msg or "corrupt" in error_msg or "expecting value" in error_msg


class TestAPIErrorHandling:
    """Test cases for API error handling scenarios."""
    
    def test_database_error_handling(self):
        """Test API response to database errors."""
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            with patch('app.db.add_participant_atomic') as mock_add:
                # Simulate database error
                mock_add.side_effect = DatabaseError("Test database error")
                
                response = client.post('/api/participants', 
                                     json={'name': 'Test User'},
                                     content_type='application/json')
                
                assert response.status_code == 400
                data = json.loads(response.data)
                assert 'error' in data
    
    def test_concurrent_access_error_handling(self):
        """Test API response to concurrent access errors."""
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            # Import the app module to patch the db instance
            import app as app_module
            with patch.object(app_module, 'db') as mock_db:
                # Simulate concurrent access error
                mock_db.add_participant_atomic.side_effect = ConcurrentAccessError("Concurrent access conflict")
                
                response = client.post('/api/participants', 
                                     json={'name': 'Test User'},
                                     content_type='application/json')
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert 'error' in data
                assert 'try again' in data['error'].lower()
    
    def test_registration_full_error(self):
        """Test API response when registration is full."""
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            with patch('app.db.add_participant_atomic') as mock_add:
                # Simulate registration full error
                mock_add.side_effect = DatabaseError("Maximum number of participants (100) reached")
                
                response = client.post('/api/participants', 
                                     json={'name': 'Test User'},
                                     content_type='application/json')
                
                assert response.status_code == 409  # Conflict
                data = json.loads(response.data)
                assert 'error' in data
                assert 'maximum' in data['error'].lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])