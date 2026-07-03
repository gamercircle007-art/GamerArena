import { Link } from 'react-router-dom';
import type { ColumnDef } from '@tanstack/react-table';
import {
  Trash2, ChevronDown, ChevronUp, Pin, Star, Image,
} from 'lucide-react';
import type {
  Booking, Tournament, Post, Comment, ParlourEvent, CommunityPost, Rating,
  NotificationHistory, User, Booking as BookingType,
} from '@/types';
import { PERMISSIONS, PERMISSION_GROUPS, ROLES, ROLE_META, ROLE_PERMISSIONS, type Permission, type Role } from '@/utils/permissions';
import TableCellUser from '@/components/ui/TableCellUser';
import TableCellActions from '@/components/ui/TableCellActions';
import StatusBadge from '@/components/ui/StatusBadge';
import Select from '@/components/app/Select';
import {
  formatDate, formatDateTime, formatCurrency, truncate, timeAgo,
} from '@/utils/formatters';

// ── Bookings ────────────────────────────────────────────────
export function getTournamentBookingColumns(): ColumnDef<Booking>[] {
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <TableCellUser name={row.original.user_name} subtitle={row.original.user_phone} /> },
    { id: 'event', header: 'Tournament', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.event_title}</span> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'slot', header: 'Slot#', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.slot_number ?? '—'}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'payment', header: 'Payment', cell: ({ row }) => <StatusBadge status={row.original.payment_status} /> },
    { id: 'date', header: 'Date', accessorKey: 'created_at', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
  ];
}

export function getSlotBookingColumns(): ColumnDef<Booking>[] {
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <TableCellUser name={row.original.user_name} subtitle={row.original.user_phone} /> },
    { id: 'game', header: 'Game', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.event_title}</span> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'datetime', header: 'Date & Time', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDateTime(row.original.created_at)}</span> },
    { id: 'price', header: 'Price', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.price ? formatCurrency(row.original.price) : '—'}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'booked', header: 'Booked', accessorKey: 'created_at', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
  ];
}

export function getUserBookingsColumns(): ColumnDef<BookingType>[] {
  return [
    { id: 'event', header: 'Event', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.event_title}</span> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'type', header: 'Type', cell: ({ row }) => <span className="gc-badge bg-slate-100 text-slate-600 capitalize">{row.original.booking_type}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'payment', header: 'Payment', cell: ({ row }) => <StatusBadge status={row.original.payment_status} /> },
    { id: 'date', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDate(row.original.created_at)}</span> },
  ];
}

// ── Tournaments ───────────────────────────────────────────
const TOURNAMENT_STATUSES = ['open', 'live', 'completed', 'cancelled'] as const;

export function getTournamentsColumns(opts: {
  can: (p: Permission) => boolean;
  onStatusChange: (id: string, status: string) => void;
  onDelete: (t: Tournament) => void;
}): ColumnDef<Tournament>[] {
  const { can, onStatusChange, onDelete } = opts;
  return [
    { accessorKey: 'title', header: 'Title', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'game', header: 'Game', accessorKey: 'game_type', cell: ({ row }) => row.original.game_type
      ? <span className="gc-badge bg-indigo-50 text-indigo-700">{row.original.game_type}</span>
      : <span className="gc-table-cell-sub">—</span> },
    { id: 'slots', header: 'Slots', cell: ({ row }) => (
      <span className={`gc-table-cell-primary tabular-nums ${row.original.booked_slots >= row.original.total_slots ? 'text-orange-600 font-medium' : ''}`}>
        {row.original.booked_slots}/{row.original.total_slots}
      </span>
    )},
    { id: 'fee', header: 'Entry Fee', cell: ({ row }) => <span className="gc-table-cell-primary">{formatCurrency(row.original.entry_fee)}</span> },
    { accessorKey: 'start_time', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDateTime(row.original.start_time)}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <TableCellActions>
        {can(PERMISSIONS.EDIT_TOURNAMENTS) && (
          <Select value={row.original.status} onChange={e => onStatusChange(row.original.id, e.target.value)} className="w-auto text-xs py-1">
            {TOURNAMENT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        )}
        {can(PERMISSIONS.DELETE_TOURNAMENTS) && (
          <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
        )}
      </TableCellActions>
    ), enableSorting: false },
  ];
}

