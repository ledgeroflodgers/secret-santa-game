"""
End-to-End Integration Tests for Secret Santa Game Application.

This test suite covers:
- Complete user registration flow
- Concurrent registration scenarios
- Gift stealing and locking mechanics
- Admin functionality and turn management
- Data persistence across server restarts

Requirements tested: 1.1, 1.2, 4.3, 4.4, 6.1
"""
import pytest
import json
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from app import app
from database import FileDatabase
from models import Participant, Gift, GameState


class TestE2EUserRegistrationFlow:
    """End-to-end tests for complete user registration flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        # Initialize database with temp file
        from app import db
        db.data_file = self.temp_file.name
        db._ensure_data_file_exists()
        
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
        
        # Cleanup
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_complete_registration_workflow(self, client):
        """Test complete user registration workflow from start to finish."""
        # Step 1: Check initial state - no participants
        response = client.get('/api/participants/count')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert data['max_participants'] == 100
        
        # Step 2: Register first participant
        response = client.post('/api/participants',
                              json={'name': 'Alice Smith'},
                              content_type='application/json')
        assert response.status_code == 201
        alice_data = json.loads(response.data)
        assert alice_data['name'] == 'Alice Smith'
        assert 1 <= alice_data['id'] <= 100
        assert 'registration_timestamp' in alice_data
        alice_id = alice_data['id']
        
        # Step 3: Verify participant count increased
        response = client.get('/api/participants/count')
        data = json.loads(response.data)
        assert data['count'] == 1
        
        # Step 4: Register second participant
        response = client.post('/api/participants',
                              json={'name': 'Bob Johnson'},
                              content_type='application/json')
        assert response.status_code == 201
        bob_data = json.loads(response.data)
        assert bob_data['name'] == 'Bob Johnson'
        bob_id = bob_data['id']
        
        # Step 5: Verify unique IDs assigned
        assert alice_id != bob_id
        
        # Step 6: Get all participants and verify both are listed
        response = client.get('/api/participants')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['participants']) == 2
        
        # Verify participants are sorted by ID
        participant_ids = [p['id'] for p in data['participants']]
        assert participant_ids == sorted(participant_ids)
        
        # Step 7: Verify participant names are correct
        names = {p['id']: p['name'] for p in data['participants']}
        assert names[alice_id] == 'Alice Smith'
        assert names[bob_id] == 'Bob Johnson'
    
    def test_registration_validation_errors(self, client):
        """Test registration with various validation errors."""
        # Test empty name
        response = client.post('/api/participants',
                              json={'name': ''},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        
        # Test missing name field
        response = client.post('/api/participants',
                              json={},
                              content_type='application/json')
        assert response.status_code == 400
        
        # Test whitespace-only name
        response = client.post('/api/participants',
                              json={'name': '   '},
                              content_type='application/json')
        assert response.status_code == 400
        
        # Verify no participants were registered
        response = client.get('/api/participants/count')
        data = json.loads(response.data)
        assert data['count'] == 0


class TestE2EConcurrentRegistration:
    """End-to-end tests for concurrent registration scenarios."""
    
    @pytest.fixture
    def temp_db_file(self):
        """Create temporary database file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        yield temp_file.name
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_concurrent_registrations_no_duplicates(self, temp_db_file):
        """Test that concurrent registrations produce no duplicate IDs (Req 1.2, 6.1)."""
        db = FileDatabase(temp_db_file)
        num_concurrent = 25
        registered_ids = []
        errors = []
        
        def register_user(index):
            try:
                participant = db.add_participant_atomic(f"ConcurrentUser_{index}")
                return participant.id
            except Exception as e:
                errors.append(str(e))
                return None
        
        # Execute concurrent registrations
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(register_user, i) for i in range(num_concurrent)]
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    registered_ids.append(result)
        
        # Verify all registrations succeeded
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(registered_ids) == num_concurrent
        
        # Verify all IDs are unique (Requirement 1.2)
        assert len(set(registered_ids)) == len(registered_ids), \
            f"Duplicate IDs found: {registered_ids}"
        
        # Verify all IDs are in valid range (Requirement 1.1)
        for participant_id in registered_ids:
            assert 1 <= participant_id <= 100
        
        # Verify database consistency
        participants = db.get_participants()
        assert len(participants) == num_concurrent
    
    def test_concurrent_registration_at_capacity_limit(self, temp_db_file):
        """Test concurrent registrations when approaching 100 participant limit (Req 1.4)."""
        db = FileDatabase(temp_db_file)
        
        # Pre-register 95 participants
        for i in range(95):
            db.add_participant_atomic(f"PreUser_{i}")
        
        # Try to register 10 more concurrently (only 5 should succeed)
        num_attempts = 10
        successful = []
        failed = []
        
        def register_user(index):
            try:
                participant = db.add_participant_atomic(f"LimitUser_{index}")
                return ('success', participant.id)
            except Exception as e:
                return ('failed', str(e))
        
        with ThreadPoolExecutor(max_workers=num_attempts) as executor:
            futures = [executor.submit(register_user, i) for i in range(num_attempts)]
            
            for future in as_completed(futures):
                status, result = future.result()
                if status == 'success':
                    successful.append(result)
                else:
                    failed.append(result)
        
        # Verify exactly 5 succeeded and 5 failed
        assert len(successful) == 5, f"Expected 5 successful, got {len(successful)}"
        assert len(failed) == 5, f"Expected 5 failed, got {len(failed)}"
        
        # Verify total count is exactly 100
        total_count = db.get_participant_count()
        assert total_count == 100
        
        # Verify all successful IDs are unique
        assert len(set(successful)) == len(successful)


