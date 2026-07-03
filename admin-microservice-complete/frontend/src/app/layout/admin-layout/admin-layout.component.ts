import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  OnInit,
  signal,
} from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NgxSpinnerComponent } from 'ngx-spinner';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [RouterOutlet, NgxSpinnerComponent, SidebarComponent, TopbarComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="admin-wrapper"
      [class.sidebar-collapsed]="sidebarCollapsed() && !isMobile()"
      [class.mobile-open]="mobileOpen()">
      <ngx-spinner
        bdColor="rgba(0,0,0,0.4)"
        size="medium"
        color="#7367f0"
        type="ball-scale-multiple"
        [fullScreen]="true" />
      @if (isMobile() && mobileOpen()) {
        <div class="sidebar-backdrop" (click)="closeMobile()" aria-hidden="true"></div>
      }
      <app-sidebar
        [collapsed]="sidebarCollapsed() && !isMobile()"
        [mobileOpen]="mobileOpen()"
        (navigate)="closeMobile()" />
      <div class="main-content">
        <app-topbar
          [collapsed]="sidebarCollapsed()"
          (toggleSidebar)="toggleSidebar()" />
        <main class="content-area">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
  styles: `
    .admin-wrapper {
      display: flex;
      min-height: 100vh;
    }

    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.45);
      z-index: 199;
    }

    @media (max-width: 768px) {
      .admin-wrapper:not(.mobile-open) .main-content {
        margin-left: 0;
      }

      .admin-wrapper.mobile-open .main-content {
        margin-left: 0;
      }
    }

    @media (max-width: 576px) {
      .content-area {
        padding: 0.75rem !important;
      }
    }
  `,
})
export class AdminLayoutComponent implements OnInit {
  readonly sidebarCollapsed = signal(false);
  readonly mobileOpen = signal(false);
  readonly isMobile = signal(typeof window !== 'undefined' && window.innerWidth < 768);

  ngOnInit(): void {
    this.onResize();
  }

  @HostListener('window:resize')
  onResize(): void {
    const mobile = window.innerWidth < 768;
    this.isMobile.set(mobile);
    if (!mobile) {
      this.mobileOpen.set(false);
    } else {
      this.sidebarCollapsed.set(true);
    }
  }

  toggleSidebar(): void {
    if (this.isMobile()) {
      this.mobileOpen.update(v => !v);
    } else {
      this.sidebarCollapsed.update(v => !v);
    }
  }

  closeMobile(): void {
    if (this.isMobile()) {
      this.mobileOpen.set(false);
    }
  }
}