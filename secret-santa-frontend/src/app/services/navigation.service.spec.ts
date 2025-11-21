import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { NavigationService } from './navigation.service';
import { ActivatedRoute } from '@angular/router';

describe('NavigationService', () => {
  let service: NavigationService;
  let router: jasmine.SpyObj<Router>;
  let activatedRoute: jasmine.SpyObj<ActivatedRoute>;

  beforeEach(() => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate'], {
      events: { pipe: () => ({ subscribe: () => {} }) }
    });
    const activatedRouteSpy = jasmine.createSpyObj('ActivatedRoute', [], {
      firstChild: null,
      snapshot: { data: {} }
    });

    TestBed.configureTestingModule({
      providers: [
        NavigationService,
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: activatedRouteSpy }
      ]
    });
    
    service = TestBed.inject(NavigationService);
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    activatedRoute = TestBed.inject(ActivatedRoute) as jasmine.SpyObj<ActivatedRoute>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have navigation items defined', () => {
    expect(service.navigationItems).toBeDefined();
    expect(service.navigationItems.length).toBeGreaterThan(0);
  });

  it('should navigate to home', () => {
    service.navigateToHome();
    expect(router.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should navigate to register', () => {
    service.navigateToRegister();
    expect(router.navigate).toHaveBeenCalledWith(['/register']);
  });

  it('should navigate to participants', () => {
    service.navigateToParticipants();
    expect(router.navigate).toHaveBeenCalledWith(['/participants']);
  });

  it('should navigate to admin', () => {
    service.navigateToAdmin();
    expect(router.navigate).toHaveBeenCalledWith(['/admin']);
  });

  it('should check if current route matches', () => {
    Object.defineProperty(router, 'url', { value: '/register', configurable: true });
    expect(service.isCurrentRoute('/register')).toBe(true);
    expect(service.isCurrentRoute('/admin')).toBe(false);
  });

  it('should get current route', () => {
    Object.defineProperty(router, 'url', { value: '/participants', configurable: true });
    expect(service.getCurrentRoute()).toBe('/participants');
  });
});