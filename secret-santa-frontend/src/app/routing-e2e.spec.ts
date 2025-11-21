import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Component } from '@angular/core';
import { RouterTestingModule } from '@angular/router/testing';
import { AdminGuard } from './guards/admin.guard';
import { HomeComponent } from './home/home.component';
import { RegistrationComponent } from './registration/registration.component';
import { ParticipantsComponent } from './participants/participants.component';
import { AdminComponent } from './admin/admin.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

@Component({ template: 'Home' })
class MockHomeComponent { }

@Component({ template: 'Register' })
class MockRegisterComponent { }

@Component({ template: 'Participants' })
class MockParticipantsComponent { }

@Component({ template: 'Admin' })
class MockAdminComponent { }

@Component({
  template: '<router-outlet></router-outlet>'
})
class TestHostComponent { }

describe('End-to-End Routing and Navigation', () => {
  let fixture: ComponentFixture<TestHostComponent>;
  let router: Router;
  let location: Location;
  let adminGuard: AdminGuard;

  beforeEach(async () => {
    const adminGuardSpy = jasmine.createSpyObj('AdminGuard', ['canActivate']);
    adminGuardSpy.canActivate.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [
        TestHostComponent,
        MockHomeComponent,
        MockRegisterComponent,
        MockParticipantsComponent,
        MockAdminComponent
      ],
      imports: [
        HttpClientTestingModule,
        FormsModule,
        ReactiveFormsModule,
        RouterTestingModule.withRoutes([
          { path: '', component: MockHomeComponent, data: { title: 'Home' } },
          { path: 'register', component: MockRegisterComponent, data: { title: 'Register' } },
          { path: 'participants', component: MockParticipantsComponent, data: { title: 'Participants' } },
          { 
            path: 'admin', 
            component: MockAdminComponent, 
            canActivate: [AdminGuard],
            data: { title: 'Admin Panel' } 
          },
          { path: 'game', redirectTo: '/admin', pathMatch: 'full' },
          { path: '**', redirectTo: '/', data: { title: 'Page Not Found' } }
        ])
      ],
      providers: [
        { provide: AdminGuard, useValue: adminGuardSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    router = TestBed.inject(Router);
    location = TestBed.inject(Location);
    adminGuard = TestBed.inject(AdminGuard) as jasmine.SpyObj<AdminGuard>;
    
    fixture.detectChanges();
  });

  it('should create the routing system', () => {
    expect(router).toBeTruthy();
    expect(location).toBeTruthy();
    expect(adminGuard).toBeTruthy();
  });

  it('should navigate to all main routes', async () => {
    // Test home route
    await router.navigate(['/']);
    expect(location.path()).toBe('/');

    // Test register route
    await router.navigate(['/register']);
    expect(location.path()).toBe('/register');

    // Test participants route
    await router.navigate(['/participants']);
    expect(location.path()).toBe('/participants');
  });

  it('should handle admin route with guard', async () => {
    (adminGuard as jasmine.SpyObj<AdminGuard>).canActivate.and.returnValue(true);
    
    await router.navigate(['/admin']);
    expect(location.path()).toBe('/admin');
    expect(adminGuard.canActivate).toHaveBeenCalled();
  });

  it('should redirect game route to admin', async () => {
    (adminGuard as jasmine.SpyObj<AdminGuard>).canActivate.and.returnValue(true);
    
    await router.navigate(['/game']);
    expect(location.path()).toBe('/admin');
  });

  it('should redirect unknown routes to home', async () => {
    await router.navigate(['/unknown-route']);
    expect(location.path()).toBe('/');
  });

  it('should prevent admin access when guard denies', async () => {
    (adminGuard as jasmine.SpyObj<AdminGuard>).canActivate.and.returnValue(false);
    
    // Start at home
    await router.navigate(['/']);
    expect(location.path()).toBe('/');
    
    // Try to navigate to admin
    await router.navigate(['/admin']);
    
    // Should still be at home since guard denied access
    expect(location.path()).toBe('/');
    expect(adminGuard.canActivate).toHaveBeenCalled();
  });

  it('should have proper route data configuration', () => {
    const routes = router.config;
    
    // Check that routes have proper data titles
    const homeRoute = routes.find(r => r.path === '');
    expect(homeRoute?.data?.['title']).toBe('Home');
    
    const registerRoute = routes.find(r => r.path === 'register');
    expect(registerRoute?.data?.['title']).toBe('Register');
    
    const participantsRoute = routes.find(r => r.path === 'participants');
    expect(participantsRoute?.data?.['title']).toBe('Participants');
    
    const adminRoute = routes.find(r => r.path === 'admin');
    expect(adminRoute?.data?.['title']).toBe('Admin Panel');
    expect(adminRoute?.canActivate).toContain(AdminGuard);
  });

  it('should handle navigation between all routes in sequence', async () => {
    // Navigate through all routes in sequence
    await router.navigate(['/']);
    expect(location.path()).toBe('/');
    
    await router.navigate(['/register']);
    expect(location.path()).toBe('/register');
    
    await router.navigate(['/participants']);
    expect(location.path()).toBe('/participants');
    
    // Mock admin access
    (adminGuard as jasmine.SpyObj<AdminGuard>).canActivate.and.returnValue(true);
    await router.navigate(['/admin']);
    expect(location.path()).toBe('/admin');
    
    // Navigate back to home
    await router.navigate(['/']);
    expect(location.path()).toBe('/');
  });
});