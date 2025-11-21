"""
File-based database operations for the Secret Santa game.
Handles JSON serialization and concurrent access safety.
"""
import json
import os
import fcntl
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from models import Participant, Gift, GameState


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class ConcurrentAccessError(Exception):
    """Exception raised when concurrent access conflicts occur."""
    pass


class FileDatabase:
    """File-based database with JSON serialization and file locking."""
    
    def __init__(self, data_file: str = 'game_data.json', max_retries: int = 5, retry_delay: float = 0.1):
        """
        Initialize the file database.
        
        Args:
            data_file: Path to the JSON data file
            max_retries: Maximum number of retry attempts for operations
            retry_delay: Delay between retry attempts in seconds
        """
        self.data_file = data_file
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._ensure_data_file_exists()
    
    def _ensure_data_file_exists(self) -> None:
        """Create the data file with initial structure if it doesn't exist."""
        if not os.path.exists(self.data_file) or os.path.getsize(self.data_file) == 0:
            initial_data = {
                "participants": [],
                "gifts": [],
                "game_state": {
                    "current_turn": None,
                    "turn_order": [],
                    "game_phase": "registration"
                },
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            # Write directly without using the file lock context manager to avoid recursion
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    @contextmanager
    def _file_lock(self, mode: str = 'r', lock_type: int = fcntl.LOCK_SH):
        """
        Context manager for file locking.
        
        Args:
            mode: File open mode ('r' for read, 'w' for write)
            lock_type: Type of lock (LOCK_SH for shared, LOCK_EX for exclusive)
        """
        file_handle = None
        try:
            file_handle = open(self.data_file, mode)
            fcntl.flock(file_handle.fileno(), lock_type)
            yield file_handle
        finally:
            if file_handle:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                file_handle.close()
    
    def _read_data_from_file(self) -> Dict[str, Any]:
        """Read data from file with shared lock."""
        with self._file_lock('r', fcntl.LOCK_SH) as f:
            return json.load(f)
    
    def _write_data_to_file(self, data: Dict[str, Any]) -> None:
        """Write data to file with exclusive lock."""
        data['metadata']['last_updated'] = datetime.now().isoformat()
        with self._file_lock('w', fcntl.LOCK_EX) as f:
            json.dump(data, f, indent=2)
    
    def _retry_operation(self, operation, *args, **kwargs):
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Function to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            ConcurrentAccessError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (OSError, IOError, json.JSONDecodeError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                continue
        
        raise ConcurrentAccessError(f"Operation failed after {self.max_retries} attempts: {last_exception}")
    
    def read_all_data(self) -> Tuple[List[Participant], List[Gift], GameState]:
        """
        Read all data from the database.
        
        Returns:
            Tuple of (participants, gifts, game_state)
        """
        def _read():
            data = self._read_data_from_file()
            
            participants = [Participant.from_dict(p) for p in data.get("participants", [])]
            gifts = [Gift.from_dict(g) for g in data.get("gifts", [])]
            game_state = GameState.from_dict(data.get("game_state", {}))
            
            return participants, gifts, game_state
        
        return self._retry_operation(_read)
    
    def write_all_data(self, participants: List[Participant], gifts: List[Gift], game_state: GameState) -> None:
        """
        Write all data to the database.
        
        Args:
            participants: List of participants
            gifts: List of gifts
            game_state: Current game state
        """
        def _write():
            data = {
                "participants": [p.to_dict() for p in participants],
                "gifts": [g.to_dict() for g in gifts],
                "game_state": game_state.to_dict(),
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            self._write_data_to_file(data)
        
        self._retry_operation(_write)
    
    def add_participant_atomic(self, name: str) -> Participant:
        """
        Atomically add a participant with unique number assignment.
        
        Args:
            name: Participant's name
            
        Returns:
            Created participant
            
        Raises:
            DatabaseError: If participant limit reached or name is invalid
        """
        def _add_participant():
            # Use exclusive lock for the entire operation to ensure atomicity
            with self._file_lock('r+', fcntl.LOCK_EX) as f:
                # Read current data
                f.seek(0)
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    # File is corrupted, reinitialize
                    data = {
                        "participants": [],
                        "gifts": [],
                        "game_state": {
                            "current_turn": None,
                            "turn_order": [],
                            "game_phase": "registration"
                        },
                        "metadata": {
                            "last_updated": datetime.now().isoformat(),
                            "version": "1.0"
                        }
                    }
                
                participants = [Participant.from_dict(p) for p in data.get("participants", [])]
                gifts = [Gift.from_dict(g) for g in data.get("gifts", [])]
                game_state = GameState.from_dict(data.get("game_state", {}))
                
                # Validate name
                if not name or not name.strip():
                    raise DatabaseError("Participant name cannot be empty")
                
                # Check participant limit
                if len(participants) >= 100:
                    raise DatabaseError("Maximum number of participants (100) reached")
                
                # Generate random available number
                import random
                used_numbers = {p.id for p in participants}
                available_numbers = [i for i in range(1, 101) if i not in used_numbers]
                
                if not available_numbers:
                    raise DatabaseError("No available participant numbers")
                
                next_number = random.choice(available_numbers)
                
                # Create new participant
                new_participant = Participant(next_number, name.strip())
                participants.append(new_participant)
                
                # Write back to file atomically
                new_data = {
                    "participants": [p.to_dict() for p in participants],
                    "gifts": [g.to_dict() for g in gifts],
                    "game_state": game_state.to_dict(),
                    "metadata": {
                        "last_updated": datetime.now().isoformat(),
                        "version": "1.0"
                    }
                }
                
                f.seek(0)
                f.truncate()
                json.dump(new_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                
                return new_participant
        
        return self._retry_operation(_add_participant)
    
    def get_participants(self) -> List[Participant]:
        """Get all participants."""
        participants, _, _ = self.read_all_data()
        return participants
    
    def get_participant_count(self) -> int:
        """Get the current number of participants."""
        participants = self.get_participants()
        return len(participants)
    
    def add_gift(self, name: str, owner_id: Optional[int] = None) -> Gift:
        """
        Add a new gift to the database.
        
        Args:
            name: Gift name
            owner_id: Optional initial owner ID
            
        Returns:
            Created gift
        """
        def _add_gift():
            participants, gifts, game_state = self.read_all_data()
            
            # Validate gift name
            if not name or not name.strip():
                raise DatabaseError("Gift name cannot be empty")
            
            # Generate unique gift ID
            gift_id = str(uuid.uuid4())
            
            # Create new gift
            new_gift = Gift(gift_id, name.strip(), owner_id)
            gifts.append(new_gift)
            
            # Write back to file
            self.write_all_data(participants, gifts, game_state)
            
            return new_gift
        
        return self._retry_operation(_add_gift)
    
    def steal_gift_atomic(self, gift_id: str, new_owner_id: int) -> bool:
        """
        Atomically steal a gift.
        
        Args:
            gift_id: ID of gift to steal
            new_owner_id: ID of participant stealing the gift
            
        Returns:
            True if steal was successful, False if gift is locked
            
        Raises:
            DatabaseError: If gift not found
        """
        def _steal_gift():
            participants, gifts, game_state = self.read_all_data()
            
            # Find the gift
            gift = None
            for g in gifts:
                if g.id == gift_id:
                    gift = g
                    break
            
            if gift is None:
                raise DatabaseError(f"Gift with ID {gift_id} not found")
            
            # Attempt to steal
            success = gift.steal_gift(new_owner_id)
            
            if success:
                # Write back to file
                self.write_all_data(participants, gifts, game_state)
            
            return success
        
        return self._retry_operation(_steal_gift)
    
    def get_gifts(self) -> List[Gift]:
        """Get all gifts."""
        _, gifts, _ = self.read_all_data()
        return gifts
    
    def reset_gift_steals_atomic(self, gift_id: str) -> bool:
        """
        Atomically reset a gift's steal count to 0 (admin override).
        This also unlocks the gift.
        
        Args:
            gift_id: ID of the gift to reset
            
        Returns:
            True if gift was reset, False if gift not found
            
        Raises:
            DatabaseError: If gift not found
        """
        def _reset_gift():
            participants, gifts, game_state = self.read_all_data()
            
            # Find the gift
            target_gift = None
            for gift in gifts:
                if gift.id == gift_id:
                    target_gift = gift
                    break
            
            if not target_gift:
                raise DatabaseError(f"Gift with ID '{gift_id}' not found")
            
            # Reset steal count and unlock
            was_reset = target_gift.reset_steal_count()
            
            # Write back to database
            self.write_all_data(participants, gifts, game_state)
            
            return was_reset
        
        return self._retry_operation(_reset_gift)
    
    def update_gift_name_atomic(self, gift_id: str, new_name: str) -> Gift:
        """
        Atomically update a gift's name while preserving all other properties.
        
        Args:
            gift_id: ID of the gift to update
            new_name: New name for the gift
            
        Returns:
            Updated gift object
            
        Raises:
            DatabaseError: If gift not found or name is invalid
        """
        def _update_gift_name():
            participants, gifts, game_state = self.read_all_data()
            
            # Validate gift name
            if not new_name or not new_name.strip():
                raise DatabaseError("Gift name cannot be empty")
            
            # Find the gift
            target_gift = None
            for gift in gifts:
                if gift.id == gift_id:
                    target_gift = gift
                    break
            
            if not target_gift:
                raise DatabaseError(f"Gift with ID '{gift_id}' not found")
            
            # Update the gift name (preserves all other properties)
            target_gift.name = new_name.strip()
            
            # Write back to database
            self.write_all_data(participants, gifts, game_state)
            
            return target_gift
        
        return self._retry_operation(_update_gift_name)
    
    def get_game_state(self) -> GameState:
        """Get current game state."""
        _, _, game_state = self.read_all_data()
        return game_state
    
    def update_game_state(self, game_state: GameState) -> None:
        """
        Update the game state.
        
        Args:
            game_state: New game state
        """
        def _update_game_state():
            participants, gifts, _ = self.read_all_data()
            self.write_all_data(participants, gifts, game_state)
        
        return self._retry_operation(_update_game_state)
    
    def reset_database(self) -> None:
        """
        Nuclear reset - Delete all data and reset to initial state.
        This is a destructive operation that cannot be undone.
        """
        initial_data = {
            "participants": [],
            "gifts": [],
            "game_state": {
                "current_turn": None,
                "turn_order": [],
                "game_phase": "registration"
            },
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        self._write_data_to_file(initial_data)
