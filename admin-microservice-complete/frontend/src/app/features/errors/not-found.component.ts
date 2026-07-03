import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="error-page">
      <div class="error-code">404</div>
      <h1>Page not found</h1>
      <p>The page you are looking for does not exist or was moved.</p>
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
      background: linear-gradient(118deg, #7367f0, rgba(115, 103, 240, 0.5));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
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
      max-width: 400px;
    }
  `,
  imports: [RouterLink],
})
export class NotFoundComponent {}