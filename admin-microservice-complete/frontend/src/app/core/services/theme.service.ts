import { Injectable, signal } from '@angular/core';

const THEME_KEY = 'gc_admin_theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly isDark = signal(this.readStored());

  constructor() {
    this.apply(this.isDark());
  }

  toggle(): void {
    this.set(!this.isDark());
  }

  set(dark: boolean): void {
    this.isDark.set(dark);
    localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light');
    this.apply(dark);
  }

  private apply(dark: boolean): void {
    document.body.classList.toggle('dark', dark);
  }

  private readStored(): boolean {
    return localStorage.getItem(THEME_KEY) === 'dark';
  }
}