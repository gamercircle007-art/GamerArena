import { Loader2 } from 'lucide-react';
import { Button as ShadcnButton, type ButtonProps } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type LegacyVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'icon';
type LegacySize = 'sm' | 'md' | 'lg';

const variantMap: Record<LegacyVariant, ButtonProps['variant']> = {
  primary: 'default',
  secondary: 'outline',
  danger: 'destructive',
  ghost: 'ghost',
  icon: 'ghost',
};

const sizeMap: Record<LegacySize, ButtonProps['size']> = {
  sm: 'sm',
  md: 'default',
  lg: 'lg',
};

interface Props extends Omit<ButtonProps, 'variant' | 'size'> {
  variant?: LegacyVariant;
  size?: LegacySize;
  loading?: boolean;
}

export default function Button({
  variant = 'primary', size = 'md', loading, disabled, className, children, ...props
}: Props) {
  return (
    <ShadcnButton
      variant={variantMap[variant]}
      size={variant === 'icon' ? 'icon' : sizeMap[size]}
      disabled={disabled || loading}
      className={cn(className)}
      aria-busy={loading}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" />}
      {children}
    </ShadcnButton>
  );
}