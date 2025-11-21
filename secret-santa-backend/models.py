"""
Data models for the Secret Santa game application.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


class Participant:
    """Model representing a game participant."""
    
    def __init__(self, participant_id: int, name: str, registration_timestamp: Optional[str] = None):
        """
        Initialize a participant.
        
        Args:
            participant_id: Unique number between 1 and 100
            name: Participant's name
            registration_timestamp: ISO datetime string, defaults to current time
        """
        self.id = participant_id
        self.name = name
        self.registration_timestamp = registration_timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert participant to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "registration_timestamp": self.registration_timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Participant':
        """Create participant from dictionary."""
        return cls(
            participant_id=data["id"],
            name=data["name"],
            registration_timestamp=data["registration_timestamp"]
        )
    
    def __repr__(self) -> str:
        return f"Participant(id={self.id}, name='{self.name}')"


class Gift:
    """Model representing a gift in the game."""
    
    def __init__(self, gift_id: str, name: str, current_owner: Optional[int] = None):
        """
        Initialize a gift.
        
        Args:
            gift_id: Unique identifier for the gift
            name: Name/description of the gift
            current_owner: ID of participant who currently owns the gift
        """
        self.id = gift_id
        self.name = name
        self.steal_count = 0
        self.is_locked = False
        self.current_owner = current_owner
        self.steal_history: List[int] = []
    
    def steal_gift(self, new_owner_id: int) -> bool:
        """
        Record a gift steal.
        
        Args:
            new_owner_id: ID of participant stealing the gift
            
        Returns:
            True if steal was successful, False if gift is locked
        """
        if self.is_locked:
            return False
        
        if self.current_owner is not None:
            self.steal_history.append(self.current_owner)
        
        self.current_owner = new_owner_id
        self.steal_count += 1
        
        # Lock gift after 3 steals
        if self.steal_count >= 3:
            self.is_locked = True
        
        return True
    
    def reset_steal_count(self) -> bool:
        """
        Reset the steal count to 0 (admin override).
        This also unlocks the gift if it was locked.
        
        Returns:
            True if the gift was reset, False if it was already at 0 steals
        """
        if self.steal_count == 0 and not self.is_locked:
            return False
        
        self.steal_count = 0
        self.is_locked = False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gift to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "steal_count": self.steal_count,
            "is_locked": self.is_locked,
            "current_owner": self.current_owner,
            "steal_history": self.steal_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gift':
        """Create gift from dictionary."""
        gift = cls(
            gift_id=data["id"],
            name=data["name"],
            current_owner=data.get("current_owner")
        )
        gift.steal_count = data.get("steal_count", 0)
        gift.is_locked = data.get("is_locked", False)
        gift.steal_history = data.get("steal_history", [])
        return gift
    
    def __repr__(self) -> str:
        return f"Gift(id='{self.id}', name='{self.name}', steals={self.steal_count}, locked={self.is_locked})"


class GameState:
    """Model representing the overall game state."""
    
    def __init__(self):
        """Initialize game state."""
        self.current_turn: Optional[int] = None
        self.turn_order: List[int] = []
        self.game_phase = "registration"  # registration, active, completed
    
    def set_turn_order(self, participant_ids: List[int]) -> None:
        """Set the turn order for the game."""
        self.turn_order = participant_ids.copy()
        if self.turn_order and self.current_turn is None:
            self.current_turn = self.turn_order[0]
    
    def next_turn(self) -> Optional[int]:
        """
        Advance to the next turn.
        
        Returns:
            ID of next participant, or None if game is complete
        """
        if not self.turn_order or self.current_turn is None:
            return None
        
        try:
            current_index = self.turn_order.index(self.current_turn)
            next_index = current_index + 1
            
            if next_index >= len(self.turn_order):
                # Game complete
                self.game_phase = "completed"
                self.current_turn = None
                return None
            else:
                self.current_turn = self.turn_order[next_index]
                return self.current_turn
        except ValueError:
            # Current turn not in turn order, reset to first
            self.current_turn = self.turn_order[0] if self.turn_order else None
            return self.current_turn
    
    def previous_turn(self) -> Optional[int]:
        """
        Go back to the previous turn.
        
        Returns:
            ID of previous participant, or None if already at first turn
        """
        if not self.turn_order:
            return None
        
        # If game is completed, go back to last participant
        if self.game_phase == "completed":
            self.game_phase = "active"
            self.current_turn = self.turn_order[-1] if self.turn_order else None
            return self.current_turn
        
        if self.current_turn is None:
            return None
        
        try:
            current_index = self.turn_order.index(self.current_turn)
            
            if current_index == 0:
                # Already at first turn, can't go back further
                return None
            else:
                previous_index = current_index - 1
                self.current_turn = self.turn_order[previous_index]
                # Ensure game is in active state if we're going back
                if self.game_phase == "completed":
                    self.game_phase = "active"
                return self.current_turn
        except ValueError:
            # Current turn not in turn order, reset to first
            self.current_turn = self.turn_order[0] if self.turn_order else None
            return self.current_turn
    
    def start_game(self) -> None:
        """Start the active game phase."""
        self.game_phase = "active"
        if self.turn_order and self.current_turn is None:
            self.current_turn = self.turn_order[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for JSON serialization."""
        return {
            "current_turn": self.current_turn,
            "turn_order": self.turn_order,
            "game_phase": self.game_phase
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create game state from dictionary."""
        game_state = cls()
        game_state.current_turn = data.get("current_turn")
        game_state.turn_order = data.get("turn_order", [])
        game_state.game_phase = data.get("game_phase", "registration")
        return game_state
    
    def __repr__(self) -> str:
        return f"GameState(phase='{self.game_phase}', current_turn={self.current_turn}, participants={len(self.turn_order)})"