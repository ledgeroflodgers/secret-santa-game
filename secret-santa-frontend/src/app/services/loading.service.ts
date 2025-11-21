import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface LoadingState {
  [key: string]: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<LoadingState>({});
  public loading$ = this.loadingSubject.asObservable();

  constructor() { }

  /**
   * Set loading state for a specific operation
   */
  setLoading(key: string, loading: boolean): void {
    const currentState = this.loadingSubject.value;
    this.loadingSubject.next({
      ...currentState,
      [key]: loading
    });
  }

  /**
   * Get loading state for a specific operation
   */
  isLoading(key: string): Observable<boolean> {
    return new Observable(observer => {
      this.loading$.subscribe(state => {
        observer.next(!!state[key]);
      });
    });
  }

  /**
   * Get current loading state for a specific operation (synchronous)
   */
  isLoadingSync(key: string): boolean {
    return !!this.loadingSubject.value[key];
  }

  /**
   * Check if any operation is loading
   */
  isAnyLoading(): Observable<boolean> {
    return new Observable(observer => {
      this.loading$.subscribe(state => {
        const hasLoading = Object.values(state).some(loading => loading);
        observer.next(hasLoading);
      });
    });
  }

  /**
   * Clear all loading states
   */
  clearAll(): void {
    this.loadingSubject.next({});
  }

  /**
   * Clear loading state for a specific operation
   */
  clear(key: string): void {
    const currentState = this.loadingSubject.value;
    const newState = { ...currentState };
    delete newState[key];
    this.loadingSubject.next(newState);
  }

  /**
   * Start loading for an operation and return a function to stop it
   */
  startLoading(key: string): () => void {
    this.setLoading(key, true);
    return () => this.setLoading(key, false);
  }

  /**
   * Wrap an observable with loading state management
   */
  wrapWithLoading<T>(key: string, source: Observable<T>): Observable<T> {
    this.setLoading(key, true);
    
    return new Observable(observer => {
      const subscription = source.subscribe({
        next: (value) => observer.next(value),
        error: (error) => {
          this.setLoading(key, false);
          observer.error(error);
        },
        complete: () => {
          this.setLoading(key, false);
          observer.complete();
        }
      });

      return () => {
        this.setLoading(key, false);
        subscription.unsubscribe();
      };
    });
  }
}