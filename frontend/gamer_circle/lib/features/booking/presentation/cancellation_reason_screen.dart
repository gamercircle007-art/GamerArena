import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';

const kCancellationReasons = [
  'Change of plans',
  'Found a better deal',
  'Booked by mistake',
  'Parlour is too far',
  'Health reasons',
  'Other',
];

class CancellationReasonScreen extends StatefulWidget {
  const CancellationReasonScreen({super.key, required this.bookingId});

  final String bookingId;

  @override
  State<CancellationReasonScreen> createState() =>
      _CancellationReasonScreenState();
}

class _CancellationReasonScreenState extends State<CancellationReasonScreen> {
  String? _selected;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cancel Booking'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'Why are you cancelling?',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          Expanded(
            child: ListView(
              children: kCancellationReasons
                  .map(
                    (reason) => RadioListTile<String>(
                      title: Text(reason),
                      value: reason,
                      groupValue: _selected,
                      activeColor: BookingColors.oyoRed,
                      onChanged: (v) => setState(() => _selected = v),
                    ),
                  )
                  .toList(),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: FilledButton(
              onPressed: _selected == null
                  ? null
                  : () {
                      if (_selected == 'Other') {
                        context.push(
                          '/booking/${widget.bookingId}/cancel-detail',
                          extra: _selected,
                        );
                      } else {
                        context.push(
                          '/booking/${widget.bookingId}/cancel-detail',
                          extra: _selected,
                        );
                      }
                    },
              style: FilledButton.styleFrom(
                backgroundColor: BookingColors.cancelledOrange,
                minimumSize: const Size(double.infinity, 48),
              ),
              child: const Text('Continue'),
            ),
          ),
        ],
      ),
    );
  }
}