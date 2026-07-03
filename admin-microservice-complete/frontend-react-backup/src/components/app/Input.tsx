import { Input as ShadcnInput } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Input({ label, error, className, id, ...props }: Props) {
  const inputId = id ?? label?.toLowerCase().replace(/\s/g, '-');
  return (
    <div className="w-full space-y-1.5">
      {label && <Label htmlFor={inputId}>{label}</Label>}
      <ShadcnInput
        id={inputId}
        className={cn(error && 'border-destructive focus-visible:ring-destructive', className)}
        {...props}
      />
      {error && <p className="text-xs text-destructive" role="alert">{error}</p>}
    </div>
  );
}