import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:gamer_circle/shared/models/gaming_booking.dart';
import 'package:intl/intl.dart';
import 'package:shimmer/shimmer.dart';

class GamingMyBookingsScreen extends ConsumerStatefulWidget {
  const GamingMyBookingsScreen({super.key});

  @override
  ConsumerState<GamingMyBookingsScreen> createState() =>
      _GamingMyBookingsScreenState();
}

class _GamingMyBookingsScreenState extends ConsumerState<GamingMyBookingsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 2, vsync: this);

  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(gamingBookingProvider.notifier).loadMyBookings(),
    );
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(gamingBookingProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Bookings'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(text: 'Upcoming'),
            Tab(text: 'Past'),
          ],
        ),
      ),
      body: state.isLoadingList
          ? ListView.builder(
              itemCount: 4,
              itemBuilder: (_, __) => const _BookingCardShimmer(),
            )
          : RefreshIndicator(
              color: BookingColors.oyoRed,
              onRefresh: () =>
                  ref.read(gamingBookingProvider.notifier).loadMyBookings(),
              child: TabBarView(
                controller: _tabs,
                children: [
                  _BookingList(
                    bookings: state.upcoming,
                    emptyMessage: 'No upcoming bookings',
                  ),
                  _BookingList(
                    bookings: state.past,
                    emptyMessage: 'No past bookings',
                  ),
                ],
              ),
            ),
    );
  }
}

class _BookingList extends StatelessWidget {
  const _BookingList({
    required this.bookings,
    required this.emptyMessage,
  });

  final List<GamingBooking> bookings;
  final String emptyMessage;

  @override
  Widget build(BuildContext context) {
    if (bookings.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          Center(
            child: Column(
              children: [
                Icon(
                  Icons.event_note_outlined,
                  size: 48,
                  color: Colors.grey.shade400,
                ),
                const SizedBox(height: 12),
                Text(
                  emptyMessage,
                  style: const TextStyle(color: BookingColors.textSecondary),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => context.go('/home-booking'),
                  style: FilledButton.styleFrom(
                    backgroundColor: BookingColors.oyoRed,
                  ),
                  child: const Text('Explore Parlours'),
                ),
              ],
            ),
          ),
        ],
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: bookings.length,
      itemBuilder: (_, i) => _BookingCard(booking: bookings[i]),
    );
  }
}

class _BookingCard extends StatelessWidget {
  const _BookingCard({required this.booking});

  final GamingBooking booking;

  @override
  Widget build(BuildContext context) {
    final statusColor = booking.isCancelled
        ? BookingColors.cancelledOrange
        : BookingColors.confirmedGreen;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: () => context.push('/booking/${booking.id}/details'),
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: BookingColors.border),
            ),
            child: Row(
              children: [
                if (booking.parlourImage != null)
                  ClipRRect(
                    borderRadius: const BorderRadius.horizontal(
                      left: Radius.circular(11),
                    ),
                    child: CachedNetworkImage(
                      imageUrl: booking.parlourImage!,
                      width: 90,
                      height: 100,
                      fit: BoxFit.cover,
                    ),
                  )
                else
                  Container(
                    width: 90,
                    height: 100,
                    decoration: const BoxDecoration(
                      color: BookingColors.background,
                      borderRadius: BorderRadius.horizontal(
                        left: Radius.circular(11),
                      ),
                    ),
                    child: const Icon(Icons.videogame_asset),
                  ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          booking.parlourName ?? 'Gaming Parlour',
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          booking.bookingRef,
                          style: const TextStyle(
                            fontSize: 12,
                            color: BookingColors.textSecondary,
                          ),
                        ),
                        if (booking.slotDate != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            DateFormat('dd MMM yyyy').format(booking.slotDate!),
                            style: const TextStyle(fontSize: 12),
                          ),
                        ],
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: statusColor.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                booking.isCancelled ? 'Cancelled' : 'Confirmed',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: statusColor,
                                ),
                              ),
                            ),
                            const Spacer(),
                            if (booking.finalPrice != null)
                              Text(
                                formatInr(booking.finalPrice!),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _BookingCardShimmer extends StatelessWidget {
  const _BookingCardShimmer();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        height: 100,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}