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

  /**
   * Confirm + collect a mandatory free-text reason (platform override audit trail).
   * Resolves to the trimmed reason, or null when cancelled.
   */
  async confirmWithReason(
    title: string,
    text: string,
    confirmText = 'Confirm',
    placeholder = 'Reason',
  ): Promise<string | null> {
    const result = await Swal.fire<string>({
      title,
      text,
      icon: 'warning',
      input: 'text',
      inputPlaceholder: placeholder,
      inputAttributes: { maxlength: '200' },
      showCancelButton: true,
      confirmButtonColor: '#ea5455',
      cancelButtonColor: '#82868b',
      confirmButtonText: confirmText,
      cancelButtonText: 'Cancel',
      inputValidator: value => (value && value.trim() ? null : 'A reason is required'),
    });
    if (!result.isConfirmed) return null;
    return (result.value ?? '').trim() || null;
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