import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/home/providers/home_filters_provider.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

class NearbyParlorsSection extends StatelessWidget {
  const NearbyParlorsSection({
    super.key,
    required this.parlours,
    required this.selectedRadius,
    required this.isLoading,
    required this.onRadiusChanged,
    required this.onParlourTap,
  });

  final List<ParlourSearchItem> parlours;
  final HomeRadiusFilter selectedRadius;
  final bool isLoading;
  final ValueChanged<HomeRadiusFilter> onRadiusChanged;
  final ValueChanged<ParlourSearchItem> onParlourTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, 12),
          child: Text(
            'Gaming parlors near you',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: OnboardingColors.textPrimary,
            ),
          ),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: HomeRadiusFilter.values.map((filter) {
              final selected = filter == selectedRadius;
              return Padding(
                padding: const EdgeInsets.only(right: 10),
                child: ChoiceChip(
                  label: Text(filter.label),
                  selected: selected,
                  showCheckmark: false,
                  labelStyle: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: selected
                        ? OnboardingColors.textPrimary
                        : OnboardingColors.textSecondary,
                  ),
                  side: BorderSide(
                    color: selected
                        ? OnboardingColors.textPrimary
                        : const Color(0xFFD1D5DB),
                    width: selected ? 1.5 : 1,
                  ),
                  backgroundColor: Colors.white,
                  selectedColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
                  onSelected: (_) => onRadiusChanged(filter),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 16),
        if (isLoading && parlours.isEmpty)
          const Padding(
            padding: EdgeInsets.all(32),
            child: Center(
              child: CircularProgressIndicator(color: OnboardingColors.primary),
            ),
          )
        else if (parlours.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 24),
            child: Text(
              'No gaming parlors in this range. Try a wider distance filter or switch to Nearby.',
              style: TextStyle(
                color: OnboardingColors.textSecondary,
                fontSize: 14,
              ),
            ),
          )
        else
          ...parlours.map(
            (item) => _ParlorCard(
              item: item,
              onTap: () => onParlourTap(item),
            ),
          ),
      ],
    );
  }
}

class _ParlorCard extends StatelessWidget {
  const _ParlorCard({
    required this.item,
    required this.onTap,
  });

  final ParlourSearchItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final subtitle = item.distanceLabel.isNotEmpty
        ? item.distanceLabel
        : item.locationLine.isNotEmpty
            ? item.locationLine
            : 'Gaming parlor';

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        elevation: 1,
        shadowColor: Colors.black.withOpacity(0.06),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(14),
          child: Row(
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.horizontal(
                  left: Radius.circular(14),
                ),
                child: item.imageUrl != null
                    ? CachedNetworkImage(
                        imageUrl: item.imageUrl!,
                        width: 110,
                        height: 96,
                        fit: BoxFit.cover,
                        errorWidget: (_, __, ___) => _imageFallback(),
                      )
                    : _imageFallback(),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              item.name,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 15,
                                color: OnboardingColors.textPrimary,
                              ),
                            ),
                          ),
                          if (item.isVerified)
                            const Padding(
                              padding: EdgeInsets.only(left: 4),
                              child: Icon(
                                Icons.verified,
                                size: 16,
                                color: OnboardingColors.primary,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 12,
                          color: OnboardingColors.textSecondary,
                        ),
                      ),
                      if (item.startingPrice != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          'From ₹${item.startingPrice!.round()}/hr',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: OnboardingColors.primary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              if (item.rating != null)
                Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A7A4A),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '${item.rating!.toStringAsFixed(1)} ★',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _imageFallback() {
    return Container(
      width: 110,
      height: 96,
      color: AppColors.divider,
      child: const Icon(Icons.sports_esports, color: OnboardingColors.textSecondary),
    );
  }
}