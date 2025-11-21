import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-error-display',
  templateUrl: './error-display.component.html',
  styleUrls: ['./error-display.component.css']
})
export class ErrorDisplayComponent {
  @Input() error: string | null = null;
  @Input() retryable: boolean = false;
  @Input() dismissible: boolean = true;
  @Input() type: 'error' | 'warning' | 'info' = 'error';
  
  @Output() retry = new EventEmitter<void>();
  @Output() dismiss = new EventEmitter<void>();

  onRetry(): void {
    this.retry.emit();
  }

  onDismiss(): void {
    this.dismiss.emit();
  }
}
