import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { RegistrationComponent } from './registration.component';
import { ParticipantService, ParticipantRegistrationResponse } from '../services/participant.service';

describe('RegistrationComponent', () => {
  let component: RegistrationComponent;
  let fixture: ComponentFixture<RegistrationComponent>;
  let mockParticipantService: jasmine.SpyObj<ParticipantService>;

  beforeEach(() => {
    const spy = jasmine.createSpyObj('ParticipantService', ['registerParticipant', 'getParticipantCount']);

    TestBed.configureTestingModule({
      declarations: [RegistrationComponent],
      imports: [ReactiveFormsModule, RouterTestingModule],
      providers: [
        { provide: ParticipantService, useValue: spy }
      ]
    });

    fixture = TestBed.createComponent(RegistrationComponent);
    component = fixture.componentInstance;
    mockParticipantService = TestBed.inject(ParticipantService) as jasmine.SpyObj<ParticipantService>;
  });

  it('should create', () => {
    mockParticipantService.getParticipantCount.and.returnValue(of(0));
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should initialize form with empty name', () => {
    mockParticipantService.getParticipantCount.and.returnValue(of(0));
    fixture.detectChanges();
    
    expect(component.registrationForm.get('name')?.value).toBe('');
    expect(component.registrationForm.valid).toBeFalsy();
  });

  it('should load participant count on init', () => {
    mockParticipantService.getParticipantCount.and.returnValue(of(25));
    
    component.ngOnInit();
    
    expect(mockParticipantService.getParticipantCount).toHaveBeenCalled();
    expect(component.participantCount).toBe(25);
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      mockParticipantService.getParticipantCount.and.returnValue(of(0));
      fixture.detectChanges();
    });

    it('should require name', () => {
      const nameControl = component.registrationForm.get('name');
      nameControl?.setValue('');
      nameControl?.markAsTouched();
      
      expect(nameControl?.hasError('required')).toBeTruthy();
      expect(component.getNameErrorMessage()).toBe('Name is required');
    });

    it('should require minimum length', () => {
      const nameControl = component.registrationForm.get('name');
      nameControl?.setValue('A');
      nameControl?.markAsTouched();
      
      expect(nameControl?.hasError('minlength')).toBeTruthy();
      expect(component.getNameErrorMessage()).toBe('Name must be at least 2 characters long');
    });

    it('should enforce maximum length', () => {
      const nameControl = component.registrationForm.get('name');
      const longName = 'A'.repeat(51);
      nameControl?.setValue(longName);
      nameControl?.markAsTouched();
      
      expect(nameControl?.hasError('maxlength')).toBeTruthy();
      expect(component.getNameErrorMessage()).toBe('Name must not exceed 50 characters');
    });

    it('should validate name pattern', () => {
      const nameControl = component.registrationForm.get('name');
      nameControl?.setValue('John123');
      nameControl?.markAsTouched();
      
      expect(nameControl?.hasError('pattern')).toBeTruthy();
      expect(component.getNameErrorMessage()).toBe('Name can only contain letters, spaces, hyphens, and apostrophes');
    });

    it('should accept valid names', () => {
      const validNames = ['John Doe', "O'Connor", 'Mary-Jane', 'José'];
      
      validNames.forEach(name => {
        const nameControl = component.registrationForm.get('name');
        nameControl?.setValue(name);
        expect(nameControl?.valid).toBeTruthy();
      });
    });
  });

  describe('Registration Submission', () => {
    beforeEach(() => {
      mockParticipantService.getParticipantCount.and.returnValue(of(0));
      fixture.detectChanges();
    });

    it('should not submit if form is invalid', () => {
      component.registrationForm.get('name')?.setValue('');
      
      component.onSubmit();
      
      expect(mockParticipantService.registerParticipant).not.toHaveBeenCalled();
    });

    it('should not submit if at capacity', () => {
      component.participantCount = 100;
      component.registrationForm.get('name')?.setValue('John Doe');
      
      component.onSubmit();
      
      expect(mockParticipantService.registerParticipant).not.toHaveBeenCalled();
    });

    it('should submit valid form', () => {
      const mockResponse: ParticipantRegistrationResponse = {
        success: true,
        participant: {
          id: 1,
          name: 'John Doe',
          registration_timestamp: '2023-12-01T10:00:00Z'
        }
      };
      
      mockParticipantService.registerParticipant.and.returnValue(of(mockResponse));
      mockParticipantService.getParticipantCount.and.returnValue(of(1));
      
      component.registrationForm.get('name')?.setValue('John Doe');
      
      component.onSubmit();
      
      expect(mockParticipantService.registerParticipant).toHaveBeenCalledWith('John Doe');
      expect(component.registrationSuccess).toBeTruthy();
      expect(component.successMessage).toContain('number 1');
    });

    it('should handle registration failure', () => {
      const mockResponse: ParticipantRegistrationResponse = {
        success: false,
        error: 'Registration failed'
      };
      
      mockParticipantService.registerParticipant.and.returnValue(of(mockResponse));
      
      component.registrationForm.get('name')?.setValue('John Doe');
      
      component.onSubmit();
      
      expect(component.registrationSuccess).toBeFalsy();
      expect(component.errorMessage).toBe('Registration failed');
    });

    it('should handle service error', () => {
      mockParticipantService.registerParticipant.and.returnValue(
        throwError(() => new Error('Network error'))
      );
      
      component.registrationForm.get('name')?.setValue('John Doe');
      
      component.onSubmit();
      
      expect(component.registrationSuccess).toBeFalsy();
      expect(component.errorMessage).toBe('Network error');
    });

    it('should set submitting state during registration', () => {
      const mockResponse: ParticipantRegistrationResponse = {
        success: true,
        participant: {
          id: 1,
          name: 'John Doe',
          registration_timestamp: '2023-12-01T10:00:00Z'
        }
      };
      
      mockParticipantService.registerParticipant.and.returnValue(of(mockResponse));
      mockParticipantService.getParticipantCount.and.returnValue(of(1));
      
      component.registrationForm.get('name')?.setValue('John Doe');
      
      expect(component.isSubmitting).toBeFalsy();
      
      component.onSubmit();
      
      expect(component.isSubmitting).toBeFalsy(); // Should be false after completion
    });
  });

  describe('Capacity Management', () => {
    beforeEach(() => {
      mockParticipantService.getParticipantCount.and.returnValue(of(100));
      fixture.detectChanges();
    });

    it('should detect when at capacity', () => {
      component.participantCount = 100;
      expect(component.isAtCapacity).toBeTruthy();
    });

    it('should not be at capacity when under limit', () => {
      component.participantCount = 99;
      expect(component.isAtCapacity).toBeFalsy();
    });
  });

  describe('Form Reset', () => {
    beforeEach(() => {
      mockParticipantService.getParticipantCount.and.returnValue(of(0));
      fixture.detectChanges();
    });

    it('should reset form and messages', () => {
      component.registrationForm.get('name')?.setValue('John Doe');
      component.registrationSuccess = true;
      component.errorMessage = 'Some error';
      component.successMessage = 'Success message';
      
      component.resetForm();
      
      expect(component.registrationForm.get('name')?.value).toBeNull();
      expect(component.registrationSuccess).toBeFalsy();
      expect(component.errorMessage).toBe('');
      expect(component.successMessage).toBe('');
    });
  });
});
