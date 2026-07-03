import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageShell, PageHeader, FilterBar, SearchInput, Select, DataTable, ConfirmModal } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { Comment } from '@/types';
import { getCommentsColumns } from '../_shared/listColumns';

export default function CommentsPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [search, setSearch] = useState('');
  const [deletedFilter, setDeletedFilter] = useState('');
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<Comment | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-comments', page, search, deletedFilter],
    queryFn: () => adminApi.getComments({ page, search, ...(deletedFilter !== '' ? { is_deleted: deletedFilter === 'true' } : {}) }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteComment(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-comments'] }); toast.success('Comment removed'); setConfirm(null); },
    onError: () => toast.error('Failed'),
  });

  const columns = useMemo(() => getCommentsColumns({ can, onDelete: setConfirm }), [can]);

  return (
    <PageShell>
      <PageHeader title="Comments" subtitle="Moderate post comments and replies" />
      <FilterBar>
        <SearchInput placeholder="Search user or comment..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <Select value={deletedFilter} onChange={e => { setDeletedFilter(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">All Comments</option>
          <option value="false">Active only</option>
          <option value="true">Removed only</option>
        </Select>
        <span className="text-sm text-slate-400 ml-auto">{data?.total ?? 0} comments</span>
      </FilterBar>
      <DataTable columns={columns} data={data?.items ?? []} isLoading={isLoading} isError={isError} onRetry={() => refetch()}
        emptyMessage="No comments found" pagination={{ page, pages: data?.pages ?? 1, total: data?.total ?? 0, onPageChange: setPage }}
        getRowClassName={row => row.is_deleted ? 'opacity-60' : undefined} />
      <ConfirmModal isOpen={!!confirm} danger title="Remove Comment" message="This will soft-delete the comment."
        confirmLabel="Remove" onConfirm={() => confirm && deleteMutation.mutate(confirm.id)}
        onCancel={() => setConfirm(null)} loading={deleteMutation.isPending} />
    </PageShell>
  );
}