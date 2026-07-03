import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-unauthorized',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="error-page">
      <div class="error-code">403</div>
      <h1>Access denied</h1>
      <p>You do not have permission to view this page. Contact a super admin if you need access.</p>
      <a routerLink="/dashboard" class="btn btn-primary">Back to Dashboard</a>
    </div>
  `,
  styles: `
    .error-page {
      min-height: 70vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 2rem;
    }

    .error-code {
      font-size: 6rem;
      font-weight: 800;
      line-height: 1;
      color: #ea5455;
      margin-bottom: 0.5rem;
    }

    h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #5e5873;
      margin-bottom: 0.5rem;
    }

    p {
      color: #b9b9c3;
      margin-bottom: 1.5rem;
      max-width: 420px;
    }
  `,
  imports: [RouterLink],
})
export class UnauthorizedComponent {}