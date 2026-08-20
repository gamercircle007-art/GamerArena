import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/api_error_utils.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/booking_flow_provider.dart';
import 'package:intl/intl.dart';
import 'package:shimmer/shimmer.dart';

/// Screen 1 of 3 — pick date / station / duration / time (before device).
///
/// UX assumption: time is the fixed constraint; units = how many seats/PCs.
class BookTimeScreen extends ConsumerStatefulWidget {
  const BookTimeScreen({
    super.key,
    required this.parlorId,
    this.parlorName,
    this.parlorImage,
  });

  final String parlorId;
  final String? parlorName;
  final String? parlorImage;

  @override
  ConsumerState<BookTimeScreen> createState() => _BookTimeScreenState();
}

class _BookTimeScreenState extends ConsumerState<BookTimeScreen> {
  DateTime _date = DateTime.now();
  String _station = 'PC';
  int _duration = 1;
  int _units = 1;
  String? _selectedStart;
  int _selectedPricePaise = 0;

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 30)),
    );
    if (picked != null) {
      setState(() {
        _date = picked;
        _selectedStart = null;
      });
    }
  }

  void _continue() {
    if (_selectedStart == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pick a start time')),
      );
      return;
    }
    ref.read(bookingSelectionProvider.notifier).state = BookingSelection(
      parlorId: widget.parlorId,
      parlorName: widget.parlorName ?? 'Centre',
      parlorImage: widget.parlorImage,
      date: _date,
      startTime: _selectedStart!,
      stationType: _station,
      durationHours: _duration,
      units: _units,
      pricePaise: _selectedPricePaise * _duration * _units,
    );
    context.push('/parlour/${widget.parlorId}/checkout');
  }

  @override
  Widget build(BuildContext context) {
    final snapAsync = ref.watch(
      availabilitySnapshotProvider(
        AvailabilityParams(
          parlorId: widget.parlorId,
          date: _date,
          stationType: _station,
        ),
      ),
    );

    return Scaffold(
      backgroundColor: BookingColors.background,
      appBar: AppBar(
        title: Text(widget.parlorName ?? 'Book a slot'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              children: [
                const Text(
                  '1 · When',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: BookingColors.textSecondary,
                    letterSpacing: 0.4,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Pick your time first',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Devices are assigned after payment — no dead ends.',
                  style: TextStyle(color: BookingColors.textSecondary),
                ),
                const SizedBox(height: 20),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.calendar_today, color: BookingColors.oyoRed),
                  title: const Text('Date'),
                  subtitle: Text(DateFormat('EEE, dd MMM yyyy').format(_date)),
                  trailing: const Icon(Icons.edit_calendar_outlined),
                  onTap: _pickDate,
                ),
                const SizedBox(height: 8),
                const Text('Station type', style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: ['PC', 'PS5', 'VR', 'XBOX', 'POOL']
                      .map(
                        (t) => ChoiceChip(
                          label: Text(t),
                          selected: _station == t,
                          selectedColor: BookingColors.oyoRed.withValues(alpha: 0.15),
                          onSelected: (_) => setState(() {
                            _station = t;
                            _selectedStart = null;
                          }),
                        ),
                      )
                      .toList(),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    const Text('Duration', style: TextStyle(fontWeight: FontWeight.w600)),
                    const Spacer(),
                    for (final h in [1, 2, 3])
                      Padding(
                        padding: const EdgeInsets.only(left: 6),
                        child: ChoiceChip(
                          label: Text('${h}h'),
                          selected: _duration == h,
                          onSelected: (_) => setState(() => _duration = h),
                        ),
                      ),
                  ],
                ),
                Row(
                  children: [
                    const Text('Seats / units', style: TextStyle(fontWeight: FontWeight.w600)),
                    const Spacer(),
                    IconButton(
                      onPressed: _units > 1 ? () => setState(() => _units--) : null,
                      icon: const Icon(Icons.remove_circle_outline),
                    ),
                    Text('$_units', style: const TextStyle(fontWeight: FontWeight.w700)),
                    IconButton(
                      onPressed: _units < 4 ? () => setState(() => _units++) : null,
                      icon: const Icon(Icons.add_circle_outline),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Text('Available times', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                snapAsync.when(
                  loading: () => const _GridShimmer(),
                  error: (e, _) {
                    final msg = e is DioException
                        ? messageFromDioException(e, 'Could not load times')
                        : e.toString();
                    return Text(
                      'Could not load times.\n$msg',
                      style: const TextStyle(color: Colors.red),
                    );
                  },
                  data: (snap) {
                    final slots = (snap['slots'] as List<dynamic>? ?? [])
                        .map((e) => Map<String, dynamic>.from(e as Map))
                        .toList();
                    if (slots.isEmpty) {
                      return const Padding(
                        padding: EdgeInsets.symmetric(vertical: 24),
                        child: Text('No open slots for this date — try another day.'),
                      );
                    }
                    return Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: slots.map((slot) {
                        final start = (slot['start_time'] as String? ?? '');
                        final avail = (slot['available_units'] as num?)?.toInt() ?? 0;
                        final disabled = slot['disabled'] == true || avail < _units;
                        final pricePaise = (slot['price_paise'] as num?)?.toInt() ?? 0;
                        final selected = _selectedStart == start;
                        final label = start.length >= 5 ? start.substring(0, 5) : start;
                        return Semantics(
                          button: true,
                          label: 'slot_$label',
                          child: FilterChip(
                            label: Text(
                              disabled
                                  ? '$label · full'
                                  : '$label · ${formatInr(pricePaise / 100)}',
                            ),
                            selected: selected,
                            showCheckmark: false,
                            selectedColor: BookingColors.oyoRed.withValues(alpha: 0.18),
                            onSelected: disabled
                                ? null
                                : (_) => setState(() {
                                      _selectedStart = start;
                                      _selectedPricePaise = pricePaise;
                                    }),
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: BookingColors.oyoRed,
                    disabledBackgroundColor: Colors.grey.shade300,
                  ),
                  onPressed: _selectedStart == null ? null : _continue,
                  child: Text(
                    _selectedStart == null
                        ? 'Select a time'
                        : 'Continue · ${formatInr((_selectedPricePaise / 100) * _duration * _units)}',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GridShimmer extends StatelessWidget {
  const _GridShimmer();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: List.generate(
          8,
          (_) => Container(
            width: 100,
            height: 36,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
      ),
    );
  }
}
