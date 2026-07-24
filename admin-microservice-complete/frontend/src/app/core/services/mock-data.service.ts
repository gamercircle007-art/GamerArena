import { Injectable } from '@angular/core';
import {
  AdminStats,
  AnalyticsData,
  Booking,
  BroadcastHistory,
  BroadcastRequest,
  Comment,
  CommunityPost,
  DayCount,
  GamingBooking,
  GamingSlot,
  GcPointsEntry,
  GeoActivity,
  Like,
  ListParams,
  Offer,
  OfferCreateRequest,
  PaginatedResponse,
  ParlourEvent,
  Parlor,
  Post,
  Rating,
  Tournament,
  User,
} from '../models';

@Injectable({ providedIn: 'root' })
export class MockDataService {
  private mockUsers: User[] = [
    {
      id: 'u1',
      name: 'Manish Kumar',
      username: 'manishk',
      email: 'admin@gameconnect.in',
      phone_number: '+919999999999',
      role: 'super_admin',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: true,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Bangalore',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-28T10:00:00Z',
      updated_at: '2026-06-28T10:00:00Z',
    },
    {
      id: 'u2',
      name: 'Priya Sharma',
      username: 'priyas',
      email: 'priya@gameconnect.in',
      phone_number: '+919876543210',
      role: 'admin',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: true,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Bangalore',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-27T08:00:00Z',
      updated_at: '2026-06-27T08:00:00Z',
    },
    {
      id: 'u3',
      name: 'Rahul Gaming',
      username: 'rahulg',
      email: 'rahul@gmail.com',
      phone_number: '+919111111111',
      role: 'user',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: false,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Mumbai',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-26T12:00:00Z',
      updated_at: '2026-06-26T12:00:00Z',
    },
    {
      id: 'u4',
      name: 'Anita Reddy',
      username: 'anitar',
      email: 'owner@cybercafe.in',
      phone_number: '+919222222222',
      role: 'parlor_owner',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: true,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Bangalore',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-25T09:00:00Z',
      updated_at: '2026-06-25T09:00:00Z',
    },
    {
      id: 'u5',
      name: 'Vikram Singh',
      username: 'vikrams',
      email: 'vikram@gamehub.in',
      phone_number: '+919444444444',
      role: 'parlor_owner',
      avatar_url: null,
      is_active: true,
      is_verified: false,
      email_verified: false,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Pune',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-24T14:00:00Z',
      updated_at: '2026-06-24T14:00:00Z',
    },
    {
      id: 'u6',
      name: 'Deepak Mehta',
      username: 'deepakm',
      email: 'deepak@spam.com',
      phone_number: '+919555555555',
      role: 'user',
      avatar_url: null,
      is_active: false,
      is_verified: false,
      email_verified: false,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Delhi',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-20T11:00:00Z',
      updated_at: '2026-06-21T09:00:00Z',
    },
    {
      id: 'u7',
      name: 'Sneha Patel',
      username: 'snehap',
      email: 'sneha@gmail.com',
      phone_number: '+919666666666',
      role: 'user',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: true,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Ahmedabad',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-19T16:00:00Z',
      updated_at: '2026-06-19T16:00:00Z',
    },
    {
      id: 'u8',
      name: 'Karan Joshi',
      username: 'karanj',
      email: 'karan@gamehub.in',
      phone_number: '+919777777777',
      role: 'user',
      avatar_url: null,
      is_active: true,
      is_verified: true,
      email_verified: false,
      phone_verified: true,
      latitude: null,
      longitude: null,
      city: 'Pune',
      country: 'India',
      location_updated_at: null,
      created_at: '2026-06-18T08:30:00Z',
      updated_at: '2026-06-18T08:30:00Z',
    },
  ];

  private mockParlors: Parlor[] = [
    {
      id: 'p1',
      owner_id: 'u4',
      name: 'Arena Zone',
      description: 'Premium esports lounge',
      logo_url: null,
      address: 'MG Road, Bangalore',
      latitude: 12.9716,
      longitude: 77.5946,
      game_types: ['Valorant', 'CS2', 'FIFA'],
      is_verified: true,
      follower_count: 1250,
      post_count: 48,
      is_following: false,
      rating: 4.6,
      phone: '+919222222222',
      website: null,
      created_at: '2026-01-10T10:00:00Z',
      updated_at: '2026-06-20T10:00:00Z',
    },
    {
      id: 'p2',
      owner_id: 'u5',
      name: 'GameHub Pro',
      description: 'Casual gaming café',
      logo_url: null,
      address: 'Koramangala, Bangalore',
      latitude: 12.9352,
      longitude: 77.6245,
      game_types: ['PUBG', 'BGMI'],
      is_verified: false,
      follower_count: 340,
      post_count: 12,
      is_following: false,
      rating: 4.1,
      phone: '+919444444444',
      website: null,
      created_at: '2026-04-01T10:00:00Z',
      updated_at: '2026-06-22T10:00:00Z',
    },
    {
      id: 'p3',
      owner_id: null,
      name: 'Cyber Café X',
      description: '24/7 gaming center',
      logo_url: null,
      address: 'Indiranagar, Bangalore',
      latitude: 12.9784,
      longitude: 77.6408,
      game_types: ['Dota 2', 'LoL'],
      is_verified: false,
      follower_count: 890,
      post_count: 31,
      is_following: false,
      rating: 4.8,
      phone: '+919555555555',
      website: null,
      created_at: '2026-02-15T10:00:00Z',
      updated_at: '2026-06-21T10:00:00Z',
    },
    {
      id: 'p4',
      owner_id: null,
      name: 'Pixel Arena',
      description: 'Console gaming hub',
      logo_url: null,
      address: 'HSR Layout, Bangalore',
      latitude: 12.9116,
      longitude: 77.6389,
      game_types: ['FIFA', 'Tekken'],
      is_verified: false,
      follower_count: 210,
      post_count: 8,
      is_following: false,
      rating: 4.0,
      phone: '+919666666666',
      website: null,
      created_at: '2026-05-10T10:00:00Z',
      updated_at: '2026-06-23T10:00:00Z',
    },
  ];

  private readonly userStats: Record<
    string,
    Pick<User, 'bookings_count' | 'likes_count' | 'following_count' | 'reviews_count'>
  > = {
    u1: { bookings_count: 3, likes_count: 45, following_count: 12, reviews_count: 2 },
    u2: { bookings_count: 5, likes_count: 22, following_count: 8, reviews_count: 4 },
    u3: { bookings_count: 12, likes_count: 120, following_count: 34, reviews_count: 5 },
    u4: { bookings_count: 0, likes_count: 5, following_count: 0, reviews_count: 1 },
    u5: { bookings_count: 2, likes_count: 18, following_count: 6, reviews_count: 0 },
    u6: { bookings_count: 0, likes_count: 0, following_count: 0, reviews_count: 0 },
    u7: { bookings_count: 4, likes_count: 32, following_count: 15, reviews_count: 2 },
    u8: { bookings_count: 7, likes_count: 58, following_count: 22, reviews_count: 3 },
  };

