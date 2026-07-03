import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapInbox } from '@ng-icons/bootstrap-icons';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgIcon],
  providers: [provideIcons({ bootstrapInbox })],
  template: `
    <div class="empty-state-block">
      <div class="empty-icon">
        <ng-icon [name]="icon()" size="40" />
      </div>
      <h6 class="empty-title">{{ title() }}</h6>
      @if (message()) {
        <p class="empty-message">{{ message() }}</p>
      }
      <ng-content />
    </div>
  `,
  styles: `
    .empty-state-block {
      padding: 3rem 1.5rem;
      text-align: center;
    }

    .empty-icon {
      width: 72px;
      height: 72px;
      margin: 0 auto 1rem;
      border-radius: 50%;
      background: rgba(115, 103, 240, 0.08);
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .empty-title {
      font-weight: 600;
      color: #5e5873;
      margin-bottom: 0.35rem;
    }

    .empty-message {
      color: #b9b9c3;
      font-size: 0.875rem;
      margin: 0;
      max-width: 320px;
      margin-inline: auto;
    }
  `,
})
export class EmptyStateComponent {
  readonly title = input('No data found');
  readonly message = input('Try adjusting your filters or check back later.');
  readonly icon = input('bootstrapInbox');
}