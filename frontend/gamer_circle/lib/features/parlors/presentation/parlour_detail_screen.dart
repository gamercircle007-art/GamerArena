import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/features/booking/providers/gaming_booking_provider.dart';
import 'package:gamer_circle/features/parlors/providers/parlor_search_provider.dart';
import 'package:gamer_circle/shared/models/gaming_booking.dart';
import 'package:gamer_circle/shared/widgets/booking_bottom_cta.dart';
import 'package:gamer_circle/shared/widgets/category_rating_bar.dart';
import 'package:gamer_circle/shared/widgets/offer_card.dart';
import 'package:gamer_circle/shared/widgets/rating_stars.dart';
import 'package:intl/intl.dart';
import 'package:readmore/readmore.dart';
import 'package:shimmer/shimmer.dart';
import 'package:url_launcher/url_launcher.dart';

class ParlourDetailScreen extends ConsumerStatefulWidget {
  const ParlourDetailScreen({super.key, required this.parlourId});

  final String parlourId;

  @override
  ConsumerState<ParlourDetailScreen> createState() =>
      _ParlourDetailScreenState();
}

class _ParlourDetailScreenState extends ConsumerState<ParlourDetailScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 3, vsync: this);
  DateTime _selectedDate = DateTime.now();
  GamingSlot? _selectedSlot;
  String _stationType = 'PC';
  int _durationHours = 1;
  int _units = 1;
  bool _booking = false;

  @override
  void initState() {
    super.initState();
    _tabs.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 30)),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = picked;
        _selectedSlot = null;
      });
    }
  }

  Future<void> _bookNow(String parlourName, String? image) async {
    if (_selectedSlot == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a time slot')),
      );
      return;
    }
    // Prefer v2 booking (hold + Cashfree-ready). Fall back to legacy draft flow.
    setState(() => _booking = true);
    try {
      final repo = ref.read(gamingBookingRepositoryProvider);
      final idem = DateTime.now().microsecondsSinceEpoch.toString();
      final result = await repo.createBookingV2(
        parlorId: widget.parlourId,
        stationType: _stationType,
        date: _selectedDate,
        startTime: _selectedSlot!.startTime,
        durationHours: _durationHours,
        units: _units,
        paymentMode: 'pay_at_parlor',
        idempotencyKey: idem,
      );
      final booking = result['booking'] as Map<String, dynamic>?;
      final id = booking?['id']?.toString();
      if (id != null && mounted) {
        context.push(
          '/booking/status/$id',
          extra: {'mockMode': result['mock_mode'] == true},
        );
        return;
      }
    } catch (_) {
      // Legacy path
      ref.read(gamingBookingDraftProvider.notifier).state = GamingBookingDraft(
        parlourId: widget.parlourId,
        parlourName: parlourName,
        parlourImage: image,
        slot: _selectedSlot,
      );
      if (mounted) context.push('/booking/confirm');
    } finally {
      if (mounted) setState(() => _booking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(parlourDetailProvider(widget.parlourId));
    final slotsAsync = ref.watch(
      gamingSlotsProvider(
        GamingSlotsParams(
          parlourId: widget.parlourId,
          date: _selectedDate,
        ),
      ),
    );

    return detailAsync.when(
      loading: () => const Scaffold(
        body: Center(
          child: CircularProgressIndicator(color: BookingColors.oyoRed),
        ),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: const Text('Parlour')),
        body: Center(child: Text('Error: $e')),
      ),
      data: (detail) {
        final base = _selectedSlot?.pricePerHour ?? detail.startingPrice ?? 0;
        final price = base * _durationHours * _units;
        return Scaffold(
          body: NestedScrollView(
            headerSliverBuilder: (_, __) => [
              SliverAppBar(
                expandedHeight: 240,
                pinned: true,
                backgroundColor: BookingColors.oyoRed,
                foregroundColor: Colors.white,
                flexibleSpace: FlexibleSpaceBar(
                  background: detail.displayImage.isNotEmpty
                      ? GestureDetector(
                          onTap: () => context.push(
                            '/parlour/${widget.parlourId}/gallery',
                            extra: detail.images,
                          ),
                          child: CachedNetworkImage(
                            imageUrl: detail.displayImage,
                            fit: BoxFit.cover,
                          ),
                        )
                      : Container(color: BookingColors.oyoRed),
                ),
                actions: [
                  if (detail.images.length > 1)
                    TextButton(
                      onPressed: () => context.push(
                        '/parlour/${widget.parlourId}/gallery',
                        extra: detail.images,
                      ),
                      child: Text('${detail.images.length} photos'),
                    ),
                ],
              ),
            ],
            body: Column(
              children: [
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              detail.name,
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          if (detail.isVerified)
                            const Icon(Icons.verified, color: BookingColors.oyoRed),
                        ],
                      ),
                      const SizedBox(height: 8),
                      if (detail.rating != null)
                        InkWell(
                          onTap: () =>
                              context.push('/ratings/${widget.parlourId}'),
                          child: Row(
                            children: [
                              RatingStars(rating: detail.rating!, showValue: true),
                              const SizedBox(width: 8),
                              Text(
                                '${detail.reviewCount} reviews',
                                style: const TextStyle(
                                  color: BookingColors.oyoRed,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      if (detail.locationLine.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            const Icon(Icons.location_on_outlined, size: 16),
                            const SizedBox(width: 4),
                            Expanded(child: Text(detail.locationLine)),
                          ],
                        ),
                      ],
                      if (detail.description != null) ...[
                        const SizedBox(height: 12),
                        ReadMoreText(
                          detail.description!,
                          trimLines: 3,
                          style: const TextStyle(color: BookingColors.textSecondary),
                          moreStyle: const TextStyle(
                            color: BookingColors.oyoRed,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                      if (detail.offers.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        const Text(
                          'Offers',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          height: 180,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: detail.offers.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 12),
                            itemBuilder: (_, i) =>
                                OfferCard(parlourOffer: detail.offers[i], width: 220),
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      TabBar(
                        controller: _tabs,
                        labelColor: BookingColors.oyoRed,
                        tabs: const [
                          Tab(text: 'Slots'),
                          Tab(text: 'Amenities'),
                          Tab(text: 'Contact'),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_tabs.index == 0) ...[
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('Select date'),
                          subtitle: Text(
                            DateFormat('EEE, dd MMM').format(_selectedDate),
                          ),
                          trailing: const Icon(Icons.calendar_today),
                          onTap: _pickDate,
                        ),
                        const SizedBox(height: 8),
                        Semantics(
                          label: 'station_type_selector',
                          child: Wrap(
                            spacing: 8,
                            children: ['PC', 'PS5', 'VR', 'XBOX', 'POOL']
                                .map(
                                  (t) => ChoiceChip(
                                    label: Text(t),
                                    selected: _stationType == t,
                                    onSelected: (_) => setState(() {
                                      _stationType = t;
                                      _selectedSlot = null;
                                    }),
                                  ),
                                )
                                .toList(),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            const Text('Duration'),
                            const Spacer(),
                            for (final h in [1, 2, 3])
                              Padding(
                                padding: const EdgeInsets.only(left: 6),
                                child: ChoiceChip(
                                  label: Text('${h}h'),
                                  selected: _durationHours == h,
                                  onSelected: (_) =>
                                      setState(() => _durationHours = h),
                                ),
                              ),
                          ],
                        ),
                        Row(
                          children: [
                            const Text('Units'),
                            const Spacer(),
                            IconButton(
                              onPressed: _units > 1
                                  ? () => setState(() => _units--)
                                  : null,
                              icon: const Icon(Icons.remove_circle_outline),
                            ),
                            Text('$_units'),
                            IconButton(
                              onPressed: _units < 4
                                  ? () => setState(() => _units++)
                                  : null,
                              icon: const Icon(Icons.add_circle_outline),
                            ),
                          ],
                        ),
                        slotsAsync.when(
                          loading: () => const _SlotsShimmer(),
                          error: (_, __) => const Text('No slots available'),
                          data: (slots) => slots.isEmpty
                              ? const Text('No slots for this date')
                              : Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: slots.map((slot) {
                                    final selected =
                                        _selectedSlot?.id == slot.id;
                                    return Semantics(
                                      button: true,
                                      label: 'slot_${slot.startTime}',
                                      child: ChoiceChip(
                                        label: Text(
                                          '${slot.startTime} · ${formatInr(slot.pricePerHour)}/hr',
                                        ),
                                        selected: selected,
                                        selectedColor: BookingColors.oyoRed
                                            .withOpacity(0.15),
                                        onSelected: slot.isAvailable
                                            ? (_) => setState(
                                                  () => _selectedSlot = slot,
                                                )
                                            : null,
                                      ),
                                    );
                                  }).toList(),
                                ),
                        ),
                      ] else if (_tabs.index == 1) ...[
                        if (detail.amenities.isNotEmpty)
                          Wrap(
                            spacing: 8,
                            children: detail.amenities
                                .map(
                                  (a) => Chip(
                                    label: Text(a),
                                    backgroundColor: BookingColors.background,
                                  ),
                                )
                                .toList(),
                          )
                        else
                          const Text('No amenities listed'),
                        const SizedBox(height: 16),
                        CategoryRatingsSection(ratings: detail.categoryRatings),
                      ] else ...[
                        if (detail.phone != null)
                          ListTile(
                            leading: const Icon(Icons.phone),
                            title: Text(detail.phone!),
                            onTap: () => launchUrl(Uri.parse('tel:${detail.phone}')),
                          ),
                        if (detail.website != null)
                          ListTile(
                            leading: const Icon(Icons.language),
                            title: Text(detail.website!),
                            onTap: () => launchUrl(Uri.parse(detail.website!)),
                          ),
                      ],
                    ],
                  ),
                ),
                BookingBottomCta(
                  price: price,
                  originalPrice: _selectedSlot?.originalPrice,
                  subtitle: _selectedSlot != null
                      ? '$_stationType · ${_selectedSlot!.startTime} · ${_durationHours}h · x$_units'
                      : 'Select a slot',
                  enabled: _selectedSlot != null && !_booking,
                  onPressed: () => _bookNow(detail.name, detail.displayImage),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _SlotsShimmer extends StatelessWidget {
  const _SlotsShimmer();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Wrap(
        spacing: 8,
        children: List.generate(
          4,
          (_) => Container(
            width: 120,
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