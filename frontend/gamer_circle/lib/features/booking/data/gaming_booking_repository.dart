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
}