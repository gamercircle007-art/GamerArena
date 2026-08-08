// Club Management — owner-operations repository.
//
// Follows `lib/features/booking/data/gaming_booking_repository.dart` exactly:
// constructor-injected Dio, one method per endpoint, tolerant response parsing,
// and `on DioException` with a 404 -> empty-list escape hatch for list reads.
//
// The optional `parlor_id` query param is deliberately never sent: the owner's
// club is inferred server-side from the JWT (see the build spec's API surface).

import 'package:dio/dio.dart';
import 'package:gamer_circle/features/club_management/domain/club_analytics.dart';
import 'package:gamer_circle/features/club_management/domain/club_customer.dart';
import 'package:gamer_circle/features/club_management/domain/club_resource.dart';
import 'package:gamer_circle/features/club_management/domain/owner_booking.dart';
import 'package:gamer_circle/features/club_management/domain/pricing_rule.dart';
import 'package:gamer_circle/features/club_management/domain/promotion.dart';

String _ymd(DateTime date) => date.toIso8601String().split('T').first;

List<dynamic> _asList(dynamic data) => data is Map
    ? (data['items'] as List<dynamic>? ?? data['rows'] as List<dynamic>? ?? [])
    : (data as List<dynamic>? ?? []);

class ClubManagementRepository {
  ClubManagementRepository(this._dio);

  final Dio _dio;

  // ---------------------------------------------------------------- zones ----

  Future<List<ClubZone>> fetchZones({CancelToken? cancelToken}) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/zones',
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => ClubZone.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<ClubZone> createZone({
    required String name,
    String? description,
    int sortOrder = 0,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/zones',
      data: {
        'name': name,
        if (description != null) 'description': description,
        'sort_order': sortOrder,
      },
    );
    return ClubZone.fromJson(response.data ?? {});
  }

