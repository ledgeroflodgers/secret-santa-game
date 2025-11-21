import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-nuclear',
  templateUrl: './nuclear.component.html',
  styleUrls: ['./nuclear.component.css']
})
export class NuclearComponent {
  passwordForm: FormGroup;
  isAuthenticated = false;
  passwordError = '';
  resetSuccess = false;
  resetError = '';
  isResetting = false;
  
  private readonly NUCLEAR_PASSWORD = 'saeed';
  private readonly apiUrl = `${environment.apiUrl}/api`;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient
  ) {
    this.passwordForm = this.fb.group({
      password: ['', [Validators.required]]
    });
  }

  checkPassword(): void {
    const password = this.passwordForm.get('password')?.value;
    
    if (password === this.NUCLEAR_PASSWORD) {
      this.isAuthenticated = true;
      this.passwordError = '';
      this.passwordForm.reset();
    } else {
      this.passwordError = 'Incorrect password. Please try again.';
      this.passwordForm.get('password')?.setValue('');
    }
  }

  resetAllData(): void {
    if (!confirm('⚠️ WARNING: This will permanently delete ALL data including participants, gifts, and game state. This action CANNOT be undone. Are you absolutely sure?')) {
      return;
    }

    this.isResetting = true;
    this.resetSuccess = false;
    this.resetError = '';

    this.http.post(`${this.apiUrl}/nuclear/reset`, {})
      .subscribe({
        next: (response: any) => {
          this.resetSuccess = true;
          this.isResetting = false;
          console.log('All data reset successfully:', response);
        },
        error: (error) => {
          this.resetError = 'Failed to reset data. Please try again.';
          this.isResetting = false;
          console.error('Error resetting data:', error);
        }
      });
  }
}
