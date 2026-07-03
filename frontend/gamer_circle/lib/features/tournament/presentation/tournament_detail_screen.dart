import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/features/tournament/providers/booking_provider.dart';
import 'package:gamer_circle/features/tournament/providers/tournament_provider.dart';
import 'package:gamer_circle/shared/widgets/slot_selector.dart';
import 'package:intl/intl.dart';

class TournamentDetailScreen extends ConsumerStatefulWidget {
  const TournamentDetailScreen({super.key, required this.tournamentId});

  final String tournamentId;

  @override
  ConsumerState<TournamentDetailScreen> createState() => _TournamentDetailScreenState();
}

class _TournamentDetailScreenState extends ConsumerState<TournamentDetailScreen> {
  @override
  void initState() {
    super.initState();
    WsService.instance.subscribe('tournament:${widget.tournamentId}');
    WsService.instance.events.listen((event) {
      if (event['event'] == 'slot_booked') {
        final payload = event['payload'] as Map<String, dynamic>?;
        final booked = payload?['booked_slots'] as int?;
        if (booked != null) {
          ref.read(tournamentProvider(widget.tournamentId).notifier).updateSlots(booked);
        }
      }
    });
  }

  @override
  void dispose() {
    WsService.instance.unsubscribe('tournament:${widget.tournamentId}');
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tournamentAsync = ref.watch(tournamentProvider(widget.tournamentId));
    final booking = ref.watch(bookingProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Tournament')),
      body: tournamentAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (t) {
          final date = DateFormat('d MMM yyyy · h:mm a').format(t.startTime);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Container(
                height: 160,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  gradient: LinearGradient(
                    colors: [Colors.deepPurple.shade400, Colors.deepPurple.shade800],
                  ),
                ),
                alignment: Alignment.bottomLeft,
                padding: const EdgeInsets.all(16),
                child: Text(
                  t.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(t.parlor?.name ?? t.gameType, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text('$date · ${t.format}'),
              const SizedBox(height: 16),
              SlotSelector(
                totalSlots: t.totalSlots,
                bookedSlots: t.bookedSlots,
                mySlotNumber: booking.lastBooking?.tournamentId == t.id
                    ? booking.lastBooking?.slotNumber
                    : null,
              ),
              const SizedBox(height: 16),
              if (t.prizes != null && t.prizes!.isNotEmpty)
                ExpansionTile(
                  title: const Text('Prizes'),
                  children: t.prizes!.entries
                      .map((e) => ListTile(title: Text(e.key), subtitle: Text(e.value.toString())))
                      .toList(),
                ),
              if (t.rules != null)
                ExpansionTile(
                  title: const Text('Rules'),
                  children: [Padding(padding: const EdgeInsets.all(16), child: Text(t.rules!))],
                ),
              if (booking.lastBooking?.tournamentId == t.id &&
                  booking.lastBooking?.paymentStatus == 'pending') ...[
                const SizedBox(height: 12),
                Card(
                  color: Colors.orange.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Payment required: ₹${t.entryFee.toStringAsFixed(0)}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 8),
                        FilledButton(
                          onPressed: booking.isPaying
                              ? null
                              : () async {
                                  final id = booking.lastBooking!.id;
                                  final paid = await ref
                                      .read(bookingProvider.notifier)
                                      .payForBooking(id);
                                  if (paid != null && context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text('Payment confirmed')),
                                    );
                                  }
                                },
                          child: booking.isPaying
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Pay Now'),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: t.isFull || booking.isBooking
                      ? null
                      : () async {
                          final result =
                              await ref.read(bookingProvider.notifier).bookSlot(t.id);
                          if (result != null && context.mounted) {
                            ref.read(tournamentProvider(widget.tournamentId).notifier)
                                .updateSlots(result.slotNumber);
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Booked slot #${result.slotNumber}')),
                            );
                          }
                        },
                  child: booking.isBooking
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(t.isFull ? 'Sold Out' : 'Book Slot'),
                ),
              ),
              TextButton(
                onPressed: () => context.push('/posts/${t.id}/comments'),
                child: const Text('See comments'),
              ),
              TextButton(
                onPressed: () => context.push('/tournaments/${t.id}/chat'),
                child: const Text('Tournament chat'),
              ),
            ],
          );
        },
      ),
    );
  }
}