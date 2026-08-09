import 'package:dio/dio.dart';
import 'package:gamer_circle/shared/models/gaming_booking.dart';

class GamingBookingRepository {
  GamingBookingRepository(this._dio);

  final Dio _dio;

  Future<List<GamingSlot>> fetchSlots(
    String parlourId, {
    DateTime? date,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/parlors/$parlourId/slots',
        queryParameters: {
          if (date != null) 'date': date.toIso8601String().split('T').first,
        },
        cancelToken: cancelToken,
      );
      final data = response.data;
      final items = data is Map
          ? (data['slots'] as List<dynamic>? ??
              data['items'] as List<dynamic>? ??
              [])
          : (data as List<dynamic>? ?? []);
      return items
          .map((e) => GamingSlot.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<GamingBooking> createBooking({
    required String parlourId,
    required String slotId,
    int numPlayers = 1,
    String? guestName,
    String? offerId,
    String? contactEmail,
    String? contactPhone,
    String? gstin,
    String paymentMode = 'pay_at_parlor',
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings',
      data: {
        'parlour_id': parlourId,
        'slot_id': slotId,
        'num_players': numPlayers,
        if (guestName != null) 'guest_name': guestName,
        if (offerId != null) 'offer_id': offerId,
        if (contactEmail != null) 'contact_email': contactEmail,
        if (contactPhone != null) 'contact_phone': contactPhone,
        if (gstin != null) 'gstin': gstin,
        'payment_mode': paymentMode,
      },
    );
    return GamingBooking.fromJson(response.data ?? {});
  }

  Future<List<GamingBooking>> fetchMyBookings({
    bool? upcoming,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/users/me/gaming-bookings',
        queryParameters: upcoming == null
            ? null
            : {'status': upcoming ? 'upcoming' : 'past'},
        cancelToken: cancelToken,
      );
      final items = response.data is Map
          ? (response.data['items'] as List<dynamic>? ?? [])
          : (response.data as List<dynamic>? ?? []);
      return items
          .map((e) => GamingBooking.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }

  Future<GamingBooking> fetchBooking(
    String bookingId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/bookings/$bookingId',
      cancelToken: cancelToken,
    );
    return GamingBooking.fromJson(response.data ?? {});
  }

  Future<GamingBooking> cancelBooking(
    String bookingId, {
    required String reason,
    String? detail,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings/$bookingId/cancel',
      data: {
        'cancellation_reason': reason,
        if (detail != null) 'cancellation_detail': detail,
      },
    );
    return GamingBooking.fromJson(response.data ?? {});
  }

  /// Spec availability: virtual hourly inventory with capacity (+ version `v`).
  Future<Map<String, dynamic>> fetchAvailabilitySnapshot({
    required String parlorId,
    required DateTime date,
    String stationType = 'PC',
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/clubs/$parlorId/availability',
      queryParameters: {
        'date': date.toIso8601String().split('T').first,
        'station_type': stationType,
      },
    );
    return response.data ?? {};
  }

  /// Spec availability: virtual hourly inventory with capacity.
  Future<List<Map<String, dynamic>>> fetchAvailability({
    required String parlorId,
    required DateTime date,
    String stationType = 'PC',
  }) async {
    final snap = await fetchAvailabilitySnapshot(
      parlorId: parlorId,
      date: date,
      stationType: stationType,
    );
    final slots = snap['slots'] as List<dynamic>? ?? [];
    return slots.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> fetchStationTypes(String parlorId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/parlors/$parlorId/station-types',
    );
    final types = response.data?['station_types'] as List<dynamic>? ?? [];
    return types.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  /// Temporary hold — Idempotency-Key required. expires_at is authoritative.
  Future<Map<String, dynamic>> holdSlot({
    required String parlorId,
    required String stationType,
    required DateTime date,
    required String startTime,
    int durationHours = 1,
    int units = 1,
    String? guestName,
    String? contactPhone,
    required String idempotencyKey,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings/hold',
      data: {
        'parlor_id': parlorId,
        'station_type': stationType,
        'date': date.toIso8601String().split('T').first,
        'start_time': startTime.length == 5 ? '$startTime:00' : startTime,
        'duration_hours': durationHours,
        'units': units,
        if (guestName != null) 'guest_name': guestName,
        if (contactPhone != null) 'contact_phone': contactPhone,
      },
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    return response.data ?? {};
  }

  Future<Map<String, dynamic>> releaseHold(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings/$bookingId/release',
    );
    return response.data ?? {};
  }

  Future<Map<String, dynamic>> payHeldBooking(String bookingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings/$bookingId/pay',
    );
    return response.data ?? {};
  }

  /// Create booking with hold + optional Cashfree session (Idempotency-Key).
  Future<Map<String, dynamic>> createBookingV2({
    required String parlorId,
    required String stationType,
    required DateTime date,
    required String startTime,
    int durationHours = 1,
    int units = 1,
    String paymentMode = 'pay_at_parlor',
    String? guestName,
    String? contactPhone,
    required String idempotencyKey,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/bookings/v2',
      data: {
        'parlor_id': parlorId,
        'station_type': stationType,
        'date': date.toIso8601String().split('T').first,
        'start_time': startTime.length == 5 ? '$startTime:00' : startTime,
        'duration_hours': durationHours,
        'units': units,
        'payment_mode': paymentMode,
        if (guestName != null) 'guest_name': guestName,
        if (contactPhone != null) 'contact_phone': contactPhone,
      },
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    return response.data ?? {};
  }

  Future<Map<String, dynamic>> fetchBookingStatus(String bookingId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/bookings/$bookingId/status',
    );
    return response.data ?? {};
  }

  /// After payment SDK return — poll server (webhook is authoritative).
  Future<Map<String, dynamic>> pollUntilTerminal(
    String bookingId, {
    Duration interval = const Duration(seconds: 2),
    Duration timeout = const Duration(seconds: 60),
  }) async {
    final deadline = DateTime.now().add(timeout);
    while (DateTime.now().isBefore(deadline)) {
      final status = await fetchBookingStatus(bookingId);
      final s = (status['booking_status'] as String? ?? '').toLowerCase();
      if (s == 'confirmed' ||
          s == 'expired' ||
          s == 'cancelled' ||
          s == 'failed' ||
          s == 'refund_pending') {
        return status;
      }
      await Future<void>.delayed(interval);
    }
    return fetchBookingStatus(bookingId);
  }
}