// ── Posts ─────────────────────────────────────────────────
export function getPostsColumns(opts: {
  expandedId: string | null;
  can: (p: Permission) => boolean;
  onDelete: (p: Post) => void;
}): ColumnDef<Post>[] {
  const { expandedId, can, onDelete } = opts;
  return [
    { id: 'expand', header: '', cell: ({ row }) => expandedId === row.original.id
      ? <ChevronUp size={14} className="text-slate-400" />
      : <ChevronDown size={14} className="text-slate-400" />, size: 32, enableSorting: false },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'content', header: 'Content', cell: ({ row }) => <span className="gc-table-cell-primary max-w-xs block">{truncate(row.original.content, 60)}</span> },
    { accessorKey: 'media_count', header: 'Media', cell: ({ row }) => <span className="tabular-nums">{row.original.media_count}</span> },
    { accessorKey: 'likes_count', header: 'Likes', cell: ({ row }) => <span className="tabular-nums">{row.original.likes_count}</span> },
    { accessorKey: 'comments_count', header: 'Comments', cell: ({ row }) => <span className="tabular-nums">{row.original.comments_count}</span> },
    { accessorKey: 'created_at', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <div onClick={e => e.stopPropagation()}>
        <TableCellActions>
          {can(PERMISSIONS.DELETE_POSTS) && (
            <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
          )}
        </TableCellActions>
      </div>
    ), enableSorting: false },
  ];
}

