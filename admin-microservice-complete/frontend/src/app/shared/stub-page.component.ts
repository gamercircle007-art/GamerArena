import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-stub-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-wrapper">
      <h1 class="page-title">{{ title() }}</h1>
      <p class="text-muted">{{ subtitle() }}</p>
      <div class="card mt-3">
        <div class="card-body">
          <span class="badge bg-warning text-dark">Coming in next phase</span>
        </div>
      </div>
    </div>
  `,
})
export class StubPageComponent {
  readonly title = input.required<string>();
  readonly subtitle = input('This page will be implemented in the next build phase.');
}