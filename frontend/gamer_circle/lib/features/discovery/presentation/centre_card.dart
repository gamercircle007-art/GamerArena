import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/amenities.dart';
import 'package:gamer_circle/features/discovery/data/centre_summary.dart';

/// Fixed height for ListView.builder itemExtent (no layout passes while scrolling).
const double kCentreCardExtent = 112;

class CentreCard extends StatelessWidget {
  const CentreCard({
    super.key,
    required this.centre,
    this.onTap,
  });

  final CentreSummary centre;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final dpr = MediaQuery.devicePixelRatioOf(context);
    final memW = (96 * dpr).round();
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: SizedBox(
          height: kCentreCardExtent,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: SizedBox(
                    width: 88,
                    height: 88,
                    child: centre.thumbUrl != null
                        ? CachedNetworkImage(
                            imageUrl: centre.thumbUrl!,
                            fit: BoxFit.cover,
                            memCacheWidth: memW,
                            placeholder: (_, __) => const ColoredBox(
                              color: Color(0xFFE5E7EB),
                            ),
                            errorWidget: (_, __, ___) => const ColoredBox(
                              color: Color(0xFFE5E7EB),
                              child: Icon(Icons.sports_esports),
                            ),
                          )
                        : const ColoredBox(
                            color: Color(0xFFE5E7EB),
                            child: Icon(Icons.sports_esports),
                          ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        centre.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.star, size: 14, color: Color(0xFFF59E0B)),
                          const SizedBox(width: 2),
                          Text(
                            centre.ratingScore.toStringAsFixed(1),
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                          Text(
                            ' (${centre.reviewCount})',
                            style: const TextStyle(fontSize: 12, color: Color(0xFF6B7280)),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            centre.distanceLabel,
                            style: const TextStyle(fontSize: 12, color: Color(0xFF6B7280)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          if (centre.availableNow)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFDCFCE7),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                'Available',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Color(0xFF166534),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          if (centre.priceLabel != null) ...[
                            const SizedBox(width: 8),
                            Text(
                              centre.priceLabel!,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppColors.primary,
                              ),
                            ),
                          ],
                          if (centre.amenitiesMask != 0) ...[
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                Amenity.namesFromMask(centre.amenitiesMask).take(2).join(' · '),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 11, color: Color(0xFF6B7280)),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
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