class TestE2EGiftStealingMechanics:
    """End-to-end tests for gift stealing and locking mechanics."""
    
    @pytest.fixture
    def client_with_participants(self):
        """Create test client with pre-registered participants."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        from app import db
        db.data_file = self.temp_file.name
        db._ensure_data_file_exists()
        
        # Pre-register 5 participants
        self.participant_ids = []
        for i in range(5):
            participant = db.add_participant_atomic(f"Player_{i+1}")
            self.participant_ids.append(participant.id)
        
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
        
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_gift_stealing_and_locking_flow(self, client_with_participants):
        """Test complete gift stealing flow including locking after 3 steals (Req 4.1-4.4)."""
        client = client_with_participants
        
        # Step 1: Add a gift
        response = client.post('/api/gifts',
                              json={'name': 'Nintendo Switch', 'owner_id': self.participant_ids[0]},
                              content_type='application/json')
        assert response.status_code == 201
        gift_data = json.loads(response.data)
        gift_id = gift_data['id']
        assert gift_data['steal_count'] == 0
        assert gift_data['is_locked'] is False
        assert gift_data['current_owner'] == self.participant_ids[0]
        
        # Step 2: First steal (Requirement 4.1)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                             json={'new_owner_id': self.participant_ids[1]},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['gift']['steal_count'] == 1
        assert data['gift']['is_locked'] is False
        assert data['gift']['current_owner'] == self.participant_ids[1]
        
        # Step 3: Second steal (Requirement 4.2)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                             json={'new_owner_id': self.participant_ids[2]},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 2
        assert data['gift']['is_locked'] is False
        
        # Step 4: Third steal - should lock the gift (Requirement 4.3)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                             json={'new_owner_id': self.participant_ids[3]},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['gift']['steal_count'] == 3
        assert data['gift']['is_locked'] is True  # Gift should be locked
        assert 'locked' in data['message'].lower()
        
        # Step 5: Attempt fourth steal - should fail (Requirement 4.4)
        response = client.put(f'/api/gifts/{gift_id}/steal',
                             json={'new_owner_id': self.participant_ids[4]},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['gift']['steal_count'] == 3  # Count should not increase
        assert data['gift']['is_locked'] is True
        assert data['gift']['current_owner'] == self.participant_ids[3]  # Owner unchanged
        
        # Step 6: Verify steal history
        response = client.get('/api/gifts')
        data = json.loads(response.data)
        gift = next(g for g in data['gifts'] if g['id'] == gift_id)
        assert len(gift['steal_history']) == 3
        assert self.participant_ids[0] in gift['steal_history']
        assert self.participant_ids[1] in gift['steal_history']
        assert self.participant_ids[2] in gift['steal_history']
    
    def test_multiple_gifts_independent_stealing(self, client_with_participants):
        """Test that multiple gifts have independent steal counters."""
        client = client_with_participants
        
        # Add three gifts
        gift_ids = []
        for i in range(3):
            response = client.post('/api/gifts',
                                  json={'name': f'Gift_{i+1}', 'owner_id': self.participant_ids[0]},
                                  content_type='application/json')
            gift_data = json.loads(response.data)
            gift_ids.append(gift_data['id'])
        
        # Steal gift 1 once
        client.put(f'/api/gifts/{gift_ids[0]}/steal',
                  json={'new_owner_id': self.participant_ids[1]},
                  content_type='application/json')
        
        # Steal gift 2 twice
        client.put(f'/api/gifts/{gift_ids[1]}/steal',
                  json={'new_owner_id': self.participant_ids[1]},
                  content_type='application/json')
        client.put(f'/api/gifts/{gift_ids[1]}/steal',
                  json={'new_owner_id': self.participant_ids[2]},
                  content_type='application/json')
        
        # Steal gift 3 three times (should lock)
        for i in range(3):
            client.put(f'/api/gifts/{gift_ids[2]}/steal',
                      json={'new_owner_id': self.participant_ids[i+1]},
                      content_type='application/json')
        
        # Verify each gift has correct steal count
        response = client.get('/api/gifts')
        data = json.loads(response.data)
        gifts = {g['id']: g for g in data['gifts']}
        
        assert gifts[gift_ids[0]]['steal_count'] == 1
        assert gifts[gift_ids[0]]['is_locked'] is False
        
        assert gifts[gift_ids[1]]['steal_count'] == 2
        assert gifts[gift_ids[1]]['is_locked'] is False
        
        assert gifts[gift_ids[2]]['steal_count'] == 3
        assert gifts[gift_ids[2]]['is_locked'] is True


class TestE2EAdminFunctionality:
    """End-to-end tests for admin functionality and turn management."""
    
    @pytest.fixture
    def client_with_game_setup(self):
        """Create test client with participants and game setup."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        
        from app import db
        db.data_file = self.temp_file.name
        db._ensure_data_file_exists()
        
        # Register 4 participants
        self.participant_ids = []
        for i in range(4):
            participant = db.add_participant_atomic(f"Player_{i+1}")
            self.participant_ids.append(participant.id)
        
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
        
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_turn_management_workflow(self, client_with_game_setup):
        """Test complete turn management workflow."""
        client = client_with_game_setup
        
        # Step 1: Check initial game state
        response = client.get('/api/game/current-turn')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['game_phase'] == 'registration'
        assert data['total_participants'] == 4
        
        # Step 2: Start the game (first next-turn call)
        response = client.put('/api/game/next-turn')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['game_phase'] == 'active'
        assert data['current_turn'] is not None
        first_turn_id = data['current_turn']
        
        # Step 3: Verify current turn is set
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        assert data['current_turn'] == first_turn_id
        assert data['current_participant'] is not None
        assert data['current_participant']['id'] == first_turn_id
        
        # Step 4: Advance through all turns
        turns_taken = [first_turn_id]
        for i in range(3):  # 3 more turns (total 4 participants)
            response = client.put('/api/game/next-turn')
            data = json.loads(response.data)
            if data['current_turn'] is not None:
                turns_taken.append(data['current_turn'])
        
        # Step 5: Verify all participants had a turn
        assert len(turns_taken) == 4
        assert set(turns_taken) == set(self.participant_ids)
        
        # Step 6: One more next_turn to complete the game
        response = client.put('/api/game/next-turn')
        data = json.loads(response.data)
        assert data['game_phase'] == 'completed'
        
        # Step 7: Verify game is completed
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        assert data['game_phase'] == 'completed'
    
    def test_gift_management_during_game(self, client_with_game_setup):
        """Test adding and managing gifts during active game."""
        client = client_with_game_setup
        
        # Start the game
        client.put('/api/game/next-turn')
        
        # Add multiple gifts
        gift_names = ['PlayStation 5', 'AirPods Pro', 'Coffee Maker']
        gift_ids = []
        
        for name in gift_names:
            response = client.post('/api/gifts',
                                  json={'name': name},
                                  content_type='application/json')
            assert response.status_code == 201
            data = json.loads(response.data)
            gift_ids.append(data['id'])
        
        # Verify all gifts are listed
        response = client.get('/api/gifts')
        data = json.loads(response.data)
        assert len(data['gifts']) == 3
        
        # Verify gift names
        retrieved_names = [g['name'] for g in data['gifts']]
        for name in gift_names:
            assert name in retrieved_names
    
    def test_previous_turn_functionality(self, client_with_game_setup):
        """Test going back to previous turn."""
        client = client_with_game_setup
        
        # Start game and advance 2 turns
        client.put('/api/game/next-turn')  # Start game
        response = client.get('/api/game/current-turn')
        first_turn = json.loads(response.data)['current_turn']
        
        client.put('/api/game/next-turn')  # Advance to turn 2
        response = client.get('/api/game/current-turn')
        second_turn = json.loads(response.data)['current_turn']
        
        # Go back to previous turn
        response = client.put('/api/game/previous-turn')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['current_turn'] == first_turn
        
        # Verify we're back at first turn
        response = client.get('/api/game/current-turn')
        data = json.loads(response.data)
        assert data['current_turn'] == first_turn


