import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { AdminComponent } from './admin.component';
import { GiftService, Gift } from '../services/gift.service';
import { GameService, CurrentTurnResponse } from '../services/game.service';

describe('AdminComponent', () => {
  let component: AdminComponent;
  let fixture: ComponentFixture<AdminComponent>;
  let mockGiftService: jasmine.SpyObj<GiftService>;
  let mockGameService: jasmine.SpyObj<GameService>;

  const mockCurrentTurn: CurrentTurnResponse = {
    current_turn: 1,
    current_participant: {
      id: 1,
      name: 'John Doe',
      registration_timestamp: '2024-01-01T10:00:00Z'
    },
    game_phase: 'active',
    turn_order: [1, 2, 3],
    total_participants: 3
  };

  const mockGifts: Gift[] = [
    {
      id: 'gift1',
      name: 'Test Gift 1',
      steal_count: 0,
      is_locked: false,
      current_owner: null,
      steal_history: []
    },
    {
      id: 'gift2',
      name: 'Test Gift 2',
      steal_count: 2,
      is_locked: false,
      current_owner: 2,
      steal_history: [1, 3]
    },
    {
      id: 'gift3',
      name: 'Locked Gift',
      steal_count: 3,
      is_locked: true,
      current_owner: 3,
      steal_history: [1, 2, 4]
    }
  ];

  beforeEach(async () => {
    const giftServiceSpy = jasmine.createSpyObj('GiftService', ['getGifts', 'addGift', 'stealGift']);
    const gameServiceSpy = jasmine.createSpyObj('GameService', ['getCurrentTurn', 'advanceTurn']);

    await TestBed.configureTestingModule({
      declarations: [AdminComponent],
      imports: [ReactiveFormsModule],
      providers: [
        { provide: GiftService, useValue: giftServiceSpy },
        { provide: GameService, useValue: gameServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AdminComponent);
    component = fixture.componentInstance;
    mockGiftService = TestBed.inject(GiftService) as jasmine.SpyObj<GiftService>;
    mockGameService = TestBed.inject(GameService) as jasmine.SpyObj<GameService>;

    // Setup default mock responses
    mockGameService.getCurrentTurn.and.returnValue(of(mockCurrentTurn));
    mockGiftService.getGifts.and.returnValue(of({ gifts: mockGifts }));
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should initialize form with empty gift name', () => {
      expect(component.giftForm.get('name')?.value).toBe('');
      expect(component.giftForm.get('name')?.hasError('required')).toBe(true);
    });

    it('should load current turn and gifts on init', () => {
      component.ngOnInit();

      expect(mockGameService.getCurrentTurn).toHaveBeenCalled();
      expect(mockGiftService.getGifts).toHaveBeenCalled();
      expect(component.currentTurn).toEqual(mockCurrentTurn);
      expect(component.gifts).toEqual(mockGifts);
    });

    it('should handle errors when loading initial data', () => {
      mockGameService.getCurrentTurn.and.returnValue(throwError(() => new Error('Network error')));
      mockGiftService.getGifts.and.returnValue(throwError(() => new Error('Network error')));

      component.ngOnInit();

      // Since both calls fail, the error message will be from the second call (gifts)
      expect(component.error).toBe('Failed to load gifts');
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should validate required gift name', () => {
      const nameControl = component.giftForm.get('name');
      
      nameControl?.setValue('');
      expect(nameControl?.hasError('required')).toBe(true);
      
      nameControl?.setValue('Valid Gift Name');
      expect(nameControl?.hasError('required')).toBe(false);
    });

    it('should validate minimum length', () => {
      const nameControl = component.giftForm.get('name');
      
      // Empty string doesn't trigger minlength error, only required error
      nameControl?.setValue('');
      expect(nameControl?.hasError('required')).toBe(true);
      
      nameControl?.setValue('A');
      expect(nameControl?.hasError('minlength')).toBe(false);
    });

    it('should validate maximum length', () => {
      const nameControl = component.giftForm.get('name');
      const longName = 'A'.repeat(101);
      
      nameControl?.setValue(longName);
      expect(nameControl?.hasError('maxlength')).toBe(true);
      
      nameControl?.setValue('A'.repeat(100));
      expect(nameControl?.hasError('maxlength')).toBe(false);
    });
  });

  describe('Gift Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should add gift successfully', fakeAsync(() => {
      const newGift: Gift = {
        id: 'gift4',
        name: 'New Gift',
        steal_count: 0,
        is_locked: false,
        current_owner: 1,
        steal_history: []
      };

      mockGiftService.addGift.and.returnValue(of(newGift));
      mockGiftService.getGifts.and.returnValue(of({ gifts: [...mockGifts, newGift] }));

      component.giftForm.patchValue({ name: 'New Gift' });
      component.onSubmitGift();

      expect(mockGiftService.addGift).toHaveBeenCalledWith({
        name: 'New Gift',
        owner_id: 1
      });

      tick(); // Process the observable

      expect(component.successMessage).toBe('Gift "New Gift" added successfully!');
      expect(component.giftForm.get('name')?.value).toBe(null); // Form reset sets to null
      expect(component.loading).toBe(false);

      tick(3000);
      expect(component.successMessage).toBeNull();
    }));

    it('should handle gift addition error', () => {
      const errorResponse = { error: { error: 'Gift name is required' } };
      mockGiftService.addGift.and.returnValue(throwError(() => errorResponse));

      component.giftForm.patchValue({ name: 'Test Gift' });
      component.onSubmitGift();

      expect(component.error).toBe('Gift name is required');
      expect(component.loading).toBe(false);
    });

    it('should not submit invalid form', () => {
      component.giftForm.patchValue({ name: '' });
      component.onSubmitGift();

      expect(mockGiftService.addGift).not.toHaveBeenCalled();
    });

    it('should prevent double submission', () => {
      component.loading = true;
      component.giftForm.patchValue({ name: 'Test Gift' });
      component.onSubmitGift();

      expect(mockGiftService.addGift).not.toHaveBeenCalled();
    });
  });

  describe('Gift Stealing', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should steal gift successfully', fakeAsync(() => {
      const stealResponse = {
        success: true,
        message: 'Gift stolen successfully',
        gift: { ...mockGifts[0], current_owner: 1, steal_count: 1 }
      };

      mockGiftService.stealGift.and.returnValue(of(stealResponse));

      component.onStealGift(mockGifts[0]);

      expect(mockGiftService.stealGift).toHaveBeenCalledWith('gift1', { new_owner_id: 1 });
      expect(component.successMessage).toBe('Gift stolen successfully');

      tick(3000);
      expect(component.successMessage).toBeNull();
    }));

    it('should handle failed steal attempt', () => {
      const stealResponse = {
        success: false,
        message: 'Gift cannot be stolen - it is locked',
        gift: mockGifts[2]
      };

      mockGiftService.stealGift.and.returnValue(of(stealResponse));

      // Use a non-locked gift for the test since locked gifts are prevented from being stolen
      component.onStealGift(mockGifts[0]);

      expect(component.error).toBe('Gift cannot be stolen - it is locked');
    });

    it('should handle steal error', () => {
      const errorResponse = { error: { error: 'Gift not found' } };
      mockGiftService.stealGift.and.returnValue(throwError(() => errorResponse));

      component.onStealGift(mockGifts[0]);

      expect(component.error).toBe('Gift not found');
    });

    it('should not steal locked gift', () => {
      component.onStealGift(mockGifts[2]); // Locked gift

      expect(mockGiftService.stealGift).not.toHaveBeenCalled();
    });

    it('should not steal when no current turn', () => {
      component.currentTurn = { ...mockCurrentTurn, current_turn: null };
      
      component.onStealGift(mockGifts[0]);

      expect(mockGiftService.stealGift).not.toHaveBeenCalled();
    });
  });

  describe('Turn Management', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should advance turn successfully', fakeAsync(() => {
      const advanceResponse = {
        success: true,
        message: 'Advanced to next turn',
        current_turn: 2,
        current_participant: {
          id: 2,
          name: 'Jane Smith',
          registration_timestamp: '2024-01-01T10:05:00Z'
        },
        game_phase: 'active' as const
      };

      mockGameService.advanceTurn.and.returnValue(of(advanceResponse));

      component.onNextTurn();

      expect(mockGameService.advanceTurn).toHaveBeenCalled();
      expect(component.successMessage).toBe('Advanced to next turn');

      tick(3000);
      expect(component.successMessage).toBeNull();
    }));

    it('should handle turn advancement error', () => {
      const advanceResponse = {
        success: false,
        message: 'No participants registered',
        current_turn: null,
        current_participant: null,
        game_phase: 'registration' as const
      };

      mockGameService.advanceTurn.and.returnValue(of(advanceResponse));

      component.onNextTurn();

      expect(component.error).toBe('No participants registered');
    });

    it('should handle turn advancement HTTP error', () => {
      const errorResponse = { error: { error: 'Internal server error' } };
      mockGameService.advanceTurn.and.returnValue(throwError(() => errorResponse));

      component.onNextTurn();

      expect(component.error).toBe('Internal server error');
    });
  });

  describe('Helper Methods', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should get correct strike display', () => {
      expect(component.getStrikeDisplay(mockGifts[0])).toBe(''); // 0 steals
      expect(component.getStrikeDisplay(mockGifts[1])).toBe('★★'); // 2 steals
      expect(component.getStrikeDisplay(mockGifts[2])).toBe('LOCKED'); // Locked
    });

    it('should get correct strike CSS class', () => {
      expect(component.getStrikeCssClass(mockGifts[0])).toBe('no-strikes'); // 0 steals
      expect(component.getStrikeCssClass(mockGifts[1])).toBe('has-strikes'); // 2 steals
      expect(component.getStrikeCssClass(mockGifts[2])).toBe('locked'); // Locked
    });

    it('should get correct strike indicators array', () => {
      expect(component.getStrikeIndicators(mockGifts[0])).toEqual([false, false, false]); // 0 steals
      expect(component.getStrikeIndicators(mockGifts[1])).toEqual([true, true, false]); // 2 steals
      expect(component.getStrikeIndicators(mockGifts[2])).toEqual([true, true, true]); // 3 steals (locked)
    });

    it('should get correct strike count text', () => {
      expect(component.getStrikeCountText(mockGifts[0])).toBe('No steals yet - 3 steals allowed');
      expect(component.getStrikeCountText(mockGifts[1])).toBe('2/3 steals - 1 more steal will lock this gift');
      expect(component.getStrikeCountText(mockGifts[2])).toBe('LOCKED - No more steals allowed');
    });

    it('should get correct gift tooltip', () => {
      expect(component.getGiftTooltip(mockGifts[0])).toBe('Click to steal this gift (3 steals remaining before lock)');
      expect(component.getGiftTooltip(mockGifts[1])).toBe('Click to steal this gift (1 steals remaining before lock)');
      expect(component.getGiftTooltip(mockGifts[2])).toBe('This gift is locked and cannot be stolen anymore');
      
      component.currentTurn = { ...mockCurrentTurn, current_turn: null };
      expect(component.getGiftTooltip(mockGifts[0])).toBe('No active turn - cannot steal gifts');
    });

    it('should handle gift tooltip when user owns the gift', () => {
      const ownedGift = { ...mockGifts[0], current_owner: 1 };
      expect(component.getGiftTooltip(ownedGift)).toBe('You already own this gift');
    });

    it('should determine if gift can be stolen', () => {
      expect(component.canStealGift(mockGifts[0])).toBe(true); // Not locked, has current turn
      expect(component.canStealGift(mockGifts[1])).toBe(true); // Not locked, has current turn
      expect(component.canStealGift(mockGifts[2])).toBe(false); // Locked

      component.currentTurn = { ...mockCurrentTurn, current_turn: null };
      expect(component.canStealGift(mockGifts[0])).toBe(false); // No current turn
    });
  });

  describe('Gift Stealing UI Interactions', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should display gift with correct visual indicators', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      const giftItems = compiled.querySelectorAll('.gift-item');
      
      expect(giftItems.length).toBe(3);
      
      // Check first gift (no steals)
      const firstGift = giftItems[0];
      expect(firstGift.classList.contains('stealable')).toBe(true);
      expect(firstGift.classList.contains('locked')).toBe(false);
      
      // Check locked gift
      const lockedGift = giftItems[2];
      expect(lockedGift.classList.contains('locked')).toBe(true);
      expect(lockedGift.classList.contains('stealable')).toBe(false);
    });

    it('should show correct strike indicators', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      const strikeIndicators = compiled.querySelectorAll('.strike-indicators');
      
      // Should have strike indicators for non-locked gifts
      expect(strikeIndicators.length).toBe(2); // First two gifts are not locked
      
      // Check strike dots for second gift (2 steals)
      const secondGiftStrikes = strikeIndicators[1].querySelectorAll('.strike-dot');
      expect(secondGiftStrikes.length).toBe(3);
      expect(secondGiftStrikes[0].classList.contains('empty')).toBe(false);
      expect(secondGiftStrikes[1].classList.contains('empty')).toBe(false);
      expect(secondGiftStrikes[2].classList.contains('empty')).toBe(true);
    });

    it('should handle click events on stealable gifts', () => {
      spyOn(component, 'onStealGift');
      const compiled = fixture.nativeElement as HTMLElement;
      const stealableGift = compiled.querySelector('.gift-item.stealable') as HTMLElement;
      
      stealableGift.click();
      
      expect(component.onStealGift).toHaveBeenCalledWith(mockGifts[0]);
    });

    it('should not handle click events on locked gifts', () => {
      spyOn(component, 'onStealGift');
      const compiled = fixture.nativeElement as HTMLElement;
      const lockedGift = compiled.querySelector('.gift-item.locked') as HTMLElement;
      
      lockedGift.click();
      
      expect(component.onStealGift).not.toHaveBeenCalled();
    });

    it('should display correct tooltips', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      const giftItems = compiled.querySelectorAll('.gift-item');
      
      expect(giftItems[0].getAttribute('title')).toBe('Click to steal this gift (3 steals remaining before lock)');
      expect(giftItems[2].getAttribute('title')).toBe('This gift is locked and cannot be stolen anymore');
    });
  });

  describe('Component Cleanup', () => {
    it('should unsubscribe on destroy', () => {
      component.ngOnInit();
      spyOn(component['refreshSubscription']!, 'unsubscribe');

      component.ngOnDestroy();

      expect(component['refreshSubscription']!.unsubscribe).toHaveBeenCalled();
    });

    it('should handle destroy when no subscription exists', () => {
      expect(() => component.ngOnDestroy()).not.toThrow();
    });
  });
});