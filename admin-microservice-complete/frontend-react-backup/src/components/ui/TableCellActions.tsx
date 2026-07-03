import { cn } from '../../utils/cn';

export default function TableCellActions({ children, className }: {
  children: React.ReactNode; className?: string;
}) {
  return <div className={cn('gc-table-actions', className)}>{children}</div>;
}