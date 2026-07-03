import {
  useReactTable, getCoreRowModel, getSortedRowModel, flexRender,
  type ColumnDef, type SortingState,
} from '@tanstack/react-table';
import { Fragment, useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import AdminTable from './AdminTable';
import { TableHeader, TableBody, TableRow, TableHead, TableCell } from './table';
import { TableSkeleton } from '../app/Skeleton';
import EmptyState from './EmptyState';
import { cn } from '@/lib/utils';

interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
}

interface Props<T> {
  columns: ColumnDef<T, unknown>[];
  data: T[];
  title?: string;
  subtitle?: string;
  toolbar?: React.ReactNode;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  pagination?: PaginationProps;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  compact?: boolean;
  getRowClassName?: (row: T) => string | undefined;
  expandedId?: string | null;
  onToggleExpand?: (row: T) => void;
  renderExpanded?: (row: T) => React.ReactNode;
  getRowId?: (row: T) => string;
  bare?: boolean;
}

export default function DataTable<T>({
  columns, data, title, subtitle, toolbar,
  isLoading, isError, onRetry, pagination, onRowClick, emptyMessage = 'No data found',
  compact, getRowClassName, expandedId, onToggleExpand, renderExpanded, getRowId, bare,
}: Props<T>) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data, columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const colCount = columns.length;

  return (
    <AdminTable
      title={title} subtitle={subtitle} toolbar={toolbar}
      isError={isError} onRetry={onRetry}
      page={pagination?.page} pages={pagination?.pages} total={pagination?.total}
      onPageChange={pagination?.onPageChange} pageSize={pagination?.pageSize}
      compact={compact} bare={bare}
    >
      <TableHeader>
        {table.getHeaderGroups().map(hg => (
          <TableRow key={hg.id} className="border-b border-slate-100 bg-slate-50/80 hover:bg-slate-50/80">
            {hg.headers.map(h => (
              <TableHead
                key={h.id}
                className={cn(
                  'h-10 px-4 text-xs font-semibold text-slate-600 uppercase tracking-wide',
                  h.column.getCanSort() && 'cursor-pointer select-none hover:text-indigo-600',
                )}
                onClick={h.column.getToggleSortingHandler()}
              >
                <span className="inline-flex items-center gap-1">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                  {h.column.getIsSorted() === 'asc' && <ChevronUp size={13} />}
                  {h.column.getIsSorted() === 'desc' && <ChevronDown size={13} />}
                </span>
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {isLoading ? (
          <TableSkeleton rows={compact ? 4 : 5} cols={colCount} />
        ) : table.getRowModel().rows.map(row => {
          const rowId = getRowId?.(row.original) ?? row.id;
          const isExpanded = expandedId === rowId;
          return (
            <Fragment key={row.id}>
              <TableRow
                onClick={() => {
                  if (onToggleExpand) onToggleExpand(row.original);
                  else if (onRowClick) onRowClick(row.original);
                }}
                className={cn(
                  'border-b border-slate-50 transition-colors',
                  (onRowClick || onToggleExpand) && 'cursor-pointer hover:bg-indigo-50/40',
                  getRowClassName?.(row.original),
                  isExpanded && 'bg-indigo-50/30',
                )}
              >
                {row.getVisibleCells().map(cell => (
                  <TableCell key={cell.id} className="px-4 py-3.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
              {isExpanded && renderExpanded && (
                <TableRow key={`${row.id}-expanded`} className="bg-slate-50/80 hover:bg-slate-50/80">
                  <TableCell colSpan={colCount} className="px-4 py-4">
                    {renderExpanded(row.original)}
                  </TableCell>
                </TableRow>
              )}
            </Fragment>
          );
        })}
        {!isLoading && !data.length && <EmptyState message={emptyMessage} />}
      </TableBody>
    </AdminTable>
  );
}