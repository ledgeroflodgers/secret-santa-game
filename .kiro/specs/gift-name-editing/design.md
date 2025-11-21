# Design Document: Gift Name Editing

## Overview

This feature adds inline editing capability for gift names in the admin interface's Gifts Pool section. The design follows a simple edit-in-place pattern where clicking an edit button transforms the gift name into an editable input field with save/cancel actions. The implementation preserves all gift metadata (steal count, locked status, owner, steal history) while updating only the name field.

## Architecture

### Component Architecture

The feature will be implemented entirely within the existing Angular admin component and Python Flask backend:

**Frontend (Angular)**
- `AdminComponent` - Enhanced with edit mode state management and UI controls
- `GiftService` - Extended with new `updateGiftName()` method
- Template updates to `admin.component.html` for inline editing UI

**Backend (Python Flask)**
- New API endpoint: `PUT /api/gifts/<gift_id>/name`
- Database layer updates in `FileDatabase` and `S3Database` classes
- `Gift` model already supports name updates (no changes needed)

### Data Flow

```
User clicks edit → Component enters edit mode → User modifies name → 
User clicks save → Service calls API → Backend validates → 
Database updates gift → Response returns → UI updates → 
Real-time sync notifies other clients
```

## Components and Interfaces

### Frontend Components

#### AdminComponent Enhancements

**New State Properties:**
```typescript
editingGiftId: string | null = null;  // Track which gift is being edited
editGiftName: string = '';             // Store temporary edit value
editGiftError: string | null = null;   // Store validation errors
```

**New Methods:**
```typescript
// Enter edit mode for a gift
startEditGift(gift: Gift): void

// Cancel editing and revert changes
cancelEditGift(): void

// Save edited gift name
saveEditGift(giftId: string): void

// Check if a specific gift is in edit mode
isEditingGift(giftId: string): boolean

// Validate gift name before saving
validateGiftName(name: string): boolean
```

#### GiftService Extension

**New Interface:**
```typescript
export interface UpdateGiftNameRequest {
  name: string;
}

export interface UpdateGiftNameResponse {
  success: boolean;
  message: string;
  gift: Gift;
}
```

**New Method:**
```typescript
updateGiftName(giftId: string, nameData: UpdateGiftNameRequest): Observable<UpdateGiftNameResponse>
```

### Backend Components

#### New API Endpoint

**Route:** `PUT /api/gifts/<gift_id>/name`

**Request Body:**
```json
{
  "name": "Updated Gift Name"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Gift name updated successfully",
  "gift": {
    "id": "gift-uuid",
    "name": "Updated Gift Name",
    "steal_count": 2,
    "is_locked": false,
    "current_owner": 5,
    "steal_history": [3, 7]
  }
}
```

**Response (Error - 400):**
```json
{
  "error": "Gift name cannot be empty",
  "error_code": "INVALID_GIFT_NAME"
}
```

**Response (Error - 404):**
```json
{
  "error": "Gift not found",
  "error_code": "GIFT_NOT_FOUND"
}
```

#### Database Layer Updates

**FileDatabase Class:**
```python
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
```

**S3Database Class:**
```python
def update_gift_name_atomic(self, gift_id: str, new_name: str) -> Gift:
    """
    Atomically update a gift's name in S3 while preserving all other properties.
    
    Args:
        gift_id: ID of the gift to update
        new_name: New name for the gift
        
    Returns:
        Updated gift object
        
    Raises:
        DatabaseError: If gift not found or name is invalid
    """
```

## Data Models

### Gift Model

The existing `Gift` model already supports name updates. No changes needed to the model structure:

```python
class Gift:
    def __init__(self, gift_id: str, name: str, current_owner: Optional[int] = None):
        self.id = gift_id
        self.name = name  # This field will be updated
        self.steal_count = 0
        self.is_locked = False
        self.current_owner = current_owner
        self.steal_history: List[int] = []
```

### State Management

**Edit Mode State (Frontend):**
- Only one gift can be in edit mode at a time
- Edit mode is component-local (not persisted)
- Canceling edit mode discards changes
- Saving edit mode validates and persists changes

