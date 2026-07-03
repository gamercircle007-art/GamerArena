export type Role = 'super_admin'|'admin'|'parlor_owner'|'user';
export interface User { id:string; name:string; phone?:string; email?:string; role:Role; is_active:boolean; avatar_url?:string; fcm_token?:string; created_at:string; parlor_name?:string; bookings_count?:number; following_count?:number; likes_count?:number; last_active?:string; }
export interface Parlor { id:string; name:string; logo_url?:string; address?:string; game_types?:string[]; is_verified:boolean; follower_count:number; post_count:number; avg_rating:number; rating_count:number; owner_name:string; owner_phone?:string; created_at:string; }
export interface ParlorDetail extends Parlor { hours?:string; rating_distribution?:{stars:number;count:number}[]; gallery_urls?:string[]; }
export interface Tournament { id:string; title:string; game_type?:string; parlor_name:string; start_time:string; total_slots:number; booked_slots:number; entry_fee:number; status:string; created_at:string; }
export interface Booking { id:string; booking_type:string; user_name:string; user_phone?:string; parlor_name:string; event_title:string; slot_number?:number; status:string; payment_status:string; created_at:string; price?:number; }
export interface Post { id:string; parlor_name:string; content:string; media_count:number; likes_count:number; comments_count:number; created_at:string; }
export interface Comment { id:string; user_name:string; post_id:string; parlor_name:string; content:string; is_deleted:boolean; likes_count:number; created_at:string; }
export interface ParlourEvent { id:string; title:string; event_type:string; parlor_name:string; start_datetime:string; entry_fee:number; max_participants?:number; current_participants:number; status:string; is_featured:boolean; created_at:string; }
export interface CommunityPost { id:string; title:string; author_name:string; game_tag?:string; likes_count:number; comments_count:number; views_count:number; is_pinned:boolean; created_at:string; }
export interface Rating { id:string; user_name:string; parlor_name:string; rating:number; review?:string; created_at:string; }
export interface NotificationHistory { id:string; type:string; title:string; body:string; target:string; sent_to:number; sent_at:string; status:string; }
export interface OwnerStats { today_bookings:number; week_revenue:number; followers:number; avg_rating:number; bookings_trend:DayCount[]; revenue_per_week:{week:string;revenue:number}[]; }
export interface PaginatedResponse<T> { items:T[]; total:number; page:number; limit:number; pages:number; }
export interface ApiError { message:string; code?:string; }
export interface AdminStats { total_users:number; total_parlors:number; total_tournaments:number; total_bookings:number; total_slot_bookings:number; total_posts:number; total_events:number; total_community_posts:number; total_ratings:number; new_users_today:number; new_bookings_today:number; active_tournaments:number; pending_verification:number; reported_content:number; total_revenue?:number; }
export interface DayCount { date:string; count:number; }
export interface ParlorStat { parlor_id:string; parlor_name:string; bookings_count:number; revenue:number; }
export interface AnalyticsData { users_growth:DayCount[]; bookings_per_day:DayCount[]; top_parlors:ParlorStat[]; posts_per_day:DayCount[]; game_type_distribution:{name:string;value:number}[]; }
export interface AuthTokens { access_token:string; refresh_token:string; }
export interface AuthResponse extends AuthTokens { user:User; }
export interface BroadcastRequest { title:string; body:string; target:'all'|'users'|'parlor_owners'; type?:string; }
export interface TableParams { page?:number; limit?:number; search?:string; [k:string]:string|number|boolean|undefined; }