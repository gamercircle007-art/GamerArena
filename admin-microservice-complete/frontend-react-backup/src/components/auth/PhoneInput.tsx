import { forwardRef } from 'react';
import { Phone } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface Props {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
  error?: string;
  className?: string;
}

const PhoneInput = forwardRef<HTMLInputElement, Props>(function PhoneInput(
  { id = 'phone', value, onChange, onSubmit, disabled, error, className },
  ref,
) {
  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={id}>Phone Number</Label>
      <div className="flex">
        <span
          className="inline-flex items-center rounded-l-lg border border-r-0 border-input bg-muted px-3 text-sm text-muted-foreground"
          aria-hidden
        >
          +91
        </span>
        <Input
          ref={ref}
          id={id}
          type="tel"
          inputMode="numeric"
          autoComplete="tel-national"
          value={value}
          onChange={e => onChange(e.target.value.replace(/\D/g, '').slice(0, 10))}
          onKeyDown={e => e.key === 'Enter' && onSubmit?.()}
          placeholder="9876543210"
          className="rounded-l-none"
          disabled={disabled}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
        />
      </div>
      <p className="text-xs text-muted-foreground flex items-center gap-1">
        <Phone className="size-3" aria-hidden /> OTP via WhatsApp / SMS
      </p>
      {error && (
        <p id={`${id}-error`} className="text-xs text-destructive" role="alert">{error}</p>
      )}
    </div>
  );
});

export default PhoneInput;