import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';
import { MockDataService } from './mock-data.service';
import { environment } from '../../../environments/environment';
import {
  AdminStats,
  AnalyticsData,
  Booking,
  BroadcastHistory,
  BroadcastRequest,
  Comment,
  CommunityPost,
  GamingBooking,
  GamingSlot,
  GcPointsEntry,
  GeoActivity,
  Like,
  ListParams,
  MediaAssetItem,
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
export class AdminApiService {
  private readonly http = inject(HttpClient);
  private readonly mock = inject(MockDataService);
  private readonly base = `${environment.apiUrl}/admin`;

  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${this.base}/stats`).pipe(
      map(data => (this.isStubStats(data) ? this.mock.getStats() : data)),
      catchError(() => of(this.mock.getStats())),
    );
  }

  getAnalytics(period = '30d'): Observable<AnalyticsData> {
    return this.http.get<AnalyticsData>(`${this.base}/analytics`, {
      params: { period },
    }).pipe(
      map(data => (this.isStubAnalytics(data) ? this.mock.getAnalytics(period) : data)),
      catchError(() => of(this.mock.getAnalytics(period))),
    );
  }

  getUsers(params: ListParams = {}): Observable<PaginatedResponse<User>> {
    return this.http.get<PaginatedResponse<User>>(`${this.base}/users`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getUsers(params) : data)),
      catchError(() => of(this.mock.getUsers(params))),
    );
  }

  getUser(id: string): Observable<User> {
    return this.http.get<User>(`${this.base}/users/${id}`).pipe(
      map(data => {
        if (!data?.id) {
          const user = this.mock.getUser(id);
          if (!user) throw new Error('User not found');
          return user;
        }
        return data;
      }),
      catchError(() => {
        const user = this.mock.getUser(id);
        if (!user) throw new Error('User not found');
        return of(user);
      }),
    );
  }

  updateUser(id: string, data: Partial<Pick<User, 'is_active' | 'role'>>): Observable<User> {
    return this.http.patch<User>(`${this.base}/users/${id}`, data).pipe(
      catchError(() => {
        const updated = this.mock.updateUser(id, data);
        if (!updated) {
          throw new Error('User not found');
        }
        return of(updated);
      }),
    );
  }

  deleteUser(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/users/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteUser(id)) {
          throw new Error('User not found');
        }
        return of(void 0);
      }),
    );
  }

  getParlors(params: ListParams = {}): Observable<PaginatedResponse<Parlor>> {
    return this.http.get<PaginatedResponse<Parlor>>(`${this.base}/parlors`, {
      params: this.toParams(params),
    }).pipe(
      map(data => {
        if (params.is_verified === false && this.isEmptyPaginated(data)) {
          return this.mock.getPendingParlors();
        }
        return data;
      }),
      catchError(() => of(this.mock.getParlors(params))),
    );
  }

  getParlor(id: string): Observable<Parlor> {
    return this.getParlors({ limit: 100 }).pipe(
      map(res => {
        const p = res.items.find(x => x.id === id);
        if (!p) throw new Error('Not found');
        return p;
      }),
      catchError(() => {
        const p = this.mock.getParlor(id);
        if (!p) throw new Error('Not found');
        return of(p);
      }),
    );
  }

  verifyParlor(id: string, isVerified: boolean): Observable<Parlor> {
    return this.http.patch<Parlor>(`${this.base}/parlors/${id}/verify`, {
      is_verified: isVerified,
    }).pipe(
      catchError(() => {
        const updated = this.mock.verifyParlor(id, isVerified);
        if (!updated) throw new Error('Parlor not found');
        return of(updated);
      }),
    );
  }

  deleteParlor(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/parlors/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteParlor(id)) throw new Error('Parlor not found');
        return of(void 0);
      }),
    );
  }

  getPosts(params: ListParams = {}): Observable<PaginatedResponse<Post>> {
    return this.http.get<PaginatedResponse<Post>>(`${this.base}/posts`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getPosts(params) : data)),
      catchError(() => of(this.mock.getPosts(params))),
    );
  }

  deletePost(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/posts/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deletePost(id)) throw new Error('Post not found');
        return of(void 0);
      }),
    );
  }

  getComments(params: ListParams = {}): Observable<PaginatedResponse<Comment>> {
    return this.http.get<PaginatedResponse<Comment>>(`${this.base}/comments`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getComments(params) : data)),
      catchError(() => of(this.mock.getComments(params))),
    );
  }

  deleteComment(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/comments/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteComment(id)) {
          throw new Error('Comment not found');
        }
        return of(void 0);
      }),
    );
  }

  restoreComment(id: string): Observable<void> {
    return this.http.patch<void>(`${this.base}/comments/${id}/restore`, {}).pipe(
      catchError(() => {
        if (!this.mock.restoreComment(id)) {
          throw new Error('Comment not found');
        }
        return of(void 0);
      }),
    );
  }

  getLikes(params: ListParams = {}): Observable<PaginatedResponse<Like>> {
    return this.http.get<PaginatedResponse<Like>>(`${this.base}/likes`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getLikes(params) : data)),
      catchError(() => of(this.mock.getLikes(params))),
    );
  }

  deleteLike(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/likes/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteLike(id)) {
          throw new Error('Like not found');
        }
        return of(void 0);
      }),
    );
  }

  getTournaments(params: ListParams = {}): Observable<PaginatedResponse<Tournament>> {
    return this.http.get<PaginatedResponse<Tournament>>(`${this.base}/tournaments`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getTournaments(params) : data)),
      catchError(() => of(this.mock.getTournaments(params))),
    );
  }

  updateTournamentStatus(id: string, status: string): Observable<Tournament> {
    return this.http.patch<Tournament>(`${this.base}/tournaments/${id}/status`, { status }).pipe(
      catchError(() => {
        const updated = this.mock.updateTournamentStatus(id, status);
        if (!updated) {
          throw new Error('Tournament not found');
        }
        return of(updated);
      }),
    );
  }

  deleteTournament(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/tournaments/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteTournament(id)) {
          throw new Error('Tournament not found');
        }
        return of(void 0);
      }),
    );
  }

  getBookings(params: ListParams = {}): Observable<PaginatedResponse<Booking>> {
    return this.http.get<PaginatedResponse<Booking>>(`${this.base}/bookings`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getBookings(params) : data)),
      catchError(() => of(this.mock.getBookings(params))),
    );
  }

  getGamingBookings(params: ListParams = {}): Observable<PaginatedResponse<GamingBooking>> {
    return this.http.get<PaginatedResponse<GamingBooking>>(`${this.base}/gaming-bookings`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getGamingBookings(params) : data)),
      catchError(() => of(this.mock.getGamingBookings(params))),
    );
  }

  processGamingRefund(id: string): Observable<GamingBooking> {
    return this.http
      .patch<GamingBooking>(`${this.base}/gaming-bookings/${id}/process-refund`, {})
      .pipe(
        catchError(() => {
          const updated = this.mock.processGamingRefund(id);
          if (!updated) throw new Error('Booking not found or refund not pending');
          return of(updated);
        }),
      );
  }

  getGamingSlots(params: ListParams = {}): Observable<PaginatedResponse<GamingSlot>> {
    return this.http.get<PaginatedResponse<GamingSlot>>(`${this.base}/gaming-slots`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getGamingSlots(params) : data)),
      catchError(() => of(this.mock.getGamingSlots(params))),
    );
  }

  getOffers(params: ListParams = {}): Observable<PaginatedResponse<Offer>> {
    return this.http.get<PaginatedResponse<Offer>>(`${this.base}/offers`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getOffers(params) : data)),
      catchError(() => of(this.mock.getOffers(params))),
    );
  }

  createOffer(data: OfferCreateRequest): Observable<Offer> {
    return this.http.post<Offer>(`${this.base}/offers`, data).pipe(
      catchError(() => of(this.mock.createOffer(data))),
    );
  }

  getGcPoints(params: ListParams = {}): Observable<PaginatedResponse<GcPointsEntry>> {
    return this.http.get<PaginatedResponse<GcPointsEntry>>(`${this.base}/gc-points`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getGcPoints(params) : data)),
      catchError(() => of(this.mock.getGcPoints(params))),
    );
  }

  getEvents(params: ListParams = {}): Observable<PaginatedResponse<ParlourEvent>> {
    return this.http.get<PaginatedResponse<ParlourEvent>>(`${this.base}/events`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getEvents(params) : data)),
      catchError(() => of(this.mock.getEvents(params))),
    );
  }

  updateEventStatus(id: string, status: string): Observable<ParlourEvent> {
    return this.http.patch<ParlourEvent>(`${this.base}/events/${id}/status`, { status }).pipe(
      catchError(() => {
        const updated = this.mock.updateEventStatus(id, status);
        if (!updated) throw new Error('Event not found');
        return of(updated);
      }),
    );
  }

  deleteEvent(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/events/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteEvent(id)) throw new Error('Event not found');
        return of(void 0);
      }),
    );
  }

  getCommunity(params: ListParams = {}): Observable<PaginatedResponse<CommunityPost>> {
    return this.http.get<PaginatedResponse<CommunityPost>>(`${this.base}/community`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getCommunity(params) : data)),
      catchError(() => of(this.mock.getCommunity(params))),
    );
  }

  pinCommunityPost(id: string, isPinned: boolean): Observable<CommunityPost> {
    return this.http.patch<CommunityPost>(`${this.base}/community/${id}/pin`, {
      is_pinned: isPinned,
    }).pipe(
      catchError(() => {
        const updated = this.mock.pinCommunityPost(id, isPinned);
        if (!updated) throw new Error('Post not found');
        return of(updated);
      }),
    );
  }

  deleteCommunityPost(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/community/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteCommunityPost(id)) throw new Error('Post not found');
        return of(void 0);
      }),
    );
  }

  getRatings(params: ListParams = {}): Observable<PaginatedResponse<Rating>> {
    return this.http.get<PaginatedResponse<Rating>>(`${this.base}/ratings`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getRatings(params) : data)),
      catchError(() => of(this.mock.getRatings(params))),
    );
  }

  deleteRating(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/ratings/${id}`).pipe(
      catchError(() => {
        if (!this.mock.deleteRating(id)) throw new Error('Rating not found');
        return of(void 0);
      }),
    );
  }

  broadcast(data: BroadcastRequest): Observable<{ sent_to: number }> {
    return this.http.post<{ sent_to: number }>(`${this.base}/notifications/broadcast`, data).pipe(
      catchError(() => of(this.mock.broadcast(data))),
    );
  }

  getBroadcastHistory(params: ListParams = {}): Observable<PaginatedResponse<BroadcastHistory>> {
    return this.http.get<PaginatedResponse<BroadcastHistory>>(
      `${this.base}/notifications/history`,
      { params: this.toParams(params) },
    ).pipe(
      map(data =>
        this.isEmptyPaginated(data) ? this.mock.getBroadcastHistory(params) : data,
      ),
      catchError(() => of(this.mock.getBroadcastHistory(params))),
    );
  }

  getGeoActivity(params: ListParams = {}): Observable<PaginatedResponse<GeoActivity>> {
    return this.http.get<PaginatedResponse<GeoActivity>>(`${this.base}/geo-activity`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.isEmptyPaginated(data) ? this.mock.getGeoActivity(params) : data)),
      catchError(() => of(this.mock.getGeoActivity(params))),
    );
  }

  private isStubStats(data: AdminStats): boolean {
    return (
      data.status === 'stub' ||
      (data.users === 0 && data.parlors === 0 && data.tournaments === 0 && data.bookings === 0)
    );
  }

  private isStubAnalytics(data: AnalyticsData): boolean {
    return (
      !data.user_growth?.length &&
      !data.bookings_per_day?.length &&
      !data.revenue_per_day?.length &&
      !data.game_distribution?.length &&
      !data.top_parlors?.length
    );
  }

  private isEmptyPaginated<T>(data: PaginatedResponse<T>): boolean {
    return !data.items?.length;
  }

  getDmsAssets(params: ListParams & { type?: string; search?: string } = {}): Observable<PaginatedResponse<MediaAssetItem>> {
    return this.http.get<PaginatedResponse<MediaAssetItem>>(`${this.base}/dms`, {
      params: this.toParams(params),
    });
  }

  getDmsStats(): Observable<{
    total_count: number;
    total_size_bytes: number;
    total_size_label: string;
    by_type: Record<string, number>;
    by_context: Record<string, number>;
    flagged_count: number;
  }> {
    return this.http.get<{
      total_count: number;
      total_size_bytes: number;
      total_size_label: string;
      by_type: Record<string, number>;
      by_context: Record<string, number>;
      flagged_count: number;
    }>(`${this.base}/dms/stats`);
  }

  getDmsOrphans(params: ListParams = {}): Observable<PaginatedResponse<Record<string, unknown>>> {
    return this.http.get<PaginatedResponse<Record<string, unknown>>>(`${this.base}/dms/orphans`, {
      params: this.toParams(params),
    });
  }

  deleteDmsAsset(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/dms/${id}`);
  }

  flagDmsAsset(id: string, isFlagged: boolean, reason?: string): Observable<Record<string, unknown>> {
    return this.http.patch<Record<string, unknown>>(`${this.base}/dms/${id}/flag`, {
      is_flagged: isFlagged,
      reason,
    });
  }

  bulkDeleteDmsAssets(assetIds: string[]): Observable<{ deleted: number; requested: number }> {
    return this.http.post<{ deleted: number; requested: number }>(`${this.base}/dms/bulk-delete`, {
      asset_ids: assetIds,
    });
  }

  private toParams(params: ListParams): HttpParams {
    let httpParams = new HttpParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        httpParams = httpParams.set(key, String(value));
      }
    });
    return httpParams;
  }
}