import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/home/providers/home_filters_provider.dart';
import 'package:gamer_circle/shared/models/home_data.dart';

class CityFilterRail extends StatelessWidget {
  const CityFilterRail({
    super.key,
    required this.cities,
    required this.selectedCity,
    required this.onNearbyTap,
    required this.onCityTap,
  });

  final List<HomeCityItem> cities;
  final HomeCityItem? selectedCity;
  final VoidCallback onNearbyTap;
  final ValueChanged<HomeCityItem> onCityTap;

  @override
  Widget build(BuildContext context) {
    final items = cities.isNotEmpty ? cities : fallbackHomeCities;

    return SizedBox(
      height: 108,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: items.length + 1,
        separatorBuilder: (_, __) => const SizedBox(width: 14),
        itemBuilder: (context, index) {
          if (index == 0) {
            return _CityChip(
              label: 'Nearby',
              selected: selectedCity == null,
              isNearby: true,
              onTap: onNearbyTap,
            );
          }
          final city = items[index - 1];
          return _CityChip(
            label: city.name,
            imageUrl: city.imageUrl,
            selected: selectedCity?.name.toLowerCase() == city.name.toLowerCase(),
            onTap: () => onCityTap(city),
          );
        },
      ),
    );
  }
}

class _CityChip extends StatelessWidget {
  const _CityChip({
    required this.label,
    required this.selected,
    required this.onTap,
    this.imageUrl,
    this.isNearby = false,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final String? imageUrl;
  final bool isNearby;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 72,
        child: Column(
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: selected ? OnboardingColors.textPrimary : Colors.transparent,
                  width: 2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: ClipOval(
                child: isNearby
                    ? ColoredBox(
                        color: OnboardingColors.textPrimary,
                        child: Icon(
                          Icons.near_me_rounded,
                          color: Colors.white,
                          size: selected ? 26 : 24,
                        ),
                      )
                    : imageUrl != null
                        ? CachedNetworkImage(
                            imageUrl: imageUrl!,
                            fit: BoxFit.cover,
                            errorWidget: (_, __, ___) => _cityFallback(label),
                          )
                        : _cityFallback(label),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                color: OnboardingColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _cityFallback(String name) {
    return ColoredBox(
      color: AppColors.divider,
      child: Center(
        child: Text(
          name.isNotEmpty ? name[0] : '?',
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: OnboardingColors.textSecondary,
          ),
        ),
      ),
    );
  }
}