import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageShell, PageHeader, FilterBar, SearchInput, DataTable, ConfirmModal } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { CommunityPost } from '@/types';
import { getCommunityColumns } from '../_shared/listColumns';

export default function CommunityPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<CommunityPost | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-community', page, search],
    queryFn: () => adminApi.getCommunity({ page, search }),
    staleTime: 30_000,
  });

  const pinMutation = useMutation({
    mutationFn: ({ id, pinned }: { id: string; pinned: boolean }) => adminApi.pinCommunityPost(id, pinned),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-community'] }); toast.success('Pin status updated'); },
    onError: () => toast.error('Pin update failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteCommunityPost(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-community'] }); toast.success('Post deleted'); setConfirm(null); },
    onError: () => toast.error('Delete failed'),
  });

  const columns = useMemo(() => getCommunityColumns({
    can,
    onPin: (id, pinned) => pinMutation.mutate({ id, pinned }),
    onDelete: setConfirm,
  }), [can, pinMutation]);

  return (
    <PageShell>
      <PageHeader title="Community" subtitle="Forum discussions and guides" />
      <FilterBar>
        <SearchInput placeholder="Search author or title..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <span className="text-sm text-slate-400 ml-auto">{data?.total ?? 0} posts</span>
      </FilterBar>
      <DataTable columns={columns} data={data?.items ?? []} isLoading={isLoading} isError={isError} onRetry={() => refetch()}
        emptyMessage="No community posts found" pagination={{ page, pages: data?.pages ?? 1, total: data?.total ?? 0, onPageChange: setPage }}
        getRowClassName={row => row.is_pinned ? 'bg-amber-50/50' : undefined} />
      <ConfirmModal isOpen={!!confirm} danger title="Delete Community Post" message={`Permanently delete "${confirm?.title}"?`}
        confirmLabel="Delete" onConfirm={() => confirm && deleteMutation.mutate(confirm.id)}
        onCancel={() => setConfirm(null)} loading={deleteMutation.isPending} />
    </PageShell>
  );
}