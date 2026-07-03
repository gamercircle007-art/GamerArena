import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/tournament/providers/booking_provider.dart';
import 'package:gamer_circle/shared/models/booking.dart';

class MyBookingsScreen extends ConsumerStatefulWidget {
  const MyBookingsScreen({super.key});

  @override
  ConsumerState<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends ConsumerState<MyBookingsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 2, vsync: this);
  List<Booking> _upcoming = [];
  List<Booking> _past = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final api = ref.read(socialApiProvider);
    final upcoming = await api.fetchMyBookings(upcoming: true);
    final past = await api.fetchMyBookings(upcoming: false);
    setState(() {
      _upcoming = upcoming;
      _past = past;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Bookings'),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [Tab(text: 'Upcoming'), Tab(text: 'Past')],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          _BookingList(bookings: _upcoming, onChanged: _load),
          _BookingList(bookings: _past, onChanged: _load),
        ],
      ),
    );
  }
}

class _BookingList extends ConsumerWidget {
  const _BookingList({required this.bookings, required this.onChanged});

  final List<Booking> bookings;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (bookings.isEmpty) return const Center(child: Text('No bookings'));
    return ListView.builder(
      itemCount: bookings.length,
      itemBuilder: (_, i) {
        final b = bookings[i];
        final pending = b.paymentStatus == 'pending';
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: ListTile(
            title: Text('Slot #${b.slotNumber}'),
            subtitle: Text('Status: ${b.status}'),
            trailing: pending
                ? FilledButton(
                    onPressed: () async {
                      final paid = await ref
                          .read(bookingProvider.notifier)
                          .payForBooking(b.id);
                      if (paid != null) onChanged();
                    },
                    child: const Text('Pay'),
                  )
                : Chip(
                    label: Text(b.paymentStatus),
                    backgroundColor: b.paymentStatus == 'paid'
                        ? Colors.green.shade50
                        : null,
                  ),
            onTap: () => context.push('/tournaments/${b.tournamentId}'),
          ),
        );
      },
    );
  }
}