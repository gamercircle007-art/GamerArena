import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';

/// Selection carried from time grid → checkout (time-first booking).
@immutable
class BookingSelection {
  const BookingSelection({
    required this.parlorId,
    required this.parlorName,
    required this.date,
    required this.startTime,
    required this.stationType,
    required this.durationHours,
    required this.units,
    required this.pricePaise,
    this.parlorImage,
  });

  final String parlorId;
  final String parlorName;
  final String? parlorImage;
  final DateTime date;
  final String startTime; // HH:mm or HH:mm:ss
  final String stationType;
  final int durationHours;
  final int units;
  final int pricePaise;

  String get startTimeDisplay {
    final t = startTime.length >= 5 ? startTime.substring(0, 5) : startTime;
    return t;
  }

  double get priceRupees => pricePaise / 100.0;
}

final bookingSelectionProvider = StateProvider<BookingSelection?>((ref) => null);

class AvailabilityParams {
  const AvailabilityParams({
    required this.parlorId,
    required this.date,
    required this.stationType,
  });

  final String parlorId;
  final DateTime date;
  final String stationType;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AvailabilityParams &&
          parlorId == other.parlorId &&
          stationType == other.stationType &&
          date.year == other.date.year &&
          date.month == other.date.month &&
          date.day == other.date.day;

  @override
  int get hashCode => Object.hash(
        parlorId,
        stationType,
        date.year,
        date.month,
        date.day,
      );
}

/// Live capacity grid from GET /parlors/{id}/availability (includes version `v`).
final availabilitySnapshotProvider =
    FutureProvider.family<Map<String, dynamic>, AvailabilityParams>(
  (ref, params) async {
    final repo = ref.watch(gamingBookingRepositoryProvider);
    return repo.fetchAvailabilitySnapshot(
      parlorId: params.parlorId,
      date: params.date,
      stationType: params.stationType,
    );
  },
);
