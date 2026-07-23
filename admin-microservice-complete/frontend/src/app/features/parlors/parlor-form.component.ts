import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapArrowLeft, bootstrapSave } from '@ng-icons/bootstrap-icons';

import { Parlor, User } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';

@Component({
  selector: 'app-parlor-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, NgIcon, PageHeaderComponent],
  providers: [provideIcons({ bootstrapArrowLeft, bootstrapSave })],
  template: `
    <div class="parlor-form-page">
      <app-page-header
        [title]="isEdit() ? 'Edit Parlor' : 'Create Parlor'"
        [subtitle]="isEdit() ? 'Update venue details, pricing, and manager' : 'Add a new gaming venue to the catalog'"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Parlors', route: '/parlors' },
          { label: isEdit() ? 'Edit' : 'Create' },
        ]">
        <a routerLink="/parlors" class="btn btn-sm btn-light">
          <ng-icon name="bootstrapArrowLeft" size="14" class="me-1" />
          Back
        </a>
      </app-page-header>

      @if (loading()) {
        <div class="card">
          <div class="card-body text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
          </div>
        </div>
      } @else {
        <div class="card">
          <div class="card-body">
            <form [formGroup]="form" (ngSubmit)="submit()" class="row g-3">
              <div class="col-md-8">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input class="form-control" formControlName="name" placeholder="Parlor name" />
                @if (form.controls.name.touched && form.controls.name.invalid) {
                  <div class="text-danger small mt-1">Name is required (min 2 chars)</div>
                }
              </div>
              <div class="col-md-4">
                <label class="form-label">Primary type</label>
                <input class="form-control" formControlName="primary_type" placeholder="gaming / pc_cafe / console" />
              </div>

              <div class="col-12">
                <label class="form-label">Address</label>
                <input class="form-control" formControlName="address" placeholder="Full address" />
              </div>

              <div class="col-md-4">
                <label class="form-label">Phone</label>
                <input class="form-control" formControlName="phone" placeholder="+91..." />
              </div>
              <div class="col-md-4">
                <label class="form-label">Website</label>
                <input class="form-control" formControlName="website" placeholder="https://" />
              </div>
              <div class="col-md-4">
                <label class="form-label">Logo / Image URL</label>
                <input class="form-control" formControlName="image_url" placeholder="https://..." />
              </div>

              <div class="col-md-3">
                <label class="form-label">Latitude</label>
                <input type="number" step="any" class="form-control" formControlName="latitude" />
              </div>
              <div class="col-md-3">
                <label class="form-label">Longitude</label>
                <input type="number" step="any" class="form-control" formControlName="longitude" />
              </div>
              <div class="col-md-3">
                <label class="form-label">Price / hour (₹)</label>
                <input type="number" step="0.01" class="form-control" formControlName="price_per_hour" />
              </div>
              <div class="col-md-3">
                <label class="form-label">Original price (₹)</label>
                <input type="number" step="0.01" class="form-control" formControlName="original_price" />
              </div>

              <div class="col-md-6">
                <label class="form-label">Game types (comma-separated)</label>
                <input
                  class="form-control"
                  formControlName="game_types_text"
                  placeholder="PC, Console, VR, Billiards" />
              </div>
              <div class="col-md-6">
                <label class="form-label">Assign manager / owner</label>
                <select class="form-select" formControlName="owner_id">
                  <option [ngValue]="null">— Unassigned —</option>
                  @for (u of ownerCandidates(); track u.id) {
                    <option [ngValue]="u.id">
                      {{ u.name || u.username || u.email || u.id }}
                      ({{ u.role }})
                    </option>
                  }
                </select>
                <small class="text-muted">Selecting a user promotes them to parlor_owner if needed.</small>
              </div>

              <div class="col-md-4">
                <div class="form-check form-switch mt-4">
                  <input class="form-check-input" type="checkbox" id="is_verified" formControlName="is_verified" />
                  <label class="form-check-label" for="is_verified">Verified</label>
                </div>
              </div>
              <div class="col-md-4">
                <div class="form-check form-switch mt-4">
                  <input class="form-check-input" type="checkbox" id="is_active" formControlName="is_active" />
                  <label class="form-check-label" for="is_active">Active</label>
                </div>
              </div>

              <div class="col-12 d-flex gap-2 justify-content-end mt-3">
                <a routerLink="/parlors" class="btn btn-light">Cancel</a>
                <button type="submit" class="btn btn-primary" [disabled]="form.invalid || saving()">
                  <ng-icon name="bootstrapSave" size="14" class="me-1" />
                  {{ saving() ? 'Saving…' : isEdit() ? 'Save changes' : 'Create parlor' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      }
    </div>
  `,
  styles: `
    .parlor-form-page .form-label {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #5e5873;
    }
  `,
})
export class ParlorFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  readonly isEdit = signal(false);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly ownerCandidates = signal<User[]>([]);
  private parlorId: string | null = null;

  readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    primary_type: ['gaming'],
    address: [''],
    phone: [''],
    website: [''],
    image_url: [''],
    latitude: this.fb.control<number | null>(null),
    longitude: this.fb.control<number | null>(null),
    price_per_hour: this.fb.control<number | null>(null),
    original_price: this.fb.control<number | null>(null),
    game_types_text: [''],
    owner_id: this.fb.control<string | null>(null),
    is_verified: [false],
    is_active: [true],
  });

  ngOnInit(): void {
    this.loadOwners();
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.parlorId = id;
      this.isEdit.set(true);
      this.loadParlor(id);
    }
  }

  private loadOwners(): void {
    this.api
      .getUsers({ limit: 100, role: 'parlor_owner' })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: owners => {
          this.api
            .getUsers({ limit: 100 })
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
              next: all => {
                const map = new Map<string, User>();
                [...owners.items, ...all.items].forEach(u => map.set(u.id, u));
                this.ownerCandidates.set(
                  Array.from(map.values()).filter(
                    u => u.role === 'parlor_owner' || u.role === 'user' || u.role === 'admin',
                  ),
                );
              },
            });
        },
      });
  }

  private loadParlor(id: string): void {
    this.loading.set(true);
    this.api
      .getParlor(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p: Parlor) => {
          this.form.patchValue({
            name: p.name,
            primary_type: p.game_types?.[0]?.toLowerCase() || 'gaming',
            address: p.address ?? '',
            phone: p.phone ?? '',
            website: p.website ?? '',
            image_url: p.logo_url ?? '',
            latitude: p.latitude,
            longitude: p.longitude,
            price_per_hour: p.price_per_hour ?? null,
            original_price: p.original_price ?? null,
            game_types_text: (p.game_types ?? []).join(', '),
            owner_id: p.owner_id,
            is_verified: p.is_verified,
            is_active: p.is_active ?? true,
          });
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.toast.error('Failed to load parlor');
          this.router.navigate(['/parlors']);
        },
      });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    const game_types = v.game_types_text
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const payload = {
      name: v.name.trim(),
      address: v.address || null,
      phone: v.phone || null,
      website: v.website || null,
      image_url: v.image_url || null,
      latitude: v.latitude,
      longitude: v.longitude,
      primary_type: v.primary_type || 'gaming',
      game_types,
      owner_id: v.owner_id,
      is_verified: v.is_verified,
      is_active: v.is_active,
      price_per_hour: v.price_per_hour,
      original_price: v.original_price,
    };

    this.saving.set(true);
    const req$ =
      this.isEdit() && this.parlorId
        ? this.api.updateParlor(this.parlorId, payload)
        : this.api.createParlor(payload);

    req$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: parlor => {
        this.saving.set(false);
        this.toast.success(this.isEdit() ? 'Parlor updated' : 'Parlor created');
        this.router.navigate(['/parlors', parlor.id]);
      },
      error: () => {
        this.saving.set(false);
        this.toast.error('Failed to save parlor');
      },
    });
  }
}
