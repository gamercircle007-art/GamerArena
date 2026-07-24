import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/home/providers/parlor_search_provider.dart';

class ParlorFilterChips extends StatelessWidget {
  const ParlorFilterChips({
    super.key,
    required this.filters,
    required this.onChanged,
  });

  final ParlorSearchFilters filters;
  final ValueChanged<ParlorSearchFilters> onChanged;

  static const _radiusLabels = {
    5000: '5 km',
    10000: '10 km',
    25000: '25 km',
    50000: '50 km',
  };

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          ...kRadiusOptions.map((radius) {
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text(_radiusLabels[radius] ?? '$radius m'),
                selected: filters.radiusMeters == radius,
                selectedColor: AppColors.primaryLight,
                checkmarkColor: AppColors.primary,
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: filters.radiusMeters == radius
                      ? AppColors.primary
                      : const Color(0xFF4B5563),
                ),
                onSelected: (_) =>
                    onChanged(filters.copyWith(radiusMeters: radius)),
              ),
            );
          }),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: const Text('4+ Rating'),
              selected: filters.minRating == 4,
              selectedColor: AppColors.primaryLight,
              checkmarkColor: AppColors.primary,
              onSelected: (selected) => onChanged(
                filters.copyWith(
                  minRating: selected ? 4 : null,
                  clearMinRating: !selected,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: const Text('Open Now'),
              selected: filters.openNow,
              selectedColor: AppColors.primaryLight,
              checkmarkColor: AppColors.primary,
              onSelected: (selected) =>
                  onChanged(filters.copyWith(openNow: selected)),
            ),
          ),
          FilterChip(
            label: const Text('BGMI'),
            selected: filters.gameType == 'BGMI',
            selectedColor: AppColors.primaryLight,
            checkmarkColor: AppColors.primary,
            onSelected: (selected) => onChanged(
              filters.copyWith(
                gameType: selected ? 'BGMI' : null,
                clearGameType: !selected,
              ),
            ),
          ),
          const SizedBox(width: 8),
          FilterChip(
            label: const Text('Valorant'),
            selected: filters.gameType == 'Valorant',
            selectedColor: AppColors.primaryLight,
            checkmarkColor: AppColors.primary,
            onSelected: (selected) => onChanged(
              filters.copyWith(
                gameType: selected ? 'Valorant' : null,
                clearGameType: !selected,
              ),
            ),
          ),
        ],
      ),
    );
  }
}