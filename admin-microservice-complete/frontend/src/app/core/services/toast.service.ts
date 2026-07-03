import { inject, Injectable } from '@angular/core';
import { ToastrService } from 'ngx-toastr';

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly toastr = inject(ToastrService);

  success(message: string, title = 'Success'): void {
    this.toastr.success(message, title);
  }

  error(message: string, title = 'Error'): void {
    this.toastr.error(message, title);
  }

  warning(message: string, title = 'Warning'): void {
    this.toastr.warning(message, title);
  }

  info(message: string, title = 'Info'): void {
    this.toastr.info(message, title);
  }
}