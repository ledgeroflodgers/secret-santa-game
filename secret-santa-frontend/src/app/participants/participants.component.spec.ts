import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError, Subject } from 'rxjs';

import { ParticipantsComponent } from './participants.component';
import { ParticipantService, Participant } from '../services/participant.service';

describe('ParticipantsComponent', () => {
  let component: ParticipantsComponent;
  let fixture: ComponentFixture<ParticipantsComponent>;
  let mockParticipantService: jasmine.SpyObj<ParticipantService>;

  const mockParticipants: Participant[] = [
    {
      id: 1,
      name: 'John Doe',
      registration_timestamp: '2024-01-01T10:00:00Z'
    },
    {
      id: 3,
      name: 'Jane Smith',
      registration_timestamp: '2024-01-01T10:05:00Z'
    },
    {
      id: 2,
      name: 'Bob Johnson',
      registration_timestamp: '2024-01-01T10:02:00Z'
    }
  ];

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('ParticipantService', ['getParticipants']);

    await TestBed.configureTestingModule({
      declarations: [ParticipantsComponent],
      imports: [RouterTestingModule],
      providers: [
        { provide: ParticipantService, useValue: spy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ParticipantsComponent);
    component = fixture.componentInstance;
    mockParticipantService = TestBed.inject(ParticipantService) as jasmine.SpyObj<ParticipantService>;
    
    // Set up default mock behavior
    mockParticipantService.getParticipants.and.returnValue(of([]));
  });

  afterEach(() => {
    // Clean up any subscriptions to prevent timer issues
    component.ngOnDestroy();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should start with loading state', () => {
      expect(component.loading).toBe(true);
      expect(component.participants).toEqual([]);
      expect(component.error).toBeNull();
    });

    it('should load participants on init', fakeAsync(() => {
      mockParticipantService.getParticipants.and.returnValue(of(mockParticipants));
      
      component.ngOnInit();
      tick(); // Trigger the startWith(0) emission
      
      expect(mockParticipantService.getParticipants).toHaveBeenCalled();
      expect(component.loading).toBe(false);
      expect(component.participants.length).toBe(3);
      expect(component.error).toBeNull();
      
      // Clean up the interval
      component.ngOnDestroy();
    }));

    it('should sort participants by id', fakeAsync(() => {
      mockParticipantService.getParticipants.and.returnValue(of(mockParticipants));
      
      component.ngOnInit();
      tick();
      
      expect(component.participants[0].id).toBe(1);
      expect(component.participants[1].id).toBe(2);
      expect(component.participants[2].id).toBe(3);
      
      // Clean up the interval
      component.ngOnDestroy();
    }));

    it('should handle error on init', fakeAsync(() => {
      const errorMessage = 'Failed to load participants';
      mockParticipantService.getParticipants.and.returnValue(throwError(() => new Error(errorMessage)));
      
      component.ngOnInit();
      tick();
      
      expect(component.loading).toBe(false);
      expect(component.error).toBe(errorMessage);
      expect(component.participants).toEqual([]);
      
      // Clean up the interval
      component.ngOnDestroy();
    }));
  });

  describe('Auto-refresh functionality', () => {
    it('should auto-refresh every 5 seconds', fakeAsync(() => {
      mockParticipantService.getParticipants.and.returnValue(of(mockParticipants));
      
      component.ngOnInit();
      tick(); // Initial load
      
      expect(mockParticipantService.getParticipants).toHaveBeenCalledTimes(1);
      
      tick(5000); // Wait 5 seconds
      expect(mockParticipantService.getParticipants).toHaveBeenCalledTimes(2);
      
      tick(5000); // Wait another 5 seconds
      expect(mockParticipantService.getParticipants).toHaveBeenCalledTimes(3);
      
      // Clean up the interval
      component.ngOnDestroy();
    }));

    it('should stop auto-refresh on destroy', fakeAsync(() => {
      mockParticipantService.getParticipants.and.returnValue(of(mockParticipants));
      
      component.ngOnInit();
      tick();
      
      component.ngOnDestroy();
      
      tick(5000);
      expect(mockParticipantService.getParticipants).toHaveBeenCalledTimes(1); // Only initial call
    }));
  });

  describe('Manual refresh', () => {
    it('should refresh participants manually', () => {
      mockParticipantService.getParticipants.and.returnValue(of(mockParticipants));
      
      component.refreshParticipants();
      
      expect(component.loading).toBe(false);
      expect(component.participants.length).toBe(3);
      expect(component.error).toBeNull();
    });

    it('should handle error during manual refresh', () => {
      const errorMessage = 'Network error';
      mockParticipantService.getParticipants.and.returnValue(throwError(() => new Error(errorMessage)));
      
      component.refreshParticipants();
      
      expect(component.loading).toBe(false);
      expect(component.error).toBe(errorMessage);
    });

    it('should set loading state during manual refresh', () => {
      const subject = new Subject<Participant[]>();
      mockParticipantService.getParticipants.and.returnValue(subject.asObservable());
      
      component.refreshParticipants();
      
      expect(component.loading).toBe(true);
      expect(component.error).toBeNull();
      
      subject.next(mockParticipants);
      expect(component.loading).toBe(false);
    });
  });

  describe('Utility methods', () => {
    it('should format timestamp correctly', () => {
      const timestamp = '2024-01-01T10:00:00Z';
      const formatted = component.getFormattedTime(timestamp);
      
      expect(formatted).toBeTruthy();
      expect(typeof formatted).toBe('string');
    });

    it('should track participants by id', () => {
      const participant = mockParticipants[0];
      const result = component.trackByParticipantId(0, participant);
      
      expect(result).toBe(participant.id);
    });
  });

  describe('Template rendering', () => {
    beforeEach(() => {
      // Prevent auto-refresh from starting during template tests
      spyOn(component, 'startAutoRefresh' as any);
    });

    it('should show loading spinner when loading', () => {
      component.loading = true;
      fixture.detectChanges();
      
      const loadingElement = fixture.nativeElement.querySelector('.loading');
      expect(loadingElement).toBeTruthy();
      expect(loadingElement.textContent).toContain('Loading participants');
    });

    it('should show error message when there is an error', () => {
      component.loading = false;
      component.error = 'Test error message';
      fixture.detectChanges();
      
      const errorElement = fixture.nativeElement.querySelector('.error');
      expect(errorElement).toBeTruthy();
      expect(errorElement.textContent).toContain('Test error message');
    });

    it('should show empty state when no participants', () => {
      component.loading = false;
      component.error = null;
      component.participants = [];
      fixture.detectChanges();
      
      const emptyElement = fixture.nativeElement.querySelector('.empty-state');
      expect(emptyElement).toBeTruthy();
      expect(emptyElement.textContent).toContain('No participants registered yet');
    });

    it('should display participants when loaded', () => {
      component.loading = false;
      component.error = null;
      component.participants = mockParticipants.sort((a, b) => a.id - b.id);
      fixture.detectChanges();
      
      const participantBadges = fixture.nativeElement.querySelectorAll('.participant-badge');
      expect(participantBadges.length).toBe(3);
      
      const firstBadge = participantBadges[0];
      expect(firstBadge.querySelector('.badge-number').textContent.trim()).toBe('1');
      expect(firstBadge.querySelector('.badge-name').textContent.trim()).toBe('John Doe');
    });

    it('should show participant count', () => {
      component.loading = false;
      component.error = null;
      component.participants = mockParticipants;
      fixture.detectChanges();

      const headerElement = fixture.nativeElement.querySelector(
        '.participants-header h3'
      );
      expect(headerElement.textContent).toContain('3 Gift Exchangers Ready!');
    });

    it('should show singular form for one participant', () => {
      component.loading = false;
      component.error = null;
      component.participants = [mockParticipants[0]];
      fixture.detectChanges();

      const headerElement = fixture.nativeElement.querySelector(
        '.participants-header h3'
      );
      expect(headerElement.textContent).toContain('1 Gift Exchanger Ready!');
    });

    it('should have refresh button that calls refreshParticipants', () => {
      spyOn(component, 'refreshParticipants');
      component.loading = false;
      fixture.detectChanges();
      
      const refreshButton = fixture.nativeElement.querySelector('.refresh-btn');
      refreshButton.click();
      
      expect(component.refreshParticipants).toHaveBeenCalled();
    });

    it('should disable refresh button when loading', () => {
      component.loading = true;
      fixture.detectChanges();
      
      const refreshButton = fixture.nativeElement.querySelector('.refresh-btn');
      expect(refreshButton.disabled).toBe(true);
    });
  });
});
