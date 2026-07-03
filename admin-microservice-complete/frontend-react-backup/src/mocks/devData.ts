import type {
  User, Parlor, ParlorDetail, Tournament, Booking, Post, Comment,
  ParlourEvent, CommunityPost, Rating, AdminStats, AnalyticsData,
  NotificationHistory, OwnerStats, PaginatedResponse, AuthResponse, TableParams,
} from '../types';

export const DEV_PHONE = '9999999999';
export const DEV_OTP = '123456';

const USERS: User[] = [
  { id: 'u1', name: 'Manish Kumar', phone: '+919999999999', email: 'admin@gameconnect.in', role: 'super_admin', is_active: true, created_at: '2026-01-15T10:00:00Z', following_count: 12, likes_count: 45, bookings_count: 3 },
  { id: 'u2', name: 'Priya Sharma', phone: '+919876543210', email: 'priya@gameconnect.in', role: 'admin', is_active: true, created_at: '2026-02-01T08:00:00Z', following_count: 8, likes_count: 22, bookings_count: 5 },
  { id: 'u3', name: 'Rahul Gaming', phone: '+919111111111', email: 'rahul@gmail.com', role: 'user', is_active: true, created_at: '2026-03-10T12:00:00Z', following_count: 34, likes_count: 120, bookings_count: 12 },
  { id: 'u4', name: 'Arena Zone Owner', phone: '+919222222222', email: 'owner@arenazone.in', role: 'parlor_owner', is_active: true, created_at: '2026-02-20T09:00:00Z', parlor_name: 'Arena Zone', following_count: 0, likes_count: 5, bookings_count: 0 },
  { id: 'u5', name: 'Banned User', phone: '+919333333333', email: 'banned@test.com', role: 'user', is_active: false, created_at: '2026-01-05T14:00:00Z' },
];

const PARLORS: Parlor[] = [
  { id: 'p1', name: 'Arena Zone', logo_url: '', address: 'MG Road, Bangalore', game_types: ['Valorant', 'CS2', 'FIFA'], is_verified: true, follower_count: 1250, post_count: 48, avg_rating: 4.6, rating_count: 89, owner_name: 'Arena Zone Owner', owner_phone: '+919222222222', created_at: '2026-01-10T10:00:00Z' },
  { id: 'p2', name: 'GameHub Pro', address: 'Koramangala, Bangalore', game_types: ['PUBG', 'BGMI'], is_verified: false, follower_count: 340, post_count: 12, avg_rating: 4.1, rating_count: 23, owner_name: 'Vikram Singh', owner_phone: '+919444444444', created_at: '2026-04-01T10:00:00Z' },
  { id: 'p3', name: 'Cyber Café X', address: 'Indiranagar, Bangalore', game_types: ['Dota 2', 'LoL'], is_verified: true, follower_count: 890, post_count: 31, avg_rating: 4.8, rating_count: 56, owner_name: 'Anita Reddy', created_at: '2026-02-15T10:00:00Z' },
];

const TOURNAMENTS: Tournament[] = [
  { id: 't1', title: 'Valorant Weekend Cup', game_type: 'Valorant', parlor_name: 'Arena Zone', start_time: '2026-07-05T18:00:00Z', total_slots: 16, booked_slots: 12, entry_fee: 500, status: 'open', created_at: '2026-06-01T10:00:00Z' },
  { id: 't2', title: 'CS2 Pro League', game_type: 'CS2', parlor_name: 'Cyber Café X', start_time: '2026-07-10T14:00:00Z', total_slots: 8, booked_slots: 8, entry_fee: 1000, status: 'live', created_at: '2026-06-05T10:00:00Z' },
];

const BOOKINGS: Booking[] = [
  { id: 'b1', booking_type: 'tournament', user_name: 'Rahul Gaming', user_phone: '+919111111111', parlor_name: 'Arena Zone', event_title: 'Valorant Weekend Cup', slot_number: 3, status: 'confirmed', payment_status: 'paid', created_at: '2026-06-20T10:00:00Z', price: 500 },
  { id: 'b2', booking_type: 'slot', user_name: 'Priya Sharma', parlor_name: 'GameHub Pro', event_title: 'PUBG', status: 'pending', payment_status: 'pending', created_at: '2026-06-25T15:00:00Z', price: 200 },
];

const POSTS: Post[] = [
  { id: 'post1', parlor_name: 'Arena Zone', content: 'New gaming rigs installed! RTX 4090 on every station. Come try them this weekend 🎮', media_count: 3, likes_count: 45, comments_count: 12, created_at: '2026-06-22T10:00:00Z' },
];

