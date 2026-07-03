import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/core/utils/currency_formatter.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';
import 'package:gamer_circle/shared/widgets/rating_stars.dart';
import 'package:shimmer/shimmer.dart';

class ParlourListCard extends StatelessWidget {
  const ParlourListCard({
    super.key,
    required this.parlour,
    this.onTap,
    this.compact = false,
  });

  final ParlourSearchItem parlour;
  final VoidCallback? onTap;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 0, 16, compact ? 10 : 14),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: BookingColors.border),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _Image(url: parlour.imageUrl, compact: compact),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                parlour.name,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                  color: BookingColors.textPrimary,
                                ),
                              ),
                            ),
                            if (parlour.isVerified)
                              const Icon(
                                Icons.verified,
                                size: 16,
                                color: BookingColors.oyoRed,
                              ),
                          ],
                        ),
                        if (parlour.locationLine.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            parlour.locationLine,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 12,
                              color: BookingColors.textSecondary,
                            ),
                          ),
                        ],
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            if (parlour.rating != null) ...[
                              RatingStars(rating: parlour.rating!, size: 14),
                              const SizedBox(width: 4),
                              Text(
                                parlour.rating!.toStringAsFixed(1),
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              if (parlour.reviewCount > 0)
                                Text(
                                  ' (${parlour.reviewCount})',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: BookingColors.textSecondary,
                                  ),
                                ),
                              const SizedBox(width: 8),
                            ],
                            if (parlour.distanceLabel.isNotEmpty)
                              Text(
                                parlour.distanceLabel,
                                style: const TextStyle(
                                  fontSize: 11,
                                  color: BookingColors.textSecondary,
                                ),
                              ),
                          ],
                        ),
                        if (parlour.offerText != null) ...[
                          const SizedBox(height: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: BookingColors.oyoRed.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              parlour.offerText!,
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: BookingColors.oyoRed,
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            if (parlour.startingPrice != null)
                              Text(
                                formatInr(parlour.startingPrice!),
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                  color: BookingColors.textPrimary,
                                ),
                              ),
                            if (parlour.originalPrice != null &&
                                parlour.originalPrice! >
                                    (parlour.startingPrice ?? 0)) ...[
                              const SizedBox(width: 6),
                              Text(
                                formatInr(parlour.originalPrice!),
                                style: const TextStyle(
                                  fontSize: 12,
                                  decoration: TextDecoration.lineThrough,
                                  color: BookingColors.textSecondary,
                                ),
                              ),
                            ],
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: parlour.isOpen
                                    ? BookingColors.confirmedGreen
                                        .withOpacity(0.12)
                                    : BookingColors.cancelledOrange
                                        .withOpacity(0.12),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                parlour.isOpen ? 'Open' : 'Closed',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: parlour.isOpen
                                      ? BookingColors.confirmedGreen
                                      : BookingColors.cancelledOrange,
                                ),
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

class _Image extends StatelessWidget {
  const _Image({this.url, required this.compact});

  final String? url;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final size = compact ? 90.0 : 110.0;
    return ClipRRect(
      borderRadius: const BorderRadius.horizontal(left: Radius.circular(11)),
      child: SizedBox(
        width: size,
        height: size,
        child: url != null && url!.isNotEmpty
            ? CachedNetworkImage(
                imageUrl: url!,
                fit: BoxFit.cover,
                placeholder: (_, __) => const _ShimmerBox(),
                errorWidget: (_, __, ___) => const _Placeholder(),
              )
            : const _Placeholder(),
      ),
    );
  }
}

class _Placeholder extends StatelessWidget {
  const _Placeholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: BookingColors.background,
      child: const Icon(
        Icons.videogame_asset_outlined,
        color: BookingColors.textSecondary,
      ),
    );
  }
}

class _ShimmerBox extends StatelessWidget {
  const _ShimmerBox();

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Container(color: Colors.white),
    );
  }
}

class ParlourListCardShimmer extends StatelessWidget {
  const ParlourListCardShimmer({super.key});

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey.shade300,
      highlightColor: Colors.grey.shade100,
      child: Container(
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 14),
        height: 110,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}