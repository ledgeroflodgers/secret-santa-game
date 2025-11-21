import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { Component } from '@angular/core';
import { RouterTestingModule } from '@angular/router/testing';
import { AppRoutingModule } from './app-routing.module';
import { HomeComponent } from './home/home.component';
import { RegistrationComponent } from './registration/registration.component';
import { ParticipantsComponent } from './participants/participants.component';
import { AdminComponent } from './admin/admin.component';
import { AdminGuard } from './guards/admin.guard';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

// Mock components for testing
@Component({ template: 'Home Component' })
class MockHomeComponent { }

@Component({ template: 'Registration Component' })
class MockRegistrationComponent { }

@Component({ template: 'Participants Component' })
class MockParticipantsComponent { }

@Component({ template: 'Admin Component' })
class MockAdminComponent { }

@Component({ template: '<router-outlet></router-outlet>' })
class TestAppComponent { }

describe('App Routing Integration', () => {
  let router: Router;
  let location: Location;
  let fixture: ComponentFixture<TestAppComponent>;
  let adminGuard: jasmine.SpyObj<AdminGuard>;

  beforeEach(async () => {
    const adminGuardSpy = jasmine.createSpyObj('AdminGuard', ['canActivate']);
    adminGuardSpy.canActivate.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [
        TestAppComponent,
        MockHomeComponent,
        MockRegistrationComponent,
        MockParticipantsComponent,
        MockAdminComponent
      ],
      imports: [
        HttpClientTestingModule,
        FormsModule,
        ReactiveFormsModule,
        RouterTestingModule.withRoutes([
          { path: '', component: MockHomeComponent, data: { title: 'Home' } },
          { path: 'register', component: MockRegistrationComponent, data: { title: 'Register' } },
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

    router = TestBed.inject(Router);
    location = TestBed.inject(Location);
    adminGuard = TestBed.inject(AdminGuard) as jasmine.SpyObj<AdminGuard>;
    fixture = TestBed.createComponent(TestAppComponent);
    fixture.detectChanges();
  });

  it('should navigate to home route', async () => {
    await router.navigate(['']);
    expect(location.path()).toBe('/');
  });

  it('should navigate to register route', async () => {
    await router.navigate(['/register']);
    expect(location.path()).toBe('/register');
  });

  it('should navigate to participants route', async () => {
    await router.navigate(['/participants']);
    expect(location.path()).toBe('/participants');
  });

  it('should navigate to admin route when guard allows', async () => {
    adminGuard.canActivate.and.returnValue(true);
    
    await router.navigate(['/admin']);
    expect(location.path()).toBe('/admin');
    expect(adminGuard.canActivate).toHaveBeenCalled();
  });

  it('should redirect game route to admin', async () => {
    adminGuard.canActivate.and.returnValue(true);
    
    await router.navigate(['/game']);
    expect(location.path()).toBe('/admin');
  });

  it('should redirect unknown routes to home', async () => {
    await router.navigate(['/unknown-route']);
    expect(location.path()).toBe('/');
  });

  it('should handle admin guard rejection', async () => {
    adminGuard.canActivate.and.returnValue(false);
    
    await router.navigate(['/admin']);
    // The guard should prevent navigation, so we should still be at the initial route
    expect(adminGuard.canActivate).toHaveBeenCalled();
  });
});