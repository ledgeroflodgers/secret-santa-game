import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subscription, interval } from 'rxjs';
import { GiftService, Gift } from '../services/gift.service';
import { GameService, CurrentTurnResponse } from '../services/game.service';
import { ParticipantService, Participant } from '../services/participant.service';
import { LoadingService } from '../services/loading.service';
import { ErrorHandlingService } from '../services/error-handling.service';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit, OnDestroy {
  giftForm: FormGroup;
  passwordForm: FormGroup;
  currentTurn: CurrentTurnResponse | null = null;
  gifts: Gift[] = [];
  participants: Participant[] = [];
  loading = false;
  error: string | null = null;
  successMessage: string | null = null;
  isAuthenticated = false;
  passwordError = '';
  
  // Edit mode state management
  editingGiftId: string | null = null;
  editGiftName: string = '';
  editGiftError: string | null = null;
  
  private readonly ADMIN_PASSWORD = 'fx';
  private refreshSubscription?: Subscription;

  constructor(
    private fb: FormBuilder,
    private giftService: GiftService,
    private gameService: GameService,
    private participantService: ParticipantService,
    private loadingService: LoadingService,
    private errorHandlingService: ErrorHandlingService
  ) {
    this.giftForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(100)]]
    });
    
    this.passwordForm = this.fb.group({
      password: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    // Don't load data until authenticated
    if (this.isAuthenticated) {
      this.initializeAdmin();
    }
  }

  /**
   * Check password and authenticate
   */
  checkPassword(): void {
    const password = this.passwordForm.get('password')?.value;
    
    if (password === this.ADMIN_PASSWORD) {
      this.isAuthenticated = true;
      this.passwordError = '';
      this.passwordForm.reset();
      this.initializeAdmin();
    } else {
      this.passwordError = 'Incorrect password. Please try again.';
      this.passwordForm.get('password')?.setValue('');
    }
  }

  /**
   * Initialize admin interface after authentication
   */
  private initializeAdmin(): void {
    this.loadCurrentTurn();
    this.loadGifts();
    this.loadParticipants();
    
    // Auto-refresh every 10 seconds (silent refresh to avoid flickering)
    this.refreshSubscription = interval(10000).subscribe(() => {
      this.silentRefresh();
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  /**
   * Load current turn information
   */
  loadCurrentTurn(): void {
    const loadingKey = 'loadCurrentTurn';
    
    this.loadingService.wrapWithLoading(
      loadingKey,
      this.gameService.getCurrentTurn()
    ).subscribe({
      next: (response) => {
        this.currentTurn = response;
        this.error = null;
      },
      error: (error) => {
        console.error('Error loading current turn:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Silent refresh of current turn (no loading indicators)
   */
  private silentLoadCurrentTurn(): void {
    this.gameService.getCurrentTurn().subscribe({
      next: (response) => {
        this.currentTurn = response;
        // Don't clear errors during silent refresh to avoid hiding important messages
      },
      error: (error) => {
        console.error('Error during silent refresh of current turn:', error);
        // Don't show errors during silent refresh to avoid interrupting user
      }
    });
  }

  /**
   * Load all gifts
   */
  loadGifts(): void {
    const loadingKey = 'loadGifts';
    
    this.loadingService.wrapWithLoading(
      loadingKey,
      this.giftService.getGifts()
    ).subscribe({
      next: (response) => {
        this.gifts = response.gifts;
        this.error = null;
      },
      error: (error) => {
        console.error('Error loading gifts:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Silent refresh of gifts (no loading indicators)
   */
  private silentLoadGifts(): void {
    this.giftService.getGifts().subscribe({
      next: (response) => {
        this.gifts = response.gifts;
        // Don't clear errors during silent refresh to avoid hiding important messages
      },
      error: (error) => {
        console.error('Error during silent refresh of gifts:', error);
        // Don't show errors during silent refresh to avoid interrupting user
      }
    });
  }

  /**
   * Load all participants
   */
  loadParticipants(): void {
    const loadingKey = 'loadParticipants';
    
    this.loadingService.wrapWithLoading(
      loadingKey,
      this.participantService.getParticipants()
    ).subscribe({
      next: (participants) => {
        this.participants = participants;
        this.error = null;
      },
      error: (error) => {
        console.error('Error loading participants:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Silent refresh of participants (no loading indicators)
   */
  private silentLoadParticipants(): void {
    this.participantService.getParticipants().subscribe({
      next: (participants) => {
        this.participants = participants;
        // Don't clear errors during silent refresh to avoid hiding important messages
      },
      error: (error) => {
        console.error('Error during silent refresh of participants:', error);
        // Don't show errors during silent refresh to avoid interrupting user
      }
    });
  }

  /**
   * Get participant name by ID
   */
  getParticipantName(participantId: number): string {
    const participant = this.participants.find(p => p.id === participantId);
    return participant ? participant.name : `Player ${participantId}`;
  }

  /**
   * Submit new gift
   */
  onSubmitGift(): void {
    if (this.giftForm.valid && !this.loading) {
      this.loading = true;
      this.error = null;
      this.successMessage = null;

      const giftData = {
        name: this.giftForm.value.name.trim(),
        owner_id: this.currentTurn?.current_turn || undefined
      };

      const loadingKey = 'addGift';

      this.loadingService.wrapWithLoading(
        loadingKey,
        this.giftService.addGift(giftData)
      ).subscribe({
        next: (gift) => {
          this.successMessage = `Gift "${gift.name}" added successfully!`;
          this.giftForm.reset();
          this.loadGifts(); // Refresh gifts list
          this.loading = false;
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        },
        error: (error) => {
          console.error('Error adding gift:', error);
          this.error = this.errorHandlingService.getUserFriendlyMessage(error);
          this.loading = false;
        }
      });
    }
  }

  /**
   * Handle gift stealing
   */
  onStealGift(gift: Gift): void {
    if (gift.is_locked || !this.currentTurn?.current_turn) {
      return;
    }

    const stealData = {
      new_owner_id: this.currentTurn.current_turn
    };

    const loadingKey = `stealGift_${gift.id}`;

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.giftService.stealGift(gift.id, stealData)
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.successMessage = response.message;
          this.loadGifts(); // Refresh gifts list
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        } else {
          this.error = response.message;
        }
      },
      error: (error) => {
        console.error('Error stealing gift:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Handle gift steal count reset (admin override)
   */
  onResetGiftSteals(gift: Gift): void {
    const loadingKey = `resetGift_${gift.id}`;

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.giftService.resetGiftSteals(gift.id)
    ).subscribe({
      next: (response) => {
        this.successMessage = response.message;
        this.loadGifts(); // Refresh gifts list
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          this.successMessage = null;
        }, 3000);
      },
      error: (error) => {
        console.error('Error resetting gift steals:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Start the game
   */
  onStartGame(): void {
    const loadingKey = 'startGame';

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.gameService.startGame()
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.successMessage = response.message;
          this.loadCurrentTurn(); // Refresh turn information
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        } else {
          this.error = response.message;
        }
      },
      error: (error) => {
        console.error('Error starting game:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Advance to next turn
   */
  onNextTurn(): void {
    const loadingKey = 'advanceTurn';

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.gameService.advanceTurn()
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.successMessage = response.message;
          this.loadCurrentTurn(); // Refresh turn information
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        } else {
          this.error = response.message;
        }
      },
      error: (error) => {
        console.error('Error advancing turn:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Go back to previous turn
   */
  onPreviousTurn(): void {
    const loadingKey = 'previousTurn';

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.gameService.previousTurn()
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.successMessage = response.message;
          this.loadCurrentTurn(); // Refresh turn information
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        } else {
          this.error = response.message;
        }
      },
      error: (error) => {
        console.error('Error going to previous turn:', error);
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Get strike display for a gift
   */
  getStrikeDisplay(gift: Gift): string {
    if (gift.is_locked) {
      return 'LOCKED';
    }
    
    const strikes = '★'.repeat(gift.steal_count);
    return strikes || '';
  }

  /**
   * Get strike CSS class for styling
   */
  getStrikeCssClass(gift: Gift): string {
    if (gift.is_locked) {
      return 'locked';
    }
    if (gift.steal_count === 0) {
      return 'no-strikes';
    }
    return 'has-strikes';
  }

  /**
   * Get array of strike indicators for visual display
   */
  getStrikeIndicators(gift: Gift): boolean[] {
    const indicators = [false, false, false]; // 3 possible strikes
    for (let i = 0; i < Math.min(gift.steal_count, 3); i++) {
      indicators[i] = true;
    }
    return indicators;
  }

  /**
   * Get strike count text for display
   */
  getStrikeCountText(gift: Gift): string {
    if (gift.is_locked) {
      return 'LOCKED - No more steals allowed';
    }
    const remaining = 3 - gift.steal_count;
    if (remaining === 3) {
      return 'No steals yet - 3 steals allowed';
    }
    if (remaining === 1) {
      return `${gift.steal_count}/3 steals - 1 more steal will lock this gift`;
    }
    return `${gift.steal_count}/3 steals - ${remaining} more steals allowed`;
  }

  /**
   * Check if a gift can be stolen
   */
  canStealGift(gift: Gift): boolean {
    return !gift.is_locked && this.currentTurn?.current_turn !== null;
  }

  /**
   * Get tooltip text for gift stealing
   */
  getGiftTooltip(gift: Gift): string {
    if (gift.is_locked) {
      return 'This gift is locked and cannot be stolen anymore';
    }
    if (!this.currentTurn?.current_turn) {
      return 'No active turn - cannot steal gifts';
    }
    if (gift.current_owner === this.currentTurn.current_turn) {
      return 'You already own this gift';
    }
    return `Click to steal this gift (${3 - gift.steal_count} steals remaining before lock)`;
  }

  /**
   * Check if current turn is loading
   */
  get isCurrentTurnLoading(): boolean {
    return this.loadingService.isLoadingSync('loadCurrentTurn');
  }

  /**
   * Check if gifts are loading
   */
  get isGiftsLoading(): boolean {
    return this.loadingService.isLoadingSync('loadGifts');
  }

  /**
   * Check if adding gift is loading
   */
  get isAddingGift(): boolean {
    return this.loadingService.isLoadingSync('addGift');
  }

  /**
   * Check if starting game is loading
   */
  get isStartingGame(): boolean {
    return this.loadingService.isLoadingSync('startGame');
  }

  /**
   * Check if game can be started
   */
  get canStartGame(): boolean {
    return this.currentTurn?.game_phase === 'registration' && 
           this.currentTurn?.total_participants > 0;
  }

  /**
   * Check if game has started
   */
  get hasGameStarted(): boolean {
    return this.currentTurn?.game_phase === 'active' || 
           this.currentTurn?.game_phase === 'completed';
  }

  /**
   * Check if advancing turn is loading
   */
  get isAdvancingTurn(): boolean {
    return this.loadingService.isLoadingSync('advanceTurn');
  }

  /**
   * Check if going to previous turn is loading
   */
  get isGoingToPreviousTurn(): boolean {
    return this.loadingService.isLoadingSync('previousTurn');
  }

  /**
   * Check if we can go back to previous turn
   */
  get canGoToPreviousTurn(): boolean {
    if (!this.currentTurn || !this.currentTurn.turn_order.length) {
      return false;
    }
    
    // Can go back if:
    // 1. Game is completed (can go back from completed state)
    // 2. Current turn is not the first participant in turn order
    if (this.currentTurn.game_phase === 'completed') {
      return true;
    }
    
    if (this.currentTurn.current_turn === null) {
      return false;
    }
    
    const currentIndex = this.currentTurn.turn_order.indexOf(this.currentTurn.current_turn);
    return currentIndex > 0;
  }

  /**
   * Check if a specific gift is being stolen
   */
  isStealingGift(giftId: string): boolean {
    return this.loadingService.isLoadingSync(`stealGift_${giftId}`);
  }

  /**
   * Check if a specific gift is being reset
   */
  isResettingGift(giftId: string): boolean {
    return this.loadingService.isLoadingSync(`resetGift_${giftId}`);
  }

  /**
   * Retry loading current turn
   */
  retryLoadCurrentTurn(): void {
    this.loadCurrentTurn();
  }

  /**
   * Retry loading gifts
   */
  retryLoadGifts(): void {
    this.loadGifts();
  }

  /**
   * Dismiss error message
   */
  dismissError(): void {
    this.error = null;
  }

  /**
   * Silent refresh of all data (no loading indicators or error messages)
   */
  private silentRefresh(): void {
    this.silentLoadCurrentTurn();
    this.silentLoadGifts();
    this.silentLoadParticipants();
  }

  /**
   * Manual refresh with loading indicators
   */
  manualRefresh(): void {
    this.loadCurrentTurn();
    this.loadGifts();
    this.loadParticipants();
  }

  /**
   * Enter edit mode for a gift
   */
  startEditGift(gift: Gift): void {
    this.editingGiftId = gift.id;
    this.editGiftName = gift.name;
    this.editGiftError = null;
  }

  /**
   * Cancel editing and exit edit mode without saving
   */
  cancelEditGift(): void {
    this.editingGiftId = null;
    this.editGiftName = '';
    this.editGiftError = null;
  }

  /**
   * Check if a specific gift is in edit mode
   */
  isEditingGift(giftId: string): boolean {
    return this.editingGiftId === giftId;
  }

  /**
   * Validate gift name before saving
   * Returns true if valid, false otherwise and sets editGiftError
   */
  validateGiftName(name: string): boolean {
    // Check for empty name
    if (!name || name.trim().length === 0) {
      this.editGiftError = 'Gift name cannot be empty';
      return false;
    }

    // Check for length constraints (1-100 characters)
    const trimmedName = name.trim();
    if (trimmedName.length < 1) {
      this.editGiftError = 'Gift name must be at least 1 character';
      return false;
    }
    if (trimmedName.length > 100) {
      this.editGiftError = 'Gift name cannot exceed 100 characters';
      return false;
    }

    // Clear any previous errors
    this.editGiftError = null;
    return true;
  }

  /**
   * Save edited gift name
   */
  saveEditGift(giftId: string): void {
    // Validate the gift name
    if (!this.validateGiftName(this.editGiftName)) {
      return;
    }

    const trimmedName = this.editGiftName.trim();
    const loadingKey = `updateGiftName_${giftId}`;

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.giftService.updateGiftName(giftId, { name: trimmedName })
    ).subscribe({
      next: (response) => {
        if (response.success) {
          this.successMessage = response.message;
          
          // Update the gift in the local gifts array
          const giftIndex = this.gifts.findIndex(g => g.id === giftId);
          if (giftIndex !== -1) {
            this.gifts[giftIndex] = response.gift;
          }
          
          // Exit edit mode
          this.cancelEditGift();
          
          // Auto-refresh gifts list to ensure consistency
          this.loadGifts();
          
          // Clear success message after 3 seconds
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
        } else {
          this.editGiftError = response.message;
        }
      },
      error: (error) => {
        console.error('Error updating gift name:', error);
        this.editGiftError = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Check if a specific gift name is being updated
   */
  isUpdatingGiftName(giftId: string): boolean {
    return this.loadingService.isLoadingSync(`updateGiftName_${giftId}`);
  }
}
