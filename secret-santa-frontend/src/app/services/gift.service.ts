import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry, timeout } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Gift {
  id: string;
  name: string;
  steal_count: number;
  is_locked: boolean;
  current_owner: number | null;
  steal_history: number[];
}

export interface GiftResponse {
  gifts: Gift[];
}

export interface AddGiftRequest {
  name: string;
  owner_id?: number;
}

export interface StealGiftRequest {
  new_owner_id: number;
}

export interface StealGiftResponse {
  success: boolean;
  message: string;
  gift: Gift | null;
}

export interface ResetGiftResponse {
  success: boolean;
  message: string;
  gift: Gift;
}

export interface UpdateGiftNameRequest {
  name: string;
}

export interface UpdateGiftNameResponse {
  success: boolean;
  message: string;
  gift: Gift;
}

@Injectable({
  providedIn: 'root'
})
export class GiftService {
  private readonly baseUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) { }

  /**
   * Get all gifts with steal status information
   */
  getGifts(): Observable<GiftResponse> {
    return this.http.get<GiftResponse>(`${this.baseUrl}/gifts`)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(2), // Retry up to 2 times
        catchError(this.handleError)
      );
  }

  /**
   * Add a new gift to the pool
   */
  addGift(giftData: AddGiftRequest): Observable<Gift> {
    return this.http.post<Gift>(`${this.baseUrl}/gifts`, giftData)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for POST operations
        catchError(this.handleError)
      );
  }

  /**
   * Record a gift steal
   */
  stealGift(giftId: string, stealData: StealGiftRequest): Observable<StealGiftResponse> {
    return this.http.put<StealGiftResponse>(`${this.baseUrl}/gifts/${giftId}/steal`, stealData)
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for PUT operations
        catchError(this.handleError)
      );
  }

  /**
   * Reset a gift's steal count to 0 (admin override)
   */
  resetGiftSteals(giftId: string): Observable<ResetGiftResponse> {
    return this.http.put<ResetGiftResponse>(`${this.baseUrl}/gifts/${giftId}/reset-steals`, {})
      .pipe(
        timeout(10000), // 10 second timeout
        retry(1), // Retry once for PUT operations
        catchError(this.handleError)
      );
  }

  /**
   * Update a gift's name
   */
  updateGiftName(giftId: string, nameData: UpdateGiftNameRequest): Observable<UpdateGiftNameResponse> {
    return this.http.put<UpdateGiftNameResponse>(`${this.baseUrl}/gifts/${giftId}/name`, nameData)
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
          errorMessage = error.error?.error || 'Invalid request. Please check your input.';
          break;
        case 404:
          errorMessage = error.error?.error || 'Gift not found.';
          break;
        case 409:
          errorMessage = error.error?.error || 'Gift cannot be stolen - it may be locked.';
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