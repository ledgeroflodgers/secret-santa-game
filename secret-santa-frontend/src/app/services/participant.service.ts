import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map, retry, timeout } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Participant {
  id: number;
  name: string;
  registration_timestamp: string;
}

export interface ParticipantRegistrationRequest {
  name: string;
}

export interface ParticipantRegistrationResponse {
  success: boolean;
  participant?: Participant;
  message?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ParticipantService {
  private readonly baseUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  /**
   * Register a new participant
   */
  registerParticipant(name: string): Observable<ParticipantRegistrationResponse> {
    const request: ParticipantRegistrationRequest = { name: name.trim() };
    
    return this.http.post<Participant>(`${this.baseUrl}/participants`, request)
      .pipe(
        timeout(15000), // 15 second timeout for registration
        retry(1), // Retry once for registration failures
        map(participant => ({
          success: true,
          participant: participant,
          message: `Registration successful! You have been assigned number ${participant.id}.`
        })),
        catchError((error: HttpErrorResponse) => {
          // Transform error into ParticipantRegistrationResponse format
          let errorMessage = 'Registration failed. Please try again.';
          
          if (error.error instanceof ErrorEvent) {
            errorMessage = `Network error: ${error.error.message}`;
          } else if ((error as any).name === 'TimeoutError') {
            errorMessage = 'Registration timed out. Please check your connection and try again.';
          } else {
            switch (error.status) {
              case 0:
                errorMessage = 'Unable to connect to server. Please check your connection.';
                break;
              case 400:
                errorMessage = error.error?.error || 'Invalid request. Please check your input.';
                break;
              case 409:
                errorMessage = error.error?.error || 'Registration limit reached or duplicate entry.';
                break;
              case 503:
                errorMessage = error.error?.error || 'Registration temporarily unavailable due to high traffic. Please try again.';
                break;
              case 500:
                errorMessage = 'Server error. Please try again later.';
                break;
              default:
                errorMessage = error.error?.error || `Error Code: ${error.status}`;
            }
          }
          
          return throwError(() => ({
            success: false,
            error: errorMessage
          } as ParticipantRegistrationResponse));
        })
      );
  }

  /**
   * Get all registered participants
   */
  getParticipants(): Observable<Participant[]> {
    return this.http.get<{participants: Participant[]}>(`${this.baseUrl}/participants`)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(2), // Retry up to 2 times
        map(response => response.participants),
        catchError(this.handleError)
      );
  }

  /**
   * Get current participant count
   */
  getParticipantCount(): Observable<number> {
    return this.http.get<{ count: number; max_participants: number }>(`${this.baseUrl}/participants/count`)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(2), // Retry up to 2 times
        map(response => response.count),
        catchError(this.handleError)
      );
  }

  /**
   * Handle HTTP errors
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
          errorMessage = error.error?.error || 'Invalid request. Please check your input.';
          break;
        case 409:
          errorMessage = error.error?.error || 'Registration limit reached or duplicate entry.';
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