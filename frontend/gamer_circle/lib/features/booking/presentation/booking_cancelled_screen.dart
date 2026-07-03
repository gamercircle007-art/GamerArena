import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:intl/intl.dart';

class BookingCancelledScreen extends ConsumerWidget {
  const BookingCancelledScreen({super.key, required this.bookingId});

  final String bookingId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookingAsync = ref.watch(gamingBookingDetailProvider(bookingId));

    return bookingAsync.when(
      loading: () => const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: BookingColors.oyoRed),
        ),
      ),
      error: (e, _) => Scaffold(
        body: Center(child: Text('Error: $e')),
      ),
      data: (booking) => Scaffold(
        backgroundColor: BookingColors.cancelledOrange,
        body: SafeArea(
          child: Column(
            children: [
              const SizedBox(height: 48),
              const Icon(Icons.event_busy, color: Colors.white, size: 72),
              const SizedBox(height: 16),
              const Text(
                'Booking Cancelled',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                booking.bookingRef,
                style: const TextStyle(color: Colors.white70),
              ),
              const SizedBox(height: 24),
              Expanded(
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    borderRadius:
                        BorderRadius.vertical(top: Radius.circular(24)),
                  ),
                  child: ListView(
                    children: [
                      Text(
                        booking.parlourName ?? 'Gaming Parlour',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      if (booking.cancellationReason != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          'Reason: ${booking.cancellationReason}',
                          style: const TextStyle(
                            color: BookingColors.textSecondary,
                          ),
                        ),
                      ],
                      if (booking.cancelledAt != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          'Cancelled on ${DateFormat('dd MMM yyyy, hh:mm a').format(booking.cancelledAt!)}',
                          style: const TextStyle(
                            color: BookingColors.textSecondary,
                          ),
                        ),
                      ],
                      if (booking.refundAmount > 0) ...[
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: BookingColors.confirmedGreen
                                .withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.account_balance_wallet_outlined,
                                color: BookingColors.confirmedGreen,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Refund: ${formatInr(booking.refundAmount)}'
                                  '${booking.refundStatus != null ? ' (${booking.refundStatus})' : ''}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 24),
                      FilledButton(
                        onPressed: () => context.go('/home-booking'),
                        style: FilledButton.styleFrom(
                          backgroundColor: BookingColors.oyoRed,
                          minimumSize: const Size(double.infinity, 48),
                        ),
                        child: const Text('Book Another Parlour'),
                      ),
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: () => context.go('/gaming-bookings'),
                        child: const Text('View My Bookings'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}