import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import {
  TableHeader, TableBody as ShadcnTableBody, TableRow as ShadcnTableRow, TableHead, TableCell,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export { TableHeader as TableHead, ShadcnTableBody as TableBody };

export function TableRow({
  highlight, className, ...props
}: React.HTMLAttributes<HTMLTableRowElement> & { highlight?: boolean }) {
  return (
    <ShadcnTableRow
      className={cn(highlight && 'bg-amber-50/50', className)}
      {...props}
    />
  );
}

export function TableTh({ children, className, sortable, sorted, checkbox, onClick }: {
  children?: React.ReactNode; className?: string;
  sortable?: boolean; sorted?: 'asc' | 'desc' | false;
  checkbox?: React.ReactNode; onClick?: React.MouseEventHandler<HTMLTableCellElement>;
}) {
  return (
    <TableHead
      className={cn(sortable && 'cursor-pointer select-none', checkbox && 'w-12', className)}
      onClick={onClick}
    >
      {checkbox ?? (
        <span className="inline-flex items-center gap-1.5">
          {children}
          {sortable && (
            sorted === 'asc' ? <ChevronUp size={13} /> :
            sorted === 'desc' ? <ChevronDown size={13} /> :
            <ChevronsUpDown size={13} className="text-muted-foreground" />
          )}
        </span>
      )}
    </TableHead>
  );
}

export function TableTd({ children, className, actions, muted }: {
  children: React.ReactNode; className?: string; actions?: boolean; muted?: boolean;
}) {
  return (
    <TableCell className={cn(
      actions && 'text-right',
      muted && 'text-muted-foreground text-xs',
      className,
    )}>
      {children}
    </TableCell>
  );
}