import { DecimalPipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapBell,
  bootstrapGlobe,
  bootstrapPeople,
  bootstrapSend,
  bootstrapShop,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { BroadcastHistory, BroadcastRequest } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';

type Tab = 'send' | 'history';
type Target = BroadcastRequest['target'];
type NType = BroadcastRequest['type'];

const TARGETS: { value: Target; label: string; desc: string; icon: string; colorClass: string }[] = [
  { value: 'everyone', label: 'Everyone', desc: 'All active users', icon: 'bootstrapGlobe', colorClass: 'target-everyone' },
  { value: 'gamers', label: 'Gamers Only', desc: 'Regular user accounts', icon: 'bootstrapPeople', colorClass: 'target-gamers' },
  { value: 'parlor_owners', label: 'Parlor Owners', desc: 'Business accounts', icon: 'bootstrapShop', colorClass: 'target-owners' },
];

const TYPES: { value: NType; label: string; emoji: string }[] = [
  { value: 'info', label: 'Info', emoji: 'ℹ️' },
  { value: 'alert', label: 'Alert', emoji: '⚠️' },
  { value: 'promo', label: 'Promo', emoji: '🎁' },
  { value: 'event', label: 'Event', emoji: '🎮' },
];

@Component({
  selector: 'app-broadcast',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [
    provideIcons({
      bootstrapGlobe,
      bootstrapPeople,
      bootstrapShop,
      bootstrapBell,
      bootstrapSend,
    }),
  ],
  template: `
    <div class="broadcast-page">
      <app-page-header
        title="Broadcast"
        subtitle="Send push notifications to platform users"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Broadcast' }]" />

      <ul class="nav nav-tabs broadcast-tabs mb-4" role="tablist">
        <li class="nav-item" role="presentation">
          <button
            type="button"
            class="nav-link"
            [class.active]="activeTab() === 'send'"
            (click)="setTab('send')">
            <ng-icon name="bootstrapSend" size="14" class="me-1" />
            Send Broadcast
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button
            type="button"
            class="nav-link"
            [class.active]="activeTab() === 'history'"
            (click)="setTab('history')">
            History
          </button>
        </li>
      </ul>

      @if (activeTab() === 'send') {
        <div class="row g-4">
          <div class="col-lg-7">
            <!-- Target Audience -->
            <div class="card section-card mb-4">
              <div class="card-body">
                <h6 class="section-title">Target Audience</h6>
                <div class="row g-3">
                  @for (t of targets; track t.value) {
                    <div class="col-md-4">
                      <button
                        type="button"
                        class="target-card w-100"
                        [class]="t.colorClass"
                        [class.target-card--active]="selectedTarget() === t.value"
                        (click)="selectedTarget.set(t.value)">
                        <ng-icon [name]="t.icon" size="20" />
                        <span class="fw-semibold d-block mt-2">{{ t.label }}</span>
                        <small class="text-muted">{{ t.desc }}</small>
                      </button>
                    </div>
                  }
                </div>
              </div>
            </div>

            <!-- Type Pills -->
            <div class="card section-card mb-4">
              <div class="card-body">
                <h6 class="section-title">Notification Type</h6>
                <div class="d-flex flex-wrap gap-2">
                  @for (t of types; track t.value) {
                    <button
                      type="button"
                      class="btn btn-sm type-pill"
                      [class.btn-primary]="selectedType() === t.value"
                      [class.btn-outline-secondary]="selectedType() !== t.value"
                      (click)="selectedType.set(t.value)">
                      {{ t.emoji }} {{ t.label }}
                    </button>
                  }
                </div>
              </div>
            </div>

            <!-- Form -->
            <div class="card section-card">
              <div class="card-body">
                <h6 class="section-title">Message Content</h6>
                <form [formGroup]="form" (ngSubmit)="sendBroadcast()">
                  <div class="mb-3">
                    <label class="form-label" for="broadcast-title">Title <span class="text-danger">*</span></label>
                    <input
                      id="broadcast-title"
                      type="text"
                      class="form-control"
                      formControlName="title"
                      maxlength="80"
                      placeholder="e.g. New Feature Alert! 🎮" />
                    <div class="text-end small text-muted mt-1">{{ titleLength() }}/80</div>
                  </div>
                  <div class="mb-3">
                    <label class="form-label" for="broadcast-body">Message <span class="text-danger">*</span></label>
                    <textarea
                      id="broadcast-body"
                      class="form-control"
                      formControlName="body"
                      rows="4"
                      maxlength="500"
                      placeholder="Write your message here..."></textarea>
                    <div class="text-end small text-muted mt-1">{{ bodyLength() }}/500</div>
                  </div>
                  <button
                    type="submit"
                    class="btn btn-primary w-100 d-inline-flex align-items-center justify-content-center gap-2"
                    [disabled]="!canSend() || sending()">
                    @if (sending()) {
                      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    } @else {
                      <ng-icon name="bootstrapSend" size="16" />
                    }
                    Send Notification
                  </button>
                </form>
              </div>
            </div>

            @if (lastResult()) {
              <div class="alert alert-success d-flex align-items-center gap-3 mt-4 success-banner">
                <div class="success-icon">✓</div>
                <div>
                  <strong>Notification Sent!</strong>
                  <p class="mb-0 small">Delivered to {{ lastResult()!.sent_to }} users</p>
                </div>
              </div>
            }
          </div>

          <!-- Phone Preview -->
          <div class="col-lg-5">
            <div class="card section-card preview-card sticky-top">
              <div class="card-body">
                <h6 class="section-title">Preview</h6>
                <div class="phone-mockup mx-auto">
                  <div class="phone-screen">
                    <div class="notification-card">
                      <div class="d-flex align-items-center gap-2 mb-2">
                        <div class="app-icon">
                          <ng-icon name="bootstrapBell" size="12" />
                        </div>
                        <span class="small fw-medium">GameConnect</span>
                        <span class="small text-muted ms-auto">now</span>
                      </div>
                      <div class="small fw-semibold mb-1">
                        {{ previewTitle() }}
                      </div>
                      <div class="small preview-body">
                        {{ previewBody() }}
                      </div>
                    </div>
                  </div>
                </div>
                <p class="text-center small text-muted mt-3 mb-0">Preview on Android/iOS</p>
              </div>
            </div>
          </div>
        </div>
      } @else {
        <div class="card table-card">
          <div class="card-body p-0">
            <ngx-datatable
              class="bootstrap history-table"
              [rows]="history()"
              [columnMode]="ColumnMode.force"
              [headerHeight]="48"
              [rowHeight]="56"
              [footerHeight]="0"
              [scrollbarH]="true"
              [loadingIndicator]="historyLoading()">
              <ngx-datatable-column name="Type" prop="type" [flexGrow]="0.8">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="type-badge type-badge--{{ row.type }}">{{ row.type }}</span>
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Title" prop="title" [flexGrow]="1.5">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-medium">{{ row.title }}</span>
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Message" [flexGrow]="2">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.body | truncate: 60 }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Target" prop="target" [flexGrow]="1">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatTarget(row.target) }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Sent To" prop="sent_to" [flexGrow]="0.8">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.sent_to | number }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Date" prop="sent_at" [flexGrow]="1">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.sent_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Status" prop="status" [flexGrow]="0.8">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="badge bg-success-subtle text-success">{{ row.status }}</span>
                </ng-template>
              </ngx-datatable-column>
            </ngx-datatable>
            @if (!historyLoading() && !history().length) {
              <div class="empty-state">No broadcast history</div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: `
    .broadcast-tabs .nav-link {
      font-weight: 600;
      font-size: 0.875rem;
      color: #6e6b7b;
      border: none;
      padding: 0.75rem 1.25rem;
    }

    .broadcast-tabs .nav-link.active {
      color: #7367f0;
      border-bottom: 2px solid #7367f0;
      background: transparent;
    }

    .section-card .card-body { padding: 1.25rem 1.5rem; }

    .section-title {
      font-weight: 700;
      font-size: 0.9375rem;
      margin-bottom: 1rem;
      color: #5e5873;
    }

    .target-card {
      border: 2px solid #ebe9f1;
      border-radius: 0.75rem;
      padding: 1rem;
      background: #fff;
      text-align: left;
      transition: border-color 0.2s, background 0.2s;
    }

    .target-card:hover { border-color: #d8d6de; }
    .target-card--active.target-everyone { border-color: #6366f1; background: rgba(99, 102, 241, 0.06); color: #4338ca; }
    .target-card--active.target-gamers { border-color: #28c76f; background: rgba(40, 199, 111, 0.06); color: #1a8754; }
    .target-card--active.target-owners { border-color: #7367f0; background: rgba(115, 103, 240, 0.06); color: #5e50ee; }

    .type-pill { font-weight: 600; }

    .preview-card { top: 1rem; }

    .phone-mockup {
      max-width: 16rem;
      background: #1e293b;
      border-radius: 1.75rem;
      padding: 1rem;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
    }

    .phone-screen { background: #334155; border-radius: 1.25rem; padding: 0.75rem; }

    .notification-card { color: #fff; }

    .app-icon {
      width: 1.5rem;
      height: 1.5rem;
      background: #6366f1;
      border-radius: 0.375rem;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }

    .preview-body { color: #cbd5e1; line-height: 1.45; }

    .success-banner {
      border: 1px solid rgba(40, 199, 111, 0.35);
      background: rgba(40, 199, 111, 0.1);
    }

    .success-icon {
      width: 2.5rem;
      height: 2.5rem;
      border-radius: 50%;
      background: rgba(40, 199, 111, 0.2);
      color: #28c76f;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      flex-shrink: 0;
    }

    .history-table { box-shadow: none; }

    .type-badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 600;
      text-transform: capitalize;
      background: #f3f2f7;
      color: #6e6b7b;
    }

    .type-badge--promo { background: rgba(255, 159, 67, 0.15); color: #ff9f43; }
    .type-badge--alert { background: rgba(234, 84, 85, 0.12); color: #ea5455; }
    .type-badge--event { background: rgba(115, 103, 240, 0.12); color: #7367f0; }

    .empty-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class BroadcastComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  readonly activeTab = signal<Tab>('send');
  readonly selectedTarget = signal<Target>('everyone');
  readonly selectedType = signal<NType>('info');
  readonly sending = signal(false);
  readonly lastResult = signal<{ sent_to: number } | null>(null);
  readonly history = signal<BroadcastHistory[]>([]);
  readonly historyLoading = signal(false);

  readonly targets = TARGETS;
  readonly types = TYPES;
  protected readonly ColumnMode = ColumnMode;

  readonly form = this.fb.nonNullable.group({
    title: ['', [Validators.required, Validators.maxLength(80)]],
    body: ['', [Validators.required, Validators.maxLength(500)]],
  });

  readonly titleLength = computed(() => this.form.controls.title.value.length);
  readonly bodyLength = computed(() => this.form.controls.body.value.length);

  readonly canSend = computed(
    () => this.form.valid && this.titleLength() > 0 && this.bodyLength() > 0,
  );

  readonly previewTitle = computed(
    () => this.form.controls.title.value.trim() || 'Your notification title here',
  );

  readonly previewBody = computed(
    () => this.form.controls.body.value.trim() || 'Your message content will appear here.',
  );

  ngOnInit(): void {
    this.loadHistory();
  }

  setTab(tab: Tab): void {
    this.activeTab.set(tab);
    if (tab === 'history') this.loadHistory();
  }

  formatTarget(target: Target): string {
    return target.replace(/_/g, ' ');
  }

  sendBroadcast(): void {
    if (!this.canSend() || this.sending()) return;

    const payload: BroadcastRequest = {
      title: this.form.controls.title.value.trim(),
      body: this.form.controls.body.value.trim(),
      target: this.selectedTarget(),
      type: this.selectedType(),
    };

    this.sending.set(true);
    this.api
      .broadcast(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: result => {
          this.sending.set(false);
          this.lastResult.set(result);
          this.toast.success(`Sent to ${result.sent_to} users!`);
          this.form.reset();
          this.loadHistory();
        },
        error: () => {
          this.sending.set(false);
          this.toast.error('Failed to send broadcast');
        },
      });
  }

  private loadHistory(): void {
    this.historyLoading.set(true);
    this.api
      .getBroadcastHistory({ page: 1, limit: 50 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.history.set(res.items);
          this.historyLoading.set(false);
        },
        error: () => {
          this.historyLoading.set(false);
          this.toast.error('Failed to load broadcast history');
        },
      });
  }
}