class TestE2EDataPersistence:
    """End-to-end tests for data persistence across server restarts."""
    
    def test_data_persists_across_database_reloads(self):
        """Test that data persists when database is reloaded (simulating restart)."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        
        try:
            # Phase 1: Create initial data
            db1 = FileDatabase(temp_file.name)
            
            # Register participants
            p1 = db1.add_participant_atomic("Alice")
            p2 = db1.add_participant_atomic("Bob")
            p3 = db1.add_participant_atomic("Charlie")
            
            # Add gifts
            g1 = db1.add_gift("Gift 1", p1.id)
            g2 = db1.add_gift("Gift 2", p2.id)
            
            # Steal a gift
            db1.steal_gift_atomic(g1.id, p2.id)
            
            # Set up game state
            participants, _, game_state = db1.read_all_data()
            game_state.set_turn_order([p1.id, p2.id, p3.id])
            game_state.start_game()
            db1.update_game_state(game_state)
            
            # Phase 2: Simulate server restart by creating new database instance
            db2 = FileDatabase(temp_file.name)
            
            # Verify participants persisted
            participants = db2.get_participants()
            assert len(participants) == 3
            participant_names = {p.name for p in participants}
            assert participant_names == {"Alice", "Bob", "Charlie"}
            
            # Verify gifts persisted
            gifts = db2.get_gifts()
            assert len(gifts) == 2
            gift_names = {g.name for g in gifts}
            assert gift_names == {"Gift 1", "Gift 2"}
            
            # Verify steal count persisted
            gift1 = next(g for g in gifts if g.name == "Gift 1")
            assert gift1.steal_count == 1
            assert gift1.current_owner == p2.id
            
            # Verify game state persisted
            _, _, game_state = db2.read_all_data()
            assert game_state.game_phase == "active"
            assert game_state.current_turn == p1.id
            assert len(game_state.turn_order) == 3
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_concurrent_operations_persist_correctly(self):
        """Test that concurrent operations all persist correctly."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        
        try:
            db = FileDatabase(temp_file.name)
            
            # Register 10 participants concurrently
            def register(i):
                return db.add_participant_atomic(f"User_{i}")
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(register, i) for i in range(10)]
                results = [f.result() for f in as_completed(futures)]
            
            # Reload database
            db2 = FileDatabase(temp_file.name)
            participants = db2.get_participants()
            
            # Verify all 10 participants persisted
            assert len(participants) == 10
            
            # Verify all have unique IDs
            ids = [p.id for p in participants]
            assert len(set(ids)) == 10
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


