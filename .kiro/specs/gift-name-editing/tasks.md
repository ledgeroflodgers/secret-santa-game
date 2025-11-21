# Implementation Plan: Gift Name Editing

- [x] 1. Implement backend API endpoint for gift name updates
  - Create new `PUT /api/gifts/<gift_id>/name` endpoint in `app.py`
  - Add request validation using existing `validate_gift_name()` function
  - Return updated gift object with success message
  - Handle 404 error for non-existent gifts
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.4, 4.5_

- [x] 2. Add atomic gift name update to database layer
  - Implement `update_gift_name_atomic()` method in `FileDatabase` class
  - Implement `update_gift_name_atomic()` method in `S3Database` class
  - Use file locking (FileDatabase) to ensure atomicity
  - Preserve all gift metadata (steal_count, is_locked, current_owner, steal_history)
  - Add error handling for gift not found
  - _Requirements: 1.4, 4.1, 4.2_

- [x] 3. Extend Angular GiftService with update method
  - Add `UpdateGiftNameRequest` interface to `gift.service.ts`
  - Add `UpdateGiftNameResponse` interface to `gift.service.ts`
  - Implement `updateGiftName()` method with HTTP PUT call
  - Add timeout and retry logic consistent with other methods
  - Add error handling for various HTTP status codes
  - _Requirements: 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Add edit mode state management to AdminComponent
  - Add `editingGiftId` property to track which gift is being edited
  - Add `editGiftName` property to store temporary edit value
  - Add `editGiftError` property to store validation errors
  - Implement `startEditGift()` method to enter edit mode
  - Implement `cancelEditGift()` method to exit edit mode without saving
  - Implement `isEditingGift()` helper method
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3, 5.4_

- [x] 5. Implement gift name validation and save logic
  - Implement `validateGiftName()` method in AdminComponent
  - Check for empty names and whitespace-only names
  - Check for length constraints (1-100 characters)
  - Implement `saveEditGift()` method to save changes
  - Call GiftService `updateGiftName()` method
  - Handle success response and update gifts list
  - Handle error response and display error message
  - _Requirements: 1.5, 3.1, 3.2, 3.3, 3.4_

- [x] 6. Update admin template with inline editing UI
  - Add edit button next to gift name in display mode
  - Add conditional rendering for edit mode vs display mode
  - Add input field for editing gift name with two-way binding
  - Add save and cancel buttons in edit mode
  - Add error message display for validation errors
  - Add keyboard shortcuts (Enter to save, Escape to cancel)
  - Add autofocus to input field when entering edit mode
  - Disable edit buttons for other gifts when one is being edited
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3, 5.4, 6.4_

- [x] 7. Add CSS styling for edit mode UI
  - Style edit button with appropriate colors and sizing
  - Style input field with focus states and error states
  - Style save and cancel buttons with distinct colors
  - Style error message display
  - Ensure touch-friendly button sizes for mobile (44x44px minimum)
  - Add responsive styles for mobile devices
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8. Add loading states and success feedback
  - Add loading indicator while saving gift name
  - Show success message after successful update
  - Auto-refresh gifts list after successful update
  - Clear success message after 3 seconds
  - Disable save button while request is in progress
  - _Requirements: 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_
