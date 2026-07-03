import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  OnDestroy,
  signal,
  viewChildren,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';

type LoginTab = 'otp' | 'password';
type OtpStep = 'phone' | 'verify';

const FEATURES = [
  { icon: 'bi-people', text: 'Manage users, roles & permissions' },
  { icon: 'bi-shop', text: 'Verify parlors & moderate content' },
  { icon: 'bi-bar-chart-line', text: 'Platform analytics & insights' },
  { icon: 'bi-shield-check', text: 'Enterprise-grade security' },
];

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="login-page d-flex min-vh-100">
      <!-- Left hero -->
      <div class="login-hero d-none d-lg-flex col-lg-6 flex-column justify-content-center text-white p-5">
        <div class="hero-content mx-auto" style="max-width: 420px">
          <div class="brand-block d-flex align-items-center gap-3 mb-5">
            <div class="brand-icon-lg">
              <i class="bi bi-controller fs-3"></i>
            </div>
            <div>
              <h1 class="h3 fw-bold mb-0">GameConnect</h1>
              <p class="mb-0 opacity-75 small">Admin Control Panel</p>
            </div>
          </div>
          <h2 class="h4 fw-semibold mb-3">Manage your gaming platform</h2>
          <p class="opacity-75 mb-4">
            Secure admin access for authorized operators. Monitor users, parlors,
            tournaments, and community content from one dashboard.
          </p>
          <ul class="feature-list list-unstyled mb-0">
            @for (f of features; track f.text) {
              <li class="d-flex align-items-center gap-3 mb-3">
                <span class="feature-icon"><i class="bi {{ f.icon }}"></i></span>
                <span class="small">{{ f.text }}</span>
              </li>
            }
          </ul>
        </div>
      </div>

      <!-- Right card -->
      <div class="login-panel col-lg-6 d-flex align-items-center justify-content-center p-4">
        <div class="login-card card shadow-lg border-0 w-100">
          <div class="card-body p-4 p-md-5">
            <div class="text-center mb-4 d-lg-none">
              <div class="brand-icon-sm mx-auto mb-2">
                <i class="bi bi-controller text-white"></i>
              </div>
              <h2 class="h5 fw-bold mb-0">GameConnect Admin</h2>
            </div>

            <h2 class="h4 fw-bold text-center mb-1">Welcome back</h2>
            <p class="text-muted text-center small mb-4">Sign in to continue to the admin panel</p>

            @if (accessDenied()) {
              <div class="alert alert-danger d-flex align-items-center gap-2 py-2 small" role="alert">
                <i class="bi bi-exclamation-triangle-fill"></i>
                Access denied. Admin or Super Admin role required.
              </div>
            }

            <!-- Tabs -->
            <div class="login-tabs d-flex gap-1 p-1 rounded-3 mb-4">
              <button
                type="button"
                class="tab-btn flex-fill"
                [class.active]="activeTab() === 'otp'"
                (click)="setTab('otp')"
              >
                📱 Phone OTP
              </button>
              <button
                type="button"
                class="tab-btn flex-fill"
                [class.active]="activeTab() === 'password'"
                (click)="setTab('password')"
              >
                🔑 Password
              </button>
            </div>

            <!-- Phone OTP flow -->
            @if (activeTab() === 'otp') {
              @if (otpStep() === 'phone') {
                <form [formGroup]="otpPhoneForm" (ngSubmit)="sendOtp()">
                  <label class="form-label small fw-semibold">Phone Number</label>
                  <div class="input-group mb-3">
                    <span class="input-group-text">+91</span>
                    <input
                      type="tel"
                      class="form-control"
                      formControlName="phone"
                      placeholder="9876543210"
                      maxlength="10"
                      inputmode="numeric"
                    />
                  </div>
                  @if (otpPhoneForm.controls.phone.touched && otpPhoneForm.controls.phone.invalid) {
                    <p class="text-danger small mb-3">Enter a valid 10-digit mobile number</p>
                  }
                  <button
                    class="btn btn-primary w-100 py-2"
                    type="submit"
                    [disabled]="loading() || otpPhoneForm.invalid"
                  >
                    @if (loading()) {
                      <span class="spinner-border spinner-border-sm me-2"></span>
                      Sending...
                    } @else {
                      Send OTP
                    }
                  </button>
                </form>
              } @else {
                <div>
                  <p class="text-muted small mb-3">
                    Enter the 6-digit OTP sent to
                    <strong>+91 {{ otpPhoneForm.controls.phone.value }}</strong>
                  </p>
                  <div class="otp-row d-flex gap-2 justify-content-between mb-4">
                    @for (i of otpIndexes; track i) {
                      <input
                        #otpBox
                        type="text"
                        class="form-control otp-input text-center fw-bold"
                        maxlength="1"
                        inputmode="numeric"
                        [value]="otpDigits()[i]"
                        (input)="onOtpInput(i, $event)"
                        (keydown)="onOtpKeydown(i, $event)"
                        (paste)="onOtpPaste($event)"
                      />
                    }
                  </div>
                  <button
                    class="btn btn-primary w-100 py-2 mb-3"
                    type="button"
                    [disabled]="loading() || otpValue().length !== 6"
                    (click)="verifyOtp()"
                  >
                    @if (loading()) {
                      <span class="spinner-border spinner-border-sm me-2"></span>
                      Verifying...
                    } @else {
                      Verify &amp; Login
                    }
                  </button>
                  <div class="d-flex justify-content-between align-items-center">
                    <button type="button" class="btn btn-link btn-sm p-0 text-muted" (click)="backToPhone()">
                      ← Change number
                    </button>
                    @if (countdown() > 0) {
                      <span class="small text-muted">Resend in {{ countdown() }}s</span>
                    } @else {
                      <button
                        type="button"
                        class="btn btn-link btn-sm p-0"
                        [disabled]="loading()"
                        (click)="sendOtp()"
                      >
                        Resend OTP
                      </button>
                    }
                  </div>
                </div>
              }
            }

            <!-- Password flow -->
            @if (activeTab() === 'password') {
              <form [formGroup]="passwordForm" (ngSubmit)="loginWithPassword()">
                <div class="mb-3">
                  <label class="form-label small fw-semibold">Username</label>
                  <input
                    class="form-control"
                    formControlName="username"
                    placeholder="admin"
                    autocomplete="username"
                  />
                </div>
                <div class="mb-4">
                  <label class="form-label small fw-semibold">Password</label>
                  <input
                    type="password"
                    class="form-control"
                    formControlName="password"
                    placeholder="••••••••"
                    autocomplete="current-password"
                  />
                </div>
                <button
                  class="btn btn-primary w-100 py-2"
                  type="submit"
                  [disabled]="loading() || passwordForm.invalid"
                >
                  @if (loading()) {
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Signing in...
                  } @else {
                    Login
                  }
                </button>
              </form>
            }

            <div class="divider d-flex align-items-center gap-3 my-4">
              <hr class="flex-grow-1 m-0" />
              <span class="text-muted small">or</span>
              <hr class="flex-grow-1 m-0" />
            </div>

            <button type="button" class="btn btn-outline-secondary w-100 google-btn" (click)="onGoogleSignIn()">
              <svg class="google-icon me-2" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Sign in with Google
            </button>

            <p class="text-center text-muted mt-4 mb-0" style="font-size: 11px">
              Secure access for authorized administrators only
            </p>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: `
    .login-hero {
      background: linear-gradient(135deg, #283046 0%, #7367f0 100%);
      position: relative;
      overflow: hidden;
    }
    .login-hero::before {
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 20% 80%, rgba(255,255,255,0.08) 0%, transparent 50%);
    }
    .hero-content { position: relative; z-index: 1; }
    .brand-icon-lg {
      width: 52px;
      height: 52px;
      background: rgba(255,255,255,0.15);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .brand-icon-sm {
      width: 44px;
      height: 44px;
      background: #7367f0;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
    }
    .feature-icon {
      width: 36px;
      height: 36px;
      background: rgba(255,255,255,0.12);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .login-panel { background: #f8f8f8; }
    .login-card { max-width: 440px; border-radius: 12px !important; }
    .login-tabs { background: #f0f0f5; }
    .tab-btn {
      border: none;
      background: transparent;
      padding: 0.5rem 0.75rem;
      border-radius: 8px;
      font-size: 0.8125rem;
      font-weight: 600;
      color: #6e6b7b;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: #fff;
      color: #7367f0;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .otp-input {
      width: 2.75rem;
      height: 2.75rem;
      font-size: 1.125rem;
      padding: 0;
    }
    @media (min-width: 400px) {
      .otp-input { width: 3rem; height: 3rem; }
    }
    .google-btn {
      font-size: 0.875rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .google-icon { flex-shrink: 0; }
  `,
})
export class LoginComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly features = FEATURES;
  readonly otpIndexes = [0, 1, 2, 3, 4, 5];
  readonly otpBoxes = viewChildren<ElementRef<HTMLInputElement>>('otpBox');

  readonly activeTab = signal<LoginTab>('otp');
  readonly otpStep = signal<OtpStep>('phone');
  readonly loading = signal(false);
  readonly accessDenied = signal(false);
  readonly countdown = signal(0);
  readonly otpDigits = signal<string[]>(['', '', '', '', '', '']);

  private countdownTimer: ReturnType<typeof setInterval> | null = null;

  readonly otpPhoneForm = this.fb.nonNullable.group({
    phone: ['', [Validators.required, Validators.pattern(/^[6-9]\d{9}$/)]],
  });

  readonly passwordForm = this.fb.nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  readonly otpValue = () => this.otpDigits().join('');

  ngOnDestroy(): void {
    this.clearCountdown();
  }

  setTab(tab: LoginTab): void {
    this.activeTab.set(tab);
    this.accessDenied.set(false);
    if (tab === 'otp') {
      this.otpStep.set('phone');
      this.resetOtpDigits();
    }
  }

  sendOtp(): void {
    if (this.otpPhoneForm.invalid) {
      this.otpPhoneForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.accessDenied.set(false);
    const phoneNumber = this.formatPhone();

    this.auth
      .requestLoginOtp(phoneNumber)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.otpStep.set('verify');
          this.resetOtpDigits();
          this.startCountdown();
          this.toast.success(res.message ?? 'OTP sent to your WhatsApp');
          this.loading.set(false);
          setTimeout(() => this.focusOtpBox(0), 100);
        },
        error: (err) => {
          this.toast.error(err?.error?.message ?? 'Failed to send OTP');
          this.loading.set(false);
        },
      });
  }

  verifyOtp(): void {
    const otp = this.otpValue();
    if (otp.length !== 6) {
      this.toast.error('Please enter the 6-digit OTP');
      return;
    }

    this.loading.set(true);
    this.accessDenied.set(false);

    this.auth
      .verifyLoginOtp(this.formatPhone(), otp)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.handleAuthSuccess(),
        error: (err) => {
          this.toast.error(err?.error?.message ?? 'Invalid OTP. Please try again.');
          this.loading.set(false);
        },
      });
  }

  loginWithPassword(): void {
    if (this.passwordForm.invalid) return;

    this.loading.set(true);
    this.accessDenied.set(false);
    const { username, password } = this.passwordForm.getRawValue();

    this.auth
      .loginWithPassword(username, password)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.handleAuthSuccess(),
        error: (err) => {
          this.toast.error(err?.error?.message ?? 'Login failed');
          this.loading.set(false);
        },
      });
  }

  onGoogleSignIn(): void {
    this.toast.info('Google Sign-In will be available in a future release.');
  }

  backToPhone(): void {
    this.otpStep.set('phone');
    this.resetOtpDigits();
    this.clearCountdown();
  }

  onOtpInput(index: number, event: Event): void {
    const input = event.target as HTMLInputElement;
    const digit = input.value.replace(/\D/g, '').slice(-1);
    const digits = [...this.otpDigits()];
    digits[index] = digit;
    this.otpDigits.set(digits);
    input.value = digit;

    if (digit && index < 5) {
      this.focusOtpBox(index + 1);
    }
  }

  onOtpKeydown(index: number, event: KeyboardEvent): void {
    if (event.key === 'Backspace' && !this.otpDigits()[index] && index > 0) {
      this.focusOtpBox(index - 1);
    }
  }

  onOtpPaste(event: ClipboardEvent): void {
    event.preventDefault();
    const pasted = (event.clipboardData?.getData('text') ?? '').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const digits = pasted.split('').concat(Array(6).fill('')).slice(0, 6);
    this.otpDigits.set(digits);
    this.focusOtpBox(Math.min(pasted.length, 5));
  }

  private handleAuthSuccess(): void {
    if (this.auth.canAccessAdminPanel()) {
      this.toast.success(`Welcome, ${this.auth.currentUser()?.name ?? 'Admin'}!`);
      this.router.navigate(['/dashboard']);
    } else {
      this.auth.logout();
      this.accessDenied.set(true);
      this.toast.error('Access denied. Admin role required.');
    }
    this.loading.set(false);
  }

  private formatPhone(): string {
    const raw = this.otpPhoneForm.controls.phone.value.replace(/\D/g, '');
    return raw.startsWith('+') ? raw : `+91${raw}`;
  }

  private resetOtpDigits(): void {
    this.otpDigits.set(['', '', '', '', '', '']);
  }

  private focusOtpBox(index: number): void {
    const boxes = this.otpBoxes();
    boxes[index]?.nativeElement.focus();
  }

  private startCountdown(): void {
    this.clearCountdown();
    this.countdown.set(60);
    this.countdownTimer = setInterval(() => {
      const next = this.countdown() - 1;
      this.countdown.set(next);
      if (next <= 0) this.clearCountdown();
    }, 1000);
  }

  private clearCountdown(): void {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
    this.countdown.set(0);
  }
}