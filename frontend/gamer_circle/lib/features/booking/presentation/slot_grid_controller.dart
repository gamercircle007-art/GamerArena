/// Slot grid state for live availability (Phase 7).
///
/// Apply WS deltas to this map; rebuild only the affected cell via
/// [ValueNotifier] — never setState the whole grid on every message.

import 'package:flutter/foundation.dart';

enum SlotState {
  available,
  booked,
  heldByOther,
  heldByMe,
  pending,
}

class SlotGridController {
  SlotGridController();

  /// resourceId → start → state
  final Map<int, Map<String, ValueNotifier<SlotState>>> cells = {};

  int version = 0;
  String? myHoldBookingId;
  DateTime? holdExpiresAt;

  ValueNotifier<SlotState> cell(int resourceId, String startIso) {
    final byStart = cells.putIfAbsent(resourceId, () => {});
    return byStart.putIfAbsent(
      startIso,
      () => ValueNotifier(SlotState.available),
    );
  }

  void applyDelta(Map<String, dynamic> msg) {
    final t = msg['t'] as String?;
    final start = msg['start'] as String?;
    if (t == null || start == null) return;
    final v = msg['v'];
    if (v is int) version = v;

    final units = (msg['units'] as int?) ?? 1;
    final bookingId = msg['booking_id'] as String?;
    for (var i = 0; i < units; i++) {
      final notifier = cell(i, start);
      if (t == 'slot_held') {
        notifier.value = bookingId != null && bookingId == myHoldBookingId
            ? SlotState.heldByMe
            : SlotState.heldByOther;
      } else if (t == 'slot_released') {
        if (notifier.value != SlotState.booked) {
          notifier.value = SlotState.available;
        }
      } else if (t == 'slot_confirmed') {
        notifier.value = SlotState.booked;
      }
    }
  }

  /// Optimistic tap — pending until server confirms or reverts with toast.
  void markPending(int resourceId, String startIso) {
    cell(resourceId, startIso).value = SlotState.pending;
  }

  void revert(int resourceId, String startIso, SlotState to) {
    cell(resourceId, startIso).value = to;
  }

  /// Countdown from server [holdExpiresAt], recomputed against device clock.
  Duration? remainingHold(DateTime now) {
    final exp = holdExpiresAt;
    if (exp == null) return null;
    final d = exp.difference(now);
    return d.isNegative ? Duration.zero : d;
  }

  void dispose() {
    for (final m in cells.values) {
      for (final n in m.values) {
        n.dispose();
      }
    }
    cells.clear();
  }
}
