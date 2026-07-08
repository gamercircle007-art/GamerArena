import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/shared/models/home_data.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

class QuickPicksSection extends StatelessWidget {
  const QuickPicksSection({
    super.key,
    required this.parlours,
    required this.selectedFilter,
    required this.isLoading,
    required this.onFilterChanged,
    required this.onParlourTap,
  });

  final List<ParlourSearchItem> parlours;
  final HomeQuickPickFilter selectedFilter;
  final bool isLoading;
  final ValueChanged<HomeQuickPickFilter> onFilterChanged;
  final ValueChanged<ParlourSearchItem> onParlourTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: Text(
            'Quick picks for you',
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
            children: HomeQuickPickFilter.values.map((filter) {
              final selected = filter == selectedFilter;
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
                  onSelected: (_) => onFilterChanged(filter),
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
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
            child: Text(
              _emptyMessage(selectedFilter),
              style: const TextStyle(
                color: OnboardingColors.textSecondary,
                fontSize: 14,
              ),
            ),
          )
        else
          ...parlours.map(
            (item) => _ParlourPickCard(
              item: item,
              onTap: () => onParlourTap(item),
            ),
          ),
      ],
    );
  }

  String _emptyMessage(HomeQuickPickFilter filter) {
    return switch (filter) {
      HomeQuickPickFilter.recommended =>
        'No gaming parlours found here yet. Try another city or Nearby.',
      HomeQuickPickFilter.pastStays =>
        'No past stays yet. Book a gaming session to see it here.',
      HomeQuickPickFilter.recentlyViewed =>
        'No recently viewed parlours. Open a parlour detail to track it here.',
    };
  }
}

class _ParlourPickCard extends StatelessWidget {
  const _ParlourPickCard({
    required this.item,
    required this.onTap,
  });

  final ParlourSearchItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
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
                      Text(
                        item.name,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: OnboardingColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item.locationLine.isNotEmpty
                            ? item.locationLine
                            : item.distanceLabel.isNotEmpty
                                ? item.distanceLabel
                                : 'Gaming parlour',
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