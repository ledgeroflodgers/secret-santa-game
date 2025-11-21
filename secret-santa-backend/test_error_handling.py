"""
Tests for comprehensive error handling in the Secret Santa backend.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from flask import Flask
from app import app, db
from error_handlers import (
    APIError, 
    validate_participant_name, 
    validate_gift_name, 
    validate_participant_id,
    register_error_handlers
)
from database import DatabaseError, ConcurrentAccessError


class TestAPIError:
    """Test the custom APIError class."""
    
    def test_api_error_creation(self):
        """Test creating APIError with all parameters."""
        error = APIError(
            message="Test error",
            status_code=400,
            error_code="TEST_ERROR",
            details={"field": "value"}
        )
        
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"field": "value"}
    
    def test_api_error_defaults(self):
        """Test APIError with default values."""
        error = APIError("Test error")
        
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.error_code is None
        assert error.details == {}


class TestValidationFunctions:
    """Test validation functions."""
    
    def test_validate_participant_name_valid(self):
        """Test valid participant names."""
        assert validate_participant_name("John Doe") == "John Doe"
        assert validate_participant_name("  Alice  ") == "Alice"
        assert validate_participant_name("Bob Smith-Jones") == "Bob Smith-Jones"
    
    def test_validate_participant_name_invalid_type(self):
        """Test invalid participant name types."""
        with pytest.raises(APIError) as exc_info:
            validate_participant_name(123)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "INVALID_NAME_TYPE"
    
    def test_validate_participant_name_empty(self):
        """Test empty participant names."""
        with pytest.raises(APIError) as exc_info:
            validate_participant_name("")
        
        assert exc_info.value.error_code == "EMPTY_NAME"
        
        with pytest.raises(APIError) as exc_info:
            validate_participant_name("   ")
        
        assert exc_info.value.error_code == "EMPTY_NAME"
    
    def test_validate_participant_name_too_short(self):
        """Test participant names that are too short."""
        with pytest.raises(APIError) as exc_info:
            validate_participant_name("A")
        
        assert exc_info.value.error_code == "NAME_TOO_SHORT"
    
    def test_validate_participant_name_too_long(self):
        """Test participant names that are too long."""
        long_name = "A" * 51
        with pytest.raises(APIError) as exc_info:
            validate_participant_name(long_name)
        
        assert exc_info.value.error_code == "NAME_TOO_LONG"
    
    def test_validate_gift_name_valid(self):
        """Test valid gift names."""
        assert validate_gift_name("iPhone") == "iPhone"
        assert validate_gift_name("  Gift Card  ") == "Gift Card"
    
    def test_validate_gift_name_invalid_type(self):
        """Test invalid gift name types."""
        with pytest.raises(APIError) as exc_info:
            validate_gift_name(123)
        
        assert exc_info.value.error_code == "INVALID_GIFT_NAME_TYPE"
    
    def test_validate_gift_name_empty(self):
        """Test empty gift names."""
        with pytest.raises(APIError) as exc_info:
            validate_gift_name("")
        
        assert exc_info.value.error_code == "EMPTY_GIFT_NAME"
    
    def test_validate_gift_name_too_long(self):
        """Test gift names that are too long."""
        long_name = "A" * 101
        with pytest.raises(APIError) as exc_info:
            validate_gift_name(long_name)
        
        assert exc_info.value.error_code == "GIFT_NAME_TOO_LONG"
    
    def test_validate_participant_id_valid(self):
        """Test valid participant IDs."""
        assert validate_participant_id(1) == 1
        assert validate_participant_id(50) == 50
        assert validate_participant_id(100) == 100
    
    def test_validate_participant_id_invalid_type(self):
        """Test invalid participant ID types."""
        with pytest.raises(APIError) as exc_info:
            validate_participant_id("1")
        
        assert exc_info.value.error_code == "INVALID_PARTICIPANT_ID_TYPE"
    
    def test_validate_participant_id_out_of_range(self):
        """Test participant IDs out of valid range."""
        with pytest.raises(APIError) as exc_info:
            validate_participant_id(0)
        
        assert exc_info.value.error_code == "INVALID_PARTICIPANT_ID_RANGE"
        
        with pytest.raises(APIError) as exc_info:
            validate_participant_id(101)
        
        assert exc_info.value.error_code == "INVALID_PARTICIPANT_ID_RANGE"


class TestErrorHandlers:
    """Test error handlers with Flask app."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_error_handler(self, client):
        """Test APIError handler."""
        with app.app_context():
            # Create a route that raises APIError
            @app.route('/test-api-error')
            def test_api_error():
                raise APIError(
                    "Test API error",
                    status_code=422,
                    error_code="TEST_ERROR",
                    details={"field": "test"}
                )
            
            response = client.get('/test-api-error')
            
            assert response.status_code == 422
            data = json.loads(response.data)
            assert data['error'] == "Test API error"
            assert data['error_code'] == "TEST_ERROR"
            assert 'timestamp' in data
    
    def test_database_error_handler(self, client):
        """Test DatabaseError handler."""
        with app.app_context():
            @app.route('/test-database-error')
            def test_database_error():
                raise DatabaseError("Test database error")
            
            response = client.get('/test-database-error')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['error'] == "Test database error"
            assert data['error_code'] == "DATABASE_ERROR"
    
    def test_concurrent_access_error_handler(self, client):
        """Test ConcurrentAccessError handler."""
        with app.app_context():
            @app.route('/test-concurrent-error')
            def test_concurrent_error():
                raise ConcurrentAccessError("Test concurrent access error")
            
            response = client.get('/test-concurrent-error')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert "temporarily unavailable" in data['error']
            assert data['error_code'] == "CONCURRENT_ACCESS"
            assert 'retry_after' in data
    
    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == "Resource not found."
        assert data['error_code'] == "NOT_FOUND"
        assert data['path'] == "/nonexistent-endpoint"
    
    def test_405_error_handler(self, client):
        """Test 405 method not allowed error handler."""
        # Try POST to a GET-only endpoint
        response = client.post('/api/health')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert "Method POST not allowed" in data['error']
        assert data['error_code'] == "METHOD_NOT_ALLOWED"
    
    def test_500_error_handler(self, client):
        """Test 500 internal server error handler."""
        with app.app_context():
            @app.route('/test-500-error')
            def test_500_error():
                raise Exception("Test internal error")
            
            response = client.get('/test-500-error')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['error'] == "Internal server error. Please try again later."
            assert data['error_code'] == "INTERNAL_SERVER_ERROR"