  private readonly mockBookings: Booking[] = [
    {
      id: 'b1',
      tournament_id: 't1',
      user_id: 'u3',
      slot_number: 3,
      status: 'confirmed',
      payment_status: 'paid',
      booking_type: 'tournament',
      created_at: '2026-06-20T10:00:00Z',
      tournament: {
        id: 't1',
        parlor_id: 'p1',
        title: 'Valorant Weekend Cup',
        game_type: 'Valorant',
        format: '5v5',
        start_time: '2026-07-05T18:00:00Z',
        end_time: '2026-07-05T22:00:00Z',
        total_slots: 16,
        booked_slots: 12,
        entry_fee: 500,
        status: 'open',
        created_at: '2026-06-01T10:00:00Z',
        updated_at: '2026-06-01T10:00:00Z',
        parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      },
    },
    {
      id: 'b2',
      tournament_id: 't2',
      user_id: 'u3',
      slot_number: 1,
      status: 'confirmed',
      payment_status: 'paid',
      booking_type: 'tournament',
      created_at: '2026-06-18T14:00:00Z',
      tournament: {
        id: 't2',
        parlor_id: 'p3',
        title: 'CS2 Pro League',
        game_type: 'CS2',
        format: '5v5',
        start_time: '2026-07-10T14:00:00Z',
        end_time: '2026-07-10T18:00:00Z',
        total_slots: 8,
        booked_slots: 8,
        entry_fee: 1000,
        status: 'live',
        created_at: '2026-06-05T10:00:00Z',
        updated_at: '2026-06-05T10:00:00Z',
        parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      },
    },
    {
      id: 'b3',
      tournament_id: 't1',
      user_id: 'u2',
      slot_number: 5,
      status: 'pending',
      payment_status: 'pending',
      booking_type: 'tournament',
      created_at: '2026-06-25T15:00:00Z',
      tournament: {
        id: 't1',
        parlor_id: 'p1',
        title: 'Valorant Weekend Cup',
        game_type: 'Valorant',
        format: '5v5',
        start_time: '2026-07-05T18:00:00Z',
        end_time: '2026-07-05T22:00:00Z',
        total_slots: 16,
        booked_slots: 12,
        entry_fee: 500,
        status: 'open',
        created_at: '2026-06-01T10:00:00Z',
        updated_at: '2026-06-01T10:00:00Z',
        parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      },
    },
    {
      id: 'b4',
      tournament_id: 't3',
      user_id: 'u7',
      slot_number: 2,
      status: 'confirmed',
      payment_status: 'paid',
      booking_type: 'slot',
      created_at: '2026-06-24T11:00:00Z',
      tournament: {
        id: 't3',
        parlor_id: 'p2',
        title: 'PUBG Evening Slot',
        game_type: 'PUBG',
        format: 'solo',
        start_time: '2026-07-01T20:00:00Z',
        end_time: '2026-07-01T22:00:00Z',
        total_slots: 20,
        booked_slots: 14,
        entry_fee: 200,
        status: 'open',
        created_at: '2026-06-10T10:00:00Z',
        updated_at: '2026-06-10T10:00:00Z',
        parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      },
    },
    {
      id: 'b5',
      tournament_id: 't1',
      user_id: 'u1',
      slot_number: 1,
      status: 'confirmed',
      payment_status: 'paid',
      booking_type: 'tournament',
      created_at: '2026-06-15T09:00:00Z',
      tournament: {
        id: 't1',
        parlor_id: 'p1',
        title: 'Valorant Weekend Cup',
        game_type: 'Valorant',
        format: '5v5',
        start_time: '2026-07-05T18:00:00Z',
        end_time: '2026-07-05T22:00:00Z',
        total_slots: 16,
        booked_slots: 12,
        entry_fee: 500,
        status: 'open',
        created_at: '2026-06-01T10:00:00Z',
        updated_at: '2026-06-01T10:00:00Z',
        parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      },
    },
  ];

  private mockEvents: ParlourEvent[] = [
    {
      id: 'e1',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      title: 'Friday Night Fights',
      event_type: 'tournament',
      cover_url: null,
      start_time: '2026-07-04T20:00:00Z',
      max_participants: 32,
      participant_count: 18,
      entry_fee: 0,
      status: 'open',
      created_at: '2026-06-01T10:00:00Z',
    },
    {
      id: 'e2',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      title: 'CS2 Community Night',
      event_type: 'community',
      cover_url: null,
      start_time: '2026-07-08T18:00:00Z',
      max_participants: 24,
      participant_count: 24,
      entry_fee: 200,
      status: 'live',
      created_at: '2026-06-05T10:00:00Z',
    },
    {
      id: 'e3',
      parlor_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      title: 'BGMI Squad Scrim',
      event_type: 'scrim',
      cover_url: null,
      start_time: '2026-07-12T16:00:00Z',
      max_participants: 16,
      participant_count: 9,
      entry_fee: 150,
      status: 'open',
      created_at: '2026-06-10T10:00:00Z',
    },
    {
      id: 'e4',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      title: 'FIFA 25 Launch Party',
      event_type: 'party',
      cover_url: null,
      start_time: '2026-06-28T14:00:00Z',
      max_participants: 50,
      participant_count: 50,
      entry_fee: 0,
      status: 'completed',
      created_at: '2026-05-20T10:00:00Z',
    },
    {
      id: 'e5',
      parlor_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      title: 'Tekken 8 Exhibition',
      event_type: 'exhibition',
      cover_url: null,
      start_time: '2026-08-01T12:00:00Z',
      max_participants: 8,
      participant_count: 2,
      entry_fee: 500,
      status: 'cancelled',
      created_at: '2026-06-15T10:00:00Z',
    },
  ];

  private mockCommunity: CommunityPost[] = [
    {
      id: 'cp1',
      author_id: 'u3',
      author: { id: 'u3', name: 'Rahul Gaming' },
      title: 'Best Valorant settings for low-end PCs',
      tag: 'Valorant',
      views_count: 1200,
      likes_count: 89,
      comments_count: 23,
      is_pinned: true,
      created_at: '2026-06-15T10:00:00Z',
    },
    {
      id: 'cp2',
      author_id: 'u7',
      author: { id: 'u7', name: 'Sneha Patel' },
      title: 'How to find good parlors in Bangalore',
      tag: 'Guide',
      views_count: 856,
      likes_count: 45,
      comments_count: 12,
      is_pinned: false,
      created_at: '2026-06-18T14:00:00Z',
    },
    {
      id: 'cp3',
      author_id: 'u8',
      author: { id: 'u8', name: 'Karan Joshi' },
      title: 'CS2 smoke lineups for Mirage',
      tag: 'CS2',
      views_count: 2100,
      likes_count: 156,
      comments_count: 34,
      is_pinned: false,
      created_at: '2026-06-20T09:00:00Z',
    },
    {
      id: 'cp4',
      author_id: 'u3',
      author: { id: 'u3', name: 'Rahul Gaming' },
      title: 'PUBG sensitivity guide 2026',
      tag: 'PUBG',
      views_count: 540,
      likes_count: 28,
      comments_count: 8,
      is_pinned: false,
      created_at: '2026-06-22T16:00:00Z',
    },
    {
      id: 'cp5',
      author_id: 'u2',
      author: { id: 'u2', name: 'Priya Sharma' },
      title: 'Tournament etiquette for new players',
      tag: 'Tips',
      views_count: 320,
      likes_count: 19,
      comments_count: 5,
      is_pinned: false,
      created_at: '2026-06-25T11:00:00Z',
    },
  ];

  private mockRatings: Rating[] = [
    {
      id: 'r1',
      user_id: 'u3',
      parlor_id: 'p1',
      user: { id: 'u3', name: 'Rahul Gaming' },
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      rating: 5,
      review: 'Best gaming café in Bangalore! RTX rigs are insane.',
      created_at: '2026-06-10T10:00:00Z',
    },
    {
      id: 'r2',
      user_id: 'u2',
      parlor_id: 'p2',
      user: { id: 'u2', name: 'Priya Sharma' },
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      rating: 3,
      review: 'Good but needs better AC during summer.',
      created_at: '2026-06-12T10:00:00Z',
    },
    {
      id: 'r3',
      user_id: 'u7',
      parlor_id: 'p3',
      user: { id: 'u7', name: 'Sneha Patel' },
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      rating: 5,
      review: '24/7 access is a game changer for night owls.',
      created_at: '2026-06-14T18:00:00Z',
    },
    {
      id: 'r4',
      user_id: 'u8',
      parlor_id: 'p4',
      user: { id: 'u8', name: 'Karan Joshi' },
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      rating: 4,
      review: 'Great console setup, friendly staff.',
      created_at: '2026-06-17T09:00:00Z',
    },
  ];

