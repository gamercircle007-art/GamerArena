import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';

export interface BreadcrumbItem {
  label: string;
  route?: string;
}

@Component({
  selector: 'app-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="page-header mb-4">
      <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
        <div>
          @if (breadcrumbs().length) {
            <nav aria-label="breadcrumb">
              <ol class="breadcrumb mb-2">
                @for (crumb of breadcrumbs(); track crumb.label; let last = $last) {
                  <li class="breadcrumb-item" [class.active]="last">
                    @if (!last && crumb.route) {
                      <a [routerLink]="crumb.route">{{ crumb.label }}</a>
                    } @else {
                      {{ crumb.label }}
                    }
                  </li>
                }
              </ol>
            </nav>
          }
          <h1 class="page-title mb-0">{{ title() }}</h1>
          @if (subtitle()) {
            <p class="text-muted mb-0 mt-1">{{ subtitle() }}</p>
          }
        </div>
        @if (hasActions()) {
          <div class="page-actions d-flex gap-2">
            <ng-content />
          </div>
        }
      </div>
    </div>
  `,
  styles: `
    .page-header .page-title {
      font-size: 1.375rem;
      font-weight: 700;
      color: #5e5873;
    }
    .page-actions :ng-deep .btn { white-space: nowrap; }
  `,
})
export class PageHeaderComponent {
  readonly title = input.required<string>();
  readonly subtitle = input<string>();
  readonly breadcrumbs = input<BreadcrumbItem[]>([]);

  readonly hasActions = computed(() => true);
}