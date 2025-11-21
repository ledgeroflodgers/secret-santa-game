import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ParticipantService, ParticipantRegistrationResponse } from '../services/participant.service';
import { LoadingService } from '../services/loading.service';
import { ErrorHandlingService } from '../services/error-handling.service';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent implements OnInit {
  registrationForm: FormGroup;
  isSubmitting = false;
  registrationSuccess = false;
  errorMessage = '';
  successMessage = '';
  participantCount = 0;
  retryableError = false;

  constructor(
    private formBuilder: FormBuilder,
    private participantService: ParticipantService,
    private loadingService: LoadingService,
    private errorHandlingService: ErrorHandlingService
  ) {
    this.registrationForm = this.formBuilder.group({
      name: ['', [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(50),
        Validators.pattern(/^[a-zA-ZÀ-ÿ\s'-]+$/)
      ]]
    });
  }

  ngOnInit(): void {
    this.loadParticipantCount();
  }

  /**
   * Load current participant count
   */
  loadParticipantCount(): void {
    const loadingKey = 'loadParticipantCount';
    
    this.loadingService.wrapWithLoading(
      loadingKey,
      this.participantService.getParticipantCount()
    ).subscribe({
      next: (count) => {
        this.participantCount = count;
        this.errorMessage = ''; // Clear any previous errors
      },
      error: (error) => {
        console.error('Error loading participant count:', error);
        this.errorMessage = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Get form control for easy access in template
   */
  get nameControl() {
    return this.registrationForm.get('name');
  }

  /**
   * Check if registration is at capacity
   */
  get isAtCapacity(): boolean {
    return this.participantCount >= 100;
  }

  /**
   * Get name validation error message
   */
  getNameErrorMessage(): string {
    const nameControl = this.nameControl;
    if (nameControl?.hasError('required')) {
      return 'Name is required';
    }
    if (nameControl?.hasError('minlength')) {
      return 'Name must be at least 2 characters long';
    }
    if (nameControl?.hasError('maxlength')) {
      return 'Name must not exceed 50 characters';
    }
    if (nameControl?.hasError('pattern')) {
      return 'Name can only contain letters, spaces, hyphens, and apostrophes';
    }
    return '';
  }

  /**
   * Handle form submission
   */
  onSubmit(): void {
    if (this.registrationForm.invalid || this.isSubmitting || this.isAtCapacity) {
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';
    this.successMessage = '';

    const name = this.registrationForm.get('name')?.value?.trim();
    const loadingKey = 'registerParticipant';

    this.loadingService.wrapWithLoading(
      loadingKey,
      this.participantService.registerParticipant(name)
    ).subscribe({
      next: (response: ParticipantRegistrationResponse) => {
        this.isSubmitting = false;
        
        if (response.success && response.participant) {
          this.registrationSuccess = true;
          this.successMessage = `Registration successful! You have been assigned number ${response.participant.id}.`;
          this.registrationForm.reset();
          this.loadParticipantCount(); // Refresh count
        } else {
          this.errorMessage = response.message || response.error || 'Registration failed. Please try again.';
        }
      },
      error: (error) => {
        this.isSubmitting = false;
        this.errorMessage = this.errorHandlingService.getUserFriendlyMessage(error);
      }
    });
  }

  /**
   * Reset form and messages
   */
  resetForm(): void {
    this.registrationForm.reset();
    this.registrationSuccess = false;
    this.errorMessage = '';
    this.successMessage = '';
    this.retryableError = false;
  }

  /**
   * Check if registration is loading
   */
  get isRegistrationLoading(): boolean {
    return this.loadingService.isLoadingSync('registerParticipant');
  }

  /**
   * Check if participant count is loading
   */
  get isCountLoading(): boolean {
    return this.loadingService.isLoadingSync('loadParticipantCount');
  }

  /**
   * Retry registration
   */
  retryRegistration(): void {
    this.onSubmit();
  }

  /**
   * Retry loading participant count
   */
  retryLoadCount(): void {
    this.loadParticipantCount();
  }

  /**
   * Dismiss error message
   */
  dismissError(): void {
    this.errorMessage = '';
    this.retryableError = false;
  }
}