  private broadcastHistory: BroadcastHistory[] = [
    {
      id: 'n1',
      type: 'info',
      title: 'New Feature!',
      body: 'Tournament brackets are now live on the app.',
      target: 'everyone',
      sent_to: 1250,
      sent_at: '2026-06-20T10:00:00Z',
      status: 'sent',
    },
    {
      id: 'n2',
      type: 'promo',
      title: 'Weekend Sale',
      body: '50% off slot bookings this Friday only.',
      target: 'gamers',
      sent_to: 890,
      sent_at: '2026-06-18T10:00:00Z',
      status: 'sent',
    },
    {
      id: 'n3',
      type: 'alert',
      title: 'Maintenance Notice',
      body: 'Scheduled maintenance on Sunday 2–4 AM IST.',
      target: 'everyone',
      sent_to: 1250,
      sent_at: '2026-06-15T08:00:00Z',
      status: 'sent',
    },
    {
      id: 'n4',
      type: 'event',
      title: 'Valorant Cup Registration',
      body: 'Register now for the Arena Zone weekend cup!',
      target: 'parlor_owners',
      sent_to: 48,
      sent_at: '2026-06-12T14:00:00Z',
      status: 'sent',
    },
  ];

  private readonly mockLikes: Like[] = [
    {
      id: 'l1',
      user_id: 'u3',
      target_type: 'post',
      target_id: 'post1',
      target_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      parlor_name: 'Arena Zone',
      created_at: '2026-06-22T10:00:00Z',
    },
    {
      id: 'l2',
      user_id: 'u3',
      target_type: 'post',
      target_id: 'post2',
      target_preview: 'Weekend tournament brackets are live — register now!',
      parlor_name: 'Cyber Café X',
      created_at: '2026-06-21T16:00:00Z',
    },
    {
      id: 'l3',
      user_id: 'u3',
      target_type: 'post',
      target_id: 'post3',
      target_preview: '50% off slot bookings this Friday only.',
      parlor_name: 'GameHub Pro',
      created_at: '2026-06-19T12:00:00Z',
    },
    {
      id: 'l4',
      user_id: 'u2',
      target_type: 'post',
      target_id: 'post1',
      target_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      parlor_name: 'Arena Zone',
      created_at: '2026-06-22T11:00:00Z',
    },
    {
      id: 'l5',
      user_id: 'u7',
      target_type: 'post',
      target_id: 'post4',
      target_preview: 'Join our BGMI squad night — free entry for members.',
      parlor_name: 'GameHub Pro',
      created_at: '2026-06-20T18:00:00Z',
    },
    {
      id: 'l6',
      user_id: 'u8',
      target_type: 'post',
      target_id: 'post5',
      target_preview: 'FIFA 25 launch party at Pixel Arena this Saturday.',
      parlor_name: 'Pixel Arena',
      created_at: '2026-06-17T09:00:00Z',
    },
    {
      id: 'l7',
      user_id: 'u1',
      target_type: 'post',
      target_id: 'post1',
      target_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      parlor_name: 'Arena Zone',
      created_at: '2026-06-30T08:00:00Z',
    },
    {
      id: 'l8',
      user_id: 'u7',
      target_type: 'post',
      target_id: 'post1',
      target_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      parlor_name: 'Arena Zone',
      created_at: '2026-06-30T11:30:00Z',
    },
    {
      id: 'l9',
      user_id: 'u8',
      target_type: 'comment',
      target_id: 'c1',
      target_preview: 'Amazing setup! When can I book?',
      parlor_name: 'Arena Zone',
      created_at: '2026-06-30T09:15:00Z',
    },
    {
      id: 'l10',
      user_id: 'u2',
      target_type: 'post',
      target_id: 'post2',
      target_preview: 'Weekend tournament brackets are live — register now!',
      parlor_name: 'Cyber Café X',
      created_at: '2026-06-28T14:00:00Z',
    },
  ];

  private readonly deletedLikeIds = new Set<string>();

  private readonly mockComments: Comment[] = [
    {
      id: 'c1',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming', avatar_url: null },
      content: 'Amazing setup! When can I book?',
      parent_id: null,
      likes_count: 5,
      is_deleted: false,
      reply_count: 2,
      post_id: 'post1',
      post_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      created_at: '2026-06-29T10:00:00Z',
    },
    {
      id: 'c2',
      user_id: 'u7',
      user: { id: 'u7', name: 'Sneha Patel', avatar_url: null },
      content: 'Count me in for the weekend cup!',
      parent_id: null,
      likes_count: 3,
      is_deleted: false,
      reply_count: 0,
      post_id: 'post2',
      post_preview: 'Weekend tournament brackets are live — register now!',
      created_at: '2026-06-28T16:30:00Z',
    },
    {
      id: 'c3',
      user_id: 'u8',
      user: { id: 'u8', name: 'Karan Joshi', avatar_url: null },
      content: 'This is spam content — reported.',
      parent_id: null,
      likes_count: 0,
      is_deleted: true,
      reply_count: 0,
      post_id: 'post3',
      post_preview: '50% off slot bookings this Friday only.',
      created_at: '2026-06-27T09:00:00Z',
    },
    {
      id: 'c4',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming', avatar_url: null },
      content: 'Thanks! Slots open at 6 PM.',
      parent_id: 'c1',
      likes_count: 1,
      is_deleted: false,
      reply_count: 0,
      post_id: 'post1',
      post_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      created_at: '2026-06-29T11:00:00Z',
    },
    {
      id: 'c5',
      user_id: 'u1',
      user: { id: 'u1', name: 'Manish Kumar', avatar_url: null },
      content: 'Great turnout last night!',
      parent_id: null,
      likes_count: 8,
      is_deleted: false,
      reply_count: 1,
      post_id: 'post4',
      post_preview: 'Join our BGMI squad night — free entry for members.',
      created_at: '2026-06-30T07:45:00Z',
    },
    {
      id: 'c6',
      user_id: 'u6',
      user: { id: 'u6', name: 'Deepak Mehta', avatar_url: null },
      content: 'Offensive language removed.',
      parent_id: null,
      likes_count: 0,
      is_deleted: true,
      reply_count: 0,
      post_id: 'post5',
      post_preview: 'FIFA 25 launch party at Pixel Arena this Saturday.',
      created_at: '2026-06-25T18:00:00Z',
    },
  ];

