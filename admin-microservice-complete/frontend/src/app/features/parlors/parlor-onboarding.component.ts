import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

/**
 * Partner onboarding wizard (Phase 5 simplified).
 * Steps: stations → hours → preview availability.
 */
@Component({
  selector: 'app-parlor-onboarding',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="p-6 max-w-3xl mx-auto">
      <h1 class="text-2xl font-bold mb-4">Partner onboarding</h1>
      <p class="text-sm text-gray-600 mb-6">
        Configure stations & hours, then preview generated slots (same engine users see).
      </p>

      <label class="block mb-2 text-sm font-medium">Parlor ID (UUID)</label>
      <input class="border rounded w-full p-2 mb-4" [formControl]="parlorId" />

      <section class="mb-6 border rounded p-4">
        <h2 class="font-semibold mb-2">1. Stations</h2>
        <div class="grid grid-cols-3 gap-2 mb-2">
          <select class="border p-2" [formControl]="stationType">
            <option>PC</option><option>PS5</option><option>VR</option><option>XBOX</option><option>POOL</option>
          </select>
          <input type="number" class="border p-2" placeholder="Count" [formControl]="stationCount" />
          <input type="number" class="border p-2" placeholder="₹/hr" [formControl]="stationPrice" />
        </div>
        <button type="button" class="bg-red-600 text-white px-4 py-2 rounded" (click)="saveStations()" [disabled]="busy()">
          Save stations
        </button>
      </section>

      <section class="mb-6 border rounded p-4">
        <h2 class="font-semibold mb-2">2. Hours (Mon–Sun 10:00–23:00 default)</h2>
        <button type="button" class="bg-red-600 text-white px-4 py-2 rounded" (click)="saveDefaultHours()" [disabled]="busy()">
          Apply default week hours
        </button>
      </section>

      <section class="mb-6 border rounded p-4">
        <h2 class="font-semibold mb-2">3. Live slot preview (tomorrow)</h2>
        <button type="button" class="bg-black text-white px-4 py-2 rounded mb-3" (click)="preview()" [disabled]="busy()">
          Preview slots
        </button>
        @if (previewSlots().length) {
          <div class="flex flex-wrap gap-2">
            @for (s of previewSlots(); track s.start_time) {
              <span class="text-xs border rounded px-2 py-1"
                [class.opacity-40]="s.disabled">
                {{ s.start_time }} · ₹{{ (s.price_paise / 100) | number:'1.0-0' }}
                ({{ s.available_units }} left)
              </span>
            }
          </div>
        }
      </section>

      @if (message()) {
        <p class="text-sm mt-2" [class.text-red-600]="error()" [class.text-green-700]="!error()">{{ message() }}</p>
      }
    </div>
  `,
})
export class ParlorOnboardingComponent {
  private readonly http = inject(HttpClient);
  private readonly fb = inject(FormBuilder);
  private readonly base = environment.apiUrl;

  parlorId = this.fb.nonNullable.control('', Validators.required);
  stationType = this.fb.nonNullable.control('PC');
  stationCount = this.fb.nonNullable.control(4);
  stationPrice = this.fb.nonNullable.control(80);

  busy = signal(false);
  message = signal('');
  error = signal(false);
  previewSlots = signal<Array<{ start_time: string; price_paise: number; available_units: number; disabled?: boolean }>>([]);

  saveStations(): void {
    const id = this.parlorId.value.trim();
    if (!id) return;
    this.busy.set(true);
    this.http
      .put(`${this.base}/owner/parlors/${id}/stations`, [
        {
          station_type: this.stationType.value,
          total_count: this.stationCount.value,
          hourly_price_rupees: this.stationPrice.value,
        },
      ])
      .subscribe({
        next: () => {
          this.message.set('Stations saved');
          this.error.set(false);
          this.busy.set(false);
        },
        error: (e) => {
          this.message.set(e?.error?.detail || e?.message || 'Failed');
          this.error.set(true);
          this.busy.set(false);
        },
      });
  }

  saveDefaultHours(): void {
    const id = this.parlorId.value.trim();
    if (!id) return;
    const hours = Array.from({ length: 7 }, (_, weekday) => ({
      weekday,
      open_time: '10:00:00',
      close_time: '23:00:00',
    }));
    this.busy.set(true);
    this.http.put(`${this.base}/owner/parlors/${id}/hours`, hours).subscribe({
      next: () => {
        this.message.set('Hours saved (10:00–23:00 all week)');
        this.error.set(false);
        this.busy.set(false);
      },
      error: (e) => {
        this.message.set(e?.error?.detail || e?.message || 'Failed');
        this.error.set(true);
        this.busy.set(false);
      },
    });
  }

  preview(): void {
    const id = this.parlorId.value.trim();
    if (!id) return;
    this.busy.set(true);
    this.http
      .get<{ slots: Array<{ start_time: string; price_paise: number; available_units: number; disabled?: boolean }> }>(
        `${this.base}/owner/parlors/${id}/preview`,
        { params: { station_type: this.stationType.value } },
      )
      .subscribe({
        next: (res) => {
          this.previewSlots.set(res.slots || []);
          this.message.set(`Preview: ${(res.slots || []).length} slots`);
          this.error.set(false);
          this.busy.set(false);
        },
        error: (e) => {
          this.message.set(e?.error?.detail || e?.message || 'Failed');
          this.error.set(true);
          this.busy.set(false);
        },
      });
  }
}