export function renderPostExpanded(post: Post) {
  return (
    <div>
      <p className="text-slate-700 text-sm whitespace-pre-wrap mb-3">{post.content}</p>
      {post.media_count > 0 && (
        <div className="flex gap-2 flex-wrap">
          {Array.from({ length: Math.min(post.media_count, 4) }).map((_, i) => (
            <div key={i} className="w-20 h-20 bg-slate-200 rounded-xl flex items-center justify-center">
              <Image size={20} className="text-slate-400" />
            </div>
          ))}
          {post.media_count > 4 && (
            <div className="w-20 h-20 bg-slate-100 rounded-xl flex items-center justify-center text-xs text-slate-500">
              +{post.media_count - 4}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Comments ──────────────────────────────────────────────
export function getCommentsColumns(opts: {
  can: (p: Permission) => boolean;
  onDelete: (c: Comment) => void;
}): ColumnDef<Comment>[] {
  const { can, onDelete } = opts;
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <TableCellUser name={row.original.user_name} /> },
    { id: 'context', header: 'Post Context', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'comment', header: 'Comment', cell: ({ row }) => (
      <span className="gc-table-cell-primary max-w-xs block">
        {row.original.is_deleted ? <span className="italic text-slate-400">[Removed by admin]</span> : truncate(row.original.content, 80)}
      </span>
    )},
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.is_deleted ? 'deleted' : 'active'} /> },
    { accessorKey: 'likes_count', header: 'Likes', cell: ({ row }) => <span className="tabular-nums">{row.original.likes_count}</span> },
    { accessorKey: 'created_at', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <TableCellActions>
        {can(PERMISSIONS.DELETE_COMMENTS) && !row.original.is_deleted && (
          <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Remove"><Trash2 size={14} /></button>
        )}
      </TableCellActions>
    ), enableSorting: false },
  ];
}

// ── Events ────────────────────────────────────────────────
export function getEventsColumns(opts: {
  can: (p: Permission) => boolean;
  onStatusChange: (id: string, status: string) => void;
  onDelete: (e: ParlourEvent) => void;
}): ColumnDef<ParlourEvent>[] {
  const { can, onStatusChange, onDelete } = opts;
  return [
    { accessorKey: 'title', header: 'Title', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { id: 'type', header: 'Type', cell: ({ row }) => <span className="gc-badge bg-violet-50 text-violet-700 capitalize">{row.original.event_type}</span> },
    { accessorKey: 'start_datetime', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDateTime(row.original.start_datetime)}</span> },
    { id: 'participants', header: 'Participants', cell: ({ row }) => (
      <span className="gc-table-cell-primary tabular-nums">
        {row.original.current_participants}{row.original.max_participants != null && `/${row.original.max_participants}`}
      </span>
    )},
    { id: 'fee', header: 'Entry Fee', cell: ({ row }) => row.original.entry_fee > 0
      ? <span className="gc-table-cell-primary">{formatCurrency(row.original.entry_fee)}</span>
      : <span className="gc-table-cell-sub">Free</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <TableCellActions>
        {can(PERMISSIONS.EDIT_EVENTS) && (
          <Select value={row.original.status} onChange={e => onStatusChange(row.original.id, e.target.value)} className="w-auto text-xs py-1">
            {TOURNAMENT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        )}
        {can(PERMISSIONS.DELETE_EVENTS) && (
          <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
        )}
      </TableCellActions>
    ), enableSorting: false },
  ];
}

// ── Community ─────────────────────────────────────────────
export function getCommunityColumns(opts: {
  can: (p: Permission) => boolean;
  onPin: (id: string, pinned: boolean) => void;
  onDelete: (p: CommunityPost) => void;
}): ColumnDef<CommunityPost>[] {
  const { can, onPin, onDelete } = opts;
  return [
    { id: 'author', header: 'Author', cell: ({ row }) => (
      <TableCellUser
        name={row.original.author_name}
        avatar={row.original.is_pinned ? <div className="gc-table-avatar bg-amber-100 text-amber-600"><Pin size={12} /></div> : undefined}
      />
    )},
    { accessorKey: 'title', header: 'Title', cell: ({ row }) => <span className="gc-table-cell-primary max-w-xs truncate block">{row.original.title}</span> },
    { id: 'tag', header: 'Tag', cell: ({ row }) => row.original.game_tag
      ? <span className="gc-badge bg-indigo-50 text-indigo-700">{row.original.game_tag}</span>
      : <span className="gc-table-cell-sub">—</span> },
    { accessorKey: 'views_count', header: 'Views', cell: ({ row }) => <span className="tabular-nums">{row.original.views_count}</span> },
    { accessorKey: 'likes_count', header: 'Likes', cell: ({ row }) => <span className="tabular-nums">{row.original.likes_count}</span> },
    { accessorKey: 'comments_count', header: 'Comments', cell: ({ row }) => <span className="tabular-nums">{row.original.comments_count}</span> },
    { id: 'pinned', header: 'Pinned', cell: ({ row }) => can(PERMISSIONS.PIN_COMMUNITY) ? (
      <button
        type="button"
        onClick={() => onPin(row.original.id, !row.original.is_pinned)}
        className={`relative w-10 h-5 rounded-full transition-colors ${row.original.is_pinned ? 'bg-indigo-600' : 'bg-slate-200'}`}
        title={row.original.is_pinned ? 'Unpin' : 'Pin'}
      >
        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${row.original.is_pinned ? 'left-5' : 'left-0.5'}`} />
      </button>
    ) : <span className="gc-table-cell-sub">{row.original.is_pinned ? 'Yes' : 'No'}</span>, enableSorting: false },
    { accessorKey: 'created_at', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <TableCellActions>
        {can(PERMISSIONS.DELETE_COMMUNITY) && (
          <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
        )}
      </TableCellActions>
    ), enableSorting: false },
  ];
}

// ── Ratings ───────────────────────────────────────────────
function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} size={12} className={i < rating ? 'text-amber-400 fill-amber-400' : 'text-slate-200'} />
      ))}
    </div>
  );
}

export function getRatingsColumns(opts: {
  can: (p: Permission) => boolean;
  onDelete: (r: Rating) => void;
}): ColumnDef<Rating>[] {
  const { can, onDelete } = opts;
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <TableCellUser name={row.original.user_name} /> },
    { id: 'parlor', header: 'Parlor', cell: ({ row }) => <TableCellUser name={row.original.parlor_name} square avatarColor="bg-violet-100 text-violet-600" /> },
    { accessorKey: 'rating', header: 'Rating', cell: ({ row }) => <StarRating rating={row.original.rating} /> },
    { id: 'review', header: 'Review', cell: ({ row }) => (
      <span className="gc-table-cell-primary max-w-xs block">
        {row.original.review ? truncate(row.original.review, 60) : <span className="gc-table-cell-sub">—</span>}
      </span>
    )},
    { accessorKey: 'created_at', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500 whitespace-nowrap">{formatDate(row.original.created_at)}</span> },
    { id: 'actions', header: '', cell: ({ row }) => (
      <TableCellActions>
        {can(PERMISSIONS.DELETE_RATINGS) && (
          <button onClick={() => onDelete(row.original)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete"><Trash2 size={14} /></button>
        )}
      </TableCellActions>
    ), enableSorting: false },
  ];
}

// ── Notifications history ─────────────────────────────────
export function getNotificationHistoryColumns(): ColumnDef<NotificationHistory>[] {
  return [
    { accessorKey: 'type', header: 'Type', cell: ({ row }) => <span className="gc-table-cell-primary capitalize">{row.original.type}</span> },
    { accessorKey: 'title', header: 'Title', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { accessorKey: 'body', header: 'Message', cell: ({ row }) => <span className="gc-table-cell-sub max-w-xs truncate block">{row.original.body}</span> },
    { accessorKey: 'target', header: 'Target', cell: ({ row }) => <span className="capitalize">{row.original.target.replace('_', ' ')}</span> },
    { accessorKey: 'sent_to', header: 'Sent to', cell: ({ row }) => <span className="tabular-nums">{row.original.sent_to}</span> },
    { accessorKey: 'sent_at', header: 'Sent at', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDate(row.original.sent_at)}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
  ];
}

// ── Roles ─────────────────────────────────────────────────
export function getRoleUsersColumns(): ColumnDef<User>[] {
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <TableCellUser name={row.original.name} /> },
    { id: 'email', header: 'Email', cell: ({ row }) => <span className="gc-table-cell-sub">{row.original.email ?? row.original.phone}</span> },
    { id: 'active', header: 'Last Active', cell: ({ row }) => (
      <span className="text-sm text-slate-500">{row.original.last_active ? timeAgo(row.original.last_active) : formatDate(row.original.created_at)}</span>
    )},
    { id: 'status', header: 'Status', cell: ({ row }) => (
      <span className={`gc-badge ${row.original.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
        {row.original.is_active ? 'Active' : 'Banned'}
      </span>
    )},
  ];
}

export interface PermCompareRow { key: Permission; label: string }

export function getPermissionCompareColumns(): ColumnDef<PermCompareRow>[] {
  const roles = Object.values(ROLES) as Role[];
  return [
    { accessorKey: 'label', header: 'Permission', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.label}</span> },
    ...roles.map(role => ({
      id: role,
      header: ROLE_META[role].label,
      cell: ({ row }: { row: { original: PermCompareRow } }) => (
        <div className="text-center">
          {ROLE_PERMISSIONS[role].includes(row.original.key)
            ? <span className="text-emerald-500 text-base" aria-label="Yes">✓</span>
            : <span className="text-slate-200 text-base" aria-label="No">✕</span>}
        </div>
      ),
      enableSorting: false,
    })),
  ];
}

export function buildPermissionCompareRows(): PermCompareRow[] {
  return PERMISSION_GROUPS.flatMap(g =>
    g.perms.map(p => ({ key: p.key, label: p.label })),
  );
}

// ── Owner dashboard ───────────────────────────────────────
export function getOwnerBookingColumns(): ColumnDef<Booking>[] {
  return [
    { id: 'user', header: 'User', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.user_name}</span> },
    { id: 'event', header: 'Event', cell: ({ row }) => <span className="gc-table-cell-sub truncate max-w-[12rem] block">{row.original.event_title}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { id: 'date', header: 'Booked', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDate(row.original.created_at)}</span> },
  ];
}

