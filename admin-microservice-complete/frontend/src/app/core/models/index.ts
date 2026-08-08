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
  is_active?: boolean;
  is_deleted?: boolean;
  business_status?: string | null;
  opening_hours?: Record<string, unknown> | null;
  price_per_hour?: number | null;
  original_price?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ParlorCreateRequest {
  name: string;
  address?: string | null;
  phone?: string | null;
  website?: string | null;
  image_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  primary_type?: string | null;
  game_types?: string[];
  owner_id?: string | null;
  is_verified?: boolean;
  is_active?: boolean;
  price_per_hour?: number | null;
  original_price?: number | null;
  opening_hours?: Record<string, unknown> | null;
}

export interface ParlorUpdateRequest extends Partial<ParlorCreateRequest> {
  business_status?: string | null;
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
  offset?: number;
  range?: string;
  view?: string;
  from_date?: string;
  to_date?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Club Management (platform oversight — read-only views + platform overrides)
// Money fields are integer paise. *_bps fields: 10000 = 100%.
// ─────────────────────────────────────────────────────────────────────────────

export type ClubResourceType = 'seat' | 'pc' | 'console' | 'ps5' | 'pool' | 'vr' | 'other';

export type ClubResourceStatus =
  | 'available'
  | 'occupied'
  | 'reserved'
  | 'maintenance'
  | 'offline';

export type ClubRevenueRange = 'today' | 'week' | 'month';

export type ClubBookingView = 'day' | 'week';

export interface ClubSummary {
  parlor_id: string;
  name: string;
  owner_id: string | null;
}

export interface ClubListResponse {
  items: ClubSummary[];
  limit: number;
  offset: number;
}

export interface ClubResource {
  id: string;
  label: string;
  resource_type: ClubResourceType;
  status: ClubResourceStatus;
  zone_name: string | null;
  zone_id: string | null;
  hourly_rate_override_paise: number | null;
  layout_x: number | null;
  layout_y: number | null;
  is_active: boolean;
  status_note: string | null;
}

export interface ClubResourceListResponse {
  parlor_id: string;
  items: ClubResource[];
}

export interface ClubOccupant {
  booking_id: string;
  booking_ref: string | null;
  resource_id: string | null;
  resource_label: string | null;
  resource_type: ClubResourceType | null;
  customer_name: string | null;
  contact_phone: string | null;
  checked_in_at: string | null;
  ends_at: string | null;
  minutes_remaining: number | null;
  is_overdue: boolean;
  units: number | null;
  amount_paise: number | null;
}

export interface ClubLiveResponse {
  parlor_id: string;
  occupants: ClubOccupant[];
}

export interface ClubRevenueByResourceType {
  resource_type: string;
  gross_paise: number;
  booking_count: number;
}

export interface ClubRevenueByPaymentMethod {
  payment_method: string;
  gross_paise: number;
  booking_count: number;
}

export interface ClubRevenueDailyPoint {
  date: string;
  gross_paise: number;
  net_paise: number;
  booking_count: number;
}

export interface ClubRevenueSummary {
  range: ClubRevenueRange;
  from_date: string;
  to_date: string;
  gross_paise: number;
  gross_rupees: number;
  commission_paise: number;
  net_paise: number;
  net_rupees: number;
  discount_paise: number;
  booking_count: number;
  completed_count: number;
  cancelled_count: number;
  no_show_count: number;
  avg_session_paise: number;
  by_resource_type: ClubRevenueByResourceType[];
  by_payment_method: ClubRevenueByPaymentMethod[];
  daily: ClubRevenueDailyPoint[];
}

export interface ClubHeatmapCell {
  weekday: number;
  hour: number;
  occupied_minutes: number;
  capacity_minutes: number;
  utilization_bps: number;
  booking_count: number;
}

export interface ClubUtilizationRow {
  grain: string;
  grain_key: string;
  label: string;
  occupied_minutes: number;
  capacity_minutes: number;
  utilization_bps: number;
  booking_count: number;
  revenue_paise: number;
}

export interface ClubNoShowByResourceType {
  resource_type: string;
  booking_count: number;
  no_show_count: number;
  no_show_rate_bps: number;
}

export interface ClubNoShowSummary {
  from_date: string;
  to_date: string;
  booking_count: number;
  no_show_count: number;
  no_show_rate_bps: number;
  by_resource_type: ClubNoShowByResourceType[];
}

export interface ClubOccupancyResponse {
  parlor_id: string;
  from_date: string;
  to_date: string;
  heatmap: ClubHeatmapCell[];
  utilization: ClubUtilizationRow[];
  no_show: ClubNoShowSummary;
}

export interface ClubBooking {
  id: string;
  booking_ref: string | null;
  slot_date: string | null;
  start_time: string | null;
  booking_status: string;
  payment_status: string | null;
  amount_paise: number | null;
  commission_paise: number | null;
  is_walk_in: boolean;
  station_type: string | null;
  guest_name: string | null;
  contact_phone: string | null;
}

export interface ClubBookingListResponse {
  parlor_id: string;
  items: ClubBooking[];
}

export interface ClubPromotion {
  id: string;
  name: string;
  promo_type: string;
  percent_bps: number | null;
  flat_paise: number | null;
  code: string | null;
  used_count: number;
  usage_limit: number | null;
  is_active: boolean;
  disabled_by_platform: boolean;
  disabled_reason: string | null;
  valid_from: string | null;
  valid_to: string | null;
}

export interface ClubPromotionListResponse {
  parlor_id: string;
  items: ClubPromotion[];
}

export interface ClubCustomer {
  id: string;
  display_name: string | null;
  phone: string | null;
  user_id: string | null;
  visit_count: number;
  total_spend_paise: number;
  loyalty_points: number;
  is_banned: boolean;
  ban_reason: string | null;
  platform_flagged: boolean;
  platform_flag_reason: string | null;
  last_visit_at: string | null;
}

export interface ClubCustomerListResponse {
  parlor_id: string;
  items: ClubCustomer[];
  total: number;
}

export interface ClubForceCancelResponse {
  id: string;
  booking_status: string;
  cancelled_by: string | null;
  cancellation_reason: string | null;
}

export interface ClubPromotionOverrideResponse {
  id: string;
  disabled_by_platform: boolean;
  disabled_reason: string | null;
}

export interface ClubResourceOverrideResponse {
  id: string;
  is_active: boolean;
  status: ClubResourceStatus;
  status_note: string | null;
}

export interface ClubCustomerFlagResponse {
  id: string;
  platform_flagged: boolean;
  platform_flag_reason: string | null;
}