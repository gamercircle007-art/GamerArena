import {
  Card as ShadcnCard, CardContent, CardHeader as ShadcnCardHeader,
} from '@/components/ui/card';
import { cn } from '@/lib/utils';

export function Card({ children, className, padding }: {
  children: React.ReactNode; className?: string; padding?: boolean;
}) {
  return (
    <ShadcnCard className={cn(className)}>
      {padding ? <CardContent className="p-4 sm:p-5">{children}</CardContent> : children}
    </ShadcnCard>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <ShadcnCardHeader className={cn('px-4 sm:px-5 py-4', className)}>{children}</ShadcnCardHeader>;
}

export function CardBody({ children, className }: { children: React.ReactNode; className?: string }) {
  return <CardContent className={cn('p-4 sm:p-5', className)}>{children}</CardContent>;
}