const COMMENTS: Comment[] = [
  { id: 'c1', user_name: 'Rahul Gaming', post_id: 'post1', parlor_name: 'Arena Zone', content: 'This is amazing! Can\'t wait to try.', is_deleted: false, likes_count: 5, created_at: '2026-06-22T11:00:00Z' },
  { id: 'c2', user_name: 'Banned User', post_id: 'post1', parlor_name: 'Arena Zone', content: '[Removed by admin]', is_deleted: true, likes_count: 0, created_at: '2026-06-22T12:00:00Z' },
];

const EVENTS: ParlourEvent[] = [
  { id: 'e1', title: 'Friday Night Fights', event_type: 'tournament', parlor_name: 'Arena Zone', start_datetime: '2026-07-04T20:00:00Z', entry_fee: 0, max_participants: 32, current_participants: 18, status: 'open', is_featured: true, created_at: '2026-06-01T10:00:00Z' },
];

const COMMUNITY: CommunityPost[] = [
  { id: 'cp1', title: 'Best Valorant settings for low-end PCs', author_name: 'Rahul Gaming', game_tag: 'Valorant', likes_count: 89, comments_count: 23, views_count: 1200, is_pinned: true, created_at: '2026-06-15T10:00:00Z' },
];

const RATINGS: Rating[] = [
  { id: 'r1', user_name: 'Rahul Gaming', parlor_name: 'Arena Zone', rating: 5, review: 'Best gaming café in Bangalore!', created_at: '2026-06-10T10:00:00Z' },
  { id: 'r2', user_name: 'Priya Sharma', parlor_name: 'GameHub Pro', rating: 3, review: 'Good but needs better AC', created_at: '2026-06-12T10:00:00Z' },
];

const NOTIFICATION_HISTORY: NotificationHistory[] = [
  { id: 'n1', type: 'info', title: 'New Feature!', body: 'Tournament brackets are now live', target: 'all', sent_to: 1250, sent_at: '2026-06-20T10:00:00Z', status: 'sent' },
  { id: 'n2', type: 'promotion', title: 'Weekend Sale', body: '50% off slot bookings', target: 'users', sent_to: 890, sent_at: '2026-06-18T10:00:00Z', status: 'sent' },
];

function paginate<T>(items: T[], p: TableParams): PaginatedResponse<T> {
  const page = Number(p.page ?? 1);
  const limit = Number(p.limit ?? 20);
  let filtered = [...items];
  if (p.search) {
    const s = String(p.search).toLowerCase();
    filtered = filtered.filter(item =>
      JSON.stringify(item).toLowerCase().includes(s)
    );
  }
  if (p.role) filtered = filtered.filter((u: T) => (u as User).role === p.role);
  if (p.is_active !== undefined) filtered = filtered.filter((u: T) => (u as User).is_active === p.is_active);
  if (p.is_verified !== undefined) filtered = filtered.filter((item: T) => (item as Parlor).is_verified === p.is_verified);
  if (p.status) filtered = filtered.filter((item: T) => (item as Tournament).status === p.status);
  if (p.booking_type) filtered = filtered.filter((b: T) => (b as Booking).booking_type === p.booking_type);
  if (p.is_deleted !== undefined) filtered = filtered.filter((c: T) => (c as Comment).is_deleted === p.is_deleted);
  if (p.user_id) filtered = filtered.filter((b: T) => (b as Booking).user_name && USERS.find(u => u.id === p.user_id)?.name === (b as Booking).user_name);
  if (p.parlor_id) {
    const parlor = PARLORS.find(x => x.id === p.parlor_id);
    if (parlor) filtered = filtered.filter((item: T) => JSON.stringify(item).includes(parlor.name));
  }
  if (p.min_rating) filtered = filtered.filter((r: T) => (r as Rating).rating >= Number(p.min_rating));
  if (p.max_rating) filtered = filtered.filter((r: T) => (r as Rating).rating <= Number(p.max_rating));
  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / limit));
  const start = (page - 1) * limit;
  return { items: filtered.slice(start, start + limit), total, page, limit, pages };
}

const delay = (ms = 300) => new Promise(r => setTimeout(r, ms));

