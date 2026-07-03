import { Skeleton as ShadcnSkeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <ShadcnSkeleton className={cn(className)} style={style} />;
}

export function TableSkeleton({ rows = 6, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="p-2"><ShadcnSkeleton className="h-5 w-full max-w-[8rem]" /></td>
          ))}
        </tr>
      ))}
    </>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return <ShadcnSkeleton className={cn('h-24 w-full rounded-xl', className)} />;
}