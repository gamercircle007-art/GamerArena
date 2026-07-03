import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';

class CancellationDetailScreen extends ConsumerStatefulWidget {
  const CancellationDetailScreen({
    super.key,
    required this.bookingId,
    this.reason,
  });

  final String bookingId;
  final String? reason;

  @override
  ConsumerState<CancellationDetailScreen> createState() =>
      _CancellationDetailScreenState();
}

class _CancellationDetailScreenState
    extends ConsumerState<CancellationDetailScreen> {
  final _detailController = TextEditingController();

  @override
  void dispose() {
    _detailController.dispose();
    super.dispose();
  }

  Future<void> _confirmCancel() async {
    final reason = widget.reason ?? 'Other';
    final booking = await ref.read(gamingBookingProvider.notifier).cancelBooking(
          widget.bookingId,
          reason: reason,
          detail: _detailController.text.trim().isEmpty
              ? null
              : _detailController.text.trim(),
        );
    if (booking != null && mounted) {
      context.go('/booking/${widget.bookingId}/cancelled');
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(gamingBookingProvider);
    final showDetail = widget.reason == 'Other';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirm Cancellation'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: BookingColors.cancelledOrange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, color: BookingColors.cancelledOrange),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Cancellation may be subject to refund policy. '
                      'Free cancellation before the deadline earns full refund.',
                      style: TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Reason: ${widget.reason ?? 'Not specified'}',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            if (showDetail) ...[
              const SizedBox(height: 16),
              TextField(
                controller: _detailController,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Please tell us more',
                  alignLabelWithHint: true,
                ),
              ),
            ],
            const Spacer(),
            if (state.error != null)
              Text(
                state.error!,
                style: const TextStyle(color: BookingColors.cancelledOrange),
              ),
            FilledButton(
              onPressed: state.isSubmitting ? null : _confirmCancel,
              style: FilledButton.styleFrom(
                backgroundColor: BookingColors.cancelledOrange,
                minimumSize: const Size(double.infinity, 48),
              ),
              child: state.isSubmitting
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Cancel Booking'),
            ),
          ],
        ),
      ),
    );
  }
}