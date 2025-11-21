"""
Comprehensive error handling for the Secret Santa backend application.
"""

from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime
from database import DatabaseError, ConcurrentAccessError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API error class for structured error responses."""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

def register_error_handlers(app):
    """Register all error handlers with the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        response = {
            'error': error.message,
            'error_code': error.error_code,
            'timestamp': datetime.now().isoformat()
        }
        
        if error.details:
            response['details'] = error.details
            
        logger.warning(f"API Error: {error.message} (Status: {error.status_code})")
        return jsonify(response), error.status_code

    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        """Handle database-related errors."""
        error_message = str(error)
        status_code = 400
        error_code = 'DATABASE_ERROR'
        
        # Determine appropriate status code based on error type
        if "empty" in error_message.lower():
            status_code = 400
            error_code = 'VALIDATION_ERROR'
        elif "maximum" in error_message.lower() or "limit" in error_message.lower():
            status_code = 409
            error_code = 'CAPACITY_EXCEEDED'
        elif "not found" in error_message.lower():
            status_code = 404
            error_code = 'NOT_FOUND'
        else:
            status_code = 500
            error_code = 'DATABASE_ERROR'
            
        response = {
            'error': error_message,
            'error_code': error_code,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f"Database Error: {error_message}")
        return jsonify(response), status_code

    @app.errorhandler(ConcurrentAccessError)
    def handle_concurrent_access_error(error):
        """Handle concurrent access errors."""
        response = {
            'error': 'Service temporarily unavailable due to high traffic. Please try again.',
            'error_code': 'CONCURRENT_ACCESS',
            'timestamp': datetime.now().isoformat(),
            'retry_after': 1  # Suggest retry after 1 second
        }
        
        logger.warning(f"Concurrent Access Error: {str(error)}")
        return jsonify(response), 503

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors."""
        response = {
            'error': 'Bad request. Please check your input.',
            'error_code': 'BAD_REQUEST',
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to get more specific error message
        if hasattr(error, 'description'):
            response['error'] = error.description
            
        logger.warning(f"Bad Request: {request.url} - {error}")
        return jsonify(response), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors."""
        response = {
            'error': 'Resource not found.',
            'error_code': 'NOT_FOUND',
            'timestamp': datetime.now().isoformat(),
            'path': request.path
        }
        
        logger.warning(f"Not Found: {request.url}")
        return jsonify(response), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle method not allowed errors."""
        response = {
            'error': f'Method {request.method} not allowed for this endpoint.',
            'error_code': 'METHOD_NOT_ALLOWED',
            'timestamp': datetime.now().isoformat(),
            'allowed_methods': list(error.valid_methods) if hasattr(error, 'valid_methods') else []
        }
        
        logger.warning(f"Method Not Allowed: {request.method} {request.url}")
        return jsonify(response), 405

    @app.errorhandler(413)
    def handle_payload_too_large(error):
        """Handle payload too large errors."""
        response = {
            'error': 'Request payload too large.',
            'error_code': 'PAYLOAD_TOO_LARGE',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f"Payload Too Large: {request.url}")
        return jsonify(response), 413

    @app.errorhandler(415)
    def handle_unsupported_media_type(error):
        """Handle unsupported media type errors."""
        response = {
            'error': 'Unsupported media type. Expected application/json.',
            'error_code': 'UNSUPPORTED_MEDIA_TYPE',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f"Unsupported Media Type: {request.url}")
        return jsonify(response), 415

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded errors."""
        response = {
            'error': 'Too many requests. Please wait before trying again.',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'timestamp': datetime.now().isoformat(),
            'retry_after': 60  # Suggest retry after 60 seconds
        }
        
        logger.warning(f"Rate Limit Exceeded: {request.remote_addr}")
        return jsonify(response), 429

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle internal server errors."""
        response = {
            'error': 'Internal server error. Please try again later.',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the full traceback for debugging
        logger.error(f"Internal Server Error: {request.url}")
        logger.error(traceback.format_exc())
        
        return jsonify(response), 500

    @app.errorhandler(502)
    def handle_bad_gateway(error):
        """Handle bad gateway errors."""
        response = {
            'error': 'Bad gateway. Service temporarily unavailable.',
            'error_code': 'BAD_GATEWAY',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f"Bad Gateway: {request.url}")
        return jsonify(response), 502

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle service unavailable errors."""
        response = {
            'error': 'Service temporarily unavailable. Please try again later.',
            'error_code': 'SERVICE_UNAVAILABLE',
            'timestamp': datetime.now().isoformat(),
            'retry_after': 30  # Suggest retry after 30 seconds
        }
        
        logger.error(f"Service Unavailable: {request.url}")
        return jsonify(response), 503

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle any other HTTP exceptions."""
        response = {
            'error': error.description or 'An error occurred.',
            'error_code': 'HTTP_ERROR',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f"HTTP Exception: {error.code} - {request.url}")
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors."""
        response = {
            'error': 'An unexpected error occurred. Please try again later.',
            'error_code': 'UNEXPECTED_ERROR',
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the full traceback for debugging
        logger.error(f"Unexpected Error: {request.url}")
        logger.error(f"Error type: {type(error).__name__}")
        logger.error(f"Error message: {str(error)}")
        logger.error(traceback.format_exc())
        
        return jsonify(response), 500

def validate_json_request(required_fields=None):
    """Decorator to validate JSON requests."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Check if request has JSON content type
            if not request.is_json:
                raise APIError(
                    'Content-Type must be application/json',
                    status_code=415,
                    error_code='INVALID_CONTENT_TYPE'
                )
            
            # Check if request has valid JSON
            try:
                data = request.get_json()
            except Exception as e:
                raise APIError(
                    'Invalid JSON format',
                    status_code=400,
                    error_code='INVALID_JSON'
                )
            
            if data is None:
                raise APIError(
                    'Request body must contain valid JSON',
                    status_code=400,
                    error_code='EMPTY_JSON'
                )
            
            # Check required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    raise APIError(
                        f'Missing required fields: {", ".join(missing_fields)}',
                        status_code=400,
                        error_code='MISSING_FIELDS',
                        details={'missing_fields': missing_fields}
                    )
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def validate_participant_name(name):
    """Validate participant name."""
    if not isinstance(name, str):
        raise APIError(
            'Name must be a string',
            status_code=400,
            error_code='INVALID_NAME_TYPE'
        )
    
    name = name.strip()
    if not name:
        raise APIError(
            'Name cannot be empty',
            status_code=400,
            error_code='EMPTY_NAME'
        )
    
    if len(name) < 2:
        raise APIError(
            'Name must be at least 2 characters long',
            status_code=400,
            error_code='NAME_TOO_SHORT'
        )
    
    if len(name) > 50:
        raise APIError(
            'Name must not exceed 50 characters',
            status_code=400,
            error_code='NAME_TOO_LONG'
        )
    
    return name

def validate_gift_name(name):
    """Validate gift name."""
    if not isinstance(name, str):
        raise APIError(
            'Gift name must be a string',
            status_code=400,
            error_code='INVALID_GIFT_NAME_TYPE'
        )
    
    name = name.strip()
    if not name:
        raise APIError(
            'Gift name cannot be empty',
            status_code=400,
            error_code='EMPTY_GIFT_NAME'
        )
    
    if len(name) > 100:
        raise APIError(
            'Gift name must not exceed 100 characters',
            status_code=400,
            error_code='GIFT_NAME_TOO_LONG'
        )
    
    return name

def validate_participant_id(participant_id):
    """Validate participant ID."""
    if not isinstance(participant_id, int):
        raise APIError(
            'Participant ID must be an integer',
            status_code=400,
            error_code='INVALID_PARTICIPANT_ID_TYPE'
        )
    
    if participant_id < 1 or participant_id > 100:
        raise APIError(
            'Participant ID must be between 1 and 100',
            status_code=400,
            error_code='INVALID_PARTICIPANT_ID_RANGE'
        )
    
    return participant_id