## User Interface Design

### Edit Mode UI Flow

**Display Mode (Default):**
```
┌─────────────────────────────────────────────────┐
│ Gift Name                              [Edit] │
│ Owner: Player Name                              │
│ ★★☆ 2/3 steals - 1 more steal will lock       │
└─────────────────────────────────────────────────┘
```

**Edit Mode (Active):**
```
┌─────────────────────────────────────────────────┐
│ [Input: Gift Name____________] [Save] [Cancel] │
│ Owner: Player Name                              │
│ ★★☆ 2/3 steals - 1 more steal will lock       │
└─────────────────────────────────────────────────┘
```

**Edit Mode (Error):**
```
┌─────────────────────────────────────────────────┐
│ [Input: _______________] [Save] [Cancel]       │
│ ⚠ Gift name cannot be empty                    │
│ Owner: Player Name                              │
│ ★★☆ 2/3 steals - 1 more steal will lock       │
└─────────────────────────────────────────────────┘
```

### HTML Structure

```html
<div class="gift-item">
  <!-- Display Mode -->
  <div *ngIf="!isEditingGift(gift.id)" class="gift-info">
    <span class="gift-name">{{ gift.name }}</span>
    <button class="btn-edit" (click)="startEditGift(gift)">✏️ Edit</button>
  </div>
  
  <!-- Edit Mode -->
  <div *ngIf="isEditingGift(gift.id)" class="gift-edit">
    <input 
      type="text" 
      [(ngModel)]="editGiftName"
      class="gift-name-input"
      [class.error]="editGiftError"
      (keyup.enter)="saveEditGift(gift.id)"
      (keyup.escape)="cancelEditGift()"
      autofocus>
    <button class="btn-save" (click)="saveEditGift(gift.id)">💾 Save</button>
    <button class="btn-cancel" (click)="cancelEditGift()">✖ Cancel</button>
    <div *ngIf="editGiftError" class="edit-error">{{ editGiftError }}</div>
  </div>
  
  <!-- Rest of gift display (owner, steals, etc.) -->
</div>
```

### CSS Styling

```css
.gift-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gift-name-input {
  flex: 1;
  padding: 6px 10px;
  border: 2px solid #4CAF50;
  border-radius: 4px;
  font-size: 16px;
}

.gift-name-input.error {
  border-color: #f44336;
}

.btn-edit {
  padding: 4px 8px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-save {
  padding: 6px 12px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  padding: 6px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.edit-error {
  color: #f44336;
  font-size: 12px;
  margin-top: 4px;
}
```

## Error Handling

### Validation Rules

**Frontend Validation:**
1. Gift name cannot be empty
2. Gift name cannot be only whitespace
3. Gift name must be between 1-100 characters
4. Validate before sending to backend

**Backend Validation:**
1. Reuse existing `validate_gift_name()` function from `error_handlers.py`
2. Return 400 error for invalid names
3. Return 404 error if gift not found

### Error Scenarios

| Scenario | Frontend Behavior | Backend Response |
|----------|------------------|------------------|
| Empty name | Show inline error, prevent save | 400 - "Gift name cannot be empty" |
| Whitespace only | Show inline error, prevent save | 400 - "Gift name cannot be empty" |
| Gift not found | Show error message, exit edit mode | 404 - "Gift not found" |
| Network error | Show error message, stay in edit mode | Connection error |
| Concurrent update | Retry operation, show updated data | 503 - Retry with backoff |

### Error Recovery

1. **Validation errors:** User can correct input and retry
2. **Network errors:** User can retry save operation
3. **Gift not found:** Exit edit mode, refresh gift list
4. **Concurrent access:** Automatic retry with exponential backoff

## Testing Strategy

### Unit Tests

**Frontend (AdminComponent):**
- Test `startEditGift()` sets correct state
- Test `cancelEditGift()` clears edit state
- Test `saveEditGift()` validates before calling service
- Test `isEditingGift()` returns correct boolean
- Test validation logic for empty/whitespace names

**Frontend (GiftService):**
- Test `updateGiftName()` makes correct HTTP request
- Test error handling for various HTTP status codes
- Test timeout and retry behavior