class TestE2ECompleteGameScenario:
    """End-to-end test for a complete game scenario."""
    
    def test_full_game_scenario(self):
        """Test a complete game scenario from registration to completion."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        
        try:
            from app import db
            db.data_file = temp_file.name
            db._ensure_data_file_exists()
            
            app.config['TESTING'] = True
            with app.test_client() as client:
                # Phase 1: Registration
                participant_ids = []
                for i in range(5):
                    response = client.post('/api/participants',
                                          json={'name': f'Player_{i+1}'},
                                          content_type='application/json')
                    data = json.loads(response.data)
                    participant_ids.append(data['id'])
                
                # Verify registration
                response = client.get('/api/participants/count')
                data = json.loads(response.data)
                assert data['count'] == 5
                
                # Phase 2: Start game
                response = client.put('/api/game/next-turn')
                assert response.status_code == 200
                
                # Phase 3: Add gifts and play
                gift_ids = []
                for i in range(3):
                    response = client.post('/api/gifts',
                                          json={'name': f'Gift_{i+1}', 
                                                'owner_id': participant_ids[i]},
                                          content_type='application/json')
                    data = json.loads(response.data)
                    gift_ids.append(data['id'])
                
                # Phase 4: Steal gifts
                # Steal gift 0 three times to lock it
                for i in range(3):
                    response = client.put(f'/api/gifts/{gift_ids[0]}/steal',
                                         json={'new_owner_id': participant_ids[(i+1) % 5]},
                                         content_type='application/json')
                    data = json.loads(response.data)
                    if i < 2:
                        assert data['success'] is True
                    else:
                        # Third steal should lock it
                        assert data['gift']['is_locked'] is True
                
                # Phase 5: Advance through all turns (5 participants, already at turn 1)
                # Need 4 more turns to go through all participants, then 1 more to complete
                for _ in range(5):  # 4 more turns + 1 to complete
                    client.put('/api/game/next-turn')
                
                # Phase 6: Verify game completion
                response = client.get('/api/game/current-turn')
                data = json.loads(response.data)
                assert data['game_phase'] == 'completed'
                
                # Phase 7: Verify final state
                response = client.get('/api/gifts')
                data = json.loads(response.data)
                locked_gifts = [g for g in data['gifts'] if g['is_locked']]
                assert len(locked_gifts) == 1
                assert locked_gifts[0]['steal_count'] == 3
                
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
