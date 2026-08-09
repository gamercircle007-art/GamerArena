import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/parlors/providers/parlor_search_provider.dart';
import 'package:gamer_circle/shared/widgets/booking_bottom_cta.dart';
import 'package:gamer_circle/shared/widgets/category_rating_bar.dart';
import 'package:gamer_circle/shared/widgets/offer_card.dart';
import 'package:gamer_circle/shared/widgets/rating_stars.dart';
import 'package:readmore/readmore.dart';
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

  void _openBookFlow(String parlourName, String? image) {
    context.push(
      '/parlour/${widget.parlourId}/book',
      extra: {'name': parlourName, 'image': image},
    );
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(parlourDetailProvider(widget.parlourId));

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
        final price = detail.startingPrice ?? 0;
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
                          Tab(text: 'Overview'),
                          Tab(text: 'Amenities'),
                          Tab(text: 'Contact'),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_tabs.index == 0) ...[
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: BookingColors.border),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Book a session',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 6),
                              const Text(
                                'Choose your time first — we hold the slot for 8 minutes while you pay.',
                                style: TextStyle(color: BookingColors.textSecondary),
                              ),
                              const SizedBox(height: 12),
                              FilledButton.icon(
                                style: FilledButton.styleFrom(
                                  backgroundColor: BookingColors.oyoRed,
                                ),
                                onPressed: () =>
                                    _openBookFlow(detail.name, detail.displayImage),
                                icon: const Icon(Icons.schedule),
                                label: const Text('Select time'),
                              ),
                            ],
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
                  subtitle: 'Time-first booking · 8 min hold',
                  enabled: !_booking,
                  label: 'Book Now',
                  onPressed: () =>
                      _openBookFlow(detail.name, detail.displayImage),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}