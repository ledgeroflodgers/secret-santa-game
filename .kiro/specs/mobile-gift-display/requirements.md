# Requirements Document

## Introduction

This feature implements a mobile-friendly, real-time gift display page for the Secret Santa game application. The display provides a full-screen, space-efficient view of all gifts with visual indicators for their steal status, designed specifically for mobile devices and optimized for participants to follow the game progress from their phones.

## Glossary

- **Gift_Display_System**: The mobile-friendly page component that shows all gifts in real-time
- **Steal_Status**: The current state of a gift indicating how many times it has been stolen (0, 1, 2, or 3+ times)
- **Screen_Division**: The automatic layout system that divides the screen space equally among all displayed gifts
- **Status_Color_Coding**: The visual system using background colors to indicate gift steal status

## Requirements

### Requirement 1

**User Story:** As a participant, I want to view all gifts on a mobile-friendly display page, so that I can easily follow the game progress from my phone.

#### Acceptance Criteria

1. WHEN a user navigates to the gift display page, THE Gift_Display_System SHALL render a full-screen view without margins, padding, or gaps
2. WHEN the page loads on a mobile device, THE Gift_Display_System SHALL optimize the layout for mobile viewing
3. WHEN gifts are displayed, THE Gift_Display_System SHALL use the entire available screen space
4. WHEN no gifts exist, THE Gift_Display_System SHALL display an appropriate waiting message
5. WHEN the page is accessed, THE Gift_Display_System SHALL be accessible via a dedicated route

### Requirement 2

**User Story:** As a participant, I want to see gift names with clear visual indicators, so that I can easily read and understand the current state of each gift.

#### Acceptance Criteria

1. WHEN a gift is first added by admin, THE Gift_Display_System SHALL display the gift name with a green background and dark grey font
2. WHEN gift text is displayed, THE Gift_Display_System SHALL use fonts that are clearly readable on mobile devices
3. WHEN multiple gifts exist, THE Gift_Display_System SHALL ensure each gift name is fully visible and readable
4. WHEN gift names are long, THE Gift_Display_System SHALL handle text wrapping or truncation appropriately
5. WHEN gifts are displayed, THE Gift_Display_System SHALL maintain consistent font styling across all gifts

### Requirement 3

**User Story:** As a participant, I want the screen to automatically divide space for new gifts, so that all gifts remain visible as more are added.

#### Acceptance Criteria

1. WHEN the first gift is added, THE Gift_Display_System SHALL display it covering the entire screen
2. WHEN a second gift is added, THE Gift_Display_System SHALL divide the screen into two equal parts
3. WHEN additional gifts are added, THE Gift_Display_System SHALL continuously divide the available space equally among all gifts
4. WHEN the screen division occurs, THE Gift_Display_System SHALL maintain readability of all gift names
5. WHEN gifts are removed or the list changes, THE Gift_Display_System SHALL recalculate and redistribute the screen space

### Requirement 4

**User Story:** As a participant, I want to see color-coded steal status for each gift, so that I can quickly understand how many times each gift has been stolen.

#### Acceptance Criteria

1. WHEN a gift has zero steals, THE Gift_Display_System SHALL display it with a green background
2. WHEN a gift is stolen once, THE Gift_Display_System SHALL change the background color to yellow
3. WHEN a gift is stolen twice, THE Gift_Display_System SHALL change the background color to red
4. WHEN a gift is stolen three or more times, THE Gift_Display_System SHALL display it with a grey background and white font
5. WHEN the steal status changes, THE Gift_Display_System SHALL update the color immediately

### Requirement 5

**User Story:** As a participant, I want the display to show real-time updates, so that I can see changes as they happen during the game.

#### Acceptance Criteria

1. WHEN gifts are added by the admin, THE Gift_Display_System SHALL update the display automatically
2. WHEN gifts are stolen, THE Gift_Display_System SHALL reflect the status change immediately
3. WHEN the backend data changes, THE Gift_Display_System SHALL poll for updates or receive real-time notifications
4. WHEN network connectivity is lost, THE Gift_Display_System SHALL handle the disconnection gracefully
5. WHEN connectivity is restored, THE Gift_Display_System SHALL resume real-time updates

### Requirement 6

**User Story:** As a participant, I want the display to work efficiently on mobile devices, so that I can follow the game without performance issues.

#### Acceptance Criteria

1. WHEN the page loads on mobile devices, THE Gift_Display_System SHALL render quickly and efficiently
2. WHEN screen orientation changes, THE Gift_Display_System SHALL adapt the layout appropriately
3. WHEN multiple gifts are displayed, THE Gift_Display_System SHALL maintain smooth performance
4. WHEN updates occur, THE Gift_Display_System SHALL minimize battery drain and data usage
5. WHEN the page is viewed on different mobile screen sizes, THE Gift_Display_System SHALL scale appropriately