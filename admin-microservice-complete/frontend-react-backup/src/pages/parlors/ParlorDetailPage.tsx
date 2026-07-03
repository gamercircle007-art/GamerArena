import { useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BadgeCheck, BadgeX, Trash2, Star, Store, Image } from 'lucide-react';
import { toast } from 'sonner';
import {
  PageShell, DetailHeader, Card, Button, DataTable,
  ConfirmModal, StatusBadge, CardSkeleton,
} from '../../components/ui';
import {
  getParlorTournamentColumns, getParlorEventColumns, getParlorPostColumns,
} from '../_shared/listColumns';
import { adminApi } from '../../api/admin.api';
import { usePermissions } from '../../hooks/usePermissions';
import { PERMISSIONS } from '../../utils/permissions';
import { formatDate } from '../../utils/formatters';

type Tab = 'tournaments' | 'events' | 'posts' | 'gallery';

export default function ParlorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { can } = usePermissions();
  const [tab, setTab] = useState<Tab>('tournaments');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const tournamentColumns = useMemo(() => getParlorTournamentColumns(), []);
  const eventColumns = useMemo(() => getParlorEventColumns(), []);
  const postColumns = useMemo(() => getParlorPostColumns(), []);

  const { data: parlor, isLoading, isError } = useQuery({
    queryKey: ['admin-parlor', id],
    queryFn: () => adminApi.getParlor(id!),
    enabled: !!id,
  });

  const { data: tournaments, isLoading: tournamentsLoading } = useQuery({
    queryKey: ['parlor-tournaments', id],
    queryFn: () => adminApi.getTournaments({ parlor_id: id, limit: 10 }),
    enabled: !!id && tab === 'tournaments',
  });

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['parlor-events', id],
    queryFn: () => adminApi.getEvents({ parlor_id: id, limit: 10 }),
    enabled: !!id && tab === 'events',
  });

  const { data: posts, isLoading: postsLoading } = useQuery({
    queryKey: ['parlor-posts', id],
    queryFn: () => adminApi.getPosts({ parlor_id: id, limit: 10 }),
    enabled: !!id && tab === 'posts',
  });

  const verifyMutation = useMutation({
    mutationFn: (verified: boolean) => adminApi.verifyParlor(id!, verified),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-parlor', id] }); toast.success('Updated'); },
    onError: () => toast.error('Failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => adminApi.deleteParlor(id!),
    onSuccess: () => { toast.success('Deleted'); navigate('/parlors'); },
    onError: () => toast.error('Delete failed'),
  });

  if (isLoading) {
    return (
      <PageShell>
        <CardSkeleton className="h-8 w-48" />
        <CardSkeleton className="h-40" />
      </PageShell>
    );
  }

  if (isError || !parlor) {
    return (
      <PageShell>
        <Card padding className="text-center py-12">
          <p className="text-slate-500 mb-4">Parlor not found</p>
          <Link to="/parlors" className="text-indigo-600 text-sm hover:underline">← Back</Link>
        </Card>
      </PageShell>
    );
  }

  const dist = parlor.rating_distribution ?? [
    { stars: 5, count: 0 }, { stars: 4, count: 0 }, { stars: 3, count: 0 },
    { stars: 2, count: 0 }, { stars: 1, count: 0 },
  ];
  const maxDist = Math.max(...dist.map(d => d.count), 1);

  return (
    <PageShell>
      <DetailHeader
        onBack={() => navigate('/parlors')}
        title={parlor.name}
        badge={<StatusBadge status={parlor.is_verified ? 'verified' : 'unverified'} />}
        avatar={
          parlor.logo_url ? (
            <img src={parlor.logo_url} alt="" className="w-12 h-12 rounded-xl object-cover flex-shrink-0" />
          ) : (
            <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Store size={20} className="text-violet-600" />
            </div>
          )
        }
        actions={
          <>
            {can(PERMISSIONS.VERIFY_PARLORS) && (
              <Button variant="secondary" onClick={() => verifyMutation.mutate(!parlor.is_verified)} loading={verifyMutation.isPending}>
                {parlor.is_verified ? <><BadgeX size={14} /> Unverify</> : <><BadgeCheck size={14} /> Verify</>}
              </Button>
            )}
            {can(PERMISSIONS.DELETE_PARLORS) && (
              <Button variant="danger" onClick={() => setConfirmDelete(true)}>
                <Trash2 size={14} /> Delete
              </Button>
            )}
          </>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <Card padding className="lg:col-span-2 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div><span className="gc-label mb-0">Address</span><p className="text-slate-700">{parlor.address ?? '—'}</p></div>
            <div><span className="gc-label mb-0">Hours</span><p className="text-slate-700">{parlor.hours ?? '10 AM – 11 PM'}</p></div>
            <div><span className="gc-label mb-0">Owner</span><p className="text-slate-700">{parlor.owner_name} · {parlor.owner_phone}</p></div>
            <div><span className="gc-label mb-0">Joined</span><p className="text-slate-700">{formatDate(parlor.created_at)}</p></div>
          </div>
          <div>
            <span className="gc-label mb-0">Games</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {(parlor.game_types ?? []).map(g => (
                <span key={g} className="gc-badge bg-indigo-50 text-indigo-700">{g}</span>
              ))}
            </div>
          </div>
        </Card>

        <Card padding>
          <div className="flex items-center gap-2 mb-4">
            <Star size={18} className="text-amber-500" fill="currentColor" />
            <span className="text-2xl font-bold text-slate-800">{parlor.avg_rating.toFixed(1)}</span>
            <span className="text-sm text-slate-400">({parlor.rating_count} reviews)</span>
          </div>
          <div className="space-y-2">
            {[...dist].sort((a, b) => b.stars - a.stars).map(d => (
              <div key={d.stars} className="flex items-center gap-2 text-xs">
                <span className="w-8 text-slate-500">{d.stars}★</span>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-400 rounded-full" style={{ width: `${(d.count / maxDist) * 100}%` }} />
                </div>
                <span className="w-6 text-slate-400">{d.count}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t text-xs text-slate-500">
            {parlor.follower_count} followers · {parlor.post_count} posts
          </div>
        </Card>
      </div>

      <div className="gc-card-flat overflow-hidden">
        <div className="gc-detail-tabs">
          {(['tournaments', 'events', 'posts', 'gallery'] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={tab === t ? 'gc-detail-tab-active' : 'gc-detail-tab'}>
              {t}
            </button>
          ))}
        </div>
        <div className="p-0">
          {tab === 'tournaments' && (
            <DataTable
              columns={tournamentColumns}
              data={tournaments?.items ?? []}
              isLoading={tournamentsLoading}
              emptyMessage="No tournaments"
              bare
            />
          )}
          {tab === 'events' && (
            <DataTable
              columns={eventColumns}
              data={events?.items ?? []}
              isLoading={eventsLoading}
              emptyMessage="No events"
              bare
            />
          )}
          {tab === 'posts' && (
            <DataTable
              columns={postColumns}
              data={posts?.items ?? []}
              isLoading={postsLoading}
              emptyMessage="No posts"
              bare
            />
          )}
          {tab === 'gallery' && (
            <div className="p-4 sm:p-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {(parlor.gallery_urls ?? []).map((url, i) => (
                <img key={i} src={url} alt="" className="aspect-square rounded-lg object-cover" />
              ))}
              {!(parlor.gallery_urls?.length) && Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="aspect-square gc-skeleton flex items-center justify-center">
                  <Image size={24} className="text-slate-300" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ConfirmModal isOpen={confirmDelete} danger title="Delete Parlor"
        message={`Permanently delete "${parlor.name}"?`} confirmLabel="Delete"
        onConfirm={() => deleteMutation.mutate()} onCancel={() => setConfirmDelete(false)}
        loading={deleteMutation.isPending} />
    </PageShell>
  );
}