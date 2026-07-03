import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

const KNOWN_STATUSES = new Set([
  'active',
  'confirmed',
  'verified',
  'open',
  'banned',
  'cancelled',
  'deleted',
  'pending',
  'draft',
  'live',
  'completed',
  'full',
  'paid',
  'refunded',
  'refund_pending',
]);

@Component({
  selector: 'app-status-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="badge-status" [class]="'status-' + cssClass()">{{ label() }}</span>
  `,
})
export class StatusBadgeComponent {
  readonly status = input.required<string>();

  readonly cssClass = computed(() => {
    const key = this.status().toLowerCase();
    return KNOWN_STATUSES.has(key) ? key : 'completed';
  });

  readonly label = computed(() => this.status().replace(/_/g, ' '));
}