class TestEnhancedAPIEndpoints:
    """Test API endpoints with enhanced error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database."""
        app.config['TESTING'] = True
        
        # Create temporary file for testing
        temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
        os.close(temp_fd)
        
        # Initialize database with temp file
        db.data_file = temp_path
        db._ensure_data_file_exists()
        
        with app.test_client() as client:
            yield client
        
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_register_participant_invalid_json(self, client):
        """Test participant registration with invalid JSON."""
        response = client.post('/api/participants', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_JSON"
    
    def test_register_participant_missing_content_type(self, client):
        """Test participant registration without JSON content type."""
        response = client.post('/api/participants', 
                             data=json.dumps({'name': 'Test'}))
        
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_CONTENT_TYPE"
    
    def test_register_participant_missing_name(self, client):
        """Test participant registration without name field."""
        response = client.post('/api/participants', 
                             json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "MISSING_FIELDS"
        assert 'name' in data['details']['missing_fields']
    
    def test_register_participant_invalid_name_type(self, client):
        """Test participant registration with invalid name type."""
        response = client.post('/api/participants', 
                             json={'name': 123})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_NAME_TYPE"
    
    def test_register_participant_empty_name(self, client):
        """Test participant registration with empty name."""
        response = client.post('/api/participants', 
                             json={'name': ''})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "EMPTY_NAME"
    
    def test_register_participant_success(self, client):
        """Test successful participant registration."""
        response = client.post('/api/participants', 
                             json={'name': 'John Doe'})
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'John Doe'
        assert 'id' in data
        assert 'registration_timestamp' in data
    
    def test_add_gift_invalid_name_type(self, client):
        """Test gift addition with invalid name type."""
        response = client.post('/api/gifts', 
                             json={'name': 123})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_GIFT_NAME_TYPE"
    
    def test_add_gift_empty_name(self, client):
        """Test gift addition with empty name."""
        response = client.post('/api/gifts', 
                             json={'name': ''})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "EMPTY_GIFT_NAME"
    
    def test_add_gift_success(self, client):
        """Test successful gift addition."""
        response = client.post('/api/gifts', 
                             json={'name': 'iPhone'})
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'iPhone'
        assert 'id' in data
    
    def test_steal_gift_invalid_gift_id(self, client):
        """Test gift stealing with invalid gift ID."""
        response = client.put('/api/gifts//steal', 
                            json={'new_owner_id': 1})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_GIFT_ID"
    
    def test_steal_gift_invalid_owner_id(self, client):
        """Test gift stealing with invalid owner ID."""
        response = client.put('/api/gifts/test-gift/steal', 
                            json={'new_owner_id': 'invalid'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "INVALID_PARTICIPANT_ID_TYPE"
    
    def test_steal_gift_not_found(self, client):
        """Test gift stealing with non-existent gift."""
        response = client.put('/api/gifts/nonexistent/steal', 
                            json={'new_owner_id': 1})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error_code'] == "GIFT_NOT_FOUND"
    
    def test_advance_turn_no_participants(self, client):
        """Test advancing turn with no participants."""
        response = client.put('/api/game/next-turn', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error_code'] == "NO_PARTICIPANTS"


class TestConcurrentAccessHandling:
    """Test concurrent access error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('app.db.add_participant_atomic')
    def test_concurrent_access_during_registration(self, mock_add_participant, client):
        """Test concurrent access error during participant registration."""
        mock_add_participant.side_effect = ConcurrentAccessError("High traffic")
        
        response = client.post('/api/participants', 
                             json={'name': 'John Doe'})
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error_code'] == "CONCURRENT_ACCESS"
        assert 'retry_after' in data
    
    @patch('app.db.get_participants')
    def test_concurrent_access_during_get_participants(self, mock_get_participants, client):
        """Test concurrent access error when getting participants."""
        mock_get_participants.side_effect = ConcurrentAccessError("High traffic")
        
        response = client.get('/api/participants')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error_code'] == "CONCURRENT_ACCESS"


if __name__ == '__main__':
    pytest.main([__file__])