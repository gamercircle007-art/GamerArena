import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageShell, PageHeader, FilterBar, SearchInput, Select, DataTable, ConfirmModal } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { Rating } from '@/types';
import { getRatingsColumns } from '../_shared/listColumns';

export default function RatingsPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [search, setSearch] = useState('');
  const [minRating, setMinRating] = useState('');
  const [maxRating, setMaxRating] = useState('');
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<Rating | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-ratings', page, search, minRating, maxRating],
    queryFn: () => adminApi.getRatings({
      page, search,
      ...(minRating ? { min_rating: Number(minRating) } : {}),
      ...(maxRating ? { max_rating: Number(maxRating) } : {}),
    }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteRating(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-ratings'] }); toast.success('Rating deleted'); setConfirm(null); },
    onError: () => toast.error('Delete failed'),
  });

  const columns = useMemo(() => getRatingsColumns({ can, onDelete: setConfirm }), [can]);

  return (
    <PageShell>
      <PageHeader title="Ratings" subtitle="Parlor reviews and star ratings" />
      <FilterBar>
        <SearchInput placeholder="Search user or parlor..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <Select value={minRating} onChange={e => { setMinRating(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">Min stars</option>
          {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}+ stars</option>)}
        </Select>
        <Select value={maxRating} onChange={e => { setMaxRating(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">Max stars</option>
          {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} stars</option>)}
        </Select>
        <span className="text-sm text-slate-400 ml-auto">{data?.total ?? 0} ratings</span>
      </FilterBar>
      <DataTable columns={columns} data={data?.items ?? []} isLoading={isLoading} isError={isError} onRetry={() => refetch()}
        emptyMessage="No ratings found" pagination={{ page, pages: data?.pages ?? 1, total: data?.total ?? 0, onPageChange: setPage }} />
      <ConfirmModal isOpen={!!confirm} danger title="Delete Rating" message={`Delete review by "${confirm?.user_name}"?`}
        confirmLabel="Delete" onConfirm={() => confirm && deleteMutation.mutate(confirm.id)}
        onCancel={() => setConfirm(null)} loading={deleteMutation.isPending} />
    </PageShell>
  );
}