import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageShell, PageHeader, FilterBar, SearchInput, DataTable } from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { getSlotBookingColumns, getTournamentBookingColumns } from '../_shared/listColumns';

type Tab = 'tournament' | 'slot';

export default function BookingsPage() {
  const [tab, setTab] = useState<Tab>('tournament');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-bookings', tab, page, search, dateFrom, dateTo],
    queryFn: () => adminApi.getBookings({
      page, search, booking_type: tab,
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
    }),
    staleTime: 30_000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  const columns = useMemo(
    () => tab === 'tournament' ? getTournamentBookingColumns() : getSlotBookingColumns(),
    [tab],
  );

  return (
    <PageShell>
      <PageHeader title="Bookings" subtitle="Tournament and time-slot reservations" />

      <div className="gc-tabs">
        {([['tournament', 'Tournament Bookings'], ['slot', 'Time Slot Bookings']] as const).map(([key, label]) => (
          <button key={key} type="button" onClick={() => { setTab(key); setPage(1); }} className={tab === key ? 'gc-tab-active' : 'gc-tab'}>
            {label}
          </button>
        ))}
      </div>

      <FilterBar>
        <SearchInput placeholder="Search user, parlor, event..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1); }} className="gc-input w-auto" />
        <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(1); }} className="gc-input w-auto" />
        <span className="text-sm text-slate-400 ml-auto">{total} bookings</span>
      </FilterBar>

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        emptyMessage="No bookings found"
        pagination={{ page, pages, total, onPageChange: setPage }}
      />
    </PageShell>
  );
}