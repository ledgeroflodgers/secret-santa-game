import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NuclearComponent } from './nuclear.component';

describe('NuclearComponent', () => {
  let component: NuclearComponent;
  let fixture: ComponentFixture<NuclearComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NuclearComponent ],
      imports: [ ReactiveFormsModule, HttpClientTestingModule ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NuclearComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should authenticate with correct password', () => {
    component.passwordForm.patchValue({ password: 'saeed' });
    component.checkPassword();
    expect(component.isAuthenticated).toBe(true);
    expect(component.passwordError).toBe('');
  });

  it('should reject incorrect password', () => {
    component.passwordForm.patchValue({ password: 'wrong' });
    component.checkPassword();
    expect(component.isAuthenticated).toBe(false);
    expect(component.passwordError).toBeTruthy();
  });
});
