import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { GameService, CurrentTurnResponse, AdvanceTurnResponse, Participant } from './game.service';

describe('GameService', () => {
  let service: GameService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:5000/api';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [GameService]
    });
    service = TestBed.inject(GameService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getCurrentTurn', () => {
    it('should return current turn information with participant', () => {
      const mockParticipant: Participant = {
        id: 1,
        name: 'John Doe',
        registration_timestamp: '2024-01-01T10:00:00Z'
      };

      const mockResponse: CurrentTurnResponse = {
        current_turn: 1,
        current_participant: mockParticipant,
        game_phase: 'active',
        turn_order: [1, 2, 3],
        total_participants: 3
      };

      service.getCurrentTurn().subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.current_turn).toBe(1);
        expect(response.current_participant?.name).toBe('John Doe');
        expect(response.game_phase).toBe('active');
        expect(response.total_participants).toBe(3);
      });

      const req = httpMock.expectOne(`${baseUrl}/game/current-turn`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should return current turn information without participant', () => {
      const mockResponse: CurrentTurnResponse = {
        current_turn: null,
        current_participant: null,
        game_phase: 'registration',
        turn_order: [],
        total_participants: 0
      };

      service.getCurrentTurn().subscribe(response => {
        expect(response.current_turn).toBeNull();
        expect(response.current_participant).toBeNull();
        expect(response.game_phase).toBe('registration');
        expect(response.total_participants).toBe(0);
      });

      const req = httpMock.expectOne(`${baseUrl}/game/current-turn`);
      req.flush(mockResponse);
    });

    it('should handle completed game phase', () => {
      const mockResponse: CurrentTurnResponse = {
        current_turn: null,
        current_participant: null,
        game_phase: 'completed',
        turn_order: [1, 2, 3],
        total_participants: 3
      };

      service.getCurrentTurn().subscribe(response => {
        expect(response.game_phase).toBe('completed');
        expect(response.current_turn).toBeNull();
      });

      const req = httpMock.expectOne(`${baseUrl}/game/current-turn`);
      req.flush(mockResponse);
    });
  });

  describe('advanceTurn', () => {
    it('should advance turn successfully', () => {
      const mockParticipant: Participant = {
        id: 2,
        name: 'Jane Smith',
        registration_timestamp: '2024-01-01T10:05:00Z'
      };

      const mockResponse: AdvanceTurnResponse = {
        success: true,
        message: 'Advanced to next turn',
        current_turn: 2,
        current_participant: mockParticipant,
        game_phase: 'active'
      };

      service.advanceTurn().subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.message).toBe('Advanced to next turn');
        expect(response.current_turn).toBe(2);
        expect(response.current_participant?.name).toBe('Jane Smith');
        expect(response.game_phase).toBe('active');
      });

      const req = httpMock.expectOne(`${baseUrl}/game/next-turn`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({});
      req.flush(mockResponse);
    });

    it('should handle game completion', () => {
      const mockResponse: AdvanceTurnResponse = {
        success: true,
        message: 'Game completed - all participants have had their turn',
        current_turn: null,
        current_participant: null,
        game_phase: 'completed'
      };

      service.advanceTurn().subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.message).toContain('Game completed');
        expect(response.current_turn).toBeNull();
        expect(response.game_phase).toBe('completed');
      });

      const req = httpMock.expectOne(`${baseUrl}/game/next-turn`);
      req.flush(mockResponse);
    });

    it('should handle no participants error', () => {
      const mockResponse: AdvanceTurnResponse = {
        success: false,
        message: 'No participants registered',
        current_turn: null,
        current_participant: null,
        game_phase: 'registration'
      };

      service.advanceTurn().subscribe(response => {
        expect(response.success).toBe(false);
        expect(response.message).toBe('No participants registered');
        expect(response.current_turn).toBeNull();
      });

      const req = httpMock.expectOne(`${baseUrl}/game/next-turn`);
      req.flush(mockResponse);
    });

    it('should handle game start transition', () => {
      const mockParticipant: Participant = {
        id: 1,
        name: 'First Player',
        registration_timestamp: '2024-01-01T10:00:00Z'
      };

      const mockResponse: AdvanceTurnResponse = {
        success: true,
        message: 'Advanced to next turn',
        current_turn: 1,
        current_participant: mockParticipant,
        game_phase: 'active'
      };

      service.advanceTurn().subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.game_phase).toBe('active');
        expect(response.current_turn).toBe(1);
      });

      const req = httpMock.expectOne(`${baseUrl}/game/next-turn`);
      req.flush(mockResponse);
    });
  });

  describe('error handling', () => {
    it('should handle HTTP errors for getCurrentTurn', () => {
      service.getCurrentTurn().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(503);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/game/current-turn`);
      req.flush('Service Unavailable', { status: 503, statusText: 'Service Unavailable' });
    });

    it('should handle HTTP errors for advanceTurn', () => {
      service.advanceTurn().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(500);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/game/next-turn`);
      req.flush('Internal Server Error', { status: 500, statusText: 'Internal Server Error' });
    });

    it('should handle network errors', () => {
      service.getCurrentTurn().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.error).toBeTruthy();
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/game/current-turn`);
      req.error(new ErrorEvent('Network error'));
    });
  });
});