  Future<ClubZone> updateZone(
    String zoneId, {
    String? name,
    String? description,
    int? sortOrder,
    bool? isActive,
  }) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/club/zones/$zoneId',
      data: {
        if (name != null) 'name': name,
        if (description != null) 'description': description,
        if (sortOrder != null) 'sort_order': sortOrder,
        if (isActive != null) 'is_active': isActive,
      },
    );
    return ClubZone.fromJson(response.data ?? {});
  }

  Future<void> deleteZone(String zoneId) async {
    await _dio.delete<dynamic>('/club/zones/$zoneId');
  }

  // ------------------------------------------------------------ resources ----

  Future<List<ClubResource>> fetchResources({
    String? zoneId,
    String? resourceType,
    String? status,
    bool? includeInactive,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/resources',
        queryParameters: {
          if (zoneId != null) 'zone_id': zoneId,
          if (resourceType != null) 'resource_type': resourceType,
          if (status != null) 'status': status,
          if (includeInactive != null) 'include_inactive': includeInactive,
        },
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => ClubResource.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<ClubResource> fetchResource(
    String resourceId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/resources/$resourceId',
      cancelToken: cancelToken,
    );
    return ClubResource.fromJson(response.data ?? {});
  }

  Future<ClubResource> createResource({
    required String label,
    required String resourceType,
    String? zoneId,
    String status = ClubResourceStatus.available,
    Map<String, dynamic>? specs,
    int? hourlyRateOverridePaise,
    int? layoutX,
    int? layoutY,
    bool isActive = true,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/resources',
      data: {
        'label': label,
        'resource_type': resourceType,
        if (zoneId != null) 'zone_id': zoneId,
        'status': status,
        if (specs != null) 'specs': specs,
        if (hourlyRateOverridePaise != null)
          'hourly_rate_override_paise': hourlyRateOverridePaise,
        if (layoutX != null) 'layout_x': layoutX,
        if (layoutY != null) 'layout_y': layoutY,
        'is_active': isActive,
      },
    );
    return ClubResource.fromJson(response.data ?? {});
  }

  Future<ClubResource> updateResource(
    String resourceId, {
    String? label,
    String? resourceType,
    String? zoneId,
    String? status,
    Map<String, dynamic>? specs,
    int? hourlyRateOverridePaise,
    int? layoutX,
    int? layoutY,
    bool? isActive,
  }) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/club/resources/$resourceId',
      data: {
        if (label != null) 'label': label,
        if (resourceType != null) 'resource_type': resourceType,
        if (zoneId != null) 'zone_id': zoneId,
        if (status != null) 'status': status,
        if (specs != null) 'specs': specs,
        if (hourlyRateOverridePaise != null)
          'hourly_rate_override_paise': hourlyRateOverridePaise,
        if (layoutX != null) 'layout_x': layoutX,
        if (layoutY != null) 'layout_y': layoutY,
        if (isActive != null) 'is_active': isActive,
      },
    );
    return ClubResource.fromJson(response.data ?? {});
  }

  Future<void> deleteResource(String resourceId) async {
    await _dio.delete<dynamic>('/club/resources/$resourceId');
  }

  Future<ClubResource> updateResourceStatus(
    String resourceId, {
    required String status,
    String? statusNote,
  }) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/club/resources/$resourceId/status',
      data: {
        'status': status,
        if (statusNote != null) 'status_note': statusNote,
      },
    );
    return ClubResource.fromJson(response.data ?? {});
  }

  /// Returns the number of resources the backend actually updated.
  Future<int> bulkUpdateResourceStatus({
    required List<String> resourceIds,
    required String status,
    String? statusNote,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/resources/status/bulk',
      data: {
        'resource_ids': resourceIds,
        'status': status,
        if (statusNote != null) 'status_note': statusNote,
      },
    );
    return (response.data?['updated'] as num?)?.toInt() ?? 0;
  }

  Future<bool> saveFloorLayout(List<ClubResource> resources) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/club/floor-layout',
      data: {
        'positions': [
          for (final r in resources)
            {
              'resource_id': r.id,
              'layout_x': r.layoutX ?? 0,
              'layout_y': r.layoutY ?? 0,
            },
        ],
      },
    );
    return response.data?['saved'] as bool? ?? false;
  }

  // ------------------------------------------------------------- bookings ----

  Future<List<OwnerBooking>> fetchBookings({
    required DateTime date,
    String view = 'day',
    String? status,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/bookings',
        queryParameters: {
          'date': _ymd(date),
          'view': view,
          if (status != null) 'status': status,
        },
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => OwnerBooking.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<OwnerBooking> createWalkIn({
    required String resourceType,
    String? resourceId,
    DateTime? bookingDate,
    String? startTime,
    int durationHours = 1,
    int units = 1,
    String? guestName,
    String? contactPhone,
    String? promoCode,
    String paymentMode = 'cash',
    bool checkInNow = true,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/walk-in',
      data: {
        'resource_type': resourceType,
        if (resourceId != null) 'resource_id': resourceId,
        if (bookingDate != null) 'booking_date': _ymd(bookingDate),
        if (startTime != null) 'start_time': startTime,
        'duration_hours': durationHours,
        'units': units,
        if (guestName != null) 'guest_name': guestName,
        if (contactPhone != null) 'contact_phone': contactPhone,
        if (promoCode != null) 'promo_code': promoCode,
        'payment_mode': paymentMode,
        'check_in_now': checkInNow,
      },
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> confirmBooking(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/confirm',
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> cancelBooking(
    String bookingId, {
    required String reason,
    String? detail,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/cancel',
      data: {
        'reason': reason,
        if (detail != null) 'detail': detail,
      },
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> checkInBooking(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/check-in',
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> checkOutBooking(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/check-out',
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> extendBooking(
    String bookingId, {
    required int additionalHours,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/extend',
      data: {'additional_hours': additionalHours},
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  Future<OwnerBooking> markNoShow(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/bookings/$bookingId/no-show',
    );
    return OwnerBooking.fromJson(response.data ?? {});
  }

  // ----------------------------------------------------------------- live ----

  Future<List<LiveOccupant>> fetchLive({CancelToken? cancelToken}) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/live',
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => LiveOccupant.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  // ------------------------------------------------------------ customers ----

  Future<ClubCustomerPage> fetchCustomers({
    String? search,
    int limit = 20,
    int offset = 0,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/customers',
        queryParameters: {
          if (search != null && search.isNotEmpty) 'search': search,
          'limit': limit,
          'offset': offset,
        },
        cancelToken: cancelToken,
      );
      final data = response.data;
      if (data is Map) {
        return ClubCustomerPage.fromJson(Map<String, dynamic>.from(data));
      }
      final items = (data as List<dynamic>? ?? [])
          .map((e) => ClubCustomer.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
      return ClubCustomerPage(
        items: items,
        total: items.length,
        limit: limit,
        offset: offset,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return const ClubCustomerPage();
      rethrow;
    }
  }

  Future<ClubCustomerDetail> fetchCustomer(
    String customerId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/customers/$customerId',
      cancelToken: cancelToken,
    );
    return ClubCustomerDetail.fromJson(response.data ?? {});
  }

  Future<void> addCustomerNote(String customerId, {required String body}) async {
    await _dio.post<dynamic>(
      '/club/customers/$customerId/note',
      data: {'body': body},
    );
  }

  Future<void> setCustomerTags(
    String customerId, {
    required List<String> tags,
  }) async {
    await _dio.post<dynamic>(
      '/club/customers/$customerId/tags',
      data: {'tags': tags},
    );
  }

  Future<void> setCustomerBan(
    String customerId, {
    required bool isBanned,
    String? reason,
  }) async {
    await _dio.post<dynamic>(
      '/club/customers/$customerId/ban',
      data: {
        'is_banned': isBanned,
        if (reason != null) 'reason': reason,
      },
    );
  }

  // -------------------------------------------------------------- pricing ----

  Future<List<PricingRule>> fetchPricingRules({CancelToken? cancelToken}) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/pricing/rules',
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => PricingRule.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<PricingRule> fetchPricingRule(
    String ruleId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/pricing/rules/$ruleId',
      cancelToken: cancelToken,
    );
    return PricingRule.fromJson(response.data ?? {});
  }

  Future<PricingRule> createPricingRule({
    required String name,
    required String scope,
    required int baseRatePaise,
    String? scopeValue,
    List<TimeSlab> timeSlabs = const [],
    Map<String, int> dayOfWeekOverrides = const {},
    List<PackageDef> packageDefs = const [],
    int priority = 0,
    DateTime? validFrom,
    DateTime? validTo,
    bool isActive = true,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/pricing/rules',
      data: _pricingRulePayload(
        name: name,
        scope: scope,
        baseRatePaise: baseRatePaise,
        scopeValue: scopeValue,
        timeSlabs: timeSlabs,
        dayOfWeekOverrides: dayOfWeekOverrides,
        packageDefs: packageDefs,
        priority: priority,
        validFrom: validFrom,
        validTo: validTo,
        isActive: isActive,
      ),
    );
    return PricingRule.fromJson(response.data ?? {});
  }

  Future<PricingRule> updatePricingRule(
    String ruleId, {
    String? name,
    String? scope,
    int? baseRatePaise,
    String? scopeValue,
    List<TimeSlab>? timeSlabs,
    Map<String, int>? dayOfWeekOverrides,
    List<PackageDef>? packageDefs,
    int? priority,
    DateTime? validFrom,
    DateTime? validTo,
    bool? isActive,
  }) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/club/pricing/rules/$ruleId',
      data: _pricingRulePayload(
        name: name,
        scope: scope,
        baseRatePaise: baseRatePaise,
        scopeValue: scopeValue,
        timeSlabs: timeSlabs,
        dayOfWeekOverrides: dayOfWeekOverrides,
        packageDefs: packageDefs,
        priority: priority,
        validFrom: validFrom,
        validTo: validTo,
        isActive: isActive,
      ),
    );
    return PricingRule.fromJson(response.data ?? {});
  }

  Future<void> deletePricingRule(String ruleId) async {
    await _dio.delete<dynamic>('/club/pricing/rules/$ruleId');
  }

  Map<String, dynamic> _pricingRulePayload({
    String? name,
    String? scope,
    int? baseRatePaise,
    String? scopeValue,
    List<TimeSlab>? timeSlabs,
    Map<String, int>? dayOfWeekOverrides,
    List<PackageDef>? packageDefs,
    int? priority,
    DateTime? validFrom,
    DateTime? validTo,
    bool? isActive,
  }) =>
      {
        if (name != null) 'name': name,
        if (scope != null) 'scope': scope,
        if (baseRatePaise != null) 'base_rate_paise': baseRatePaise,
        if (scopeValue != null) 'scope_value': scopeValue,
        if (timeSlabs != null)
          'time_slabs': timeSlabs.map((e) => e.toJson()).toList(),
        if (dayOfWeekOverrides != null)
          'day_of_week_overrides': dayOfWeekOverrides,
        if (packageDefs != null)
          'package_defs': packageDefs.map((e) => e.toJson()).toList(),
        if (priority != null) 'priority': priority,
        if (validFrom != null) 'valid_from': _ymd(validFrom),
        if (validTo != null) 'valid_to': _ymd(validTo),
        if (isActive != null) 'is_active': isActive,
      };

  Future<PricePreview> previewPrice({
    required String resourceType,
    required DateTime bookingDate,
    required String startTime,
    int durationHours = 1,
    int units = 1,
    String? resourceId,
    String? zoneId,
    String? promoCode,
    String? clubCustomerId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/pricing/preview',
      data: {
        'resource_type': resourceType,
        'booking_date': _ymd(bookingDate),
        'start_time': startTime,
        'duration_hours': durationHours,
        'units': units,
        if (resourceId != null) 'resource_id': resourceId,
        if (zoneId != null) 'zone_id': zoneId,
        if (promoCode != null && promoCode.isNotEmpty) 'promo_code': promoCode,
        if (clubCustomerId != null) 'club_customer_id': clubCustomerId,
      },
    );
    return PricePreview.fromJson(response.data ?? {});
  }

  // ----------------------------------------------------------- promotions ----

  Future<List<Promotion>> fetchPromotions({
    bool? activeOnly,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/club/promotions',
        queryParameters: {
          if (activeOnly != null) 'active_only': activeOnly,
        },
        cancelToken: cancelToken,
      );
      return _asList(response.data)
          .map((e) => Promotion.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<Promotion> fetchPromotion(
    String promotionId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/promotions/$promotionId',
      cancelToken: cancelToken,
    );
    return Promotion.fromJson(response.data ?? {});
  }

  Future<Promotion> createPromotion(Map<String, dynamic> payload) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/promotions',
      data: payload,
    );
    return Promotion.fromJson(response.data ?? {});
  }

  Future<Promotion> updatePromotion(
    String promotionId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/club/promotions/$promotionId',
      data: payload,
    );
    return Promotion.fromJson(response.data ?? {});
  }

  Future<void> deletePromotion(String promotionId) async {
    await _dio.delete<dynamic>('/club/promotions/$promotionId');
  }

  Future<PricePromotion> validatePromotion({
    required int subtotalPaise,
    required String resourceType,
    required DateTime bookingDate,
    required String startTime,
    String? code,
    String? promotionId,
    String? clubCustomerId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/club/promotions/validate',
      data: {
        'subtotal_paise': subtotalPaise,
        'resource_type': resourceType,
        'booking_date': _ymd(bookingDate),
        'start_time': startTime,
        if (code != null && code.isNotEmpty) 'code': code,
        if (promotionId != null) 'promotion_id': promotionId,
        if (clubCustomerId != null) 'club_customer_id': clubCustomerId,
      },
    );
    return PricePromotion.fromJson(response.data ?? {});
  }

  // -------------------------------------------------------------- revenue ----

  Future<RevenueSummary> fetchRevenueSummary({
    String range = RevenueRange.today,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/revenue/summary',
      queryParameters: {'range': range},
      cancelToken: cancelToken,
    );
    return RevenueSummary.fromJson(response.data ?? {});
  }

  // ------------------------------------------------------------ occupancy ----

  Future<OccupancyTimeseries> fetchOccupancyTimeseries({
    required DateTime fromDate,
    required DateTime toDate,
    String grain = 'club',
    String? grainKey,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/occupancy/timeseries',
      queryParameters: {
        'from_date': _ymd(fromDate),
        'to_date': _ymd(toDate),
        'grain': grain,
        if (grainKey != null) 'grain_key': grainKey,
      },
      cancelToken: cancelToken,
    );
    return OccupancyTimeseries.fromJson(response.data ?? {});
  }

  Future<OccupancyHeatmap> fetchOccupancyHeatmap({
    required DateTime fromDate,
    required DateTime toDate,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/occupancy/heatmap',
      queryParameters: {
        'from_date': _ymd(fromDate),
        'to_date': _ymd(toDate),
      },
      cancelToken: cancelToken,
    );
    return OccupancyHeatmap.fromJson(response.data ?? {});
  }

  Future<UtilizationReport> fetchUtilization({
    required DateTime fromDate,
    required DateTime toDate,
    String grain = 'resource',
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/occupancy/utilization',
      queryParameters: {
        'from_date': _ymd(fromDate),
        'to_date': _ymd(toDate),
        'grain': grain,
      },
      cancelToken: cancelToken,
    );
    return UtilizationReport.fromJson(response.data ?? {});
  }

  Future<NoShowRate> fetchNoShowRate({
    required DateTime fromDate,
    required DateTime toDate,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/club/occupancy/no-show-rate',
      queryParameters: {
        'from_date': _ymd(fromDate),
        'to_date': _ymd(toDate),
      },
      cancelToken: cancelToken,
    );
    return NoShowRate.fromJson(response.data ?? {});
  }
}
