import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapBarChart,
  bootstrapCalendarCheck,
  bootstrapCurrencyRupee,
  bootstrapPeople,
  bootstrapShop,
  bootstrapTrophy,
} from '@ng-icons/bootstrap-icons';

export type StatsCardColor = 'primary' | 'success' | 'warning' | 'danger' | 'info';

@Component({
  selector: 'app-stats-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgIcon],
  providers: [
    provideIcons({
      bootstrapPeople,
      bootstrapShop,
      bootstrapTrophy,
      bootstrapCalendarCheck,
      bootstrapCurrencyRupee,
      bootstrapBarChart,
    }),
  ],
  template: `
    <div class="card stats-card" [class]="'gradient-' + color()">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <p class="stats-title">{{ title() }}</p>
            <h2 class="stats-value">{{ value() }}</h2>
            @if (subtitle()) {
              <small class="opacity-75">{{ subtitle() }}</small>
            }
            @if (trend() !== undefined && trend() !== null) {
              <small [class]="trend()! >= 0 ? 'trend-up' : 'trend-down'">
                {{ trend()! >= 0 ? '↑' : '↓' }} {{ trend()! >= 0 ? trend() : -trend()! }}% vs last period
              </small>
            }
          </div>
          <div class="stats-icon">
            <ng-icon [name]="icon()" size="28" />
          </div>
        </div>
      </div>
    </div>
  `,
})
export class StatsCardComponent {
  readonly title = input.required<string>();
  readonly value = input.required<string | number>();
  readonly icon = input.required<string>();
  readonly color = input<StatsCardColor>('primary');
  readonly trend = input<number | undefined>();
  readonly subtitle = input<string | undefined>();
}