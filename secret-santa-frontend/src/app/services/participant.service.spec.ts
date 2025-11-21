import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ParticipantService, Participant, ParticipantRegistrationResponse } from './participant.service';

describe('ParticipantService', () => {
  let service: ParticipantService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:8080/api';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ParticipantService]
    });
    service = TestBed.inject(ParticipantService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('registerParticipant', () => {
    it('should register a participant successfully', () => {
      const mockName = 'John Doe';
      const mockParticipant: Participant = {
        id: 1,
        name: 'John Doe',
        registration_timestamp: '2023-12-01T10:00:00Z'
      };

      service.registerParticipant(mockName).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.participant?.name).toBe('John Doe');
        expect(response.participant?.id).toBe(1);
        expect(response.message).toContain('Registration successful');
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ name: 'John Doe' });
      req.flush(mockParticipant);
    });

    it('should trim whitespace from name', () => {
      const mockName = '  Jane Smith  ';
      const mockParticipant: Participant = {
        id: 2,
        name: 'Jane Smith',
        registration_timestamp: '2023-12-01T10:00:00Z'
      };

      service.registerParticipant(mockName).subscribe();

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      expect(req.request.body).toEqual({ name: 'Jane Smith' });
      req.flush(mockParticipant);
    });

    it('should handle registration failure', () => {
      const mockName = 'Test User';
      const mockErrorResponse = {
        error: 'Registration limit reached'
      };

      service.registerParticipant(mockName).subscribe({
        next: (response) => {
          expect(response.success).toBe(false);
          expect(response.error).toBe('Registration limit reached');
        },
        error: (error) => {
          expect(error.success).toBe(false);
          expect(error.error).toBe('Registration limit reached');
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      req.flush(mockErrorResponse, { status: 400, statusText: 'Bad Request' });
    });

    it('should handle HTTP 409 error (conflict)', () => {
      const mockName = 'Test User';

      service.registerParticipant(mockName).subscribe({
        next: () => fail('Should have failed'),
        error: (error) => {
          expect(error.success).toBe(false);
          expect(error.error).toBe('Registration limit reached');
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      req.flush({ error: 'Registration limit reached' }, { status: 409, statusText: 'Conflict' });
    });

    it('should handle network error', () => {
      const mockName = 'Test User';

      service.registerParticipant(mockName).subscribe({
        next: () => fail('Should have failed'),
        error: (error) => {
          expect(error.success).toBe(false);
          expect(error.error).toBe('Unable to connect to server. Please check your connection.');
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      req.error(new ProgressEvent('error'), { status: 0 });
    });
  });

  describe('getParticipants', () => {
    it('should retrieve all participants', () => {
      const mockParticipants: Participant[] = [
        { id: 1, name: 'John Doe', registration_timestamp: '2023-12-01T10:00:00Z' },
        { id: 2, name: 'Jane Smith', registration_timestamp: '2023-12-01T10:05:00Z' }
      ];

      service.getParticipants().subscribe(participants => {
        expect(participants).toEqual(mockParticipants);
        expect(participants.length).toBe(2);
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      expect(req.request.method).toBe('GET');
      req.flush({ participants: mockParticipants });
    });

    it('should handle empty participants list', () => {
      const mockParticipants: Participant[] = [];

      service.getParticipants().subscribe(participants => {
        expect(participants).toEqual([]);
        expect(participants.length).toBe(0);
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      req.flush({ participants: mockParticipants });
    });

    it('should handle server error', () => {
      service.getParticipants().subscribe({
        next: () => fail('Should have failed'),
        error: (error) => {
          expect(error.message).toContain('Server error');
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/participants`);
      req.flush({ message: 'Internal server error' }, { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('getParticipantCount', () => {
    it('should retrieve participant count', () => {
      const mockCountResponse = { count: 5, max_participants: 100 };

      service.getParticipantCount().subscribe(count => {
        expect(count).toBe(5);
      });

      const req = httpMock.expectOne(`${baseUrl}/participants/count`);
      expect(req.request.method).toBe('GET');
      req.flush(mockCountResponse);
    });

    it('should handle zero count', () => {
      const mockCountResponse = { count: 0, max_participants: 100 };

      service.getParticipantCount().subscribe(count => {
        expect(count).toBe(0);
      });

      const req = httpMock.expectOne(`${baseUrl}/participants/count`);
      req.flush(mockCountResponse);
    });

    it('should handle error when getting count', () => {
      service.getParticipantCount().subscribe({
        next: () => fail('Should have failed'),
        error: (error) => {
          expect(error.message).toBe('Bad request');
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/participants/count`);
      req.flush({ message: 'Bad request' }, { status: 400, statusText: 'Bad Request' });
    });
  });
});