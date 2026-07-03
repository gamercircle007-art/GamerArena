import { AlertTriangle } from 'lucide-react';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from './alert-dialog';
import { cn } from '@/lib/utils';

interface Props {
  isOpen: boolean; title: string; message: string;
  confirmLabel?: string; danger?: boolean;
  onConfirm: () => void; onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmModal({
  isOpen, title, message, confirmLabel = 'Confirm', danger = false,
  onConfirm, onCancel, loading,
}: Props) {
  return (
    <AlertDialog open={isOpen} onOpenChange={open => !open && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className={cn('w-12 h-12 rounded-full flex items-center justify-center mb-2', danger ? 'bg-destructive/10' : 'bg-amber-100')}>
            <AlertTriangle size={22} className={danger ? 'text-destructive' : 'text-amber-600'} />
          </div>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{message}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={loading}
            className={danger ? 'bg-destructive hover:bg-destructive/90' : ''}
          >
            {loading ? 'Please wait...' : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}