import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { NavigationComponent } from './navigation/navigation.component';
import { NavigationService } from './services/navigation.service';
import { of } from 'rxjs';

describe('AppComponent', () => {
  beforeEach(() => {
    const navigationServiceSpy = jasmine.createSpyObj('NavigationService', 
      ['isCurrentRoute'], 
      {
        navigationItems: [
          { path: '/', label: 'Home', icon: '🏠' },
          { path: '/register', label: 'Register', icon: '📝' },
          { path: '/participants', label: 'Participants', icon: '👥' },
          { path: '/admin', label: 'Admin', icon: '⚙️', requiresAdmin: true }
        ],
        currentPageTitle$: of('Secret Santa Game')
      }
    );

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [AppComponent, NavigationComponent],
      providers: [
        { provide: NavigationService, useValue: navigationServiceSpy }
      ]
    });
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it(`should have as title 'FX Holiday Gift Exchange'`, () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('FX Holiday Gift Exchange');
  });

  it('should render title', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('FX Holiday Gift Exchange');
  });
});
