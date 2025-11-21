import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { GiftService, Gift, GiftResponse, AddGiftRequest, StealGiftRequest, StealGiftResponse } from './gift.service';

describe('GiftService', () => {
  let service: GiftService;
  let httpMock: HttpTestingController;
  const baseUrl = 'http://localhost:5000/api';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [GiftService]
    });
    service = TestBed.inject(GiftService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getGifts', () => {
    it('should return gifts list', () => {
      const mockResponse: GiftResponse = {
        gifts: [
          {
            id: 'gift1',
            name: 'Test Gift',
            steal_count: 0,
            is_locked: false,
            current_owner: null,
            steal_history: []
          }
        ]
      };

      service.getGifts().subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.gifts.length).toBe(1);
        expect(response.gifts[0].name).toBe('Test Gift');
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle empty gifts list', () => {
      const mockResponse: GiftResponse = { gifts: [] };

      service.getGifts().subscribe(response => {
        expect(response.gifts).toEqual([]);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      req.flush(mockResponse);
    });
  });

  describe('addGift', () => {
    it('should add a new gift', () => {
      const giftData: AddGiftRequest = { name: 'New Gift' };
      const mockResponse: Gift = {
        id: 'gift1',
        name: 'New Gift',
        steal_count: 0,
        is_locked: false,
        current_owner: null,
        steal_history: []
      };

      service.addGift(giftData).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.name).toBe('New Gift');
        expect(response.steal_count).toBe(0);
        expect(response.is_locked).toBe(false);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(giftData);
      req.flush(mockResponse);
    });

    it('should add a gift with owner', () => {
      const giftData: AddGiftRequest = { name: 'Gift with Owner', owner_id: 1 };
      const mockResponse: Gift = {
        id: 'gift2',
        name: 'Gift with Owner',
        steal_count: 0,
        is_locked: false,
        current_owner: 1,
        steal_history: []
      };

      service.addGift(giftData).subscribe(response => {
        expect(response.current_owner).toBe(1);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      expect(req.request.body).toEqual(giftData);
      req.flush(mockResponse);
    });
  });

  describe('stealGift', () => {
    it('should steal a gift successfully', () => {
      const giftId = 'gift1';
      const stealData: StealGiftRequest = { new_owner_id: 2 };
      const mockResponse: StealGiftResponse = {
        success: true,
        message: 'Gift stolen successfully',
        gift: {
          id: 'gift1',
          name: 'Stolen Gift',
          steal_count: 1,
          is_locked: false,
          current_owner: 2,
          steal_history: [1]
        }
      };

      service.stealGift(giftId, stealData).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.message).toBe('Gift stolen successfully');
        expect(response.gift?.current_owner).toBe(2);
        expect(response.gift?.steal_count).toBe(1);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts/${giftId}/steal`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(stealData);
      req.flush(mockResponse);
    });

    it('should handle locked gift steal attempt', () => {
      const giftId = 'gift1';
      const stealData: StealGiftRequest = { new_owner_id: 2 };
      const mockResponse: StealGiftResponse = {
        success: false,
        message: 'Gift cannot be stolen - it is locked',
        gift: {
          id: 'gift1',
          name: 'Locked Gift',
          steal_count: 3,
          is_locked: true,
          current_owner: 1,
          steal_history: [2, 3, 4]
        }
      };

      service.stealGift(giftId, stealData).subscribe(response => {
        expect(response.success).toBe(false);
        expect(response.message).toContain('locked');
        expect(response.gift?.is_locked).toBe(true);
        expect(response.gift?.steal_count).toBe(3);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts/${giftId}/steal`);
      req.flush(mockResponse);
    });

    it('should handle gift locking after 3 steals', () => {
      const giftId = 'gift1';
      const stealData: StealGiftRequest = { new_owner_id: 4 };
      const mockResponse: StealGiftResponse = {
        success: true,
        message: 'Gift stolen successfully - Gift is now locked after 3 steals',
        gift: {
          id: 'gift1',
          name: 'Now Locked Gift',
          steal_count: 3,
          is_locked: true,
          current_owner: 4,
          steal_history: [1, 2, 3]
        }
      };

      service.stealGift(giftId, stealData).subscribe(response => {
        expect(response.success).toBe(true);
        expect(response.message).toContain('locked after 3 steals');
        expect(response.gift?.is_locked).toBe(true);
        expect(response.gift?.steal_count).toBe(3);
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts/${giftId}/steal`);
      req.flush(mockResponse);
    });
  });

  describe('error handling', () => {
    it('should handle HTTP errors for getGifts', () => {
      service.getGifts().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(500);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });

    it('should handle HTTP errors for addGift', () => {
      const giftData: AddGiftRequest = { name: 'Test Gift' };

      service.addGift(giftData).subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(400);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts`);
      req.flush('Bad Request', { status: 400, statusText: 'Bad Request' });
    });

    it('should handle HTTP errors for stealGift', () => {
      const giftId = 'gift1';
      const stealData: StealGiftRequest = { new_owner_id: 2 };

      service.stealGift(giftId, stealData).subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(404);
        }
      });

      const req = httpMock.expectOne(`${baseUrl}/gifts/${giftId}/steal`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });
  });
});