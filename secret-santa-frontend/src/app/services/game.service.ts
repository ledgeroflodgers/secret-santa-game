import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry, timeout } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Participant {
  id: number;
  name: string;
  registration_timestamp: string;
}

export interface CurrentTurnResponse {
  current_turn: number | null;
  current_participant: Participant | null;
  game_phase: 'registration' | 'active' | 'completed';
  turn_order: number[];
  total_participants: number;
}

export interface AdvanceTurnResponse {
  success: boolean;
  message: string;
  current_turn: number | null;
  current_participant: Participant | null;
  game_phase: 'registration' | 'active' | 'completed';
}

export interface PreviousTurnResponse {
  success: boolean;
  message: string;
  current_turn: number | null;
  current_participant: Participant | null;
  game_phase: 'registration' | 'active' | 'completed';
}

@Injectable({
  providedIn: 'root'
})
export class GameService {
  private readonly baseUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  /**
   * Get the current turn information
   */
  getCurrentTurn(): Observable<CurrentTurnResponse> {
    return this.http.get<CurrentTurnResponse>(`${this.baseUrl}/game/current-turn`)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(2), // Retry up to 2 times for GET operations
        catchError(this.handleError)
      );
  }

  /**
   * Start the game
   */
  startGame(): Observable<AdvanceTurnResponse> {
    return this.http.put<AdvanceTurnResponse>(`${this.baseUrl}/game/start`, {})
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for PUT operations
        catchError(this.handleError)
      );
  }

  /**
   * Advance to the next turn
   */
  advanceTurn(): Observable<AdvanceTurnResponse> {
    return this.http.put<AdvanceTurnResponse>(`${this.baseUrl}/game/next-turn`, {})
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for PUT operations
        catchError(this.handleError)
      );
  }

  /**
   * Go back to the previous turn
   */
  previousTurn(): Observable<PreviousTurnResponse> {
    return this.http.put<PreviousTurnResponse>(`${this.baseUrl}/game/previous-turn`, {})
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for PUT operations
        catchError(this.handleError)
      );
  }

  /**
   * Handle HTTP errors with user-friendly messages
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Network error: ${error.error.message}`;
    } else if ((error as any).name === 'TimeoutError') {
      // Timeout error
      errorMessage = 'Request timed out. Please check your connection and try again.';
    } else {
      // Server-side error
      switch (error.status) {
        case 0:
          errorMessage = 'Unable to connect to server. Please check your connection.';
          break;
        case 400:
          errorMessage = error.error?.error || 'Invalid request. Cannot advance turn.';
          break;
        case 500:
          errorMessage = 'Server error. Please try again later.';
          break;
        case 503:
          errorMessage = error.error?.error || 'Service temporarily unavailable. Please try again.';
          break;
        default:
          errorMessage = error.error?.error || `Error Code: ${error.status}`;
      }
    }
    
    return throwError(() => new Error(errorMessage));
  }
}