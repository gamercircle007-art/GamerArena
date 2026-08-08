// Club Management — display formatting helpers.
//
// Two rules from the build spec live here so no screen re-implements them:
//   1. Money is integer paise everywhere; only formatting converts to rupees.
//      Reuses the app-wide `formatInr` from core/utils/currency_formatter.dart.
//   2. Every date/time shown to an owner is Asia/Kolkata (IST). The app has no
//      timezone package, so the fixed +05:30 offset is applied explicitly
//      (India has no DST, so a fixed offset is exact).

import 'package:intl/intl.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';

const Duration kIstOffset = Duration(hours: 5, minutes: 30);

/// `now` in IST wall-clock terms.
DateTime nowIst() => DateTime.now().toUtc().add(kIstOffset);

/// Today in IST, truncated to midnight.
DateTime todayIst() {
  final now = nowIst();
  return DateTime(now.year, now.month, now.day);
}

/// Shifts a server timestamp (UTC) to IST wall-clock.
DateTime toIst(DateTime value) => value.toUtc().add(kIstOffset);

/// ₹ amount from integer paise. Never use floats to *store* money.
String formatPaise(int paise) => formatInr(paise / 100);

/// Basis points -> percent string (10000 bps == 100%).
String formatBps(int bps) => '${(bps / 100).toStringAsFixed(1)}%';

/// Basis points -> 0.0..1.0 fraction, clamped for bar/tint rendering.
double bpsFraction(int bps) => (bps / 10000).clamp(0.0, 1.0);

String formatIstDate(DateTime value) =>
    DateFormat('EEE, dd MMM').format(toIst(value));

String formatIstDateTime(DateTime value) =>
    '${DateFormat('dd MMM, hh:mm a').format(toIst(value))} IST';

String formatIstTime(DateTime value) =>
    '${DateFormat('hh:mm a').format(toIst(value))} IST';

/// Local (already-IST) calendar date, for a header the owner picked themselves.
String formatPickedDate(DateTime value) =>
    DateFormat('EEE, dd MMM yyyy').format(value);

/// `HH:MM[:SS]` -> `hh:mm a`, tolerant of a bad/short value.
String formatClockTime(String? raw) {
  if (raw == null || raw.length < 4) return '--:--';
  final parts = raw.split(':');
  final hour = int.tryParse(parts.first) ?? 0;
  final minute = parts.length > 1 ? int.tryParse(parts[1]) ?? 0 : 0;
  return DateFormat('hh:mm a').format(DateTime(2000, 1, 1, hour, minute));
}

/// Minutes -> `1h 20m`, used by the Live screen countdown.
String formatMinutes(int minutes) {
  final abs = minutes.abs();
  final hours = abs ~/ 60;
  final mins = abs % 60;
  if (hours == 0) return '${mins}m';
  return '${hours}h ${mins}m';
}

/// Human label for an enum-ish snake_case API value.
String humanizeToken(String token) => token
    .split(RegExp(r'[_\s]+'))
    .where((part) => part.isNotEmpty)
    .map((part) => part.length <= 3
        ? part.toUpperCase()
        : '${part[0].toUpperCase()}${part.substring(1)}')
    .join(' ');

/// Monday-first weekday labels matching the heatmap's `weekday` (0 == Mon).
const List<String> kWeekdayLabels = [
  'Mon',
  'Tue',
  'Wed',
  'Thu',
  'Fri',
  'Sat',
  'Sun',
];
