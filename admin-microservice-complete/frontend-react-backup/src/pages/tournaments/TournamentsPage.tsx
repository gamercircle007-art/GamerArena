import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { PageShell, PageHeader, FilterBar, SearchInput, Select, DataTable, ConfirmModal } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { Tournament } from '@/types';
import { getTournamentsColumns } from '../_shared/listColumns';

const STATUSES = ['open', 'live', 'completed', 'cancelled'] as const;

export default function TournamentsPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<Tournament | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-tournaments', page, search, statusFilter],
    queryFn: () => adminApi.getTournaments({ page, search, ...(statusFilter ? { status: statusFilter } : {}) }),
    staleTime: 30_000,
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => adminApi.updateTournamentStatus(id, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-tournaments'] }); toast.success('Status updated'); },
    onError: () => toast.error('Status update failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteTournament(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-tournaments'] }); toast.success('Tournament deleted'); setConfirm(null); },
    onError: () => toast.error('Delete failed'),
  });

  const items = data?.items ?? [];
  const columns = useMemo(() => getTournamentsColumns({
    can,
    onStatusChange: (id, status) => statusMutation.mutate({ id, status }),
    onDelete: setConfirm,
  }), [can, statusMutation]);

  return (
    <PageShell>
      <PageHeader title="Tournaments" subtitle="Manage tournament events and slots" />
      <FilterBar>
        <SearchInput placeholder="Search title or parlor..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <Select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">All Status</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </Select>
        <span className="text-sm text-slate-400 ml-auto">{data?.total ?? 0} tournaments</span>
      </FilterBar>
      <DataTable columns={columns} data={items} isLoading={isLoading} isError={isError} onRetry={() => refetch()}
        emptyMessage="No tournaments found" pagination={{ page, pages: data?.pages ?? 1, total: data?.total ?? 0, onPageChange: setPage }} />
      <ConfirmModal isOpen={!!confirm} danger title="Delete Tournament"
        message={`Permanently delete "${confirm?.title}"?`} confirmLabel="Delete"
        onConfirm={() => confirm && deleteMutation.mutate(confirm.id)} onCancel={() => setConfirm(null)} loading={deleteMutation.isPending} />
    </PageShell>
  );
}