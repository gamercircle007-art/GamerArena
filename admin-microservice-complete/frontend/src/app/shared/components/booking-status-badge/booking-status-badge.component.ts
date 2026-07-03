import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

import { StatusBadgeComponent } from '../status-badge/status-badge.component';

const BOOKING_STATUS_MAP: Record<string, string> = {
  paid: 'confirmed',
  confirmed: 'confirmed',
  completed: 'completed',
  pending: 'pending',
  cancelled: 'cancelled',
  canceled: 'cancelled',
  refund_pending: 'pending',
  refunded: 'completed',
  processed: 'completed',
  failed: 'cancelled',
};

@Component({
  selector: 'app-booking-status-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StatusBadgeComponent],
  template: `
    <app-status-badge [status]="mappedStatus()" />
  `,
})
export class BookingStatusBadgeComponent {
  readonly status = input.required<string>();

  readonly mappedStatus = computed(() => {
    const key = this.status().toLowerCase();
    return BOOKING_STATUS_MAP[key] ?? key;
  });
}