export const devApi = {
  sendOtp: async () => { await delay(); return { data: { ok: true } }; },

  verifyOtp: async (phone: string, otp: string): Promise<{ data: AuthResponse }> => {
    await delay();
    if (otp !== DEV_OTP) throw new Error('Invalid OTP');
    const digits = phone.replace(/\D/g, '').slice(-10);
    const user = digits === '9222222222'
      ? USERS.find(u => u.role === 'parlor_owner')!
      : USERS.find(u => u.role === 'super_admin')!;
    return {
      data: {
        access_token: 'dev-mock-access-token',
        refresh_token: 'dev-mock-refresh-token',
        user,
      },
    };
  },

  devLogin: async (role: User['role'] = 'super_admin'): Promise<AuthResponse> => {
    await delay(200);
    const user = USERS.find(u => u.role === role) ?? USERS[0];
    return {
      access_token: 'dev-mock-access-token',
      refresh_token: 'dev-mock-refresh-token',
      user,
    };
  },

  getStats: async (): Promise<AdminStats> => {
    await delay();
    return {
      total_users: 1250, total_parlors: 48, total_tournaments: 23, total_bookings: 890,
      total_slot_bookings: 456, total_posts: 320, total_events: 67, total_community_posts: 145,
      total_ratings: 234, new_users_today: 12, new_bookings_today: 34, active_tournaments: 8,
      pending_verification: 3, reported_content: 2, total_revenue: 125000,
    };
  },

  getAnalytics: async (): Promise<AnalyticsData> => {
    await delay();
    const days = Array.from({ length: 14 }, (_, i) => {
      const d = new Date(); d.setDate(d.getDate() - (13 - i));
      return d.toISOString().slice(0, 10);
    });
    return {
      users_growth: days.map(d => ({ date: d, count: Math.floor(Math.random() * 20) + 5 })),
      bookings_per_day: days.map(d => ({ date: d, count: Math.floor(Math.random() * 40) + 10 })),
      posts_per_day: days.map(d => ({ date: d, count: Math.floor(Math.random() * 15) + 2 })),
      game_type_distribution: [
        { name: 'Valorant', value: 35 }, { name: 'CS2', value: 25 },
        { name: 'PUBG', value: 20 }, { name: 'FIFA', value: 12 }, { name: 'Other', value: 8 },
      ],
      top_parlors: PARLORS.map(p => ({
        parlor_id: p.id, parlor_name: p.name,
        bookings_count: Math.floor(Math.random() * 200) + 50,
        revenue: Math.floor(Math.random() * 50000) + 10000,
      })),
    };
  },

  getUsers: async (p: TableParams) => { await delay(); return paginate(USERS, p); },
  getUser: async (id: string) => { await delay(); const u = USERS.find(x => x.id === id); if (!u) throw new Error('Not found'); return u; },
  getParlors: async (p: TableParams) => { await delay(); return paginate(PARLORS, p); },
  getParlor: async (id: string): Promise<ParlorDetail> => {
    await delay();
    const p = PARLORS.find(x => x.id === id);
    if (!p) throw new Error('Not found');
    return { ...p, hours: '10 AM – 11 PM', rating_distribution: [{ stars: 5, count: 45 }, { stars: 4, count: 28 }, { stars: 3, count: 10 }, { stars: 2, count: 4 }, { stars: 1, count: 2 }], gallery_urls: [] };
  },
  getTournaments: async (p: TableParams) => { await delay(); return paginate(TOURNAMENTS, p); },
  getBookings: async (p: TableParams) => { await delay(); return paginate(BOOKINGS, p); },
  getPosts: async (p: TableParams) => { await delay(); return paginate(POSTS, p); },
  getComments: async (p: TableParams) => { await delay(); return paginate(COMMENTS, p); },
  getEvents: async (p: TableParams) => { await delay(); return paginate(EVENTS, p); },
  getCommunity: async (p: TableParams) => { await delay(); return paginate(COMMUNITY, p); },
  getRatings: async (p: TableParams) => { await delay(); return paginate(RATINGS, p); },
  getNotificationHistory: async (p?: TableParams) => { await delay(); return paginate(NOTIFICATION_HISTORY, p ?? {}); },
  getOwnerStats: async (): Promise<OwnerStats> => ({
    today_bookings: 8, week_revenue: 12500, followers: 1250, avg_rating: 4.6,
    bookings_trend: Array.from({ length: 7 }, (_, i) => ({ date: `2026-06-${22 + i}`, count: Math.floor(Math.random() * 15) + 3 })),
    revenue_per_week: [{ week: 'W1', revenue: 8000 }, { week: 'W2', revenue: 12500 }, { week: 'W3', revenue: 10200 }],
  }),

  noop: async () => { await delay(100); },
};

export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';