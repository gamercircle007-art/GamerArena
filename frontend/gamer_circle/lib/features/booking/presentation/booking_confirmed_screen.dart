import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/presentation/booking_details_tab.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:gamer_circle/shared/widgets/booking_bottom_cta.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

class BookingConfirmedScreen extends ConsumerStatefulWidget {
  const BookingConfirmedScreen({super.key, this.booking});

  final dynamic booking;

  @override
  ConsumerState<BookingConfirmedScreen> createState() =>
      _BookingConfirmedScreenState();
}

class _BookingConfirmedScreenState extends ConsumerState<BookingConfirmedScreen> {
  String? _guestName;
  String? _email;
  String? _phone;
  String? _gstin;
  int _numPlayers = 1;

  @override
  Widget build(BuildContext context) {
    final existingBooking = widget.booking;
    if (existingBooking != null) {
      return _SuccessView(booking: existingBooking);
    }

    final draft = ref.watch(gamingBookingDraftProvider);
    final bookingState = ref.watch(gamingBookingProvider);

    if (draft == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Confirm Booking')),
        body: const Center(child: Text('No booking in progress')),
      );
    }

    final slot = draft.slot!;
    const hours = 1.0;
    final price = slot.pricePerHour * hours * _numPlayers;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirm Booking'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Expanded(
            child: BookingDetailsTab(
              draft: draft.copyWith(
                numPlayers: _numPlayers,
                guestName: _guestName,
                contactEmail: _email,
                contactPhone: _phone,
                gstin: _gstin,
              ),
              onNumPlayersChanged: (v) => setState(() => _numPlayers = v),
              onGuestNameChanged: (v) => _guestName = v,
              onContactEmailChanged: (v) => _email = v,
              onContactPhoneChanged: (v) => _phone = v,
              onGstinChanged: (v) => _gstin = v,
            ),
          ),
          if (bookingState.error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                bookingState.error!,
                style: const TextStyle(color: BookingColors.cancelledOrange),
              ),
            ),
          BookingBottomCta(
            price: price,
            label: 'Confirm Booking',
            isLoading: bookingState.isSubmitting,
            onPressed: () async {
              final updated = draft.copyWith(
                numPlayers: _numPlayers,
                guestName: _guestName,
                contactEmail: _email,
                contactPhone: _phone,
                gstin: _gstin,
              );
              ref.read(gamingBookingDraftProvider.notifier).state = updated;
              final booking = await ref
                  .read(gamingBookingProvider.notifier)
                  .confirmBooking(updated);
              if (booking != null && context.mounted) {
                context.go('/booking/confirm', extra: booking);
              }
            },
          ),
        ],
      ),
    );
  }
}

class _SuccessView extends StatelessWidget {
  const _SuccessView({required this.booking});

  final dynamic booking;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: BookingColors.confirmedGreen,
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 40),
            const Icon(Icons.check_circle, color: Colors.white, size: 72),
            const SizedBox(height: 16),
            const Text(
              'Booking Confirmed!',
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Ref: ${booking.bookingRef}',
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
            const SizedBox(height: 24),
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                ),
                child: ListView(
                  children: [
                    Text(
                      booking.parlourName ?? 'Gaming Parlour',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    if (booking.slotDate != null) ...[
                      const SizedBox(height: 12),
                      _InfoRow(
                        Icons.calendar_today,
                        DateFormat('EEE, dd MMM yyyy').format(booking.slotDate!),
                      ),
                    ],
                    if (booking.startTime != null)
                      _InfoRow(
                        Icons.schedule,
                        '${booking.startTime} - ${booking.endTime ?? ''}',
                      ),
                    if (booking.finalPrice != null)
                      _InfoRow(
                        Icons.payments,
                        formatInr(booking.finalPrice!),
                      ),
                    if (booking.gcPointsEarned > 0)
                      _InfoRow(
                        Icons.stars,
                        '+${booking.gcPointsEarned} GC Points earned',
                      ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: () =>
                          context.go('/booking/${booking.id}/details'),
                      style: FilledButton.styleFrom(
                        backgroundColor: BookingColors.oyoRed,
                        minimumSize: const Size(double.infinity, 48),
                      ),
                      child: const Text('View Booking Details'),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => Share.share(
                        'Booking confirmed at ${booking.parlourName}! Ref: ${booking.bookingRef}',
                      ),
                      child: const Text('Share'),
                    ),
                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () => context.go('/gaming-bookings'),
                      child: const Text('Go to My Bookings'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.icon, this.text);

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: BookingColors.textSecondary),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}