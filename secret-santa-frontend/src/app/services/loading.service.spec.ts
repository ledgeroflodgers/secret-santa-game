import { TestBed } from '@angular/core/testing';
import { LoadingService } from './loading.service';
import { of, throwError, delay } from 'rxjs';

describe('LoadingService', () => {
  let service: LoadingService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LoadingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('setLoading', () => {
    it('should set loading state for a key', () => {
      service.setLoading('test-key', true);
      
      expect(service.isLoadingSync('test-key')).toBe(true);
    });

    it('should update loading state', () => {
      service.setLoading('test-key', true);
      service.setLoading('test-key', false);
      
      expect(service.isLoadingSync('test-key')).toBe(false);
    });
  });

  describe('isLoading', () => {
    it('should return observable of loading state', (done) => {
      service.setLoading('test-key', true);
      
      service.isLoading('test-key').subscribe(loading => {
        expect(loading).toBe(true);
        done();
      });
    });

    it('should emit updates when loading state changes', (done) => {
      let emissionCount = 0;
      const expectedValues = [false, true, false];
      
      service.isLoading('test-key').subscribe(loading => {
        expect(loading).toBe(expectedValues[emissionCount]);
        emissionCount++;
        
        if (emissionCount === expectedValues.length) {
          done();
        }
      });
      
      service.setLoading('test-key', true);
      service.setLoading('test-key', false);
    });
  });

  describe('isLoadingSync', () => {
    it('should return current loading state synchronously', () => {
      expect(service.isLoadingSync('test-key')).toBe(false);
      
      service.setLoading('test-key', true);
      expect(service.isLoadingSync('test-key')).toBe(true);
      
      service.setLoading('test-key', false);
      expect(service.isLoadingSync('test-key')).toBe(false);
    });
  });

  describe('isAnyLoading', () => {
    it('should return true when any operation is loading', (done) => {
      service.setLoading('key1', true);
      service.setLoading('key2', false);
      
      service.isAnyLoading().subscribe(anyLoading => {
        expect(anyLoading).toBe(true);
        done();
      });
    });

    it('should return false when no operations are loading', (done) => {
      service.setLoading('key1', false);
      service.setLoading('key2', false);
      
      service.isAnyLoading().subscribe(anyLoading => {
        expect(anyLoading).toBe(false);
        done();
      });
    });
  });

  describe('clearAll', () => {
    it('should clear all loading states', () => {
      service.setLoading('key1', true);
      service.setLoading('key2', true);
      
      service.clearAll();
      
      expect(service.isLoadingSync('key1')).toBe(false);
      expect(service.isLoadingSync('key2')).toBe(false);
    });
  });

  describe('clear', () => {
    it('should clear loading state for specific key', () => {
      service.setLoading('key1', true);
      service.setLoading('key2', true);
      
      service.clear('key1');
      
      expect(service.isLoadingSync('key1')).toBe(false);
      expect(service.isLoadingSync('key2')).toBe(true);
    });
  });

  describe('startLoading', () => {
    it('should start loading and return stop function', () => {
      const stopLoading = service.startLoading('test-key');
      
      expect(service.isLoadingSync('test-key')).toBe(true);
      
      stopLoading();
      
      expect(service.isLoadingSync('test-key')).toBe(false);
    });
  });

  describe('wrapWithLoading', () => {
    it('should set loading state during observable execution', (done) => {
      const source = of('test-value').pipe(delay(10));
      
      const wrapped = service.wrapWithLoading('test-key', source);
      
      // Should be loading immediately
      expect(service.isLoadingSync('test-key')).toBe(true);
      
      wrapped.subscribe({
        next: (value) => {
          expect(value).toBe('test-value');
        },
        complete: () => {
          // Should not be loading after completion
          expect(service.isLoadingSync('test-key')).toBe(false);
          done();
        }
      });
    });

    it('should clear loading state on error', (done) => {
      const source = throwError(() => new Error('Test error'));
      
      const wrapped = service.wrapWithLoading('test-key', source);
      
      expect(service.isLoadingSync('test-key')).toBe(true);
      
      wrapped.subscribe({
        error: (error) => {
          expect(error.message).toBe('Test error');
          expect(service.isLoadingSync('test-key')).toBe(false);
          done();
        }
      });
    });

    it('should clear loading state on unsubscribe', () => {
      const source = of('test-value').pipe(delay(100));
      
      const wrapped = service.wrapWithLoading('test-key', source);
      
      expect(service.isLoadingSync('test-key')).toBe(true);
      
      const subscription = wrapped.subscribe();
      subscription.unsubscribe();
      
      expect(service.isLoadingSync('test-key')).toBe(false);
    });
  });
});