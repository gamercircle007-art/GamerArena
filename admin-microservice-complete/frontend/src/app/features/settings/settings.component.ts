import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';

type SettingsTab = 'general' | 'features' | 'integrations' | 'security';

interface FeatureFlag {
  key: string;
  label: string;
  description: string;
}

interface Integration {
  name: string;
  key: string;
  detail: string;
  connected: boolean;
}

const FEATURE_FLAGS: FeatureFlag[] = [
  { key: 'parlor_registrations', label: 'Allow new parlor registrations', description: 'Let businesses sign up as parlor owners' },
  { key: 'paid_tournaments', label: 'Paid tournaments (Razorpay)', description: 'Enable entry fee collection via Razorpay' },
  { key: 'direct_messaging', label: 'Direct messaging', description: 'User-to-user chat feature' },
  { key: 'community_posts', label: 'Community posts', description: 'Forum discussions and guides' },
  { key: 'email_notifications', label: 'Email notifications', description: 'Transactional emails via SMTP' },
  { key: 'push_notifications', label: 'Push notifications (FCM)', description: 'Mobile push via Firebase' },
  { key: 'google_signin', label: 'Google Sign-In', description: 'OAuth login with Google' },
];

const INTEGRATIONS: Integration[] = [
  { name: 'Twilio', key: 'AC••••••••••••4821', detail: 'SMS OTP delivery', connected: true },
  { name: 'Firebase', key: 'credentials.json configured', detail: 'FCM push notifications', connected: true },
  { name: 'Razorpay', key: 'rzp_live_••••••••••••', detail: 'Test mode', connected: true },
  { name: 'AWS S3', key: 'gameconnect-media (ap-south-1)', detail: 'Media uploads', connected: true },
  { name: 'CloudFront', key: 'd1234abcdef.cloudfront.net', detail: 'CDN distribution', connected: false },
];