  private mockTournaments: Tournament[] = [
    {
      id: 't1',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      title: 'Valorant Weekend Cup',
      game_type: 'Valorant',
      format: '5v5',
      start_time: '2026-07-05T18:00:00Z',
      end_time: '2026-07-05T22:00:00Z',
      total_slots: 16,
      booked_slots: 12,
      entry_fee: 500,
      status: 'open',
      created_at: '2026-06-01T10:00:00Z',
      updated_at: '2026-06-01T10:00:00Z',
    },
    {
      id: 't2',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      title: 'CS2 Pro League',
      game_type: 'CS2',
      format: '5v5',
      start_time: '2026-07-10T14:00:00Z',
      end_time: '2026-07-10T18:00:00Z',
      total_slots: 8,
      booked_slots: 8,
      entry_fee: 1000,
      status: 'full',
      created_at: '2026-06-05T10:00:00Z',
      updated_at: '2026-06-05T10:00:00Z',
    },
    {
      id: 't3',
      parlor_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      title: 'PUBG Evening Slot',
      game_type: 'PUBG',
      format: 'solo',
      start_time: '2026-07-01T20:00:00Z',
      end_time: '2026-07-01T22:00:00Z',
      total_slots: 20,
      booked_slots: 14,
      entry_fee: 200,
      status: 'open',
      created_at: '2026-06-10T10:00:00Z',
      updated_at: '2026-06-10T10:00:00Z',
    },
    {
      id: 't4',
      parlor_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      title: 'FIFA Friday Night',
      game_type: 'FIFA',
      format: '1v1',
      start_time: '2026-06-28T19:00:00Z',
      end_time: '2026-06-28T23:00:00Z',
      total_slots: 12,
      booked_slots: 12,
      entry_fee: 150,
      status: 'live',
      created_at: '2026-06-15T10:00:00Z',
      updated_at: '2026-06-28T19:00:00Z',
    },
    {
      id: 't5',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      title: 'BGMI Squad Clash',
      game_type: 'BGMI',
      format: '4v4',
      start_time: '2026-06-20T18:00:00Z',
      end_time: '2026-06-20T22:00:00Z',
      total_slots: 10,
      booked_slots: 10,
      entry_fee: 300,
      status: 'completed',
      created_at: '2026-06-01T10:00:00Z',
      updated_at: '2026-06-20T22:00:00Z',
    },
    {
      id: 't6',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      title: 'Dota 2 Open Qualifier',
      game_type: 'Dota 2',
      format: '5v5',
      start_time: '2026-08-01T12:00:00Z',
      end_time: '2026-08-01T18:00:00Z',
      total_slots: 16,
      booked_slots: 0,
      entry_fee: 750,
      status: 'draft',
      created_at: '2026-06-29T10:00:00Z',
      updated_at: '2026-06-29T10:00:00Z',
    },
  ];

  private readonly mockGeoActivity: GeoActivity[] = [
    {
      id: 'g1',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming' },
      latitude: 12.9716,
      longitude: 77.5946,
      post_preview: 'New gaming rigs installed! RTX 4090 on every station.',
      created_at: '2026-06-30T10:00:00Z',
    },
    {
      id: 'g2',
      user_id: 'u7',
      user: { id: 'u7', name: 'Sneha Patel' },
      latitude: 12.9352,
      longitude: 77.6245,
      post_preview: 'Join our BGMI squad night — free entry for members.',
      created_at: '2026-06-29T15:30:00Z',
    },
    {
      id: 'g3',
      user_id: 'u8',
      user: { id: 'u8', name: 'Karan Joshi' },
      latitude: 12.9784,
      longitude: 77.6408,
      post_preview: 'Weekend tournament brackets are live — register now!',
      created_at: '2026-06-28T12:00:00Z',
    },
    {
      id: 'g4',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming' },
      latitude: 12.9116,
      longitude: 77.6389,
      post_preview: 'FIFA 25 launch party at Pixel Arena this Saturday.',
      created_at: '2026-06-27T09:45:00Z',
    },
    {
      id: 'g5',
      user_id: 'u1',
      user: { id: 'u1', name: 'Manish Kumar' },
      latitude: 12.9698,
      longitude: 77.75,
      post_preview: 'Admin check-in at Nexus Gaming lounge.',
      created_at: '2026-06-26T18:20:00Z',
    },
  ];

  private mockPosts: Post[] = [
    {
      id: 'post1',
      content: 'New gaming rigs installed! RTX 4090 on every station.',
      media_urls: ['https://picsum.photos/seed/gc-post1/640/480'],
      media_type: 'image',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      likes_count: 245,
      comments_count: 32,
      geo_lat: 12.9716,
      geo_lng: 77.5946,
      created_at: '2026-06-22T10:00:00Z',
    },
    {
      id: 'post2',
      content: 'Weekend tournament brackets are live — register now!',
      media_urls: [],
      media_type: 'text',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      likes_count: 128,
      comments_count: 15,
      created_at: '2026-06-21T16:00:00Z',
    },
    {
      id: 'post3',
      content: '50% off slot bookings this Friday only. Tag your squad!',
      media_urls: ['https://picsum.photos/seed/gc-post3/640/480'],
      media_type: 'image',
      parlor_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      likes_count: 89,
      comments_count: 12,
      geo_lat: 12.9352,
      geo_lng: 77.6245,
      created_at: '2026-06-19T12:00:00Z',
    },
    {
      id: 'post4',
      content: 'Join our BGMI squad night — free entry for members.',
      media_urls: [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
      ],
      media_type: 'video',
      parlor_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      likes_count: 156,
      comments_count: 24,
      created_at: '2026-06-20T18:00:00Z',
    },
    {
      id: 'post5',
      content: 'FIFA 25 launch party highlights from Saturday night.',
      media_urls: [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      ],
      media_type: 'reel',
      parlor_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      likes_count: 312,
      comments_count: 41,
      geo_lat: 12.9116,
      geo_lng: 77.6389,
      created_at: '2026-06-17T09:00:00Z',
    },
    {
      id: 'post6',
      content: 'Behind the scenes: setting up our new Valorant arena.',
      media_urls: [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
      ],
      media_type: 'reel',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      likes_count: 478,
      comments_count: 56,
      geo_lat: 12.9716,
      geo_lng: 77.5946,
      created_at: '2026-06-16T14:00:00Z',
    },
    {
      id: 'post7',
      content: 'Fresh look at our console lounge — PS5 and Xbox Series X zones.',
      media_urls: [
        'https://picsum.photos/seed/gc-post7a/640/480',
        'https://picsum.photos/seed/gc-post7b/640/480',
      ],
      media_type: 'image',
      parlor_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      likes_count: 67,
      comments_count: 9,
      created_at: '2026-06-15T11:00:00Z',
    },
    {
      id: 'post8',
      content: 'CS2 pro league warm-up session — slots filling fast!',
      media_urls: [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
      ],
      media_type: 'video',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      likes_count: 203,
      comments_count: 18,
      geo_lat: 12.9784,
      geo_lng: 77.6408,
      created_at: '2026-06-14T20:00:00Z',
    },
    {
      id: 'post9',
      content: 'Daily update: all stations sanitized and ready for gamers.',
      media_urls: [],
      media_type: 'text',
      parlor_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      likes_count: 34,
      comments_count: 4,
      created_at: '2026-06-13T08:00:00Z',
    },
    {
      id: 'post10',
      content: 'Quick reel: winner celebrations from last weekend cup.',
      media_urls: [
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
      ],
      media_type: 'reel',
      parlor_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      likes_count: 521,
      comments_count: 63,
      created_at: '2026-06-12T17:30:00Z',
    },
  ];

  private readonly mockTimeSlots: {
    id: string;
    parlor_id: string;
    label: string;
    game: string;
    start_time: string;
    end_time: string;
    total_slots: number;
    booked_slots: number;
  }[] = [
    {
      id: 'ts1',
      parlor_id: 'p1',
      label: 'Morning Slots',
      game: 'Valorant',
      start_time: '10:00',
      end_time: '14:00',
      total_slots: 10,
      booked_slots: 7,
    },
    {
      id: 'ts2',
      parlor_id: 'p1',
      label: 'Evening Prime',
      game: 'CS2',
      start_time: '18:00',
      end_time: '22:00',
      total_slots: 12,
      booked_slots: 11,
    },
    {
      id: 'ts3',
      parlor_id: 'p2',
      label: 'Weekday Afternoon',
      game: 'PUBG',
      start_time: '14:00',
      end_time: '18:00',
      total_slots: 8,
      booked_slots: 5,
    },
    {
      id: 'ts4',
      parlor_id: 'p3',
      label: 'Late Night',
      game: 'Dota 2',
      start_time: '22:00',
      end_time: '02:00',
      total_slots: 6,
      booked_slots: 4,
    },
    {
      id: 'ts5',
      parlor_id: 'p4',
      label: 'Weekend FIFA',
      game: 'FIFA',
      start_time: '12:00',
      end_time: '16:00',
      total_slots: 4,
      booked_slots: 3,
    },
  ];

