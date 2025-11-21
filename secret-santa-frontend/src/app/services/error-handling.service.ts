import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { mergeMap, finalize } from 'rxjs/operators';

export interface ErrorInfo {
  message: string;
  code?: string | number;
  retryable: boolean;
  userFriendly: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ErrorHandlingService {
  private retryAttempts = new Map<string, number>();

  constructor() { }

  /**
   * Process HTTP errors and return user-friendly error information
   */
  processHttpError(error: HttpErrorResponse, context?: string): ErrorInfo {
    let errorInfo: ErrorInfo = {
      message: 'An unknown error occurred',
      retryable: false,
      userFriendly: true
    };

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorInfo = {
        message: `Network error: ${error.error.message}`,
        code: 'NETWORK_ERROR',
        retryable: true,
        userFriendly: true
      };
    } else if ((error as any).name === 'TimeoutError') {
      // Timeout error
      errorInfo = {
        message: 'Request timed out. Please check your connection and try again.',
        code: 'TIMEOUT',
        retryable: true,
        userFriendly: true
      };
    } else {
      // Server-side error
      switch (error.status) {
        case 0:
          errorInfo = {
            message: 'Unable to connect to server. Please check your connection.',
            code: 'CONNECTION_ERROR',
            retryable: true,
            userFriendly: true
          };
          break;
        case 400:
          errorInfo = {
            message: error.error?.error || 'Invalid request. Please check your input.',
            code: 'BAD_REQUEST',
            retryable: false,
            userFriendly: true
          };
          break;
        case 404:
          errorInfo = {
            message: error.error?.error || 'Resource not found.',
            code: 'NOT_FOUND',
            retryable: false,
            userFriendly: true
          };
          break;
        case 409:
          errorInfo = {
            message: error.error?.error || 'Conflict occurred. Please try again.',
            code: 'CONFLICT',
            retryable: true,
            userFriendly: true
          };
          break;
        case 429:
          errorInfo = {
            message: 'Too many requests. Please wait a moment and try again.',
            code: 'RATE_LIMITED',
            retryable: true,
            userFriendly: true
          };
          break;
        case 500:
          errorInfo = {
            message: 'Server error. Please try again later.',
            code: 'SERVER_ERROR',
            retryable: true,
            userFriendly: true
          };
          break;
        case 503:
          errorInfo = {
            message: error.error?.error || 'Service temporarily unavailable. Please try again.',
            code: 'SERVICE_UNAVAILABLE',
            retryable: true,
            userFriendly: true
          };
          break;
        default:
          errorInfo = {
            message: error.error?.error || `Error Code: ${error.status}`,
            code: error.status,
            retryable: error.status >= 500,
            userFriendly: true
          };
      }
    }

    // Add context to error message if provided
    if (context) {
      errorInfo.message = `${context}: ${errorInfo.message}`;
    }

    return errorInfo;
  }

  /**
   * Create a retry mechanism with exponential backoff
   */
  retryWithBackoff<T>(
    source: Observable<T>,
    maxRetries: number = 3,
    initialDelay: number = 1000,
    maxDelay: number = 10000,
    backoffMultiplier: number = 2
  ): Observable<T> {
    return source.pipe(
      mergeMap((value, index) => {
        if (index === 0) {
          return [value];
        }
        
        const delay = Math.min(initialDelay * Math.pow(backoffMultiplier, index - 1), maxDelay);
        return timer(delay).pipe(mergeMap(() => [value]));
      }),
      finalize(() => {
        // Clean up retry attempts tracking if needed
      })
    );
  }

  /**
   * Check if an error is retryable based on error info
   */
  isRetryable(errorInfo: ErrorInfo): boolean {
    return errorInfo.retryable;
  }

  /**
   * Get retry delay based on attempt number
   */
  getRetryDelay(attempt: number, baseDelay: number = 1000): number {
    return Math.min(baseDelay * Math.pow(2, attempt), 10000); // Max 10 seconds
  }

  /**
   * Track retry attempts for a specific operation
   */
  trackRetryAttempt(operationId: string): number {
    const currentAttempts = this.retryAttempts.get(operationId) || 0;
    const newAttempts = currentAttempts + 1;
    this.retryAttempts.set(operationId, newAttempts);
    return newAttempts;
  }

  /**
   * Reset retry attempts for a specific operation
   */
  resetRetryAttempts(operationId: string): void {
    this.retryAttempts.delete(operationId);
  }

  /**
   * Get user-friendly error message for display
   */
  getUserFriendlyMessage(error: any): string {
    if (error instanceof Error) {
      return error.message;
    }
    
    if (typeof error === 'string') {
      return error;
    }
    
    if (error?.error) {
      return error.error;
    }
    
    if (error?.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred. Please try again.';
  }
}