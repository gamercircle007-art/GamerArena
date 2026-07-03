import { Injectable } from '@angular/core';
import Swal from 'sweetalert2';

@Injectable({ providedIn: 'root' })
export class ConfirmService {
  async confirm(
    title: string,
    text: string,
    confirmText = 'Yes',
    icon: 'warning' | 'question' | 'error' = 'warning',
  ): Promise<boolean> {
    const result = await Swal.fire({
      title,
      text,
      icon,
      showCancelButton: true,
      confirmButtonColor: '#7367f0',
      cancelButtonColor: '#82868b',
      confirmButtonText: confirmText,
      cancelButtonText: 'Cancel',
    });
    return result.isConfirmed;
  }

  async confirmDanger(title: string, text: string): Promise<boolean> {
    const result = await Swal.fire({
      title,
      text,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ea5455',
      cancelButtonColor: '#82868b',
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
    });
    return result.isConfirmed;
  }
}