  private readonly mockGamingSlots: GamingSlot[] = [
    {
      id: 'gs1',
      parlour_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      game: 'Valorant',
      slot_date: '2026-07-01',
      start_time: '10:00',
      end_time: '14:00',
      price_per_hour: 150,
      original_price: 200,
      max_players: 10,
      current_bookings: 7,
      is_available: true,
    },
    {
      id: 'gs2',
      parlour_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      game: 'CS2',
      slot_date: '2026-07-01',
      start_time: '18:00',
      end_time: '22:00',
      price_per_hour: 180,
      original_price: 220,
      max_players: 12,
      current_bookings: 11,
      is_available: true,
    },
    {
      id: 'gs3',
      parlour_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      game: 'PUBG',
      slot_date: '2026-07-02',
      start_time: '14:00',
      end_time: '18:00',
      price_per_hour: 120,
      original_price: null,
      max_players: 8,
      current_bookings: 5,
      is_available: true,
    },
    {
      id: 'gs4',
      parlour_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      game: 'Dota 2',
      slot_date: '2026-07-03',
      start_time: '22:00',
      end_time: '02:00',
      price_per_hour: 100,
      original_price: 130,
      max_players: 6,
      current_bookings: 6,
      is_available: false,
    },
    {
      id: 'gs5',
      parlour_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      game: 'FIFA',
      slot_date: '2026-07-05',
      start_time: '12:00',
      end_time: '16:00',
      price_per_hour: 90,
      original_price: null,
      max_players: 4,
      current_bookings: 2,
      is_available: true,
    },
  ];

  private mockGamingBookings: GamingBooking[] = [
    {
      id: 'gb1',
      booking_ref: 'GC-20260701-001',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming', username: 'rahulg' },
      parlour_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      slot_id: 'gs1',
      offer_id: null,
      guest_name: null,
      num_players: 2,
      slot_date: '2026-07-01',
      start_time: '10:00',
      end_time: '12:00',
      hours_booked: 2,
      price_per_hour: 150,
      total_price: 300,
      final_price: 300,
      payment_mode: 'online',
      payment_status: 'paid',
      booking_status: 'confirmed',
      refund_amount: 0,
      refund_status: null,
      gc_points_earned: 30,
      created_at: '2026-06-28T10:00:00Z',
    },
    {
      id: 'gb2',
      booking_ref: 'GC-20260701-002',
      user_id: 'u7',
      user: { id: 'u7', name: 'Sneha Patel', username: 'snehap' },
      parlour_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      slot_id: 'gs3',
      offer_id: 'of1',
      guest_name: null,
      num_players: 1,
      slot_date: '2026-07-02',
      start_time: '14:00',
      end_time: '16:00',
      hours_booked: 2,
      price_per_hour: 120,
      total_price: 240,
      final_price: 192,
      payment_mode: 'online',
      payment_status: 'paid',
      booking_status: 'cancelled',
      refund_amount: 192,
      refund_status: 'pending',
      gc_points_earned: 0,
      created_at: '2026-06-27T14:00:00Z',
    },
    {
      id: 'gb3',
      booking_ref: 'GC-20260701-003',
      user_id: 'u8',
      user: { id: 'u8', name: 'Karan Joshi', username: 'karanj' },
      parlour_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      slot_id: 'gs4',
      offer_id: null,
      guest_name: 'Karan Joshi',
      num_players: 3,
      slot_date: '2026-07-03',
      start_time: '22:00',
      end_time: '00:00',
      hours_booked: 2,
      price_per_hour: 100,
      total_price: 200,
      final_price: 200,
      payment_mode: 'pay_at_parlor',
      payment_status: 'pending',
      booking_status: 'confirmed',
      refund_amount: 0,
      refund_status: null,
      gc_points_earned: 20,
      created_at: '2026-06-29T09:00:00Z',
    },
    {
      id: 'gb4',
      booking_ref: 'GC-20260625-004',
      user_id: 'u2',
      user: { id: 'u2', name: 'Priya Sharma', username: 'priyas' },
      parlour_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      slot_id: 'gs2',
      offer_id: null,
      guest_name: null,
      num_players: 1,
      slot_date: '2026-06-25',
      start_time: '18:00',
      end_time: '20:00',
      hours_booked: 2,
      price_per_hour: 180,
      total_price: 360,
      final_price: 360,
      payment_mode: 'online',
      payment_status: 'paid',
      booking_status: 'cancelled',
      refund_amount: 360,
      refund_status: 'pending',
      gc_points_earned: 0,
      created_at: '2026-06-24T16:00:00Z',
    },
    {
      id: 'gb5',
      booking_ref: 'GC-20260620-005',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming', username: 'rahulg' },
      parlour_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      slot_id: 'gs5',
      offer_id: 'of2',
      guest_name: null,
      num_players: 2,
      slot_date: '2026-06-20',
      start_time: '12:00',
      end_time: '14:00',
      hours_booked: 2,
      price_per_hour: 90,
      total_price: 180,
      final_price: 162,
      payment_mode: 'online',
      payment_status: 'paid',
      booking_status: 'completed',
      refund_amount: 0,
      refund_status: null,
      gc_points_earned: 16,
      created_at: '2026-06-19T11:00:00Z',
    },
  ];

  private mockOffers: Offer[] = [
    {
      id: 'of1',
      parlour_id: 'p2',
      parlor: { id: 'p2', name: 'GameHub Pro', logo_url: null, is_verified: false },
      title: 'Weekday 20% Off',
      description: '20% off on weekday afternoon slots',
      discount_type: 'percentage',
      discount_value: 20,
      valid_from: '2026-06-01',
      valid_until: '2026-07-31',
      is_active: true,
      usage_count: 14,
      created_at: '2026-06-01T10:00:00Z',
    },
    {
      id: 'of2',
      parlour_id: 'p4',
      parlor: { id: 'p4', name: 'Pixel Arena', logo_url: null, is_verified: false },
      title: 'FIFA Weekend Flat ₹50 Off',
      description: 'Flat discount on FIFA weekend slots',
      discount_type: 'flat',
      discount_value: 50,
      valid_from: '2026-06-15',
      valid_until: '2026-08-15',
      is_active: true,
      usage_count: 8,
      created_at: '2026-06-15T10:00:00Z',
    },
    {
      id: 'of3',
      parlour_id: 'p1',
      parlor: { id: 'p1', name: 'Arena Zone', logo_url: null, is_verified: true },
      title: 'Prime Time 15% Off',
      description: 'Evening slot discount for members',
      discount_type: 'percentage',
      discount_value: 15,
      valid_from: '2026-07-01',
      valid_until: '2026-09-30',
      is_active: true,
      usage_count: 3,
      created_at: '2026-06-28T10:00:00Z',
    },
    {
      id: 'of4',
      parlour_id: 'p3',
      parlor: { id: 'p3', name: 'Cyber Café X', logo_url: null, is_verified: true },
      title: 'Late Night Special',
      description: 'Expired late night offer',
      discount_type: 'percentage',
      discount_value: 25,
      valid_from: '2026-05-01',
      valid_until: '2026-05-31',
      is_active: false,
      usage_count: 22,
      created_at: '2026-05-01T10:00:00Z',
    },
  ];