export function getOwnerEventColumns(): ColumnDef<ParlourEvent>[] {
  return [
    { accessorKey: 'title', header: 'Event', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { id: 'date', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDateTime(row.original.start_datetime)}</span> },
    { id: 'participants', header: 'Participants', cell: ({ row }) => (
      <span className="tabular-nums text-slate-600">
        {row.original.current_participants}{row.original.max_participants ? `/${row.original.max_participants}` : ''}
      </span>
    )},
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
  ];
}

// ── Parlor detail tabs ────────────────────────────────────
export function getParlorTournamentColumns(): ColumnDef<Tournament>[] {
  return [
    { accessorKey: 'title', header: 'Tournament', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { id: 'slots', header: 'Slots', cell: ({ row }) => (
      <span className="tabular-nums text-slate-600">{row.original.booked_slots}/{row.original.total_slots}</span>
    )},
    { id: 'fee', header: 'Entry Fee', cell: ({ row }) => <span className="gc-table-cell-primary">{formatCurrency(row.original.entry_fee)}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
  ];
}

export function getParlorEventColumns(): ColumnDef<ParlourEvent>[] {
  return [
    { accessorKey: 'title', header: 'Event', cell: ({ row }) => <span className="gc-table-cell-primary">{row.original.title}</span> },
    { id: 'date', header: 'Date', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDateTime(row.original.start_datetime)}</span> },
    { id: 'status', header: 'Status', cell: ({ row }) => <StatusBadge status={row.original.status} /> },
  ];
}

export function getParlorPostColumns(): ColumnDef<Post>[] {
  return [
    { id: 'content', header: 'Post', cell: ({ row }) => <span className="gc-table-cell-primary line-clamp-2 max-w-md">{row.original.content}</span> },
    { id: 'likes', header: 'Likes', cell: ({ row }) => <span className="tabular-nums text-slate-600">{row.original.likes_count}</span> },
    { id: 'date', header: 'Posted', cell: ({ row }) => <span className="text-sm text-slate-500">{formatDate(row.original.created_at)}</span> },
  ];
}