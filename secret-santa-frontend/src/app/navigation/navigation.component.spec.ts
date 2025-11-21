import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NavigationComponent } from './navigation.component';
import { NavigationService } from '../services/navigation.service';
import { of } from 'rxjs';

describe('NavigationComponent', () => {
  let component: NavigationComponent;
  let fixture: ComponentFixture<NavigationComponent>;
  let navigationService: jasmine.SpyObj<NavigationService>;

  beforeEach(async () => {
    const navigationServiceSpy = jasmine.createSpyObj('NavigationService',
      ['isCurrentRoute'],
      {
        navigationItems: [
          { path: '/', label: 'Home', icon: '🏠' },
          { path: '/participants', label: 'Participants', icon: '👥' },
          { path: '/mobile-display', label: 'Gift Display', icon: '📱' },
          { path: '/admin', label: 'Admin', icon: '⚙️', requiresAdmin: true },
          { path: '/db-refresh', label: 'Reset', icon: '🔄', requiresAdmin: true }
        ],
        currentPageTitle$: of('Test Title')
      }
    );

    await TestBed.configureTestingModule({
      declarations: [NavigationComponent],
      imports: [RouterTestingModule],
      providers: [
        { provide: NavigationService, useValue: navigationServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(NavigationComponent);
    component = fixture.componentInstance;
    navigationService = TestBed.inject(NavigationService) as jasmine.SpyObj<NavigationService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize navigation items on ngOnInit', () => {
    component.ngOnInit();
    expect(component.navigationItems).toBeDefined();
    expect(component.navigationItems.length).toBe(5);
  });

  it('should check if route is current', () => {
    navigationService.isCurrentRoute.and.returnValue(true);

    const result = component.isCurrentRoute('/test');

    expect(result).toBe(true);
    expect(navigationService.isCurrentRoute).toHaveBeenCalledWith('/test');
  });

  it('should log navigation on navigate', () => {
    spyOn(console, 'log');

    component.onNavigate('/test');

    expect(console.log).toHaveBeenCalledWith('Navigating to: /test');
  });

  it('should display navigation items', () => {
    component.ngOnInit();
    fixture.detectChanges();

    const navLinks = fixture.nativeElement.querySelectorAll('.nav-link');
    expect(navLinks.length).toBe(5);
  });

  it('should display current page title', () => {
    fixture.detectChanges();

    const titleElement = fixture.nativeElement.querySelector('.nav-brand h2');
    expect(titleElement.textContent.trim()).toBe('Test Title');
  });
});
