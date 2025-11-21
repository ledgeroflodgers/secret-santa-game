import { Injectable } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { filter, map } from 'rxjs/operators';

export interface NavigationItem {
  path: string;
  label: string;
  icon?: string;
  requiresAdmin?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  private currentPageTitle = new BehaviorSubject<string>('FX Holiday Gift Exchange');

  public readonly navigationItems: NavigationItem[] = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/participants', label: 'Participants', icon: '👥' },
    { path: '/mobile-display', label: 'Gift Display', icon: '📱' },
    { path: '/admin', label: 'Admin', icon: '⚙️', requiresAdmin: true },
    { path: '/db-refresh', label: 'Reset', icon: '🔄', requiresAdmin: true }
  ];

  constructor(
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {
    this.initializePageTitleTracking();
  }

  get currentPageTitle$(): Observable<string> {
    return this.currentPageTitle.asObservable();
  }

  navigateToHome(): void {
    this.router.navigate(['/']);
  }

  navigateToRegister(): void {
    this.router.navigate(['/register']);
  }

  navigateToParticipants(): void {
    this.router.navigate(['/participants']);
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }

  navigateToMobileDisplay(): void {
    this.router.navigate(['/mobile-display']);
  }

  isCurrentRoute(path: string): boolean {
    return this.router.url === path;
  }

  getCurrentRoute(): string {
    return this.router.url;
  }

  private initializePageTitleTracking(): void {
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        map(() => {
          let route = this.activatedRoute;
          while (route.firstChild) {
            route = route.firstChild;
          }
          return route.snapshot.data['title'];
        })
      )
      .subscribe(title => {
        this.currentPageTitle.next(title);
        document.title = title;
      });
  }
}
