import { apiClient } from './client';
import { devApi, USE_MOCK } from '../mocks/devData';
import type { AdminStats, AnalyticsData, PaginatedResponse, User, Parlor, ParlorDetail, Tournament, Booking, Post, Comment, ParlourEvent, CommunityPost, Rating, BroadcastRequest, NotificationHistory, OwnerStats, TableParams } from '../types';

const a = apiClient;
const pg = (p: TableParams) => ({ page: 1, limit: 20, ...p });

export const adminApi = {
  getStats: () => USE_MOCK ? devApi.getStats() : a.get<AdminStats>('/admin/stats').then(r => r.data),
  getAnalytics: (period = '30d') => USE_MOCK ? devApi.getAnalytics() : a.get<AnalyticsData>('/admin/analytics', { params: { period } }).then(r => r.data),

  getUsers: (p: TableParams) => USE_MOCK ? devApi.getUsers(pg(p)) : a.get<PaginatedResponse<User>>('/admin/users', { params: pg(p) }).then(r => r.data),
  getUser: (id: string) => USE_MOCK ? devApi.getUser(id) : a.get<User>(`/admin/users/${id}`).then(r => r.data),
  updateUser: async (id: string, d: { is_active?: boolean; role?: string }) => { if (USE_MOCK) { await devApi.noop(); return; } await a.patch(`/admin/users/${id}`, d); },
  deleteUser: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/users/${id}`); },

  getParlors: (p: TableParams) => USE_MOCK ? devApi.getParlors(pg(p)) : a.get<PaginatedResponse<Parlor>>('/admin/parlors', { params: pg(p) }).then(r => r.data),
  getParlor: (id: string) => USE_MOCK ? devApi.getParlor(id) : a.get<ParlorDetail>(`/admin/parlors/${id}`).then(r => r.data),
  verifyParlor: async (id: string, v: boolean) => { if (USE_MOCK) { await devApi.noop(); return; } await a.patch(`/admin/parlors/${id}/verify`, { is_verified: v }); },
  deleteParlor: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/parlors/${id}`); },

  getOwnerStats: () => USE_MOCK ? devApi.getOwnerStats() : a.get<OwnerStats>('/admin/owner/stats').then(r => r.data),

  getTournaments: (p: TableParams) => USE_MOCK ? devApi.getTournaments(pg(p)) : a.get<PaginatedResponse<Tournament>>('/admin/tournaments', { params: pg(p) }).then(r => r.data),
  updateTournamentStatus: async (id: string, status: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.patch(`/admin/tournaments/${id}/status`, { status }); },
  deleteTournament: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/tournaments/${id}`); },

  getBookings: (p: TableParams) => USE_MOCK ? devApi.getBookings(pg(p)) : a.get<PaginatedResponse<Booking>>('/admin/bookings', { params: pg(p) }).then(r => r.data),

  getPosts: (p: TableParams) => USE_MOCK ? devApi.getPosts(pg(p)) : a.get<PaginatedResponse<Post>>('/admin/posts', { params: pg(p) }).then(r => r.data),
  deletePost: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/posts/${id}`); },

  getComments: (p: TableParams) => USE_MOCK ? devApi.getComments(pg(p)) : a.get<PaginatedResponse<Comment>>('/admin/comments', { params: pg(p) }).then(r => r.data),
  deleteComment: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/comments/${id}`); },

  getEvents: (p: TableParams) => USE_MOCK ? devApi.getEvents(pg(p)) : a.get<PaginatedResponse<ParlourEvent>>('/admin/events', { params: pg(p) }).then(r => r.data),
  updateEventStatus: async (id: string, status: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.patch(`/admin/events/${id}/status`, { status }); },
  deleteEvent: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/events/${id}`); },

  getCommunity: (p: TableParams) => USE_MOCK ? devApi.getCommunity(pg(p)) : a.get<PaginatedResponse<CommunityPost>>('/admin/community', { params: pg(p) }).then(r => r.data),
  pinCommunityPost: async (id: string, v: boolean) => { if (USE_MOCK) { await devApi.noop(); return; } await a.patch(`/admin/community/${id}/pin`, { is_pinned: v }); },
  deleteCommunityPost: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/community/${id}`); },

  getRatings: (p: TableParams) => USE_MOCK ? devApi.getRatings(pg(p)) : a.get<PaginatedResponse<Rating>>('/admin/ratings', { params: pg(p) }).then(r => r.data),
  deleteRating: async (id: string) => { if (USE_MOCK) { await devApi.noop(); return; } await a.delete(`/admin/ratings/${id}`); },

  broadcast: (d: BroadcastRequest) => USE_MOCK ? Promise.resolve({ sent_to: 1250 }) : a.post<{ sent_to: number }>('/admin/notifications/broadcast', d).then(r => r.data),
  getNotificationHistory: (p?: TableParams) => USE_MOCK ? devApi.getNotificationHistory(p) : a.get<PaginatedResponse<NotificationHistory>>('/admin/notifications/history', { params: pg(p ?? {}) }).then(r => r.data),
};