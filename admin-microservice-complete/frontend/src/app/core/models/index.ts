export type UserRole = 'user' | 'parlor_owner' | 'admin' | 'super_admin';
export type MediaType = 'text' | 'image' | 'video' | 'reel';
export type TournamentStatus = 'draft' | 'open' | 'full' | 'live' | 'completed' | 'cancelled';

export interface User {
  id: string;
  name: string | null;
  username: string | null;
  email: string | null;
  phone_number: string | null;
  role: UserRole;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  latitude: number | null;
  longitude: number | null;
  city: string | null;
  country: string | null;
  location_updated_at: string | null;
  created_at: string;
  updated_at: string;
  parlor_name?: string | null;
  bookings_count?: number;
  likes_count?: number;
  following_count?: number;
  reviews_count?: number;
}

export interface ParlorSummary {
  id: string;
  name: string;
  logo_url: string | null;
  is_verified: boolean;
}

export interface Parlor {
  id: string;
  owner_id: string | null;
  name: string;
  description: string | null;
  logo_url: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  game_types: string[];
  is_verified: boolean;
  follower_count: number;
  post_count: number;
  is_following: boolean;
  rating: number | null;
  phone: string | null;
  website: string | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  content: string;
  media_urls: string[];
  media_type: MediaType;
  parlor_id: string;
  parlor?: ParlorSummary;
  tournament_id?: string | null;
  likes_count: number;
  comments_count: number;
  geo_lat?: number | null;
  geo_lng?: number | null;
  created_at: string;
}

export interface Comment {
  id: string;
  user_id: string;
  user?: { id: string; name: string | null; avatar_url: string | null };
  content: string;
  parent_id: string | null;
  likes_count: number;
  is_deleted: boolean;
  reply_count: number;
  post_id?: string;
  post_preview?: string;
  created_at: string;
}

export interface Like {
  id: string;
  user_id: string;
  user?: { id: string; name: string | null; avatar_url: string | null };
  target_type: 'post' | 'comment' | 'reel';
  target_id: string;
  target_preview?: string;
  parlor_name?: string;
  created_at: string;
}

export interface Tournament {
  id: string;
  parlor_id: string;
  parlor?: ParlorSummary;
  title: string;
  game_type: string;
  format: string;
  start_time: string;
  end_time: string;
  total_slots: number;
  booked_slots: number;
  entry_fee: number;
  status: TournamentStatus;
  created_at: string;
  updated_at: string;
}

export interface Booking {
  id: string;
  tournament_id: string;
  user_id: string;
  user?: User;
  tournament?: Tournament;
  slot_number: number;
  status: string;
  payment_status: string;
  booking_type?: 'tournament' | 'slot';
  created_at: string;
}

export interface GamingBooking {
  id: string;
  booking_ref: string;
  user_id: string;
  user?: { id: string; name: string | null; username?: string | null };
  parlour_id: string;
  parlor?: ParlorSummary;
  slot_id: string | null;
  offer_id: string | null;
  guest_name: string | null;
  num_players: number;
  slot_date: string | null;
  start_time: string | null;
  end_time: string | null;
  hours_booked: number | null;
  price_per_hour: number | null;
  total_price: number | null;
  final_price: number | null;
  payment_mode: string;
  payment_status: string;
  booking_status: string;
  refund_amount: number;
  refund_status: string | null;
  gc_points_earned: number;
  created_at: string;
}

export interface GamingSlot {
  id: string;
  parlour_id: string;
  parlor?: ParlorSummary;
  game: string | null;
  slot_date: string;
  start_time: string;
  end_time: string;
  price_per_hour: number;
  original_price: number | null;
  max_players: number;
  current_bookings: number;
  is_available: boolean;
}

export interface Offer {
  id: string;
  parlour_id: string;
  parlor?: ParlorSummary;
  title: string;
  description: string | null;
  discount_type: 'percentage' | 'flat';
  discount_value: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
}

export interface OfferCreateRequest {
  parlour_id: string;
  title: string;
  description?: string;
  discount_type: 'percentage' | 'flat';
  discount_value: number;
  valid_from: string;
  valid_until: string;
  is_active?: boolean;
}

export interface GcPointsEntry {
  id: string;
  user_id: string;
  user?: { id: string; name: string | null };
  points: number;
  source: string;
  booking_ref?: string | null;
  created_at: string;
}

export interface ParlourEvent {
  id: string;
  parlor_id: string;
  parlor?: ParlorSummary;
  title: string;
  event_type: string;
  cover_url: string | null;
  start_time: string;
  max_participants: number;
  participant_count: number;
  entry_fee: number;
  status: string;
  created_at: string;
}

export interface CommunityPost {
  id: string;
  author_id: string;
  author?: { id: string; name: string | null };
  title: string;
  tag: string | null;
  views_count: number;
  likes_count: number;
  comments_count: number;
  is_pinned: boolean;
  created_at: string;
}

export interface Rating {
  id: string;
  user_id: string;
  parlor_id: string;
  user?: { id: string; name: string | null };
  parlor?: ParlorSummary;
  rating: number;
  review: string | null;
  created_at: string;
}

export interface AdminStats {
  users: number;
  parlors: number;
  tournaments: number;
  bookings: number;
  posts?: number;
  revenue?: number;
  new_users_today?: number;
  pending_verification?: number;
  status?: string;
}

export interface DayCount {
  date: string;
  count: number;
}

export interface ParlorStat {
  parlor_id: string;
  parlor_name: string;
  bookings_count: number;
}

export interface ParlorRevenueStat {
  parlor_id: string;
  parlor_name: string;
  revenue: number;
}

export interface AnalyticsData {
  period: string;
  user_growth: DayCount[];
  bookings_per_day: DayCount[];
  posts_per_day: DayCount[];
  revenue_per_day: DayCount[];
  game_distribution: { label: string; value: number }[];
  top_parlors: ParlorStat[];
  top_parlors_by_revenue: ParlorRevenueStat[];
  total_users: number;
  new_users: number;
  total_bookings: number;
  revenue: number;
  conversion_rate: number;
  cancellation_rate: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface MediaAssetItem {
  id: string;
  cdn_url: string;
  thumbnail_url?: string;
  asset_type: string;
  original_filename?: string;
  file_size_label?: string;
  context: string;
  uploader_name?: string;
  status: string;
  is_flagged: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface BroadcastRequest {
  title: string;
  body: string;
  target: 'everyone' | 'gamers' | 'parlor_owners';
  type: 'info' | 'alert' | 'promo' | 'event';
}

export interface BroadcastHistory {
  id: string;
  type: 'info' | 'alert' | 'promo' | 'event';
  title: string;
  body: string;
  target: 'everyone' | 'gamers' | 'parlor_owners';
  sent_to: number;
  sent_at: string;
  status: string;
}

export interface Role {
  id: string;
  name: UserRole;
  description: string;
  permission_count: number;
}

export interface Permission {
  key: string;
  name: string;
  description: string;
  group: string;
}

export interface GeoActivity {
  id: string;
  user_id: string;
  user?: { id: string; name: string | null };
  latitude: number;
  longitude: number;
  post_preview: string | null;
  created_at: string;
}

export interface ListParams {
  page?: number;
  limit?: number;
  search?: string;
  role?: string;
  user_id?: string;
  parlor_id?: string;
  is_active?: boolean;
  is_verified?: boolean;
  status?: string;
  media_type?: MediaType;
  is_deleted?: boolean;
  target_type?: string;
  booking_type?: string;
  type?: string;
  period?: string;
  date?: string;
  date_from?: string;
  date_to?: string;
  refund_status?: string;
}