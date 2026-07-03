import Button from '@/components/app/Button';
import { cn } from '../../utils/cn';

interface Props {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
}

function getPageNumbers(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | '...')[] = [1];
  if (current > 3) pages.push('...');
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
  if (current < total - 2) pages.push('...');
  pages.push(total);
  return pages;
}

export default function Pagination({ page, pages, total, onPageChange, pageSize = 10 }: Props) {
  if (pages <= 1 && total === 0) return null;

  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);
  const pageNums = getPageNumbers(page, pages);

  return (
    <div className="gc-pagination">
      <span>
        {total > 0
          ? <>Showing <strong className="text-slate-700">{from}</strong>–<strong className="text-slate-700">{to}</strong> of <strong className="text-slate-700">{total}</strong></>
          : 'No entries'}
      </span>
      {pages > 1 && (
        <div className="flex items-center gap-2 flex-wrap justify-center">
          <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => onPageChange(page - 1)}>
            Prev
          </Button>
          <div className="gc-pagination-pages">
            {pageNums.map((p, i) =>
              p === '...' ? (
                <span key={`ellipsis-${i}`} className="px-1 text-slate-400">…</span>
              ) : (
                <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  className={page === p ? 'gc-pagination-page-active' : 'gc-pagination-page'}
                  aria-current={page === p ? 'page' : undefined}
                >
                  {p}
                </button>
              )
            )}
          </div>
          <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}