**Backend (app.py):**
- Test endpoint validates gift name
- Test endpoint returns 404 for non-existent gift
- Test endpoint preserves gift metadata
- Test endpoint returns updated gift

**Backend (database.py):**
- Test `update_gift_name_atomic()` updates name correctly
- Test atomic operation with concurrent access
- Test error handling for invalid gift ID
- Test preservation of steal count, locked status, owner

### Integration Tests

1. **End-to-end edit flow:**
   - Add gift → Edit name → Save → Verify update
   
2. **Concurrent editing:**
   - Two admins edit same gift → Last write wins
   
3. **Edit with steal operations:**
   - Edit gift name → Steal gift → Verify name persists
   
4. **Edit locked gift:**
   - Lock gift → Edit name → Verify name updates
   
5. **Real-time sync:**
   - Edit gift on admin 1 → Verify update on admin 2

### Manual Testing Checklist

- [ ] Edit button appears for all gifts
- [ ] Clicking edit enters edit mode
- [ ] Only one gift can be edited at a time
- [ ] Input field is auto-focused
- [ ] Enter key saves changes
- [ ] Escape key cancels editing
- [ ] Save button updates gift name
- [ ] Cancel button reverts changes
- [ ] Empty name shows validation error
- [ ] Whitespace-only name shows validation error
- [ ] Long names (>100 chars) show validation error
- [ ] Edited name appears immediately after save
- [ ] Steal count preserved after edit
- [ ] Locked status preserved after edit
- [ ] Owner preserved after edit
- [ ] Mobile display updates with new name
- [ ] Multiple admins see updated name
- [ ] Network errors show appropriate message
- [ ] Edit works on mobile devices
- [ ] Touch targets are appropriately sized

## Security Considerations

1. **Authentication:** Edit functionality only available in authenticated admin interface
2. **Input validation:** Sanitize gift names on both frontend and backend
3. **SQL injection:** Not applicable (using JSON file/S3 storage)
4. **XSS prevention:** Angular automatically escapes HTML in templates
5. **CSRF protection:** Flask-CORS configured for API endpoints
6. **Rate limiting:** Consider adding rate limiting for update endpoint

## Performance Considerations

1. **Atomic operations:** Use file locking (FileDatabase) or S3 versioning for atomicity
2. **Optimistic updates:** Update UI immediately, rollback on error
3. **Debouncing:** Not needed for explicit save action
4. **Caching:** Refresh gift list after successful update
5. **Network efficiency:** Only send changed name, not entire gift object

## Mobile Responsiveness

1. **Touch targets:** Buttons minimum 44x44px for touch
2. **Input field:** Large enough for mobile keyboards
3. **Keyboard handling:** Ensure input field visible when keyboard appears
4. **Orientation:** Support both portrait and landscape
5. **Font sizes:** Minimum 16px to prevent zoom on iOS

## Real-Time Synchronization

The existing auto-refresh mechanism (10-second polling) will automatically sync edited gift names across all admin clients. No additional real-time infrastructure needed.

**Sync Flow:**
1. Admin A edits gift name
2. Backend updates database
3. Admin B's auto-refresh (within 10 seconds) fetches updated gift list
4. Admin B sees new gift name

For immediate sync, admins can use the manual "Refresh" button.

## Accessibility

1. **Keyboard navigation:** Tab through edit/save/cancel buttons
2. **Screen readers:** Add ARIA labels to buttons
3. **Focus management:** Auto-focus input when entering edit mode
4. **Error announcements:** Use ARIA live regions for validation errors
5. **Button labels:** Clear text labels (not just icons)

## Future Enhancements

1. **Undo/Redo:** Add ability to undo recent name changes
2. **Edit history:** Track who edited gift names and when
3. **Bulk editing:** Edit multiple gift names at once
4. **Auto-save:** Save changes automatically after typing stops
5. **Conflict resolution:** Better handling of concurrent edits
6. **Rich text:** Support formatting in gift names
7. **Character counter:** Show remaining characters (100 max)
8. **Duplicate detection:** Warn if gift name already exists
