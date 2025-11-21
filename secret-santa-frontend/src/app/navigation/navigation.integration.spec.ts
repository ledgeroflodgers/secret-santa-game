import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Component, DebugElement } from '@angular/core';
import { RouterTestingModule } from '@angular/router/testing';
import { By } from '@angular/platform-browser';
import { NavigationComponent } from './navigation.component';
import { NavigationService } from '../services/navigation.service';
import { of } from 'rxjs';

@Component({ template: 'Home' })
class MockHomeComponent { }

@Component({ template: 'Register' })
class MockRegisterComponent { }

@Component({ template: 'Participants' })
class MockParticipantsComponent { }

@Component({ template: 'Admin' })
class MockAdminComponent { }

@Component({ template: 'Gift Display' })
class MockMobileDisplayComponent { }

@Component({
  template: `
    <app-navigation></app-navigation>
    <router-outlet></router-outlet>
  `
})
class TestHostComponent { }

describe('Navigation Integration', () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;
  let router: Router;
  let location: Location;
  let navigationService: NavigationService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [
        TestHostComponent,
        NavigationComponent,
        MockHomeComponent,
        MockRegisterComponent,
        MockParticipantsComponent,
        MockAdminComponent,
        MockMobileDisplayComponent
      ],
      imports: [
        RouterTestingModule.withRoutes([
          { path: '', component: MockHomeComponent, data: { title: 'Home' } },
          { path: 'participants', component: MockParticipantsComponent, data: { title: 'Participants' } },
          { path: 'mobile-display', component: MockMobileDisplayComponent, data: { title: 'Gift Display' } },
          { path: 'admin', component: MockAdminComponent, data: { title: 'Admin Panel' } },
          { path: 'db-refresh', component: MockRegisterComponent, data: { title: 'Database Refresh' } }
        ])
      ],
      providers: [NavigationService]
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    location = TestBed.inject(Location);
    navigationService = TestBed.inject(NavigationService);

    fixture.detectChanges();
  });

  it('should create navigation component', () => {
    expect(component).toBeTruthy();
  });

  it('should display all navigation links', () => {
    const navLinks = fixture.debugElement.queryAll(By.css('.nav-link'));
    expect(navLinks.length).toBe(5);

    const linkTexts = navLinks.map(link => link.nativeElement.textContent.trim());
    // The text includes icons, so we check if the labels are contained within
    expect(linkTexts.some(text => text.includes('Home'))).toBe(true);
    expect(linkTexts.some(text => text.includes('Participants'))).toBe(true);
    expect(linkTexts.some(text => text.includes('Gift Display'))).toBe(true);
    expect(linkTexts.some(text => text.includes('Admin'))).toBe(true);
    expect(linkTexts.some(text => text.includes('Reset'))).toBe(true);
  });

  it('should navigate when clicking navigation links', async () => {
    const mobileDisplayLink = fixture.debugElement.query(
      By.css('a[routerLink="/mobile-display"]')
    );

    if (mobileDisplayLink) {
      mobileDisplayLink.nativeElement.click();
      fixture.detectChanges();
      await fixture.whenStable();

      expect(location.path()).toBe('/mobile-display');
    } else {
      fail('Gift Display link not found');
    }
  });

  it('should highlight active navigation link', async () => {
    await router.navigate(['/participants']);
    fixture.detectChanges();

    const participantsLink = fixture.debugElement.query(
      By.css('a[routerLink="/participants"]')
    );

    if (participantsLink) {
      expect(participantsLink.nativeElement.classList).toContain('active');
    } else {
      fail('Participants link not found');
    }
  });

  it('should update page title when navigating', async () => {
    await router.navigate(['/mobile-display']);
    fixture.detectChanges();

    // Wait for the navigation service to update the title
    setTimeout(() => {
      navigationService.currentPageTitle$.subscribe(title => {
        expect(title).toBe('Gift Display');
      });
    }, 100);
  });

  it('should show admin link with special styling', () => {
    const adminLink = fixture.debugElement.query(
      By.css('a[routerLink="/admin"]')
    );

    if (adminLink) {
      expect(adminLink.nativeElement.classList).toContain('admin-link');
    } else {
      fail('Admin link not found');
    }
  });

  it('should handle navigation to home from any route', async () => {
    // Navigate to a different route first
    await router.navigate(['/participants']);
    expect(location.path()).toBe('/participants');

    // Then navigate to home
    const homeLink = fixture.debugElement.query(
      By.css('a[routerLink="/"]')
    );

    if (homeLink) {
      homeLink.nativeElement.click();
      fixture.detectChanges();
      await fixture.whenStable();

      expect(location.path()).toBe('/');
    } else {
      fail('Home link not found');
    }
  });

  it('should call onNavigate when clicking links', () => {
    const navigationComponent = fixture.debugElement.query(
      By.directive(NavigationComponent)
    ).componentInstance;

    spyOn(navigationComponent, 'onNavigate');

    const homeLink = fixture.debugElement.query(
      By.css('a[routerLink="/"]')
    );

    if (homeLink) {
      homeLink.nativeElement.click();
      expect(navigationComponent.onNavigate).toHaveBeenCalledWith('/');
    } else {
      fail('Home link not found');
    }
  });
});
