import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { AdminComponent } from './admin.component';
import { GiftService, Gift } from '../services/gift.service';
import { GameService, CurrentTurnResponse } from '../services/game.service';

describe('Gift Stealing Integration Tests', () => {
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

    mockGameService.getCurrentTurn.and.returnValue(of(mockCurrentTurn));
  });

  describe('Complete Gift Stealing Workflow', () => {
    it('should handle complete gift stealing lifecycle from creation to lock', () => {
      // Initial state - no gifts
      mockGiftService.getGifts.and.returnValue(of({ gifts: [] }));
      
      component.ngOnInit();
      fixture.detectChanges();

      expect(component.gifts.length).toBe(0);

      // Step 1: Add a new gift
      const newGift: Gift = {
        id: 'gift1',
        name: 'Test Gift',
        steal_count: 0,
        is_locked: false,
        current_owner: 1,
        steal_history: []
      };

      mockGiftService.addGift.and.returnValue(of(newGift));
      mockGiftService.getGifts.and.returnValue(of({ gifts: [newGift] }));

      component.giftForm.patchValue({ name: 'Test Gift' });
      component.onSubmitGift();

      expect(mockGiftService.addGift).toHaveBeenCalledWith({
        name: 'Test Gift',
        owner_id: 1
      });

      // Step 2: First steal (steal_count: 1)
      const giftAfterFirstSteal: Gift = {
        ...newGift,
        steal_count: 1,
        current_owner: 2,
        steal_history: [1]
      };

      mockGiftService.stealGift.and.returnValue(of({
        success: true,
        message: 'Gift stolen successfully',
        gift: giftAfterFirstSteal
      }));
      mockGiftService.getGifts.and.returnValue(of({ gifts: [giftAfterFirstSteal] }));

      component.currentTurn = { ...mockCurrentTurn, current_turn: 2 };
      component.onStealGift(newGift);

      expect(mockGiftService.stealGift).toHaveBeenCalledWith('gift1', { new_owner_id: 2 });

      // Step 3: Second steal (steal_count: 2)
      const giftAfterSecondSteal: Gift = {
        ...giftAfterFirstSteal,
        steal_count: 2,
        current_owner: 3,
        steal_history: [1, 2]
      };

      mockGiftService.stealGift.and.returnValue(of({
        success: true,
        message: 'Gift stolen successfully',
        gift: giftAfterSecondSteal
      }));
      mockGiftService.getGifts.and.returnValue(of({ gifts: [giftAfterSecondSteal] }));

      component.currentTurn = { ...mockCurrentTurn, current_turn: 3 };
      component.onStealGift(giftAfterFirstSteal);

      expect(mockGiftService.stealGift).toHaveBeenCalledWith('gift1', { new_owner_id: 3 });

      // Step 4: Third steal - gift becomes locked (steal_count: 3)
      const lockedGift: Gift = {
        ...giftAfterSecondSteal,
        steal_count: 3,
        is_locked: true,
        current_owner: 1,
        steal_history: [1, 2, 3]
      };

      mockGiftService.stealGift.and.returnValue(of({
        success: true,
        message: 'Gift stolen successfully - Gift is now locked after 3 steals',
        gift: lockedGift
      }));
      mockGiftService.getGifts.and.returnValue(of({ gifts: [lockedGift] }));

      component.currentTurn = { ...mockCurrentTurn, current_turn: 1 };
      component.onStealGift(giftAfterSecondSteal);

      expect(mockGiftService.stealGift).toHaveBeenCalledWith('gift1', { new_owner_id: 1 });

      // Step 5: Attempt to steal locked gift - should fail
      component.onStealGift(lockedGift);

      // Should not make API call for locked gift
      expect(mockGiftService.stealGift).toHaveBeenCalledTimes(3); // Only 3 successful steals
    });

    it('should display correct visual indicators throughout stealing lifecycle', () => {
      const gifts: Gift[] = [
        {
          id: 'gift1',
          name: 'No Steals Gift',
          steal_count: 0,
          is_locked: false,
          current_owner: 1,
          steal_history: []
        },
        {
          id: 'gift2',
          name: 'One Steal Gift',
          steal_count: 1,
          is_locked: false,
          current_owner: 2,
          steal_history: [1]
        },
        {
          id: 'gift3',
          name: 'Two Steals Gift',
          steal_count: 2,
          is_locked: false,
          current_owner: 3,
          steal_history: [1, 2]
        },
        {
          id: 'gift4',
          name: 'Locked Gift',
          steal_count: 3,
          is_locked: true,
          current_owner: 1,
          steal_history: [2, 3, 1]
        }
      ];

      mockGiftService.getGifts.and.returnValue(of({ gifts }));
      component.ngOnInit();
      fixture.detectChanges();

      // Test strike display
      expect(component.getStrikeDisplay(gifts[0])).toBe(''); // No strikes
      expect(component.getStrikeDisplay(gifts[1])).toBe('★'); // One strike
      expect(component.getStrikeDisplay(gifts[2])).toBe('★★'); // Two strikes
      expect(component.getStrikeDisplay(gifts[3])).toBe('LOCKED'); // Locked

      // Test CSS classes
      expect(component.getStrikeCssClass(gifts[0])).toBe('no-strikes');
      expect(component.getStrikeCssClass(gifts[1])).toBe('has-strikes');
      expect(component.getStrikeCssClass(gifts[2])).toBe('has-strikes');
      expect(component.getStrikeCssClass(gifts[3])).toBe('locked');

      // Test strike indicators
      expect(component.getStrikeIndicators(gifts[0])).toEqual([false, false, false]);
      expect(component.getStrikeIndicators(gifts[1])).toEqual([true, false, false]);
      expect(component.getStrikeIndicators(gifts[2])).toEqual([true, true, false]);
      expect(component.getStrikeIndicators(gifts[3])).toEqual([true, true, true]);

      // Test steal ability
      expect(component.canStealGift(gifts[0])).toBe(true);
      expect(component.canStealGift(gifts[1])).toBe(true);
      expect(component.canStealGift(gifts[2])).toBe(true);
      expect(component.canStealGift(gifts[3])).toBe(false); // Locked

      // Test tooltips (gifts[0] has current_owner: 1, same as current_turn: 1)
      expect(component.getGiftTooltip(gifts[0])).toBe('You already own this gift');
      expect(component.getGiftTooltip(gifts[1])).toBe('Click to steal this gift (2 steals remaining before lock)');
      expect(component.getGiftTooltip(gifts[2])).toBe('Click to steal this gift (1 steals remaining before lock)');
      expect(component.getGiftTooltip(gifts[3])).toBe('This gift is locked and cannot be stolen anymore');
    });

    it('should handle edge cases in gift stealing', () => {
      const gift: Gift = {
        id: 'gift1',
        name: 'Test Gift',
        steal_count: 0,
        is_locked: false,
        current_owner: 1,
        steal_history: []
      };

      mockGiftService.getGifts.and.returnValue(of({ gifts: [gift] }));
      component.ngOnInit();
      fixture.detectChanges();

      // Test when no current turn
      component.currentTurn = { ...mockCurrentTurn, current_turn: null };
      expect(component.canStealGift(gift)).toBe(false);
      expect(component.getGiftTooltip(gift)).toBe('No active turn - cannot steal gifts');

      // Test when user owns the gift
      component.currentTurn = mockCurrentTurn;
      const ownedGift = { ...gift, current_owner: 1 };
      expect(component.getGiftTooltip(ownedGift)).toBe('You already own this gift');

      // Test strike count text variations
      expect(component.getStrikeCountText(gift)).toBe('No steals yet - 3 steals allowed');
      
      const oneStealGift = { ...gift, steal_count: 1 };
      expect(component.getStrikeCountText(oneStealGift)).toBe('1/3 steals - 2 more steals allowed');
      
      const twoStealGift = { ...gift, steal_count: 2 };
      expect(component.getStrikeCountText(twoStealGift)).toBe('2/3 steals - 1 more steal will lock this gift');
      
      const lockedGift = { ...gift, steal_count: 3, is_locked: true };
      expect(component.getStrikeCountText(lockedGift)).toBe('LOCKED - No more steals allowed');
    });
  });
});