import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';

/// Polls GET /bookings/{id}/status after Cashfree / mock payment.
class BookingStatusScreen extends ConsumerStatefulWidget {
  const BookingStatusScreen({
    super.key,
    required this.bookingId,
    this.mockMode = false,
  });

  final String bookingId;
  final bool mockMode;

  @override
  ConsumerState<BookingStatusScreen> createState() =>
      _BookingStatusScreenState();
}

class _BookingStatusScreenState extends ConsumerState<BookingStatusScreen> {
  Timer? _timer;
  int _ticks = 0;
  String _status = 'payment_pending';
  String? _ref;
  String? _error;

  @override
  void initState() {
    super.initState();
    _poll();
    _timer = Timer.periodic(const Duration(seconds: 2), (_) => _poll());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _poll() async {
    if (_ticks > 30) {
      _timer?.cancel();
      setState(() => _error = 'Still pending — check My Bookings later');
      return;
    }
    _ticks++;
    try {
      final repo = ref.read(gamingBookingRepositoryProvider);
      final data = await repo.fetchBookingStatus(widget.bookingId);
      if (!mounted) return;
      setState(() {
        _status = data['booking_status']?.toString() ?? _status;
        _ref = data['booking_ref']?.toString();
      });
      if (_status == 'confirmed' ||
          _status == 'failed' ||
          _status == 'expired' ||
          _status == 'cancelled' ||
          _status == 'refund_pending') {
        _timer?.cancel();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final ok = _status == 'confirmed';
    final pending = _status == 'payment_pending' ||
        _status == 'initiated' ||
        _status == 'held';
    final refund = _status == 'refund_pending';
    return Scaffold(
      appBar: AppBar(
        title: const Text('3 · Confirmation'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (pending)
                const CircularProgressIndicator(color: BookingColors.oyoRed)
              else
                Icon(
                  ok
                      ? Icons.check_circle
                      : refund
                          ? Icons.replay_circle_filled
                          : Icons.error_outline,
                  size: 72,
                  color: ok
                      ? Colors.green
                      : refund
                          ? Colors.orange
                          : Colors.red,
                ),
              const SizedBox(height: 16),
              Text(
                ok
                    ? 'Booking confirmed!'
                    : pending
                        ? 'Confirming payment…'
                        : refund
                            ? 'Payment received after expiry — refund queued'
                            : 'Status: $_status',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
                textAlign: TextAlign.center,
              ),
              if (_ref != null) ...[
                const SizedBox(height: 8),
                Text('Ref: $_ref', style: const TextStyle(color: Colors.grey)),
              ],
              if (widget.mockMode && pending) ...[
                const SizedBox(height: 12),
                const Text(
                  'Cashfree sandbox not configured — booking held; pay at parlor or set CASHFREE_* keys.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: Colors.orange),
                ),
              ],
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 28),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: BookingColors.oyoRed,
                ),
                onPressed: () => context.go('/gaming-bookings'),
                child: const Text('My Bookings'),
              ),
              TextButton(
                onPressed: () => context.go('/discover'),
                child: const Text('Back to Discover'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