@Component({
  selector: 'app-settings',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, PageHeaderComponent],
  template: `
    <div class="settings-page">
      <app-page-header
        title="Settings"
        subtitle="Platform configuration and integrations"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Settings' }]" />

      @if (!canEdit()) {
        <div class="alert alert-info mb-4">
          Settings are restricted to super admins.
        </div>
      }

      <ul class="nav nav-tabs settings-tabs mb-4" role="tablist">
        @for (tab of tabs; track tab.key) {
          <li class="nav-item" role="presentation">
            <button
              type="button"
              class="nav-link"
              [class.active]="activeTab() === tab.key"
              (click)="activeTab.set(tab.key)">
              {{ tab.label }}
            </button>
          </li>
        }
      </ul>

      @switch (activeTab()) {
        @case ('general') {
          <div class="card settings-card">
            <div class="card-body">
              <h6 class="section-title">General Settings</h6>
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label" for="app-name">App Name</label>
                  <input id="app-name" type="text" class="form-control" value="GameConnect" [disabled]="!canEdit()" />
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="timezone">Timezone</label>
                  <select id="timezone" class="form-select" [disabled]="!canEdit()">
                    <option value="Asia/Kolkata" selected>Asia/Kolkata (IST)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="admin-email">Admin Email</label>
                  <input id="admin-email" type="email" class="form-control" value="admin@gameconnect.in" [disabled]="!canEdit()" />
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="support-email">Support Email</label>
                  <input id="support-email" type="email" class="form-control" value="support@gameconnect.in" [disabled]="!canEdit()" />
                </div>
              </div>

              <div class="d-flex align-items-center justify-content-between mt-4 pt-3 border-top">
                <div>
                  <div class="fw-medium">Maintenance Mode</div>
                  <small class="text-muted">Block all user access except admins</small>
                </div>
                <div class="form-check form-switch">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    role="switch"
                    id="maintenance"
                    [checked]="maintenanceMode()"
                    [disabled]="!canEdit()"
                    (change)="toggleMaintenance($any($event.target).checked)" />
                </div>
              </div>

              @if (canEdit()) {
                <button type="button" class="btn btn-primary mt-4" (click)="saveGeneral()">Save Changes</button>
              }
            </div>
          </div>
        }

        @case ('features') {
          <div class="card settings-card">
            <div class="list-group list-group-flush">
              @for (flag of featureFlags; track flag.key) {
                <div class="list-group-item d-flex align-items-center justify-content-between gap-3 py-3">
                  <div>
                    <div class="fw-medium">{{ flag.label }}</div>
                    <small class="text-muted">{{ flag.description }}</small>
                  </div>
                  <div class="form-check form-switch mb-0">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      [id]="'flag-' + flag.key"
                      [checked]="flags()[flag.key]"
                      [disabled]="!canEdit()"
                      (change)="toggleFlag(flag.key, $any($event.target).checked)" />
                  </div>
                </div>
              }
            </div>
          </div>
        }

        @case ('integrations') {
          <div class="card settings-card">
            <div class="list-group list-group-flush">
              @for (integration of integrations; track integration.name) {
                <div class="list-group-item d-flex align-items-center justify-content-between gap-3 py-3">
                  <div class="d-flex align-items-start gap-3 min-w-0">
                    <span
                      class="status-dot"
                      [class.status-dot--connected]="integration.connected"
                      [class.status-dot--disconnected]="!integration.connected">
                    </span>
                    <div class="min-w-0">
                      <div class="fw-medium">{{ integration.name }}</div>
                      <div class="font-monospace small text-muted text-truncate">{{ integration.key }}</div>
                      <small class="text-muted">{{ integration.detail }}</small>
                    </div>
                  </div>
                  <span
                    class="badge flex-shrink-0"
                    [class.bg-success-subtle]="integration.connected"
                    [class.text-success]="integration.connected"
                    [class.bg-danger-subtle]="!integration.connected"
                    [class.text-danger]="!integration.connected">
                    {{ integration.connected ? 'Connected' : 'Disconnected' }}
                  </span>
                </div>
              }
            </div>
          </div>
        }

        @case ('security') {
          <div class="card settings-card">
            <div class="card-body">
              <h6 class="section-title">Security Settings</h6>
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label" for="access-expiry">Access Token Expiry (mins)</label>
                  <input id="access-expiry" type="number" class="form-control" value="60" [disabled]="!canEdit()" />
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="refresh-expiry">Refresh Token Expiry (days)</label>
                  <input id="refresh-expiry" type="number" class="form-control" value="30" [disabled]="!canEdit()" />
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="otp-limit">OTP per phone / 10 min</label>
                  <input id="otp-limit" type="number" class="form-control" value="3" [disabled]="!canEdit()" />
                </div>
                <div class="col-md-6">
                  <label class="form-label" for="booking-limit">Bookings per user / min</label>
                  <input id="booking-limit" type="number" class="form-control" value="5" [disabled]="!canEdit()" />
                </div>
                <div class="col-12">
                  <label class="form-label" for="ip-whitelist">Admin IP Whitelist</label>
                  <textarea
                    id="ip-whitelist"
                    class="form-control font-monospace"
                    rows="3"
                    [disabled]="!canEdit()"
                    placeholder="Comma-separated IPs or CIDR ranges">192.168.1.0/24</textarea>
                </div>
              </div>
              @if (canEdit()) {
                <button type="button" class="btn btn-primary mt-4" (click)="saveSecurity()">Save Changes</button>
              }
            </div>
          </div>
        }
      }
    </div>
  `,
  styles: `
    .settings-tabs .nav-link {
      font-weight: 600;
      font-size: 0.875rem;
      color: #6e6b7b;
      border: none;
      padding: 0.75rem 1.25rem;
    }

    .settings-tabs .nav-link.active {
      color: #7367f0;
      border-bottom: 2px solid #7367f0;
      background: transparent;
    }

    .settings-card { border: 1px solid #ebe9f1; }

    .section-title {
      font-weight: 700;
      font-size: 0.9375rem;
      margin-bottom: 1.25rem;
      color: #5e5873;
    }

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
      margin-top: 0.375rem;
    }

    .status-dot--connected { background: #28c76f; }
    .status-dot--disconnected { background: #ea5455; }

    .list-group-item { border-color: #f3f2f7; }
  `,
})
export class SettingsComponent {
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);

  readonly activeTab = signal<SettingsTab>('general');
  readonly maintenanceMode = signal(false);
  readonly flags = signal<Record<string, boolean>>({
    parlor_registrations: true,
    paid_tournaments: true,
    direct_messaging: true,
    community_posts: true,
    email_notifications: false,
    push_notifications: true,
    google_signin: true,
  });

  readonly tabs: { key: SettingsTab; label: string }[] = [
    { key: 'general', label: 'General' },
    { key: 'features', label: 'Feature Flags' },
    { key: 'integrations', label: 'Integrations' },
    { key: 'security', label: 'Security' },
  ];

  readonly featureFlags = FEATURE_FLAGS;
  readonly integrations = INTEGRATIONS;

  readonly canEdit = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.MANAGE_SETTINGS) : false;
  });

  toggleMaintenance(enabled: boolean): void {
    if (!this.canEdit()) return;
    this.maintenanceMode.set(enabled);
  }

  toggleFlag(key: string, enabled: boolean): void {
    if (!this.canEdit()) return;
    this.flags.update(current => ({ ...current, [key]: enabled }));
    this.toast.success('Feature flag updated');
  }

  saveGeneral(): void {
    this.toast.success('Settings saved');
  }

  saveSecurity(): void {
    this.toast.success('Security settings saved');
  }
}