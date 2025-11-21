import { Component, OnInit, OnDestroy } from '@angular/core';
import { Participant, ParticipantService } from '../services/participant.service';
import { interval, Subscription } from 'rxjs';
import { startWith, switchMap } from 'rxjs/operators';
import { LoadingService } from '../services/loading.service';
import { ErrorHandlingService } from '../services/error-handling.service';

@Component({
  selector: 'app-participants',
  templateUrl: './participants.component.html',
  styleUrls: ['./participants.component.css']
})
export class ParticipantsComponent implements OnInit, OnDestroy {
  participants: Participant[] = [];
  loading = true;
  error: string | null = null;
  private refreshSubscription?: Subscription;
  private readonly REFRESH_INTERVAL = 5000; // 5 seconds

  constructor(
    private participantService: ParticipantService,
    private loadingService: LoadingService,
    private errorHandlingService: ErrorHandlingService
  ) {}

  ngOnInit(): void {
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  /**
   * Start auto-refresh functionality to show real-time updates
   */
  private startAutoRefresh(): void {
    this.refreshSubscription = interval(this.REFRESH_INTERVAL)
      .pipe(
        startWith(0), // Start immediately
        switchMap(() => this.loadingService.wrapWithLoading(
          'loadParticipants',
          this.participantService.getParticipants()
        ))
      )
      .subscribe({
        next: (participants) => {
          this.participants = participants.sort((a, b) => a.id - b.id); // Sort by participant number
          this.loading = false;
          this.error = null;
        },
        error: (error) => {
          this.error = this.errorHandlingService.getUserFriendlyMessage(error);
          this.loading = false;
          console.error('Error fetching participants:', error);
        }
      });
  }

  /**
   * Stop auto-refresh when component is destroyed
   */
  private stopAutoRefresh(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  /**
   * Manual refresh functionality
   */
  refreshParticipants(): void {
    this.loading = true;
    this.error = null;
    
    this.loadingService.wrapWithLoading(
      'refreshParticipants',
      this.participantService.getParticipants()
    ).subscribe({
      next: (participants) => {
        this.participants = participants.sort((a, b) => a.id - b.id);
        this.loading = false;
      },
      error: (error) => {
        this.error = this.errorHandlingService.getUserFriendlyMessage(error);
        this.loading = false;
        console.error('Error refreshing participants:', error);
      }
    });
  }

  /**
   * Get formatted registration time
   */
  getFormattedTime(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  /**
   * TrackBy function for ngFor to improve performance
   */
  trackByParticipantId(index: number, participant: Participant): number {
    return participant.id;
  }

  /**
   * Check if participants are loading
   */
  get isParticipantsLoading(): boolean {
    return this.loadingService.isLoadingSync('loadParticipants') || 
           this.loadingService.isLoadingSync('refreshParticipants');
  }

  /**
   * Retry loading participants
   */
  retryLoadParticipants(): void {
    this.refreshParticipants();
  }

  /**
   * Dismiss error message
   */
  dismissError(): void {
    this.error = null;
  }
}
