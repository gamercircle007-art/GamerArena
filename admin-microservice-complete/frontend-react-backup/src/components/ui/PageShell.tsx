import { cn } from '../../utils/cn';

export default function PageShell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('gc-page', className)}>{children}</div>;
}