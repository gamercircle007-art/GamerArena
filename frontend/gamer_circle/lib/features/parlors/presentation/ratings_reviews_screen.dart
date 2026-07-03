import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/features/parlors/providers/parlor_search_provider.dart';
import 'package:gamer_circle/shared/widgets/category_rating_bar.dart';
import 'package:gamer_circle/shared/widgets/rating_stars.dart';
import 'package:intl/intl.dart';

class RatingsReviewsScreen extends ConsumerWidget {
  const RatingsReviewsScreen({super.key, required this.parlourId});

  final String parlourId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(parlourDetailProvider(parlourId));
    final reviewsAsync = ref.watch(parlourReviewsProvider(parlourId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ratings & Reviews'),
        backgroundColor: BookingColors.oyoRed,
        foregroundColor: Colors.white,
      ),
      body: detailAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: BookingColors.oyoRed),
        ),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (detail) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                Text(
                  detail.rating?.toStringAsFixed(1) ?? '-',
                  style: const TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (detail.rating != null)
                      RatingStars(rating: detail.rating!, size: 20),
                    Text(
                      '${detail.reviewCount} reviews',
                      style: const TextStyle(color: BookingColors.textSecondary),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            CategoryRatingsSection(ratings: detail.categoryRatings),
            const Divider(height: 32),
            reviewsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (_, __) => const Text('Could not load reviews'),
              data: (reviews) => reviews.isEmpty
                  ? const Text(
                      'No reviews yet',
                      style: TextStyle(color: BookingColors.textSecondary),
                    )
                  : Column(
                      children: reviews
                          .map(
                            (r) => Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        CircleAvatar(
                                          child: Text(
                                            r.userName.isNotEmpty
                                                ? r.userName[0].toUpperCase()
                                                : '?',
                                          ),
                                        ),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                r.userName,
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w600,
                                                ),
                                              ),
                                              Text(
                                                DateFormat('dd MMM yyyy')
                                                    .format(r.createdAt),
                                                style: const TextStyle(
                                                  fontSize: 12,
                                                  color: BookingColors
                                                      .textSecondary,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                        RatingStars(rating: r.rating, size: 14),
                                      ],
                                    ),
                                    if (r.comment.isNotEmpty) ...[
                                      const SizedBox(height: 8),
                                      Text(r.comment),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}