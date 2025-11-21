import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Participant, Gift
from error_handlers import (
    register_error_handlers, 
    validate_json_request, 
    validate_participant_name,
    validate_gift_name,
    validate_participant_id,
    APIError
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database based on environment
if os.environ.get('USE_S3_DATABASE') == 'true':
    from s3_database import S3Database, DatabaseError, ConcurrentAccessError
    db = S3Database()
else:
    from database import FileDatabase, DatabaseError, ConcurrentAccessError
    db = FileDatabase()

# Register error handlers
register_error_handlers(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/participants', methods=['POST'])
@validate_json_request(required_fields=['name'])
def register_participant():
    """
    Register a new participant with unique number assignment.
    
    Expected JSON payload:
    {
        "name": "participant_name"
    }
    
    Returns:
    {
        "id": participant_number,
        "name": "participant_name", 
        "registration_timestamp": "ISO_datetime"
    }
    """
    data = request.get_json()
    
    # Validate and clean name
    name = validate_participant_name(data['name'])
    
    # Register participant using atomic operation
    participant = db.add_participant_atomic(name)
    
    return jsonify(participant.to_dict()), 201


@app.route('/api/participants', methods=['GET'])
def get_participants():
    """
    Get all registered participants.
    
    Returns:
    {
        "participants": [
            {
                "id": participant_number,
                "name": "participant_name",
                "registration_timestamp": "ISO_datetime"
            }
        ]
    }
    """
    participants = db.get_participants()
    
    # Sort participants by ID for consistent ordering
    participants.sort(key=lambda p: p.id)
    
    return jsonify({
        "participants": [p.to_dict() for p in participants]
    }), 200


@app.route('/api/participants/count', methods=['GET'])
def get_participant_count():
    """
    Get the current number of registered participants.
    
    Returns:
    {
        "count": number_of_participants,
        "max_participants": 100
    }
    """
    count = db.get_participant_count()
    
    return jsonify({
        "count": count,
        "max_participants": 100
    }), 200


@app.route('/api/gifts', methods=['POST'])
@validate_json_request(required_fields=['name'])
def add_gift():
    """
    Add a new gift to the pool.
    
    Expected JSON payload:
    {
        "name": "gift_name",
        "owner_id": optional_participant_id
    }
    
    Returns:
    {
        "id": "gift_id",
        "name": "gift_name",
        "steal_count": 0,
        "is_locked": false,
        "current_owner": owner_id_or_null,
        "steal_history": []
    }
    """
    data = request.get_json()
    
    # Validate and clean gift name
    name = validate_gift_name(data['name'])
    
    # Validate owner_id if provided
    owner_id = data.get('owner_id')
    if owner_id is not None:
        owner_id = validate_participant_id(owner_id)
    
    # Add gift using database operation
    gift = db.add_gift(name, owner_id)
    
    return jsonify(gift.to_dict()), 201


@app.route('/api/gifts', methods=['GET'])
def get_gifts():
    """
    Get all gifts with steal status information.
    
    Returns:
    {
        "gifts": [
            {
                "id": "gift_id",
                "name": "gift_name",
                "steal_count": number_of_steals,
                "is_locked": boolean,
                "current_owner": owner_id_or_null,
                "steal_history": [previous_owner_ids]
            }
        ]
    }
    """
    gifts = db.get_gifts()
    
    return jsonify({
        "gifts": [g.to_dict() for g in gifts]
    }), 200


@app.route('/api/gifts/<gift_id>/steal', methods=['PUT'])
@validate_json_request(required_fields=['new_owner_id'])
def steal_gift(gift_id):
    """
    Record a gift steal.
    
    Expected JSON payload:
    {
        "new_owner_id": participant_id
    }
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "gift": {
            "id": "gift_id",
            "name": "gift_name", 
            "steal_count": updated_count,
            "is_locked": boolean,
            "current_owner": new_owner_id,
            "steal_history": [previous_owner_ids]
        }
    }
    """
    data = request.get_json()
    
    # Validate gift_id
    if not gift_id or not isinstance(gift_id, str):
        raise APIError(
            'Invalid gift ID',
            status_code=400,
            error_code='INVALID_GIFT_ID'
        )
    
    # Validate new_owner_id
    new_owner_id = validate_participant_id(data['new_owner_id'])
    
    # Attempt to steal the gift
    success = db.steal_gift_atomic(gift_id, new_owner_id)
    
    # Get updated gift information
    gifts = db.get_gifts()
    updated_gift = None
    for g in gifts:
        if g.id == gift_id:
            updated_gift = g
            break
    
    if not updated_gift:
        raise APIError(
            'Gift not found',
            status_code=404,
            error_code='GIFT_NOT_FOUND'
        )
    
    if success:
        message = "Gift stolen successfully"
        if updated_gift.is_locked:
            message += " - Gift is now locked after 3 steals"
    else:
        message = "Gift cannot be stolen - it is locked"
    
    return jsonify({
        "success": success,
        "message": message,
        "gift": updated_gift.to_dict()
    }), 200


@app.route('/api/gifts/<gift_id>/name', methods=['PUT'])
@validate_json_request(required_fields=['name'])
def update_gift_name(gift_id):
    """
    Update a gift's name.
    
    Expected JSON payload:
    {
        "name": "new_gift_name"
    }
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "gift": {
            "id": "gift_id",
            "name": "updated_gift_name",
            "steal_count": number,
            "is_locked": boolean,
            "current_owner": owner_id_or_null,
            "steal_history": [previous_owner_ids]
        }
    }
    """
    data = request.get_json()
    
    # Validate gift_id
    if not gift_id or not isinstance(gift_id, str):
        raise APIError(
            'Invalid gift ID',
            status_code=400,
            error_code='INVALID_GIFT_ID'
        )
    
    # Validate and clean gift name
    new_name = validate_gift_name(data['name'])
    
    # Update the gift name atomically
    updated_gift = db.update_gift_name_atomic(gift_id, new_name)
    
    return jsonify({
        "success": True,
        "message": "Gift name updated successfully",
        "gift": updated_gift.to_dict()
    }), 200


@app.route('/api/game/current-turn', methods=['GET'])
def get_current_turn():
    """
    Get the current turn information.
    
    Returns:
    {
        "current_turn": participant_id_or_null,
        "current_participant": {
            "id": participant_id,
            "name": "participant_name"
        } or null,
        "game_phase": "registration|active|completed",
        "turn_order": [participant_ids],
        "total_participants": number
    }
    """
    participants, _, game_state = db.read_all_data()
    
    # Find current participant details
    current_participant = None
    if game_state.current_turn is not None:
        for p in participants:
            if p.id == game_state.current_turn:
                current_participant = p.to_dict()
                break
    
    # If game hasn't started but we have participants, set up turn order
    if game_state.game_phase == "registration" and participants and not game_state.turn_order:
        # Sort participants by ID for consistent turn order
        participant_ids = sorted([p.id for p in participants])
        game_state.set_turn_order(participant_ids)
        db.update_game_state(game_state)
        
        # Update current participant after setting turn order
        if game_state.current_turn is not None:
            for p in participants:
                if p.id == game_state.current_turn:
                    current_participant = p.to_dict()
                    break
    
    return jsonify({
        "current_turn": game_state.current_turn,
        "current_participant": current_participant,
        "game_phase": game_state.game_phase,
        "turn_order": game_state.turn_order,
        "total_participants": len(participants)
    }), 200


@app.route('/api/game/start', methods=['PUT'])
def start_game():
    """
    Start the game and set the first player's turn.
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "current_turn": participant_id,
        "current_participant": {
            "id": participant_id,
            "name": "participant_name"
        },
        "game_phase": "active"
    }
    """
    participants, gifts, game_state = db.read_all_data()
    
    # If no participants, can't start game
    if not participants:
        raise APIError(
            'No participants registered',
            status_code=400,
            error_code='NO_PARTICIPANTS'
        )
    
    # Can only start if in registration phase
    if game_state.game_phase != "registration":
        raise APIError(
            'Game has already started',
            status_code=400,
            error_code='GAME_ALREADY_STARTED'
        )
    
    # Set up turn order if not already set
    if not game_state.turn_order:
        participant_ids = sorted([p.id for p in participants])
        game_state.set_turn_order(participant_ids)
    
    # Start the game (sets phase to active and current_turn to first participant)
    game_state.start_game()
    
    # Find current participant details
    current_participant = None
    if game_state.current_turn is not None:
        for p in participants:
            if p.id == game_state.current_turn:
                current_participant = p.to_dict()
                break
    
    # Update database
    db.update_game_state(game_state)
    
    return jsonify({
        "success": True,
        "message": f"Game started! It's {current_participant['name']}'s turn.",
        "current_turn": game_state.current_turn,
        "current_participant": current_participant,
        "game_phase": game_state.game_phase
    }), 200


@app.route('/api/game/next-turn', methods=['PUT'])
def advance_turn():
    """
    Advance to the next turn.
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "current_turn": participant_id_or_null,
        "current_participant": {
            "id": participant_id,
            "name": "participant_name"
        } or null,
        "game_phase": "registration|active|completed"
    }
    """
    participants, gifts, game_state = db.read_all_data()
    
    # If no participants, can't advance turn
    if not participants:
        raise APIError(
            'No participants registered',
            status_code=400,
            error_code='NO_PARTICIPANTS'
        )
    
    # Game must be started (active phase) to advance turns
    if game_state.game_phase == "registration":
        raise APIError(
            'Game has not started yet. Please start the game first.',
            status_code=400,
            error_code='GAME_NOT_STARTED'
        )
    
    # Advance to next turn
    next_turn_id = game_state.next_turn()
    
    # Find current participant details
    current_participant = None
    if game_state.current_turn is not None:
        for p in participants:
            if p.id == game_state.current_turn:
                current_participant = p.to_dict()
                break
    
    # Update database
    db.update_game_state(game_state)
    
    # Determine success message
    if game_state.game_phase == "completed":
        message = "Game completed - all participants have had their turn"
    elif next_turn_id is not None:
        message = f"Advanced to next turn"
    else:
        message = "Game completed"
    
    return jsonify({
        "success": True,
        "message": message,
        "current_turn": game_state.current_turn,
        "current_participant": current_participant,
        "game_phase": game_state.game_phase
    }), 200


@app.route('/api/gifts/<gift_id>/reset-steals', methods=['PUT'])
def reset_gift_steals(gift_id):
    """
    Reset a gift's steal count to 0 (admin override).
    This also unlocks the gift.
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "gift": {
            "id": "gift_id",
            "name": "gift_name",
            "steal_count": 0,
            "is_locked": false,
            "current_owner": owner_id_or_null,
            "steal_history": [previous_owner_ids]
        }
    }
    """
    # Validate gift_id
    if not gift_id or not isinstance(gift_id, str):
        raise APIError(
            'Invalid gift ID',
            status_code=400,
            error_code='INVALID_GIFT_ID'
        )
    
    # Reset the gift's steal count
    was_reset = db.reset_gift_steals_atomic(gift_id)
    
    # Get updated gift information
    gifts = db.get_gifts()
    updated_gift = None
    for g in gifts:
        if g.id == gift_id:
            updated_gift = g
            break
    
    if not updated_gift:
        raise APIError(
            'Gift not found',
            status_code=404,
            error_code='GIFT_NOT_FOUND'
        )
    
    if was_reset:
        message = "Gift steal count reset to 0 and unlocked - can be stolen again!"
    else:
        message = "Gift already has 0 steals and is unlocked"
    
    return jsonify({
        "success": True,
        "message": message,
        "gift": updated_gift.to_dict()
    }), 200


@app.route('/api/game/previous-turn', methods=['PUT'])
def go_back_turn():
    """
    Go back to the previous turn.
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "current_turn": participant_id_or_null,
        "current_participant": {
            "id": participant_id,
            "name": "participant_name"
        } or null,
        "game_phase": "registration|active|completed"
    }
    """
    participants, gifts, game_state = db.read_all_data()
    
    # If no participants, can't go back
    if not participants:
        raise APIError(
            'No participants registered',
            status_code=400,
            error_code='NO_PARTICIPANTS'
        )
    
    # If turn order not set, can't go back
    if not game_state.turn_order:
        raise APIError(
            'Game has not started yet',
            status_code=400,
            error_code='GAME_NOT_STARTED'
        )
    
    # Go back to previous turn
    previous_turn_id = game_state.previous_turn()
    
    # Find current participant details
    current_participant = None
    if game_state.current_turn is not None:
        for p in participants:
            if p.id == game_state.current_turn:
                current_participant = p.to_dict()
                break
    
    # Update database
    db.update_game_state(game_state)
    
    # Determine success message
    if previous_turn_id is None:
        message = "Already at the first turn - cannot go back further"
        success = False
    else:
        message = f"Went back to previous turn"
        success = True
    
    return jsonify({
        "success": success,
        "message": message,
        "current_turn": game_state.current_turn,
        "current_participant": current_participant,
        "game_phase": game_state.game_phase
    }), 200


@app.route('/api/nuclear/reset', methods=['POST'])
def nuclear_reset():
    """
    Nuclear reset - Delete ALL data including participants, gifts, and game state.
    This is a destructive operation that cannot be undone.
    
    Returns:
    {
        "success": boolean,
        "message": "description",
        "deleted": {
            "participants": number,
            "gifts": number
        }
    }
    """
    # Get current counts before deletion
    participants, gifts, game_state = db.read_all_data()
    participant_count = len(participants)
    gift_count = len(gifts)
    
    # Reset the database completely
    db.reset_database()
    
    return jsonify({
        "success": True,
        "message": "All data has been permanently deleted",
        "deleted": {
            "participants": participant_count,
            "gifts": gift_count
        }
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)