  private readonly mockGcPoints: GcPointsEntry[] = [
    {
      id: 'gp1',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming' },
      points: 30,
      source: 'booking',
      booking_ref: 'GC-20260701-001',
      created_at: '2026-06-28T10:05:00Z',
    },
    {
      id: 'gp2',
      user_id: 'u8',
      user: { id: 'u8', name: 'Karan Joshi' },
      points: 20,
      source: 'booking',
      booking_ref: 'GC-20260701-003',
      created_at: '2026-06-29T09:05:00Z',
    },
    {
      id: 'gp3',
      user_id: 'u3',
      user: { id: 'u3', name: 'Rahul Gaming' },
      points: 16,
      source: 'booking',
      booking_ref: 'GC-20260620-005',
      created_at: '2026-06-19T11:05:00Z',
    },
    {
      id: 'gp4',
      user_id: 'u7',
      user: { id: 'u7', name: 'Sneha Patel' },
      points: 50,
      source: 'referral',
      booking_ref: null,
      created_at: '2026-06-20T12:00:00Z',
    },
  ];

  getStats(): AdminStats {
    return {
      users: 1250,
      parlors: 48,
      tournaments: 8,
      bookings: 34,
      posts: 320,
      revenue: 125000,
      new_users_today: 12,
      pending_verification: 3,
    };
  }

  getAnalytics(period = '30d'): AnalyticsData {
    const days = this.periodDays(period);
    const userGrowth = this.generateDaySeries(days, 5, 25);
    const bookingsPerDay = this.generateDaySeries(days, 10, 45);
    const revenuePerDay = this.generateRevenueSeries(days, 2000, 12000);

    return {
      period,
      user_growth: userGrowth,
      bookings_per_day: bookingsPerDay,
      posts_per_day: this.generateDaySeries(days, 2, 18),
      revenue_per_day: revenuePerDay,
      game_distribution: [
        { label: 'Valorant', value: 35 },
        { label: 'CS2', value: 25 },
        { label: 'PUBG', value: 20 },
        { label: 'FIFA', value: 12 },
        { label: 'Other', value: 8 },
      ],
      top_parlors: [
        { parlor_id: 'p1', parlor_name: 'Arena Zone', bookings_count: 186 },
        { parlor_id: 'p3', parlor_name: 'Cyber Café X', bookings_count: 142 },
        { parlor_id: 'p2', parlor_name: 'GameHub Pro', bookings_count: 98 },
        { parlor_id: 'p4', parlor_name: 'Pixel Arena', bookings_count: 67 },
        { parlor_id: 'p5', parlor_name: 'Nexus Gaming', bookings_count: 54 },
        { parlor_id: 'p6', parlor_name: 'Storm Lounge', bookings_count: 41 },
      ],
      top_parlors_by_revenue: [
        { parlor_id: 'p1', parlor_name: 'Arena Zone', revenue: 485000 },
        { parlor_id: 'p3', parlor_name: 'Cyber Café X', revenue: 362000 },
        { parlor_id: 'p2', parlor_name: 'GameHub Pro', revenue: 218000 },
        { parlor_id: 'p4', parlor_name: 'Pixel Arena', revenue: 145000 },
        { parlor_id: 'p5', parlor_name: 'Nexus Gaming', revenue: 98000 },
      ],
      total_users: 1250,
      new_users: userGrowth.reduce((sum, d) => sum + d.count, 0),
      total_bookings: bookingsPerDay.reduce((sum, d) => sum + d.count, 0),
      revenue: revenuePerDay.reduce((sum, d) => sum + d.count, 0),
      conversion_rate: 68.4,
      cancellation_rate: 4.2,
    };
  }

  getRecentUsers(): PaginatedResponse<User> {
    return this.getUsers({ page: 1, limit: 5 });
  }

  getUsers(params: ListParams = {}): PaginatedResponse<User> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    const search = (params.search ?? '').trim().toLowerCase();

    let filtered = [...this.mockUsers];

    if (search) {
      filtered = filtered.filter(
        u =>
          (u.name?.toLowerCase().includes(search) ?? false) ||
          (u.username?.toLowerCase().includes(search) ?? false) ||
          (u.email?.toLowerCase().includes(search) ?? false) ||
          (u.phone_number?.includes(search) ?? false),
      );
    }

    if (params.role) {
      filtered = filtered.filter(u => u.role === params.role);
    }

    if (params.is_active !== undefined && params.is_active !== null) {
      filtered = filtered.filter(u => u.is_active === params.is_active);
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return {
      items,
      total,
      page,
      limit,
      has_more: start + limit < total,
    };
  }

  updateUser(id: string, data: Partial<Pick<User, 'is_active' | 'role'>>): User | null {
    const index = this.mockUsers.findIndex(u => u.id === id);
    if (index === -1) return null;

    this.mockUsers[index] = {
      ...this.mockUsers[index],
      ...data,
      updated_at: new Date().toISOString(),
    };

    return this.mockUsers[index];
  }

  deleteUser(id: string): boolean {
    const before = this.mockUsers.length;
    this.mockUsers = this.mockUsers.filter(u => u.id !== id);
    return this.mockUsers.length < before;
  }

  getParlorNameForOwner(ownerId: string): string | null {
    return this.mockParlors.find(p => p.owner_id === ownerId)?.name ?? null;
  }

  getOwnerInfo(ownerId: string | null): { name: string; phone: string } | null {
    if (!ownerId) return null;
    const user = this.mockUsers.find(u => u.id === ownerId);
    if (!user) return null;
    return {
      name: user.name ?? user.username ?? 'Unknown',
      phone: user.phone_number ?? '',
    };
  }

