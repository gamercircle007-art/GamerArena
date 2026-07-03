import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageShell, PageHeader, FilterBar, SearchInput, DataTable, ConfirmModal } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { Post } from '@/types';
import { getPostsColumns, renderPostExpanded } from '../_shared/listColumns';

export default function PostsPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<Post | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-posts', page, search],
    queryFn: () => adminApi.getPosts({ page, search }),
    staleTime: 30_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deletePost(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-posts'] }); toast.success('Post deleted'); setConfirm(null); setExpanded(null); },
    onError: () => toast.error('Delete failed'),
  });

  const items = data?.items ?? [];
  const columns = useMemo(() => getPostsColumns({ expandedId: expanded, can, onDelete: setConfirm }), [expanded, can]);

  return (
    <PageShell>
      <PageHeader title="Posts" subtitle="Parlor social feed content" />
      <FilterBar>
        <SearchInput placeholder="Search parlor or content..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <span className="text-sm text-slate-400 ml-auto">{data?.total ?? 0} posts</span>
      </FilterBar>
      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        emptyMessage="No posts found"
        pagination={{ page, pages: data?.pages ?? 1, total: data?.total ?? 0, onPageChange: setPage }}
        expandedId={expanded}
        getRowId={row => row.id}
        onToggleExpand={row => setExpanded(prev => (prev === row.id ? null : row.id))}
        renderExpanded={renderPostExpanded}
      />
      <ConfirmModal isOpen={!!confirm} danger title="Delete Post" message="This will remove the post and all its comments."
        confirmLabel="Delete" onConfirm={() => confirm && deleteMutation.mutate(confirm.id)}
        onCancel={() => setConfirm(null)} loading={deleteMutation.isPending} />
    </PageShell>
  );
}