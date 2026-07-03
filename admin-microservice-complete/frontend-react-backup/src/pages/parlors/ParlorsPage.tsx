import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import {
  PageShell, PageHeader, FilterBar, SearchInput, Select, DataTable, ConfirmModal,
} from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import type { Parlor } from '@/types';
import { getParlorsColumns } from './parlorsColumns';

export default function ParlorsPage() {
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [searchParams] = useSearchParams();

  const [search, setSearch] = useState('');
  const [verifiedFilter, setVerifiedFilter] = useState(
    searchParams.get('filter') === 'unverified' ? 'false' : '',
  );
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<{ type: 'delete'; parlor: Parlor } | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-parlors', page, search, verifiedFilter],
    queryFn: () => adminApi.getParlors({
      page,
      search,
      ...(verifiedFilter !== '' ? { is_verified: verifiedFilter === 'true' } : {}),
    }),
    staleTime: 30_000,
  });

  const verifyMutation = useMutation({
    mutationFn: ({ id, verified }: { id: string; verified: boolean }) =>
      adminApi.verifyParlor(id, verified),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-parlors'] });
      toast.success('Parlor verification updated');
    },
    onError: () => toast.error('Verification failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteParlor(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-parlors'] });
      toast.success('Parlor deleted');
      setConfirm(null);
    },
    onError: () => toast.error('Delete failed'),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  const columns = useMemo(() => getParlorsColumns({
    can,
    onVerify: (id, verified) => verifyMutation.mutate({ id, verified }),
    onDelete: parlor => setConfirm({ type: 'delete', parlor }),
  }), [can, verifyMutation]);

  return (
    <PageShell>
      <PageHeader
        title="Parlors"
        subtitle="Manage gaming parlors, verification, and listings"
      />

      <FilterBar>
        <SearchInput
          placeholder="Search parlor or owner..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
        />
        <Select
          value={verifiedFilter}
          onChange={e => { setVerifiedFilter(e.target.value); setPage(1); }}
          className="w-auto min-w-[8rem]"
        >
          <option value="">All Status</option>
          <option value="true">Verified</option>
          <option value="false">Unverified</option>
        </Select>
        <span className="text-sm text-slate-400 ml-auto">{total} parlors</span>
      </FilterBar>

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        emptyMessage="No parlors found"
        pagination={{ page, pages, total, onPageChange: setPage }}
        getRowClassName={row => !row.is_verified ? 'gc-table-row-highlight bg-amber-50/20' : undefined}
      />

      <ConfirmModal
        isOpen={!!confirm}
        danger
        title="Delete Parlor"
        message={`Permanently delete "${confirm?.parlor.name}"? All associated data will be removed.`}
        confirmLabel="Delete"
        onConfirm={() => confirm && deleteMutation.mutate(confirm.parlor.id)}
        onCancel={() => setConfirm(null)}
        loading={deleteMutation.isPending}
      />
    </PageShell>
  );
}