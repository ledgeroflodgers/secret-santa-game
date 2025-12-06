import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { GiftService, Gift } from '../services/gift.service';
import { ErrorHandlingService } from '../services/error-handling.service';

@Component({
  selector: 'app-mobile-gift-display',
  templateUrl: './mobile-gift-display.component.html',
  styleUrls: ['./mobile-gift-display.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MobileGiftDisplayComponent implements OnInit, OnDestroy {
  // Core data properties
  gifts: Gift[] = [];
  loading: boolean = true;
  error: string | null = null;
  
  // Track gifts being removed for explosion animation
  explodingGiftIds: Set<string> = new Set();
  
  // Real-time update properties
  private refreshInterval: any;
  private readonly REFRESH_INTERVAL_MS = 2000; // 2 seconds as per requirements
  private giftSubscription: Subscription | null = null;
  
  // Error handling and retry properties
  public retryCount: number = 0;
  public readonly MAX_RETRY_ATTEMPTS = 5;
  public isRetrying: boolean = false;
  
  // Network connectivity properties
  private isOnline: boolean = navigator.onLine;
  private networkStatusSubscription: Subscription | null = null;
  private connectionRetryTimeout: any;
  private lastSuccessfulUpdate: Date | null = null;
  
  // Performance optimization properties
  private orientationChangeTimeout: any;
  private resizeTimeout: any;
  private readonly DEBOUNCE_DELAY = 150; // ms
  
  // Change detection optimization
  private lastGiftsHash: string = '';
  private lastLayoutHash: string = '';
  
  // Layout calculation properties
  gridColumns: number = 1;
  gridRows: number = 1;
  private currentOrientation: 'portrait' | 'landscape' = 'portrait';

  constructor(
    private giftService: GiftService,
    private errorHandlingService: ErrorHandlingService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // Initialize component and start loading gifts
    this.detectOrientation();
    this.setupNetworkConnectivityListener();
    this.loadGifts();
    this.startRealTimeUpdates();
    
    // Listen for orientation changes with debouncing
    this.setupOrientationListener();
    
    // Listen for resize events with debouncing
    this.setupResizeListener();
  }

  ngOnDestroy(): void {
    // Clean up all subscriptions and intervals
    this.stopRealTimeUpdates();
    
    if (this.giftSubscription) {
      this.giftSubscription.unsubscribe();
      this.giftSubscription = null;
    }
    
    if (this.networkStatusSubscription) {
      this.networkStatusSubscription.unsubscribe();
      this.networkStatusSubscription = null;
    }
    
    // Clean up event listener timeouts
    if (this.orientationChangeTimeout) {
      clearTimeout(this.orientationChangeTimeout);
    }
    
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout);
    }
    
    if (this.connectionRetryTimeout) {
      clearTimeout(this.connectionRetryTimeout);
    }
    
    // Remove event listeners to prevent memory leaks
    window.removeEventListener('orientationchange', this.handleOrientationChange);
    window.removeEventListener('resize', this.handleResize);
    window.removeEventListener('online', this.handleOnlineStatus);
    window.removeEventListener('offline', this.handleOfflineStatus);
    
    // Reset error handling state
    this.errorHandlingService.resetRetryAttempts('mobile-gift-display');
  }

  /**
   * Load gifts from the API
   */
  private loadGifts(): void {
    // Don't make new requests if already loading (prevent duplicate calls)
    if (this.loading && this.giftSubscription) {
      return;
    }

    this.loading = true;
    this.error = null;

    this.giftSubscription = this.giftService.getGifts().subscribe({
      next: (response) => {
        const allGifts = response.gifts || [];
        // Find gifts that just got locked (stolen 3+ times)
        const lockedGifts = allGifts.filter(gift => gift.steal_count >= 3 || gift.is_locked);
        const currentGiftIds = new Set(this.gifts.map(g => g.id));
        
        // Detect newly locked gifts that were previously visible
        const newlyLockedGifts = lockedGifts.filter(gift => currentGiftIds.has(gift.id) && !this.explodingGiftIds.has(gift.id));
        
        // Trigger explosion animation for newly locked gifts
        if (newlyLockedGifts.length > 0) {
          newlyLockedGifts.forEach(gift => {
            this.explodingGiftIds.add(gift.id);
          });
          
          // Set loading to false immediately
          this.loading = false;
          this.error = null;
          this.retryCount = 0;
          this.isRetrying = false;
          this.lastSuccessfulUpdate = new Date();
          this.errorHandlingService.resetRetryAttempts('mobile-gift-display');
          this.cdr.markForCheck();
          
          // Remove exploding gifts after animation completes (600ms)
          setTimeout(() => {
            newlyLockedGifts.forEach(gift => {
              this.explodingGiftIds.delete(gift.id);
            });
            // Now filter and update the gifts list
            const visibleGifts = allGifts.filter(gift => gift.steal_count < 3 && !gift.is_locked);
            this.gifts = visibleGifts;
            this.lastGiftsHash = this.generateGiftsHash(visibleGifts);
            this.calculateGridLayout();
            this.cdr.markForCheck();
          }, 600);
          return;
        }
        
        // Filter out locked gifts (stolen 3+ times) - they disappear from display
        const newGifts = allGifts.filter(gift => gift.steal_count < 3 && !gift.is_locked);
        
        // Check if gifts have actually changed to minimize unnecessary updates
        if (this.hasGiftsChanged(newGifts)) {
          this.gifts = newGifts;
          this.lastGiftsHash = this.generateGiftsHash(newGifts);
          
          // Recalculate grid layout when gifts change
          this.calculateGridLayout();
          
          // Trigger change detection for OnPush strategy
          this.cdr.markForCheck();
        }
        
        this.loading = false;
        this.error = null;
        this.retryCount = 0;
        this.isRetrying = false;
        this.lastSuccessfulUpdate = new Date();
        
        // Reset retry attempts on successful load
        this.errorHandlingService.resetRetryAttempts('mobile-gift-display');
        
        // Trigger change detection for loading/error state changes
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.loading = false;
        this.handleLoadError(error);
        // Trigger change detection for error state
        this.cdr.markForCheck();
      }
    });
  }

  /**
   * Start real-time updates with polling mechanism and network recovery
   */
  private startRealTimeUpdates(): void {
    // Clear any existing interval
    this.stopRealTimeUpdates();
    
    // Set up polling interval for real-time updates
    this.refreshInterval = setInterval(() => {
      // Only poll if online, not currently loading, and not in retry mode
      if (this.isOnline && !this.loading && !this.isRetrying) {
        this.loadGifts();
      }
      
      // If we have an error but it's been a while, try to recover (only if online)
      if (this.error && !this.loading && !this.isRetrying && this.isOnline) {
        // Auto-recovery after some time has passed since last successful update
        const shouldAutoRecover = this.retryCount < this.MAX_RETRY_ATTEMPTS;
        const timeSinceLastSuccess = this.lastSuccessfulUpdate ? 
          Date.now() - this.lastSuccessfulUpdate.getTime() : 
          Infinity;
        
        // Auto-recover if it's been more than 30 seconds since last success
        if (shouldAutoRecover && timeSinceLastSuccess > 30000) {
          this.retryLoading();
        }
      }
      
      // If we're offline but the browser says we're online, check connectivity
      if (!this.isOnline && navigator.onLine) {
        this.isOnline = true;
        this.handleOnlineStatus();
      }
    }, this.REFRESH_INTERVAL_MS);
  }

  /**
   * Check if gifts have changed to minimize unnecessary updates
   */
  private hasGiftsChanged(newGifts: Gift[]): boolean {
    const newHash = this.generateGiftsHash(newGifts);
    return newHash !== this.lastGiftsHash;
  }

  /**
   * Generate a hash of the gifts array for change detection
   */
  private generateGiftsHash(gifts: Gift[]): string {
    return JSON.stringify(gifts.map(gift => ({
      id: gift.id,
      name: gift.name,
      steal_count: gift.steal_count,
      is_locked: gift.is_locked,
      current_owner: gift.current_owner
    })));
  }

  /**
   * Handle errors from gift loading with retry logic and exponential backoff
   */
  private handleLoadError(error: any): void {
    const errorInfo = this.errorHandlingService.processHttpError(error, 'Loading gifts');
    
    // Check if this is a network connectivity issue
    const isNetworkError = !this.isOnline || 
                          error.status === 0 || 
                          error.name === 'TimeoutError' ||
                          errorInfo.code === 'NETWORK_ERROR' ||
                          errorInfo.code === 'CONNECTION_ERROR';
    
    // Set appropriate error message based on network status
    if (!this.isOnline) {
      this.error = 'No internet connection. Waiting for connection to be restored...';
    } else if (isNetworkError) {
      this.error = 'Connection problem. Checking network status...';
    } else {
      this.error = errorInfo.message;
    }
    
    // Implement retry logic for retryable errors
    if (errorInfo.retryable && this.retryCount < this.MAX_RETRY_ATTEMPTS && this.isOnline) {
      this.retryCount++;
      this.isRetrying = true;
      
      // Calculate exponential backoff delay with jitter to avoid thundering herd
      const baseDelay = this.errorHandlingService.getRetryDelay(this.retryCount, 1000);
      const jitter = Math.random() * 500; // Add up to 500ms jitter
      const retryDelay = baseDelay + jitter;
      
      // Update error message to show retry attempt
      if (this.isOnline) {
        this.error = `${errorInfo.message} Retrying in ${Math.ceil(retryDelay / 1000)} seconds... (Attempt ${this.retryCount}/${this.MAX_RETRY_ATTEMPTS})`;
      }
      this.cdr.markForCheck();
      
      // Schedule retry with exponential backoff
      this.connectionRetryTimeout = setTimeout(() => {
        if (!this.loading && this.isOnline) { // Only retry if not already loading and online
          this.loadGifts();
        }
      }, retryDelay);
      
    } else if (this.retryCount >= this.MAX_RETRY_ATTEMPTS) {
      // Max retries reached
      this.error = `${errorInfo.message} Maximum retry attempts reached. Please check your connection and refresh the page.`;
      this.isRetrying = false;
      this.cdr.markForCheck();
      
    } else if (!this.isOnline) {
      // Device is offline - don't retry until connection is restored
      this.isRetrying = false;
      this.cdr.markForCheck();
      
    } else {
      // Non-retryable error
      this.isRetrying = false;
      this.cdr.markForCheck();
    }
  }

  /**
   * Manual retry method for user-initiated retries
   */
  public retryLoading(): void {
    // Check network connectivity before retrying
    if (!this.isOnline) {
      this.error = 'No internet connection. Please check your network and try again.';
      this.cdr.markForCheck();
      return;
    }
    
    this.retryCount = 0;
    this.isRetrying = false;
    this.error = null;
    this.errorHandlingService.resetRetryAttempts('mobile-gift-display');
    
    // Clear any pending retry timeouts
    if (this.connectionRetryTimeout) {
      clearTimeout(this.connectionRetryTimeout);
      this.connectionRetryTimeout = null;
    }
    
    this.loadGifts();
  }

  /**
   * Check if the component is in a recoverable error state
   */
  public canRetry(): boolean {
    return this.error !== null && !this.loading && !this.isRetrying && this.isOnline;
  }

  /**
   * Stop real-time updates
   */
  private stopRealTimeUpdates(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  /**
   * Detect current screen orientation
   */
  private detectOrientation(): void {
    const width = window.innerWidth;
    const height = window.innerHeight;
    this.currentOrientation = width > height ? 'landscape' : 'portrait';
  }

  /**
   * Calculate optimal grid layout based on gift count and screen orientation
   */
  private calculateGridLayout(): void {
    const giftCount = this.gifts.length;
    
    if (giftCount === 0) {
      this.gridColumns = 1;
      this.gridRows = 1;
      return;
    }

    const layout = this.getOptimalLayout(giftCount, this.currentOrientation);
    const newLayoutHash = `${layout.columns}x${layout.rows}-${this.currentOrientation}-${giftCount}`;
    
    // Only update layout if it has actually changed to minimize DOM updates
    if (newLayoutHash !== this.lastLayoutHash) {
      this.gridColumns = layout.columns;
      this.gridRows = layout.rows;
      this.lastLayoutHash = newLayoutHash;
      
      // Mark for check only when layout actually changes
      this.cdr.markForCheck();
    }
  }

  /**
   * Get optimal layout configuration for given gift count and orientation
   */
  private getOptimalLayout(giftCount: number, orientation: 'portrait' | 'landscape'): { columns: number; rows: number } {
    if (giftCount === 1) {
      return { columns: 1, rows: 1 };
    }

    if (giftCount === 2) {
      // For 2 gifts, prefer horizontal split in landscape, vertical in portrait
      return orientation === 'landscape' 
        ? { columns: 2, rows: 1 }
        : { columns: 1, rows: 2 };
    }

    // For 3+ gifts, calculate based on aspect ratio and orientation
    const aspectRatio = window.innerWidth / window.innerHeight;
    
    // Calculate square root as starting point
    const sqrt = Math.sqrt(giftCount);
    let columns = Math.ceil(sqrt);
    let rows = Math.ceil(giftCount / columns);

    // Adjust based on orientation and aspect ratio
    if (orientation === 'landscape') {
      // In landscape, prefer more columns than rows
      while (columns * (rows - 1) >= giftCount && rows > 1) {
        rows--;
      }
      
      // If aspect ratio is very wide, add more columns
      if (aspectRatio > 2.0 && columns < giftCount) {
        columns = Math.min(columns + 1, giftCount);
        rows = Math.ceil(giftCount / columns);
      }
    } else {
      // In portrait, prefer more rows than columns
      while ((columns - 1) * rows >= giftCount && columns > 1) {
        columns--;
      }
      
      // If aspect ratio is very tall, add more rows
      if (aspectRatio < 0.6 && rows < giftCount) {
        rows = Math.min(rows + 1, giftCount);
        columns = Math.ceil(giftCount / rows);
      }
    }

    // Ensure we don't have empty cells if possible
    while (columns * rows > giftCount + Math.min(columns, rows) && (columns > 1 || rows > 1)) {
      if (orientation === 'landscape' && rows > 1) {
        rows--;
      } else if (orientation === 'portrait' && columns > 1) {
        columns--;
      } else if (rows > columns) {
        rows--;
      } else {
        columns--;
      }
    }

    // Final validation - ensure we can fit all gifts
    while (columns * rows < giftCount) {
      if (orientation === 'landscape') {
        columns++;
      } else {
        rows++;
      }
    }

    return { columns, rows };
  }

  /**
   * Get CSS grid template values for current layout
   */
  public getGridTemplateColumns(): string {
    return `repeat(${this.gridColumns}, 1fr)`;
  }

  /**
   * Get CSS grid template rows for current layout
   */
  public getGridTemplateRows(): string {
    return `repeat(${this.gridRows}, 1fr)`;
  }

  /**
   * Calculate responsive font size based on grid layout and viewport
   */
  public getResponsiveFontSize(): string {
    const cellHeight = window.innerHeight / this.gridRows;
    const cellWidth = window.innerWidth / this.gridColumns;
    const minCellSize = Math.min(cellHeight, cellWidth);
    const viewportMin = Math.min(window.innerWidth, window.innerHeight);
    
    // Base calculation using cell size
    let fontSize = minCellSize * 0.15;
    
    // Adjust based on viewport size for better scaling
    const viewportFactor = viewportMin / 400; // 400px as reference
    fontSize *= Math.max(0.7, Math.min(1.5, viewportFactor));
    
    // Apply constraints based on screen size
    let minSize = 12;
    let maxSize = 48;
    
    if (window.innerWidth <= 320) {
      minSize = 8;
      maxSize = 24;
    } else if (window.innerWidth <= 480) {
      minSize = 10;
      maxSize = 32;
    } else if (window.innerWidth >= 1200) {
      minSize = 16;
      maxSize = 64;
    }
    
    // Ensure font size is within bounds
    fontSize = Math.max(minSize, Math.min(maxSize, fontSize));
    
    return `${Math.round(fontSize)}px`;
  }

  /**
   * Color status constants for gift status indication
   */
  private readonly GIFT_STATUS_COLORS = {
    fresh: { background: '#4CAF50', color: '#FFFFFF' },      // Green bg, white text
    stolen_once: { background: '#FFEB3B', color: '#424242' }, // Yellow bg, dark grey text
    stolen_twice: { background: '#F44336', color: '#FFFFFF' }, // Red bg, white text
    locked: { background: '#9E9E9E', color: '#FFFFFF' }       // Grey bg, white text
  } as const;

  /**
   * Determine gift status based on steal count
   */
  public getGiftStatus(gift: Gift): keyof typeof this.GIFT_STATUS_COLORS {
    if (gift.steal_count === 0) return 'fresh';
    if (gift.steal_count === 1) return 'stolen_once';
    if (gift.steal_count === 2) return 'stolen_twice';
    return 'locked'; // 3+ steals
  }

  /**
   * Get CSS class name for gift status
   */
  public getGiftStatusClass(gift: Gift): string {
    const status = this.getGiftStatus(gift);
    return `gift-status-${status}`;
  }

  /**
   * Get background color for gift status
   */
  public getGiftBackgroundColor(gift: Gift): string {
    const status = this.getGiftStatus(gift);
    return this.GIFT_STATUS_COLORS[status].background;
  }

  /**
   * Get text color for gift status
   */
  public getGiftTextColor(gift: Gift): string {
    const status = this.getGiftStatus(gift);
    return this.GIFT_STATUS_COLORS[status].color;
  }

  /**
   * Get human-readable status description for accessibility
   */
  public getGiftStatusDescription(gift: Gift): string {
    const count = gift.steal_count;
    if (count === 0) return 'fresh gift, not stolen';
    if (count === 1) return 'stolen once';
    if (count === 2) return 'stolen twice';
    if (count >= 3) return 'locked after multiple steals';
    return `stolen ${count} times`;
  }

  /**
   * Setup debounced orientation change listener for performance optimization
   */
  private setupOrientationListener(): void {
    this.handleOrientationChange = this.handleOrientationChange.bind(this);
    window.addEventListener('orientationchange', this.handleOrientationChange);
  }

  /**
   * Setup debounced resize listener for performance optimization
   */
  private setupResizeListener(): void {
    this.handleResize = this.handleResize.bind(this);
    window.addEventListener('resize', this.handleResize);
  }

  /**
   * Setup network connectivity listener for online/offline detection
   */
  private setupNetworkConnectivityListener(): void {
    this.handleOnlineStatus = this.handleOnlineStatus.bind(this);
    this.handleOfflineStatus = this.handleOfflineStatus.bind(this);
    
    window.addEventListener('online', this.handleOnlineStatus);
    window.addEventListener('offline', this.handleOfflineStatus);
    
    // Initial network status check
    this.isOnline = navigator.onLine;
  }

  /**
   * Debounced orientation change handler to minimize unnecessary recalculations
   */
  private handleOrientationChange = (): void => {
    if (this.orientationChangeTimeout) {
      clearTimeout(this.orientationChangeTimeout);
    }
    
    this.orientationChangeTimeout = setTimeout(() => {
      const previousOrientation = this.currentOrientation;
      this.detectOrientation();
      
      // Only recalculate if orientation actually changed
      if (previousOrientation !== this.currentOrientation) {
        this.calculateGridLayout();
      }
    }, this.DEBOUNCE_DELAY);
  };

  /**
   * Debounced resize handler to minimize unnecessary recalculations
   */
  private handleResize = (): void => {
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout);
    }
    
    this.resizeTimeout = setTimeout(() => {
      const previousOrientation = this.currentOrientation;
      this.detectOrientation();
      
      // Only recalculate if orientation changed or significant size change
      if (previousOrientation !== this.currentOrientation) {
        this.calculateGridLayout();
      }
    }, this.DEBOUNCE_DELAY);
  };

  /**
   * Handle online status change - connection restored
   */
  private handleOnlineStatus = (): void => {
    const wasOffline = !this.isOnline;
    this.isOnline = true;
    
    if (wasOffline) {
      // Connection restored - clear error state and retry loading
      this.error = null;
      this.retryCount = 0;
      this.isRetrying = false;
      this.errorHandlingService.resetRetryAttempts('mobile-gift-display');
      
      // Immediate retry when connection is restored
      this.loadGifts();
      
      // Trigger change detection
      this.cdr.markForCheck();
    }
  };

  /**
   * Handle offline status change - connection lost
   */
  private handleOfflineStatus = (): void => {
    this.isOnline = false;
    
    // Update error message to indicate offline status
    this.error = 'No internet connection. Please check your network and try again.';
    this.loading = false;
    
    // Stop real-time updates while offline
    this.stopRealTimeUpdates();
    
    // Trigger change detection
    this.cdr.markForCheck();
  };

  /**
   * Check if device is currently online
   */
  public isDeviceOnline(): boolean {
    return this.isOnline;
  }

  /**
   * Get network status description for accessibility
   */
  public getNetworkStatusDescription(): string {
    return this.isOnline ? 'Connected' : 'Offline';
  }

  /**
   * Get loading state description for accessibility
   */
  public getLoadingStateDescription(): string {
    if (this.loading && this.isRetrying) {
      return `Loading gifts, reconnecting, attempt ${this.retryCount} of ${this.MAX_RETRY_ATTEMPTS}`;
    } else if (this.loading) {
      return 'Loading gifts, please wait';
    }
    return '';
  }

  /**
   * Get error state description for accessibility
   */
  public getErrorStateDescription(): string {
    if (!this.error) return '';
    
    let description = `Error occurred: ${this.error}`;
    if (!this.isOnline) {
      description += '. Device is currently offline.';
    } else if (this.canRetry()) {
      description += '. Retry option is available.';
    }
    return description;
  }

  /**
   * Get empty state description for accessibility
   */
  public getEmptyStateDescription(): string {
    return 'No gifts available yet. Waiting for the game administrator to add gifts. Updates will appear automatically when connected.';
  }

  /**
   * Track by function for ngFor to optimize rendering performance
   */
  public trackByGiftId(index: number, gift: Gift): string {
    return gift.id;
  }

  /**
   * Check if a gift is currently exploding (being removed)
   */
  public isExploding(gift: Gift): boolean {
    return this.explodingGiftIds.has(gift.id);
  }
}
