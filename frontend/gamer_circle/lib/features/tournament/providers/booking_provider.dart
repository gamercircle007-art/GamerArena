import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/data/social_remote_datasource.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/services/razorpay_service.dart';
import 'package:gamer_circle/shared/models/booking.dart';

class BookingState {
  const BookingState({
    this.isBooking = false,
    this.isPaying = false,
    this.lastBooking,
    this.error,
  });

  final bool isBooking;
  final bool isPaying;
  final Booking? lastBooking;
  final String? error;

  BookingState copyWith({
    bool? isBooking,
    bool? isPaying,
    Booking? lastBooking,
    String? error,
  }) =>
      BookingState(
        isBooking: isBooking ?? this.isBooking,
        isPaying: isPaying ?? this.isPaying,
        lastBooking: lastBooking ?? this.lastBooking,
        error: error,
      );
}

class BookingNotifier extends StateNotifier<BookingState> {
  BookingNotifier(this._api) : super(const BookingState());

  final SocialRemoteDataSource _api;
  final _razorpay = RazorpayService();

  Future<Booking?> bookSlot(String tournamentId) async {
    state = state.copyWith(isBooking: true, error: null);
    try {
      final booking = await _api.bookSlot(tournamentId);
      state = state.copyWith(isBooking: false, lastBooking: booking);
      return booking;
    } catch (e) {
      state = state.copyWith(isBooking: false, error: e.toString());
      return null;
    }
  }

  Future<Booking?> payForBooking(
    String bookingId, {
    String? description,
    String? contact,
    String? email,
  }) async {
    state = state.copyWith(isPaying: true, error: null);
    try {
      final order = await _api.createBookingPaymentOrder(bookingId);
      final orderId = order['order_id'] as String;
      final amountPaise = order['amount_paise'] as int;
      final keyId = order['key_id'] as String?;

      String paymentId;
      String signature;

      if (keyId != null && keyId.isNotEmpty && _razorpay.isSupported) {
        final checkout = await _razorpay.openCheckout(
          keyId: keyId,
          orderId: orderId,
          amountPaise: amountPaise,
          description: description ?? 'Tournament entry fee',
          contact: contact,
          email: email,
        );
        paymentId = checkout.paymentId;
        signature = checkout.signature;
      } else {
        // Local dev / web fallback — server accepts dev signatures in local env
        paymentId = 'pay_dev_${DateTime.now().millisecondsSinceEpoch}';
        signature = 'dev_signature';
      }

      final updated = await _api.verifyBookingPayment(
        bookingId,
        orderId: orderId,
        paymentId: paymentId,
        signature: signature,
      );
      state = state.copyWith(isPaying: false, lastBooking: updated);
      return updated;
    } catch (e) {
      state = state.copyWith(isPaying: false, error: e.toString());
      return null;
    }
  }
}

final bookingProvider = StateNotifierProvider<BookingNotifier, BookingState>((ref) {
  return BookingNotifier(ref.watch(socialApiProvider));
});

final razorpayEnabledProvider = FutureProvider<bool>((ref) async {
  try {
    final config = await ref.watch(socialApiProvider).fetchRazorpayConfig();
    return config['enabled'] as bool? ?? false;
  } catch (_) {
    return false;
  }
});