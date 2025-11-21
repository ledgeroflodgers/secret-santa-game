import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { ErrorHandlingService } from './error-handling.service';

describe('ErrorHandlingService', () => {
  let service: ErrorHandlingService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ErrorHandlingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('processHttpError', () => {
    it('should handle client-side errors', () => {
      const error = new HttpErrorResponse({
        error: new ErrorEvent('Network error', { message: 'Connection failed' })
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toContain('Network error: Connection failed');
      expect(errorInfo.code).toBe('NETWORK_ERROR');
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userFriendly).toBe(true);
    });

    it('should handle timeout errors', () => {
      const error = new HttpErrorResponse({
        error: 'timeout'
      });
      (error as any).name = 'TimeoutError';

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toContain('Request timed out');
      expect(errorInfo.code).toBe('TIMEOUT');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should handle 400 Bad Request errors', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: { error: 'Invalid input data' }
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toBe('Invalid input data');
      expect(errorInfo.code).toBe('BAD_REQUEST');
      expect(errorInfo.retryable).toBe(false);
    });

    it('should handle 404 Not Found errors', () => {
      const error = new HttpErrorResponse({
        status: 404,
        error: { error: 'Resource not found' }
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toBe('Resource not found');
      expect(errorInfo.code).toBe('NOT_FOUND');
      expect(errorInfo.retryable).toBe(false);
    });

    it('should handle 409 Conflict errors', () => {
      const error = new HttpErrorResponse({
        status: 409,
        error: { error: 'Registration limit reached' }
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toBe('Registration limit reached');
      expect(errorInfo.code).toBe('CONFLICT');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should handle 429 Rate Limited errors', () => {
      const error = new HttpErrorResponse({
        status: 429
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toContain('Too many requests');
      expect(errorInfo.code).toBe('RATE_LIMITED');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should handle 500 Server errors', () => {
      const error = new HttpErrorResponse({
        status: 500
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toContain('Server error');
      expect(errorInfo.code).toBe('SERVER_ERROR');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should handle 503 Service Unavailable errors', () => {
      const error = new HttpErrorResponse({
        status: 503,
        error: { error: 'Service temporarily unavailable' }
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toBe('Service temporarily unavailable');
      expect(errorInfo.code).toBe('SERVICE_UNAVAILABLE');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should handle connection errors (status 0)', () => {
      const error = new HttpErrorResponse({
        status: 0
      });

      const errorInfo = service.processHttpError(error);

      expect(errorInfo.message).toContain('Unable to connect to server');
      expect(errorInfo.code).toBe('CONNECTION_ERROR');
      expect(errorInfo.retryable).toBe(true);
    });

    it('should add context to error messages', () => {
      const error = new HttpErrorResponse({
        status: 400,
        error: { error: 'Invalid data' }
      });

      const errorInfo = service.processHttpError(error, 'Registration');

      expect(errorInfo.message).toBe('Registration: Invalid data');
    });
  });

  describe('isRetryable', () => {
    it('should return true for retryable errors', () => {
      const errorInfo = {
        message: 'Server error',
        retryable: true,
        userFriendly: true
      };

      expect(service.isRetryable(errorInfo)).toBe(true);
    });

    it('should return false for non-retryable errors', () => {
      const errorInfo = {
        message: 'Bad request',
        retryable: false,
        userFriendly: true
      };

      expect(service.isRetryable(errorInfo)).toBe(false);
    });
  });

  describe('getRetryDelay', () => {
    it('should calculate exponential backoff delay', () => {
      expect(service.getRetryDelay(0, 1000)).toBe(1000);
      expect(service.getRetryDelay(1, 1000)).toBe(2000);
      expect(service.getRetryDelay(2, 1000)).toBe(4000);
      expect(service.getRetryDelay(3, 1000)).toBe(8000);
    });

    it('should cap delay at maximum value', () => {
      expect(service.getRetryDelay(10, 1000)).toBe(10000);
    });
  });

  describe('trackRetryAttempt', () => {
    it('should track retry attempts', () => {
      expect(service.trackRetryAttempt('test-operation')).toBe(1);
      expect(service.trackRetryAttempt('test-operation')).toBe(2);
      expect(service.trackRetryAttempt('test-operation')).toBe(3);
    });

    it('should track different operations separately', () => {
      expect(service.trackRetryAttempt('operation-1')).toBe(1);
      expect(service.trackRetryAttempt('operation-2')).toBe(1);
      expect(service.trackRetryAttempt('operation-1')).toBe(2);
    });
  });

  describe('resetRetryAttempts', () => {
    it('should reset retry attempts for an operation', () => {
      service.trackRetryAttempt('test-operation');
      service.trackRetryAttempt('test-operation');
      
      service.resetRetryAttempts('test-operation');
      
      expect(service.trackRetryAttempt('test-operation')).toBe(1);
    });
  });

  describe('getUserFriendlyMessage', () => {
    it('should extract message from Error object', () => {
      const error = new Error('Test error message');
      expect(service.getUserFriendlyMessage(error)).toBe('Test error message');
    });

    it('should return string errors as-is', () => {
      expect(service.getUserFriendlyMessage('String error')).toBe('String error');
    });

    it('should extract error property from objects', () => {
      const error = { error: 'Object error message' };
      expect(service.getUserFriendlyMessage(error)).toBe('Object error message');
    });

    it('should extract message property from objects', () => {
      const error = { message: 'Object message' };
      expect(service.getUserFriendlyMessage(error)).toBe('Object message');
    });

    it('should return default message for unknown error types', () => {
      expect(service.getUserFriendlyMessage(null)).toBe('An unexpected error occurred. Please try again.');
      expect(service.getUserFriendlyMessage(undefined)).toBe('An unexpected error occurred. Please try again.');
      expect(service.getUserFriendlyMessage({})).toBe('An unexpected error occurred. Please try again.');
    });
  });
});