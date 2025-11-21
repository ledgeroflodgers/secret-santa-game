# Requirements Document

## Introduction

This feature implements a web-based Secret Santa game application that allows up to 100 users to sign up and participate in a gift exchange game. The system will consist of an Angular frontend deployed on AWS S3, a Python backend, and a simple text file database. The application manages user registration with unique number assignment, displays participant information, and handles gift management with theft tracking and locking mechanisms.

## Requirements

### Requirement 1

**User Story:** As a participant, I want to register for the Secret Santa game with my name, so that I can join the gift exchange and receive a unique participant number.

#### Acceptance Criteria

1. WHEN a user enters their name on the registration page THEN the system SHALL assign them a unique number between 1 and 100
2. WHEN multiple users register simultaneously THEN the system SHALL prevent duplicate number assignments
3. WHEN a user successfully registers THEN the system SHALL store their name and assigned number
4. WHEN the registration limit of 100 users is reached THEN the system SHALL prevent additional registrations
5. IF a user attempts to register with an empty name THEN the system SHALL display an error message

### Requirement 2

**User Story:** As a participant or observer, I want to view all registered participants and their assigned numbers, so that I can see who is participating in the game.

#### Acceptance Criteria

1. WHEN a user navigates to the participants page THEN the system SHALL display all registered names with their corresponding numbers
2. WHEN the participants list is displayed THEN the system SHALL show names and numbers in a clear, organized format
3. WHEN new participants register THEN the participants page SHALL update to reflect the current list
4. WHEN no participants are registered THEN the system SHALL display an appropriate message

### Requirement 3

**User Story:** As an admin, I want to manage the gift exchange process and add gifts to the pool, so that I can facilitate the Secret Santa game.

#### Acceptance Criteria

1. WHEN an admin accesses the admin page THEN the system SHALL display whose turn it is to select/steal a gift
2. WHEN an admin enters a gift name THEN the system SHALL add it to the available gifts pool
3. WHEN a gift is added THEN the system SHALL display it in the gifts list
4. WHEN the admin submits a gift THEN the system SHALL clear the input field for the next entry

### Requirement 4

**User Story:** As a participant, I want to steal gifts from other participants with limitations, so that I can participate in the gift exchange mechanics.

#### Acceptance Criteria

1. WHEN a participant clicks on a gift name THEN the system SHALL increment the steal counter for that gift
2. WHEN a gift is stolen THEN the system SHALL display a strike indicator next to the gift name
3. WHEN a gift reaches 3 steals THEN the system SHALL lock the gift and prevent further stealing
4. WHEN a gift is locked THEN the system SHALL visually indicate that it cannot be stolen anymore
5. WHEN a gift has strikes THEN the system SHALL display the current number of strikes (1, 2, or 3)

### Requirement 5

**User Story:** As a system administrator, I want the application to be deployed on AWS S3 with a Python backend, so that the application is accessible and scalable.

#### Acceptance Criteria

1. WHEN the Angular frontend is built THEN the system SHALL be deployable to AWS S3 as a static website
2. WHEN the Python backend is implemented THEN the system SHALL handle API requests from the frontend
3. WHEN data needs to be persisted THEN the system SHALL use a simple text file as the database
4. WHEN the backend processes requests THEN the system SHALL maintain data consistency across concurrent operations
5. WHEN the application is deployed THEN the system SHALL be accessible via a web URL

### Requirement 6

**User Story:** As a participant, I want the game to handle concurrent registrations properly, so that the system remains fair and consistent.

#### Acceptance Criteria

1. WHEN multiple users register at the exact same time THEN the system SHALL ensure no duplicate numbers are assigned
2. WHEN the system assigns numbers THEN the system SHALL use atomic operations to prevent race conditions
3. WHEN data is written to the text file THEN the system SHALL handle concurrent write operations safely
4. WHEN the system encounters a conflict THEN the system SHALL retry the operation or return an appropriate error