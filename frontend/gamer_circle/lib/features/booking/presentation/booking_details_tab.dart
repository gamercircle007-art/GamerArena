import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';

import 'package:intl/intl.dart';

class BookingDetailsTab extends StatelessWidget {
  const BookingDetailsTab({
    super.key,
    required this.draft,
    this.onNumPlayersChanged,
    this.onGuestNameChanged,
    this.onContactEmailChanged,
    this.onContactPhoneChanged,
    this.onGstinChanged,
  });

  final GamingBookingDraft draft;
  final ValueChanged<int>? onNumPlayersChanged;
  final ValueChanged<String>? onGuestNameChanged;
  final ValueChanged<String>? onContactEmailChanged;
  final ValueChanged<String>? onContactPhoneChanged;
  final ValueChanged<String>? onGstinChanged;

  @override
  Widget build(BuildContext context) {
    final slot = draft.slot;
    if (slot == null) {
      return const Center(child: Text('No slot selected'));
    }

    final hours = _hoursBetween(slot.startTime, slot.endTime);
    final subtotal = slot.pricePerHour * hours * draft.numPlayers;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _SectionCard(
          title: 'Parlour',
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(
              draft.parlourName,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            subtitle: slot.gameName != null ? Text(slot.gameName!) : null,
          ),
        ),
        const SizedBox(height: 12),
        _SectionCard(
          title: 'Slot details',
          child: Column(
            children: [
              _Row('Date', DateFormat('EEE, dd MMM yyyy').format(slot.slotDate)),
              _Row('Time', '${slot.startTime} - ${slot.endTime}'),
              _Row('Duration', '${hours.toStringAsFixed(1)} hrs'),
              _Row('Players', '${draft.numPlayers}'),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _SectionCard(
          title: 'Guest details',
          child: Column(
            children: [
              TextField(
                decoration: const InputDecoration(labelText: 'Guest name'),
                onChanged: onGuestNameChanged,
              ),
              const SizedBox(height: 8),
              TextField(
                decoration: const InputDecoration(labelText: 'Email'),
                keyboardType: TextInputType.emailAddress,
                onChanged: onContactEmailChanged,
              ),
              const SizedBox(height: 8),
              TextField(
                decoration: const InputDecoration(labelText: 'Phone'),
                keyboardType: TextInputType.phone,
                onChanged: onContactPhoneChanged,
              ),
              const SizedBox(height: 8),
              TextField(
                decoration: const InputDecoration(
                  labelText: 'GSTIN (optional)',
                ),
                onChanged: onGstinChanged,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Text('Number of players'),
                  const Spacer(),
                  IconButton(
                    onPressed: draft.numPlayers > 1
                        ? () => onNumPlayersChanged?.call(draft.numPlayers - 1)
                        : null,
                    icon: const Icon(Icons.remove_circle_outline),
                  ),
                  Text('${draft.numPlayers}'),
                  IconButton(
                    onPressed: () =>
                        onNumPlayersChanged?.call(draft.numPlayers + 1),
                    icon: const Icon(Icons.add_circle_outline),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _SectionCard(
          title: 'Price breakdown',
          child: Column(
            children: [
              _Row(
                'Subtotal',
                formatInr(subtotal),
              ),
              _Row(
                'Per hour',
                formatInr(slot.pricePerHour),
              ),
              const Divider(),
              _Row(
                'Total',
                formatInr(subtotal),
                bold: true,
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Payment at parlour — pay when you arrive',
          style: TextStyle(
            fontSize: 12,
            color: BookingColors.textSecondary,
          ),
        ),
      ],
    );
  }

  double _hoursBetween(String start, String end) {
    try {
      final s = _parseTime(start);
      final e = _parseTime(end);
      final diff = e.difference(s).inMinutes / 60.0;
      return diff > 0 ? diff : 1;
    } catch (_) {
      return 1;
    }
  }

  DateTime _parseTime(String t) {
    final parts = t.split(':');
    final now = DateTime.now();
    return DateTime(
      now.year,
      now.month,
      now.day,
      int.parse(parts[0]),
      parts.length > 1 ? int.parse(parts[1]) : 0,
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: BookingColors.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.label, this.value, {this.bold = false});

  final String label;
  final String value;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(
            label,
            style: TextStyle(
              color: BookingColors.textSecondary,
              fontWeight: bold ? FontWeight.w700 : FontWeight.normal,
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              fontWeight: bold ? FontWeight.w800 : FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}