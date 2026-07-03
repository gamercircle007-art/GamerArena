import 'package:flutter/material.dart';
import 'package:gamer_circle/features/home/domain/models/destination_city.dart';

class LocationPermissionBanner extends StatelessWidget {
  const LocationPermissionBanner({
    super.key,
    required this.onEnableLocation,
    required this.onCitySelected,
  });

  final VoidCallback onEnableLocation;
  final ValueChanged<String> onCitySelected;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF7ED),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFFED7AA)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.location_off_rounded, color: Color(0xFFEA580C)),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Location access needed',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: Color(0xFF9A3412),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Enable location to find gaming parlors near you, or pick a city below.',
              style: TextStyle(fontSize: 13, color: Color(0xFF9A3412)),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: onEnableLocation,
              icon: const Icon(Icons.my_location, size: 18),
              label: const Text('Enable Location'),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFEA580C),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Or choose a city',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Color(0xFF9A3412),
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: kExploreCities
                  .where((c) => !c.isNearMe)
                  .map(
                    (city) => ActionChip(
                      label: Text(city.name),
                      onPressed: () => onCitySelected(city.name),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}