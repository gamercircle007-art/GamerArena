import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, Observable, of, throwError } from 'rxjs';
import { MockDataService } from './mock-data.service';
import { environment } from '../../../environments/environment';
import {
  AdminStats,
  AnalyticsData,
  Booking,
  BroadcastHistory,
  BroadcastRequest,
  ClubBookingListResponse,
  ClubBookingView,
  ClubCustomerFlagResponse,
  ClubCustomerListResponse,
  ClubForceCancelResponse,
  ClubListResponse,
  ClubLiveResponse,
  ClubOccupancyResponse,
  ClubPromotionListResponse,
  ClubPromotionOverrideResponse,
  ClubResourceListResponse,
  ClubResourceOverrideResponse,
  ClubRevenueRange,
  ClubRevenueSummary,
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
  ParlorCreateRequest,
  ParlorUpdateRequest,
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

  private readonly allowMock = environment.useMockFallback === true;

  /** Mock only when useMockFallback is true (dev). Production surfaces real errors. */
  private mockOrThrow<T>(factory: () => T) {
    return (err: unknown) => {
      if (!this.allowMock) {
        return throwError(() => err);
      }
      return of(factory());
    };
  }


  getStats(): Observable<AdminStats> {
    return this.http.get<AdminStats>(`${this.base}/stats`).pipe(
      map(data => (this.allowMock && this.isStubStats(data) ? this.mock.getStats() : data)),
      catchError(this.mockOrThrow(() => this.mock.getStats())),
    );
  }

  getAnalytics(period = '30d'): Observable<AnalyticsData> {
    return this.http.get<AnalyticsData>(`${this.base}/analytics`, {
      params: { period },
    }).pipe(
      map(data => (this.allowMock && this.isStubAnalytics(data) ? this.mock.getAnalytics(period) : data)),
      catchError(this.mockOrThrow(() => this.mock.getAnalytics(period))),
    );
  }

  getUsers(params: ListParams = {}): Observable<PaginatedResponse<User>> {
    return this.http.get<PaginatedResponse<User>>(`${this.base}/users`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getUsers(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getUsers(params))),
    );
  }

  getUser(id: string): Observable<User> {
    return this.http.get<User>(`${this.base}/users/${id}`).pipe(
      map(data => {
        if (!data?.id) {
          if (!this.allowMock) {
            throw new Error('User not found');
          }
          const user = this.mock.getUser(id);
          if (!user) throw new Error('User not found');
          return user;
        }
        return data;
      }),
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const user = this.mock.getUser(id);
        if (!user) throw new Error('User not found');
        return of(user);
      }),
    );
  }

  updateUser(id: string, data: Partial<Pick<User, 'is_active' | 'role'>>): Observable<User> {
    return this.http.patch<User>(`${this.base}/users/${id}`, data).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
        if (this.allowMock && params.is_verified === false && this.isEmptyPaginated(data)) {
          return this.mock.getPendingParlors();
        }
        return data;
      }),
      catchError(this.mockOrThrow(() => this.mock.getParlors(params))),
    );
  }

  getParlor(id: string): Observable<Parlor> {
    return this.http.get<Parlor>(`${this.base}/parlors/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const p = this.mock.getParlor(id);
        if (!p) throw new Error('Not found');
        return of(p);
      }),
    );
  }

  createParlor(data: ParlorCreateRequest): Observable<Parlor> {
    return this.http.post<Parlor>(`${this.base}/parlors`, data).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const created = this.mock.createParlor?.(data as Partial<Parlor>);
        if (!created) throw new Error('Failed to create parlor');
        return of(created);
      }),
    );
  }

  updateParlor(id: string, data: ParlorUpdateRequest): Observable<Parlor> {
    return this.http.patch<Parlor>(`${this.base}/parlors/${id}`, data).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.updateParlor?.(id, data as Partial<Parlor>);
        if (!updated) throw new Error('Parlor not found');
        return of(updated);
      }),
    );
  }

  assignParlorOwner(id: string, ownerId: string | null, promoteToOwner = true): Observable<Parlor> {
    return this.http
      .patch<Parlor>(`${this.base}/parlors/${id}/assign-owner`, {
        owner_id: ownerId,
        promote_to_owner: promoteToOwner,
      })
      .pipe(
        catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.updateParlor?.(id, { owner_id: ownerId } as Partial<Parlor>);
        if (!updated) throw new Error('Parlor not found');
        return of(updated);
      }),
      );
  }

  restoreParlor(id: string): Observable<Parlor> {
    return this.http.post<Parlor>(`${this.base}/parlors/${id}/restore`, {}).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.updateParlor?.(id, {
        is_deleted: false,
        is_active: true,
        } as Partial<Parlor>);
        if (!updated) throw new Error('Parlor not found');
        return of(updated);
      }),
    );
  }

  verifyParlor(id: string, isVerified: boolean): Observable<Parlor> {
    return this.http.patch<Parlor>(`${this.base}/parlors/${id}/verify`, {
      is_verified: isVerified,
    }).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.verifyParlor(id, isVerified);
        if (!updated) throw new Error('Parlor not found');
        return of(updated);
      }),
    );
  }

  deleteParlor(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/parlors/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deleteParlor(id)) throw new Error('Parlor not found');
        return of(void 0);
      }),
    );
  }

  getReels(params: ListParams = {}): Observable<PaginatedResponse<Record<string, unknown>>> {
    return this.http
      .get<PaginatedResponse<Record<string, unknown>>>(`${this.base}/reels`, {
        params: this.toParams(params),
      })
      .pipe(
        map(data => (this.isEmptyPaginated(data) ? { items: [], total: 0, page: 1, limit: 20, has_more: false } : data)),
        catchError(this.mockOrThrow(() => ({ items: [], total: 0, page: 1, limit: 20, has_more: false }))),
      );
  }

  deleteReel(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/reels/${id}`).pipe(
      catchError(this.mockOrThrow(() => void 0 as void)),
    );
  }

  getPosts(params: ListParams = {}): Observable<PaginatedResponse<Post>> {
    return this.http.get<PaginatedResponse<Post>>(`${this.base}/posts`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getPosts(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getPosts(params))),
    );
  }

  deletePost(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/posts/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deletePost(id)) throw new Error('Post not found');
        return of(void 0);
      }),
    );
  }

  getComments(params: ListParams = {}): Observable<PaginatedResponse<Comment>> {
    return this.http.get<PaginatedResponse<Comment>>(`${this.base}/comments`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getComments(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getComments(params))),
    );
  }

  deleteComment(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/comments/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deleteComment(id)) {
        throw new Error('Comment not found');
        }
        return of(void 0);
      }),
    );
  }

  restoreComment(id: string): Observable<void> {
    return this.http.patch<void>(`${this.base}/comments/${id}/restore`, {}).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getLikes(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getLikes(params))),
    );
  }

  deleteLike(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/likes/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getTournaments(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getTournaments(params))),
    );
  }

  updateTournamentStatus(id: string, status: string): Observable<Tournament> {
    return this.http.patch<Tournament>(`${this.base}/tournaments/${id}/status`, { status }).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getBookings(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getBookings(params))),
    );
  }

  getGamingBookings(params: ListParams = {}): Observable<PaginatedResponse<GamingBooking>> {
    return this.http.get<PaginatedResponse<GamingBooking>>(`${this.base}/gaming-bookings`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getGamingBookings(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getGamingBookings(params))),
    );
  }

  processGamingRefund(id: string): Observable<GamingBooking> {
    return this.http
      .patch<GamingBooking>(`${this.base}/gaming-bookings/${id}/process-refund`, {})
      .pipe(
        catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
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
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getGamingSlots(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getGamingSlots(params))),
    );
  }

  getOffers(params: ListParams = {}): Observable<PaginatedResponse<Offer>> {
    return this.http.get<PaginatedResponse<Offer>>(`${this.base}/offers`, {
      params: this.toParams(params),
    }).pipe(
      map(data => {
        if (this.isEmptyPaginated(data)) return this.mock.getOffers(params);
        return {
          ...data,
          items: data.items.map(o => this.normalizeOffer(o)),
        };
      }),
      catchError(this.mockOrThrow(() => this.mock.getOffers(params))),
    );
  }

  createOffer(data: OfferCreateRequest): Observable<Offer> {
    // Map Angular form shape → main backend AdminOfferCreate
    const body = {
      parlour_id: data.parlour_id,
      title: data.title,
      description: data.description ?? null,
      discount_percent: data.discount_type === 'percentage' ? data.discount_value : 0,
      discount_amount: data.discount_type === 'flat' ? data.discount_value : null,
      valid_from: data.valid_from,
      valid_until: data.valid_until,
      is_active: data.is_active ?? true,
    };
    return this.http.post<Offer>(`${this.base}/offers`, body).pipe(
      map(res => this.normalizeOffer(res)),
      catchError(this.mockOrThrow(() => this.mock.createOffer(data))),
    );
  }

  private normalizeOffer(raw: Offer | Record<string, unknown>): Offer {
    const r = raw as Record<string, unknown>;
    if (r['discount_type']) return raw as Offer;
    const pct = Number(r['discount_percent'] ?? 0);
    const amt = r['discount_amount'] != null ? Number(r['discount_amount']) : null;
    return {
      ...(raw as Offer),
      discount_type: pct > 0 ? 'percentage' : 'flat',
      discount_value: pct > 0 ? pct : Number(amt ?? 0),
      usage_count: Number(r['usage_count'] ?? r['current_uses'] ?? 0),
    };
  }

  getGcPoints(params: ListParams = {}): Observable<PaginatedResponse<GcPointsEntry>> {
    return this.http.get<PaginatedResponse<GcPointsEntry>>(`${this.base}/gc-points`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getGcPoints(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getGcPoints(params))),
    );
  }

  getEvents(params: ListParams = {}): Observable<PaginatedResponse<ParlourEvent>> {
    return this.http.get<PaginatedResponse<ParlourEvent>>(`${this.base}/events`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getEvents(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getEvents(params))),
    );
  }

  updateEventStatus(id: string, status: string): Observable<ParlourEvent> {
    return this.http.patch<ParlourEvent>(`${this.base}/events/${id}/status`, { status }).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.updateEventStatus(id, status);
        if (!updated) throw new Error('Event not found');
        return of(updated);
      }),
    );
  }

  deleteEvent(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/events/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deleteEvent(id)) throw new Error('Event not found');
        return of(void 0);
      }),
    );
  }

  getCommunity(params: ListParams = {}): Observable<PaginatedResponse<CommunityPost>> {
    return this.http.get<PaginatedResponse<CommunityPost>>(`${this.base}/community`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getCommunity(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getCommunity(params))),
    );
  }

  pinCommunityPost(id: string, isPinned: boolean): Observable<CommunityPost> {
    return this.http.patch<CommunityPost>(`${this.base}/community/${id}/pin`, {
      is_pinned: isPinned,
    }).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        const updated = this.mock.pinCommunityPost(id, isPinned);
        if (!updated) throw new Error('Post not found');
        return of(updated);
      }),
    );
  }

  deleteCommunityPost(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/community/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deleteCommunityPost(id)) throw new Error('Post not found');
        return of(void 0);
      }),
    );
  }

  getRatings(params: ListParams = {}): Observable<PaginatedResponse<Rating>> {
    return this.http.get<PaginatedResponse<Rating>>(`${this.base}/ratings`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getRatings(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getRatings(params))),
    );
  }

  deleteRating(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/ratings/${id}`).pipe(
      catchError((err) => {
        if (!this.allowMock) {
          return throwError(() => err);
        }
        if (!this.mock.deleteRating(id)) throw new Error('Rating not found');
        return of(void 0);
      }),
    );
  }

  broadcast(data: BroadcastRequest): Observable<{ sent_to: number }> {
    return this.http.post<{ sent_to: number }>(`${this.base}/notifications/broadcast`, data).pipe(
      catchError(this.mockOrThrow(() => this.mock.broadcast(data))),
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
      catchError(this.mockOrThrow(() => this.mock.getBroadcastHistory(params))),
    );
  }

  getGeoActivity(params: ListParams = {}): Observable<PaginatedResponse<GeoActivity>> {
    return this.http.get<PaginatedResponse<GeoActivity>>(`${this.base}/geo-activity`, {
      params: this.toParams(params),
    }).pipe(
      map(data => (this.allowMock && this.isEmptyPaginated(data) ? this.mock.getGeoActivity(params) : data)),
      catchError(this.mockOrThrow(() => this.mock.getGeoActivity(params))),
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

  // ───────────────────────────────────────────────────────────────────────────
  // Club Management (platform oversight) — /admin/club-management/*
  // Read-only views + platform override actions. Money is integer paise.
  // ───────────────────────────────────────────────────────────────────────────

  getClubManagementClubs(params: ListParams = {}): Observable<ClubListResponse> {
    return this.http.get<ClubListResponse>(`${this.base}/club-management/clubs`, {
      params: this.toParams(params),
    }).pipe(
      catchError(this.mockOrThrow<ClubListResponse>(() => ({
        items: [],
        limit: Number(params.limit ?? 20),
        offset: Number(params.offset ?? 0),
      }))),
    );
  }

  getClubResources(parlorId: string): Observable<ClubResourceListResponse> {
    return this.http.get<ClubResourceListResponse>(
      `${this.base}/club-management/clubs/${parlorId}/resources`,
    ).pipe(
      catchError(this.mockOrThrow<ClubResourceListResponse>(() => ({
        parlor_id: parlorId,
        items: [],
      }))),
    );
  }

  getClubLive(parlorId: string): Observable<ClubLiveResponse> {
    return this.http.get<ClubLiveResponse>(
      `${this.base}/club-management/clubs/${parlorId}/live`,
    ).pipe(
      catchError(this.mockOrThrow<ClubLiveResponse>(() => ({
        parlor_id: parlorId,
        occupants: [],
      }))),
    );
  }

  getClubRevenue(parlorId: string, range: ClubRevenueRange = 'today'): Observable<ClubRevenueSummary> {
    return this.http.get<ClubRevenueSummary>(
      `${this.base}/club-management/clubs/${parlorId}/revenue`,
      { params: this.toParams({ range }) },
    ).pipe(
      catchError(this.mockOrThrow<ClubRevenueSummary>(() => ({
        range,
        from_date: '',
        to_date: '',
        gross_paise: 0,
        gross_rupees: 0,
        commission_paise: 0,
        net_paise: 0,
        net_rupees: 0,
        discount_paise: 0,
        booking_count: 0,
        completed_count: 0,
        cancelled_count: 0,
        no_show_count: 0,
        avg_session_paise: 0,
        by_resource_type: [],
        by_payment_method: [],
        daily: [],
      }))),
    );
  }

  getClubOccupancy(
    parlorId: string,
    params: { from_date?: string; to_date?: string } = {},
  ): Observable<ClubOccupancyResponse> {
    return this.http.get<ClubOccupancyResponse>(
      `${this.base}/club-management/clubs/${parlorId}/occupancy`,
      { params: this.toParams(params) },
    ).pipe(
      catchError(this.mockOrThrow<ClubOccupancyResponse>(() => ({
        parlor_id: parlorId,
        from_date: params.from_date ?? '',
        to_date: params.to_date ?? '',
        heatmap: [],
        utilization: [],
        no_show: {
          from_date: params.from_date ?? '',
          to_date: params.to_date ?? '',
          booking_count: 0,
          no_show_count: 0,
          no_show_rate_bps: 0,
          by_resource_type: [],
        },
      }))),
    );
  }

  getClubBookings(
    parlorId: string,
    params: { date?: string; view?: ClubBookingView } = {},
  ): Observable<ClubBookingListResponse> {
    return this.http.get<ClubBookingListResponse>(
      `${this.base}/club-management/clubs/${parlorId}/bookings`,
      { params: this.toParams(params) },
    ).pipe(
      catchError(this.mockOrThrow<ClubBookingListResponse>(() => ({
        parlor_id: parlorId,
        items: [],
      }))),
    );
  }

  getClubPromotions(parlorId: string): Observable<ClubPromotionListResponse> {
    return this.http.get<ClubPromotionListResponse>(
      `${this.base}/club-management/clubs/${parlorId}/promotions`,
    ).pipe(
      catchError(this.mockOrThrow<ClubPromotionListResponse>(() => ({
        parlor_id: parlorId,
        items: [],
      }))),
    );
  }

  getClubCustomers(parlorId: string, params: ListParams = {}): Observable<ClubCustomerListResponse> {
    return this.http.get<ClubCustomerListResponse>(
      `${this.base}/club-management/clubs/${parlorId}/customers`,
      { params: this.toParams(params) },
    ).pipe(
      catchError(this.mockOrThrow<ClubCustomerListResponse>(() => ({
        parlor_id: parlorId,
        items: [],
        total: 0,
      }))),
    );
  }

  forceCancelClubBooking(
    parlorId: string,
    bookingId: string,
    reason: string,
    detail?: string,
  ): Observable<ClubForceCancelResponse> {
    return this.http.post<ClubForceCancelResponse>(
      `${this.base}/club-management/clubs/${parlorId}/bookings/${bookingId}/force-cancel`,
      { reason, detail },
    );
  }

  disableClubPromotion(
    parlorId: string,
    promotionId: string,
    disabled: boolean,
    reason?: string,
  ): Observable<ClubPromotionOverrideResponse> {
    return this.http.post<ClubPromotionOverrideResponse>(
      `${this.base}/club-management/clubs/${parlorId}/promotions/${promotionId}/disable`,
      { disabled, reason },
    );
  }

  deactivateClubResource(
    parlorId: string,
    resourceId: string,
    isActive: boolean,
    reason?: string,
  ): Observable<ClubResourceOverrideResponse> {
    return this.http.post<ClubResourceOverrideResponse>(
      `${this.base}/club-management/clubs/${parlorId}/resources/${resourceId}/deactivate`,
      { is_active: isActive, reason },
    );
  }

  flagClubCustomer(
    parlorId: string,
    customerId: string,
    flagged: boolean,
    reason?: string,
  ): Observable<ClubCustomerFlagResponse> {
    return this.http.post<ClubCustomerFlagResponse>(
      `${this.base}/club-management/clubs/${parlorId}/customers/${customerId}/flag`,
      { flagged, reason },
    );
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