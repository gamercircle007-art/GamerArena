import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/booking/data/gaming_booking_repository.dart';
import 'package:gamer_circle/shared/models/gaming_booking.dart';

final gamingBookingRepositoryProvider = Provider<GamingBookingRepository>((ref) {
  return GamingBookingRepository(ref.watch(dioProvider));
});

class GamingBookingDraft {
  const GamingBookingDraft({
    required this.parlourId,
    required this.parlourName,
    this.parlourImage,
    this.slot,
    this.numPlayers = 1,
    this.guestName,
    this.offerId,
    this.contactEmail,
    this.contactPhone,
    this.gstin,
    this.paymentMode = 'pay_at_parlor',
  });

  final String parlourId;
  final String parlourName;
  final String? parlourImage;
  final GamingSlot? slot;
  final int numPlayers;
  final String? guestName;
  final String? offerId;
  final String? contactEmail;
  final String? contactPhone;
  final String? gstin;
  final String paymentMode;

  GamingBookingDraft copyWith({
    GamingSlot? slot,
    int? numPlayers,
    String? guestName,
    String? offerId,
    String? contactEmail,
    String? contactPhone,
    String? gstin,
    String? paymentMode,
  }) =>
      GamingBookingDraft(
        parlourId: parlourId,
        parlourName: parlourName,
        parlourImage: parlourImage,
        slot: slot ?? this.slot,
        numPlayers: numPlayers ?? this.numPlayers,
        guestName: guestName ?? this.guestName,
        offerId: offerId ?? this.offerId,
        contactEmail: contactEmail ?? this.contactEmail,
        contactPhone: contactPhone ?? this.contactPhone,
        gstin: gstin ?? this.gstin,
        paymentMode: paymentMode ?? this.paymentMode,
      );
}

final gamingBookingDraftProvider =
    StateProvider<GamingBookingDraft?>((ref) => null);

class GamingBookingState {
  const GamingBookingState({
    this.isSubmitting = false,
    this.lastBooking,
    this.error,
    this.upcoming = const [],
    this.past = const [],
    this.isLoadingList = false,
  });

  final bool isSubmitting;
  final GamingBooking? lastBooking;
  final String? error;
  final List<GamingBooking> upcoming;
  final List<GamingBooking> past;
  final bool isLoadingList;

  GamingBookingState copyWith({
    bool? isSubmitting,
    GamingBooking? lastBooking,
    String? error,
    List<GamingBooking>? upcoming,
    List<GamingBooking>? past,
    bool? isLoadingList,
    bool clearError = false,
  }) =>
      GamingBookingState(
        isSubmitting: isSubmitting ?? this.isSubmitting,
        lastBooking: lastBooking ?? this.lastBooking,
        error: clearError ? null : (error ?? this.error),
        upcoming: upcoming ?? this.upcoming,
        past: past ?? this.past,
        isLoadingList: isLoadingList ?? this.isLoadingList,
      );
}

final gamingBookingProvider =
    NotifierProvider<GamingBookingNotifier, GamingBookingState>(
  GamingBookingNotifier.new,
);

class GamingBookingNotifier extends Notifier<GamingBookingState> {
  @override
  GamingBookingState build() => const GamingBookingState();

  GamingBookingRepository get _repo => ref.read(gamingBookingRepositoryProvider);

  Future<GamingBooking?> confirmBooking(GamingBookingDraft draft) async {
    final slot = draft.slot;
    if (slot == null) {
      state = state.copyWith(error: 'Please select a slot');
      return null;
    }

    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      final booking = await _repo.createBooking(
        parlourId: draft.parlourId,
        slotId: slot.id,
        numPlayers: draft.numPlayers,
        guestName: draft.guestName,
        offerId: draft.offerId,
        contactEmail: draft.contactEmail,
        contactPhone: draft.contactPhone,
        gstin: draft.gstin,
        paymentMode: draft.paymentMode,
      );
      state = state.copyWith(isSubmitting: false, lastBooking: booking);
      ref.read(gamingBookingDraftProvider.notifier).state = null;
      return booking;
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
      return null;
    }
  }

  Future<void> loadMyBookings() async {
    state = state.copyWith(isLoadingList: true, clearError: true);
    try {
      final upcoming = await _repo.fetchMyBookings(upcoming: true);
      final past = await _repo.fetchMyBookings(upcoming: false);
      state = state.copyWith(
        upcoming: upcoming,
        past: past,
        isLoadingList: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingList: false, error: e.toString());
    }
  }

  Future<GamingBooking?> cancelBooking(
    String bookingId, {
    required String reason,
    String? detail,
  }) async {
    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      final booking = await _repo.cancelBooking(
        bookingId,
        reason: reason,
        detail: detail,
      );
      state = state.copyWith(isSubmitting: false, lastBooking: booking);
      await loadMyBookings();
      return booking;
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
      return null;
    }
  }
}

final gamingSlotsProvider =
    FutureProvider.family<List<GamingSlot>, GamingSlotsParams>(
  (ref, params) async {
    return ref.read(gamingBookingRepositoryProvider).fetchSlots(
          params.parlourId,
          date: params.date,
        );
  },
);

class GamingSlotsParams {
  const GamingSlotsParams({required this.parlourId, this.date});

  final String parlourId;
  final DateTime? date;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is GamingSlotsParams &&
          parlourId == other.parlourId &&
          date == other.date;

  @override
  int get hashCode => Object.hash(parlourId, date);
}

final gamingBookingDetailProvider =
    FutureProvider.family<GamingBooking, String>(
  (ref, bookingId) async {
    return ref.read(gamingBookingRepositoryProvider).fetchBooking(bookingId);
  },
);