import { useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props {
  value: string[];
  onChange: (next: string[]) => void;
  phone: string;
  disabled?: boolean;
  error?: string;
}

export default function OtpInput({ value, onChange, phone, disabled, error }: Props) {
  const refs = Array.from({ length: 6 }, () => useRef<HTMLInputElement>(null));

  const handleInput = (i: number, v: string) => {
    if (!/^\d?$/.test(v)) return;
    const next = [...value];
    next[i] = v;
    onChange(next);
    if (v && i < 5) refs[i + 1].current?.focus();
  };

  const handleKey = (i: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !value[i] && i > 0) refs[i - 1].current?.focus();
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const digits = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!digits) return;
    const next = [...value];
    digits.split('').forEach((d, i) => { next[i] = d; });
    onChange(next);
    refs[Math.min(digits.length, 5)].current?.focus();
  };

  return (
    <div className="space-y-2">
      <Label>Enter OTP</Label>
      <p className="text-xs text-muted-foreground">Sent to +91 {phone}</p>
      <div
        className="flex gap-2 justify-between"
        role="group"
        aria-label="One-time password digits"
        onPaste={handlePaste}
      >
        {value.map((digit, i) => (
          <Input
            key={i}
            ref={refs[i]}
            value={digit}
            onChange={e => handleInput(i, e.target.value)}
            onKeyDown={e => handleKey(i, e)}
            maxLength={1}
            type="text"
            inputMode="numeric"
            autoComplete={i === 0 ? 'one-time-code' : 'off'}
            className="size-11 sm:size-12 text-center text-lg font-bold p-0"
            disabled={disabled}
            aria-label={`Digit ${i + 1} of 6`}
          />
        ))}
      </div>
      {error && <p className="text-xs text-destructive" role="alert">{error}</p>}
    </div>
  );
}