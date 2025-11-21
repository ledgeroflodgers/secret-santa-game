"""
AWS Lambda handler for Secret Santa backend.
This module adapts the Flask application to work with AWS Lambda and API Gateway.
"""
import json
import os

# Set environment to use S3 database
os.environ['USE_S3_DATABASE'] = 'true'

from app import app

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: API Gateway event object
        context: Lambda context object
        
    Returns:
        API Gateway response object
    """
    # Extract HTTP method and path
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Handle OPTIONS requests for CORS preflight
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': ''
        }
    
    # Extract headers
    headers = event.get('headers', {})
    
    # Extract query parameters
    query_params = event.get('queryStringParameters') or {}
    
    # Extract body
    body = event.get('body', '')
    if body and event.get('isBase64Encoded', False):
        import base64
        body = base64.b64decode(body).decode('utf-8')
    
    # CORS headers to include in all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    # Create a test request context for Flask
    with app.test_request_context(
        path=path,
        method=http_method,
        headers=headers,
        query_string=query_params,
        data=body,
        content_type=headers.get('Content-Type', 'application/json')
    ):
        try:
            # Process the request through Flask
            response = app.full_dispatch_request()
            
            # Extract response data
            response_data = response.get_data(as_text=True)
            status_code = response.status_code
            
            # Return API Gateway compatible response with CORS headers
            return {
                'statusCode': status_code,
                'headers': cors_headers,
                'body': response_data
            }
        except Exception as e:
            # Handle errors with CORS headers
            error_response = {
                'error': str(e),
                'message': 'Internal server error'
            }
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps(error_response)
            }