  getParlors(params: ListParams = {}): PaginatedResponse<Parlor> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockParlors];

    if (params.is_verified === true) {
      filtered = filtered.filter(p => p.is_verified);
    } else if (params.is_verified === false) {
      filtered = filtered.filter(p => !p.is_verified);
    }

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        p =>
          p.name.toLowerCase().includes(search) ||
          (p.address?.toLowerCase().includes(search) ?? false) ||
          p.game_types.some(g => g.toLowerCase().includes(search)),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  getParlor(id: string): Parlor | null {
    return this.mockParlors.find(p => p.id === id) ?? null;
  }

  verifyParlor(id: string, isVerified: boolean): Parlor | null {
    const index = this.mockParlors.findIndex(p => p.id === id);
    if (index === -1) return null;
    this.mockParlors[index] = {
      ...this.mockParlors[index],
      is_verified: isVerified,
      updated_at: new Date().toISOString(),
    };
    return this.mockParlors[index];
  }

  deleteParlor(id: string): boolean {
    const before = this.mockParlors.length;
    this.mockParlors = this.mockParlors.filter(p => p.id !== id);
    return this.mockParlors.length < before;
  }

  createParlor(data: Partial<Parlor>): Parlor {
    const now = new Date().toISOString();
    const parlor: Parlor = {
      id: crypto.randomUUID(),
      owner_id: data.owner_id ?? null,
      name: data.name ?? 'New Parlor',
      description: data.description ?? null,
      logo_url: data.logo_url ?? null,
      address: data.address ?? null,
      latitude: data.latitude ?? null,
      longitude: data.longitude ?? null,
      game_types: data.game_types ?? [],
      is_verified: data.is_verified ?? false,
      follower_count: 0,
      post_count: 0,
      is_following: false,
      rating: null,
      phone: data.phone ?? null,
      website: data.website ?? null,
      is_active: data.is_active ?? true,
      is_deleted: false,
      created_at: now,
      updated_at: now,
    };
    this.mockParlors = [parlor, ...this.mockParlors];
    return parlor;
  }

  updateParlor(id: string, data: Partial<Parlor>): Parlor | null {
    const index = this.mockParlors.findIndex(p => p.id === id);
    if (index === -1) return null;
    this.mockParlors[index] = {
      ...this.mockParlors[index],
      ...data,
      updated_at: new Date().toISOString(),
    };
    return this.mockParlors[index];
  }

  getParlorTimeSlots(parlorId: string) {
    return this.mockTimeSlots.filter(s => s.parlor_id === parlorId);
  }

  getParlorGallery(parlorId: string): string[] {
    return this.mockPosts
      .filter(p => p.parlor_id === parlorId && p.media_type === 'image')
      .flatMap(p => p.media_urls);
  }

  getUser(id: string): User | null {
    const user = this.mockUsers.find(u => u.id === id);
    if (!user) return null;

    const stats = this.userStats[id] ?? {
      bookings_count: 0,
      likes_count: 0,
      following_count: 0,
      reviews_count: 0,
    };

    return {
      ...user,
      ...stats,
      parlor_name:
        user.role === 'parlor_owner' ? this.getParlorNameForOwner(user.id) : null,
    };
  }

  getBookings(params: ListParams = {}): PaginatedResponse<Booking> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockBookings];

    if (params.user_id) {
      filtered = filtered.filter(b => b.user_id === params.user_id);
    }

    if (params.booking_type) {
      filtered = filtered.filter(b => b.booking_type === params.booking_type);
    }

    if (params.status) {
      filtered = filtered.filter(b => b.status === params.status);
    }

    if (params.date) {
      filtered = filtered.filter(
        b => b.created_at.slice(0, 10) === params.date,
      );
    }

    filtered = filtered.map(b => ({
      ...b,
      user: this.enrichBookingUser(b.user_id),
    }));

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  getLikes(params: ListParams = {}): PaginatedResponse<Like> {
    return this.getUserLikedPosts(params);
  }

  getUserLikedPosts(params: ListParams = {}): PaginatedResponse<Like> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = this.mockLikes.filter(l => !this.deletedLikeIds.has(l.id));

    if (params.user_id) {
      filtered = filtered.filter(l => l.user_id === params.user_id);
    }

    if (params.target_type) {
      filtered = filtered.filter(l => l.target_type === params.target_type);
    }

    filtered = filtered.map(l => this.enrichLike(l));

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  deleteLike(id: string): boolean {
    if (!this.mockLikes.some(l => l.id === id)) return false;
    this.deletedLikeIds.add(id);
    return true;
  }

  computeLikeStats(): {
    today: number;
    thisWeek: number;
    mostLikedPost: { preview: string; count: number } | null;
  } {
    const active = this.mockLikes.filter(l => !this.deletedLikeIds.has(l.id));
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(now);
    weekAgo.setDate(now.getDate() - 7);

    const today = active.filter(l => new Date(l.created_at) >= startOfToday).length;
    const thisWeek = active.filter(l => new Date(l.created_at) >= weekAgo).length;

    const postCounts = new Map<string, { preview: string; count: number }>();
    for (const like of active) {
      if (like.target_type !== 'post') continue;
      const existing = postCounts.get(like.target_id);
      if (existing) {
        existing.count += 1;
      } else {
        postCounts.set(like.target_id, {
          preview: like.target_preview ?? like.target_id,
          count: 1,
        });
      }
    }

    let mostLikedPost: { preview: string; count: number } | null = null;
    for (const entry of postCounts.values()) {
      if (!mostLikedPost || entry.count > mostLikedPost.count) {
        mostLikedPost = entry;
      }
    }

    return { today, thisWeek, mostLikedPost };
  }

  getComments(params: ListParams = {}): PaginatedResponse<Comment> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockComments];

    if (params.is_deleted === true) {
      filtered = filtered.filter(c => c.is_deleted);
    } else if (params.is_deleted === false) {
      filtered = filtered.filter(c => !c.is_deleted);
    }

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        c =>
          c.content.toLowerCase().includes(search) ||
          (c.user?.name?.toLowerCase().includes(search) ?? false) ||
          (c.post_preview?.toLowerCase().includes(search) ?? false),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  deleteComment(id: string): boolean {
    const comment = this.mockComments.find(c => c.id === id);
    if (!comment) return false;
    comment.is_deleted = true;
    return true;
  }

  restoreComment(id: string): boolean {
    const comment = this.mockComments.find(c => c.id === id);
    if (!comment) return false;
    comment.is_deleted = false;
    return true;
  }

  getTournaments(params: ListParams = {}): PaginatedResponse<Tournament> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockTournaments];

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        t =>
          t.title.toLowerCase().includes(search) ||
          t.game_type.toLowerCase().includes(search) ||
          (t.parlor?.name.toLowerCase().includes(search) ?? false),
      );
    }

    if (params.status) {
      filtered = filtered.filter(t => t.status === params.status);
    }

    filtered.sort(
      (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  updateTournamentStatus(id: string, status: string): Tournament | null {
    const index = this.mockTournaments.findIndex(t => t.id === id);
    if (index === -1) return null;
    this.mockTournaments[index] = {
      ...this.mockTournaments[index],
      status: status as Tournament['status'],
      updated_at: new Date().toISOString(),
    };
    return this.mockTournaments[index];
  }

  deleteTournament(id: string): boolean {
    const before = this.mockTournaments.length;
    this.mockTournaments = this.mockTournaments.filter(t => t.id !== id);
    return this.mockTournaments.length < before;
  }

  getGeoActivity(params: ListParams = {}): PaginatedResponse<GeoActivity> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockGeoActivity];

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        g =>
          (g.user?.name?.toLowerCase().includes(search) ?? false) ||
          (g.post_preview?.toLowerCase().includes(search) ?? false),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  getPosts(params: ListParams = {}): PaginatedResponse<Post> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockPosts];

    if (params.parlor_id) {
      filtered = filtered.filter(p => p.parlor_id === params.parlor_id);
    }

    if (params.media_type) {
      filtered = filtered.filter(p => p.media_type === params.media_type);
    }

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        p =>
          p.content.toLowerCase().includes(search) ||
          (p.parlor?.name.toLowerCase().includes(search) ?? false),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  deletePost(id: string): boolean {
    const before = this.mockPosts.length;
    this.mockPosts = this.mockPosts.filter(p => p.id !== id);
    return this.mockPosts.length < before;
  }

  getPendingParlors(): PaginatedResponse<Parlor> {
    const items = this.mockParlors.filter(p => !p.is_verified).slice(0, 5);
    return { items, total: items.length, page: 1, limit: 5, has_more: false };
  }

  getEvents(params: ListParams = {}): PaginatedResponse<ParlourEvent> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockEvents];

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        e =>
          e.title.toLowerCase().includes(search) ||
          (e.parlor?.name.toLowerCase().includes(search) ?? false) ||
          e.event_type.toLowerCase().includes(search),
      );
    }

    if (params.status) {
      filtered = filtered.filter(e => e.status === params.status);
    }

    if (params.parlor_id) {
      filtered = filtered.filter(e => e.parlor_id === params.parlor_id);
    }

    filtered.sort(
      (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  updateEventStatus(id: string, status: string): ParlourEvent | null {
    const index = this.mockEvents.findIndex(e => e.id === id);
    if (index === -1) return null;
    this.mockEvents[index] = { ...this.mockEvents[index], status };
    return this.mockEvents[index];
  }

  deleteEvent(id: string): boolean {
    const before = this.mockEvents.length;
    this.mockEvents = this.mockEvents.filter(e => e.id !== id);
    return this.mockEvents.length < before;
  }

  getCommunity(params: ListParams = {}): PaginatedResponse<CommunityPost> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockCommunity];

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        p =>
          p.title.toLowerCase().includes(search) ||
          (p.author?.name?.toLowerCase().includes(search) ?? false) ||
          (p.tag?.toLowerCase().includes(search) ?? false),
      );
    }

    filtered.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  pinCommunityPost(id: string, isPinned: boolean): CommunityPost | null {
    const index = this.mockCommunity.findIndex(p => p.id === id);
    if (index === -1) return null;
    this.mockCommunity[index] = { ...this.mockCommunity[index], is_pinned: isPinned };
    return this.mockCommunity[index];
  }

  deleteCommunityPost(id: string): boolean {
    const before = this.mockCommunity.length;
    this.mockCommunity = this.mockCommunity.filter(p => p.id !== id);
    return this.mockCommunity.length < before;
  }

  getRatings(params: ListParams = {}): PaginatedResponse<Rating> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockRatings];

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        r =>
          (r.user?.name?.toLowerCase().includes(search) ?? false) ||
          (r.parlor?.name.toLowerCase().includes(search) ?? false) ||
          (r.review?.toLowerCase().includes(search) ?? false),
      );
    }

    if (params.parlor_id) {
      filtered = filtered.filter(r => r.parlor_id === params.parlor_id);
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  deleteRating(id: string): boolean {
    const before = this.mockRatings.length;
    this.mockRatings = this.mockRatings.filter(r => r.id !== id);
    return this.mockRatings.length < before;
  }

  getBroadcastHistory(params: ListParams = {}): PaginatedResponse<BroadcastHistory> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.broadcastHistory];

    if (params.type) {
      filtered = filtered.filter(h => h.type === params.type);
    }

    filtered.sort(
      (a, b) => new Date(b.sent_at).getTime() - new Date(a.sent_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  getGamingBookings(params: ListParams = {}): PaginatedResponse<GamingBooking> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockGamingBookings];

    if (params.status) {
      filtered = filtered.filter(b => b.booking_status === params.status);
    }

    if (params.refund_status) {
      filtered = filtered.filter(b => b.refund_status === params.refund_status);
    }

    if (params.parlor_id) {
      filtered = filtered.filter(b => b.parlour_id === params.parlor_id);
    }

    if (params.date) {
      filtered = filtered.filter(b => b.slot_date === params.date);
    }

    if (params.date_from) {
      filtered = filtered.filter(
        b => b.slot_date && b.slot_date >= String(params.date_from),
      );
    }

    if (params.date_to) {
      filtered = filtered.filter(
        b => b.slot_date && b.slot_date <= String(params.date_to),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  processGamingRefund(id: string): GamingBooking | null {
    const index = this.mockGamingBookings.findIndex(b => b.id === id);
    if (index === -1) return null;

    const booking = this.mockGamingBookings[index];
    if (booking.refund_status !== 'pending') return null;

    this.mockGamingBookings[index] = {
      ...booking,
      refund_status: 'processed',
      payment_status: 'refunded',
    };

    return this.mockGamingBookings[index];
  }

  getGamingSlots(params: ListParams = {}): PaginatedResponse<GamingSlot> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockGamingSlots];

    if (params.parlor_id) {
      filtered = filtered.filter(s => s.parlour_id === params.parlor_id);
    }

    if (params.date) {
      filtered = filtered.filter(s => s.slot_date === params.date);
    }

    filtered.sort((a, b) => {
      const dateCmp = b.slot_date.localeCompare(a.slot_date);
      if (dateCmp !== 0) return dateCmp;
      return a.start_time.localeCompare(b.start_time);
    });

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  getOffers(params: ListParams = {}): PaginatedResponse<Offer> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockOffers];

    if (params.parlor_id) {
      filtered = filtered.filter(o => o.parlour_id === params.parlor_id);
    }

    if (params.is_active !== undefined && params.is_active !== null) {
      filtered = filtered.filter(o => o.is_active === params.is_active);
    }

    const search = params.search?.trim().toLowerCase();
    if (search) {
      filtered = filtered.filter(
        o =>
          o.title.toLowerCase().includes(search) ||
          (o.parlor?.name.toLowerCase().includes(search) ?? false),
      );
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  createOffer(data: OfferCreateRequest): Offer {
    const parlor = this.mockParlors.find(p => p.id === data.parlour_id);
    const offer: Offer = {
      id: `of${Date.now()}`,
      parlour_id: data.parlour_id,
      parlor: parlor
        ? {
            id: parlor.id,
            name: parlor.name,
            logo_url: parlor.logo_url,
            is_verified: parlor.is_verified,
          }
        : undefined,
      title: data.title,
      description: data.description ?? null,
      discount_type: data.discount_type,
      discount_value: data.discount_value,
      valid_from: data.valid_from,
      valid_until: data.valid_until,
      is_active: data.is_active ?? true,
      usage_count: 0,
      created_at: new Date().toISOString(),
    };

    this.mockOffers.unshift(offer);
    return offer;
  }

  getGcPoints(params: ListParams = {}): PaginatedResponse<GcPointsEntry> {
    const page = params.page ?? 1;
    const limit = params.limit ?? 20;
    let filtered = [...this.mockGcPoints];

    if (params.user_id) {
      filtered = filtered.filter(e => e.user_id === params.user_id);
    }

    filtered.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);

    return { items, total, page, limit, has_more: start + limit < total };
  }

  broadcast(data: BroadcastRequest): { sent_to: number } {
    const sentTo =
      data.target === 'everyone' ? 1250 : data.target === 'gamers' ? 890 : 48;

    this.broadcastHistory.unshift({
      id: `n${Date.now()}`,
      type: data.type,
      title: data.title,
      body: data.body,
      target: data.target,
      sent_to: sentTo,
      sent_at: new Date().toISOString(),
      status: 'sent',
    });

    return { sent_to: sentTo };
  }

  private enrichLike(like: Like): Like {
    const user = this.mockUsers.find(u => u.id === like.user_id);
    return {
      ...like,
      user: user
        ? { id: user.id, name: user.name, avatar_url: user.avatar_url }
        : like.user,
    };
  }

  private enrichBookingUser(userId: string): User | undefined {
    const user = this.mockUsers.find(u => u.id === userId);
    if (!user) return undefined;
    return {
      id: user.id,
      name: user.name,
      username: user.username,
      email: user.email,
      phone_number: user.phone_number,
      role: user.role,
      avatar_url: user.avatar_url,
      is_active: user.is_active,
      is_verified: user.is_verified,
      email_verified: user.email_verified,
      phone_verified: user.phone_verified,
      latitude: user.latitude,
      longitude: user.longitude,
      city: user.city,
      country: user.country,
      location_updated_at: user.location_updated_at,
      created_at: user.created_at,
      updated_at: user.updated_at,
    };
  }

  private periodDays(period: string): number {
    if (period === '7d') return 7;
    if (period === '90d') return 90;
    return 30;
  }

  private generateDaySeries(days: number, min: number, max: number): DayCount[] {
    const series: DayCount[] = [];
    const today = new Date();

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      series.push({
        date: date.toISOString().slice(0, 10),
        count: Math.floor(Math.random() * (max - min + 1)) + min,
      });
    }

    return series;
  }

  private generateRevenueSeries(days: number, min: number, max: number): DayCount[] {
    return this.generateDaySeries(days, min, max);
  }
}