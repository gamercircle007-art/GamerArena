import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:intl/intl.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class BookingDetailsViewScreen extends ConsumerWidget {
  const BookingDetailsViewScreen({super.key, required this.bookingId});

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
        appBar: AppBar(title: const Text('Booking Details')),
        body: Center(child: Text('Error: $e')),
      ),
      data: (booking) {
        final statusColor = booking.isCancelled
            ? BookingColors.cancelledOrange
            : BookingColors.confirmedGreen;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Booking Details'),
            backgroundColor: BookingColors.oyoRed,
            foregroundColor: Colors.white,
            actions: [
              IconButton(
                icon: const Icon(Icons.share),
                onPressed: () => Share.share(
                  'Booking ${booking.bookingRef} at ${booking.parlourName}',
                ),
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      booking.isCancelled
                          ? Icons.cancel_outlined
                          : Icons.check_circle_outline,
                      color: statusColor,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      booking.isCancelled ? 'Cancelled' : 'Confirmed',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: statusColor,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      booking.bookingRef,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              if (booking.parlourImage != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: CachedNetworkImage(
                    imageUrl: booking.parlourImage!,
                    height: 160,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
              const SizedBox(height: 12),
              Text(
                booking.parlourName ?? 'Gaming Parlour',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
              if (booking.parlourAddress != null) ...[
                const SizedBox(height: 4),
                Text(
                  booking.parlourAddress!,
                  style: const TextStyle(color: BookingColors.textSecondary),
                ),
              ],
              const SizedBox(height: 16),
              _DetailTile(
                'Date',
                booking.slotDate != null
                    ? DateFormat('EEE, dd MMM yyyy').format(booking.slotDate!)
                    : '-',
              ),
              _DetailTile(
                'Time',
                '${booking.startTime ?? '-'} - ${booking.endTime ?? '-'}',
              ),
              _DetailTile('Players', '${booking.numPlayers}'),
              _DetailTile(
                'Amount',
                booking.finalPrice != null
                    ? formatInr(booking.finalPrice!)
                    : '-',
              ),
              _DetailTile('Payment', booking.paymentMode),
              _DetailTile('Payment status', booking.paymentStatus),
              if (booking.gcPointsEarned > 0)
                _DetailTile('GC Points', '+${booking.gcPointsEarned}'),
              const SizedBox(height: 16),
              Center(
                child: QrImageView(
                  data: booking.bookingRef,
                  version: QrVersions.auto,
                  size: 140,
                ),
              ),
              const SizedBox(height: 8),
              const Center(
                child: Text(
                  'Show this QR at the parlour',
                  style: TextStyle(
                    fontSize: 12,
                    color: BookingColors.textSecondary,
                  ),
                ),
              ),
              if (booking.contactPhone != null) ...[
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () =>
                      launchUrl(Uri.parse('tel:${booking.contactPhone}')),
                  icon: const Icon(Icons.phone),
                  label: const Text('Call parlour'),
                ),
              ],
              if (booking.isConfirmed) ...[
                const SizedBox(height: 24),
                OutlinedButton(
                  onPressed: () =>
                      context.push('/booking/$bookingId/cancel-reason'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: BookingColors.cancelledOrange,
                    side: const BorderSide(color: BookingColors.cancelledOrange),
                    minimumSize: const Size(double.infinity, 48),
                  ),
                  child: const Text('Cancel Booking'),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _DetailTile extends StatelessWidget {
  const _DetailTile(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(
            label,
            style: const TextStyle(color: BookingColors.textSecondary),
          ),
          const Spacer(),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}