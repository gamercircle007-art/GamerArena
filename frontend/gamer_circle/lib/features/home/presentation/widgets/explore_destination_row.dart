import 'package:flutter/material.dart';
import 'package:gamer_circle/features/home/domain/models/destination_city.dart';

class ExploreDestinationRow extends StatelessWidget {
  final List<DestinationCity> cities;
  final ValueChanged<DestinationCity> onCityTap;

  const ExploreDestinationRow({
    super.key,
    required this.cities,
    required this.onCityTap,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 118,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: cities.length,
        separatorBuilder: (_, __) => const SizedBox(width: 14),
        itemBuilder: (context, index) {
          final city = cities[index];
          return _DestinationChip(city: city, onTap: () => onCityTap(city));
        },
      ),
    );
  }
}

class _DestinationChip extends StatelessWidget {
  final DestinationCity city;
  final VoidCallback onTap;

  const _DestinationChip({required this.city, required this.onTap});

  static const _cityGradients = [
    [Color(0xFF667EEA), Color(0xFF764BA2)],
    [Color(0xFFf093fb), Color(0xFFf5576c)],
    [Color(0xFF4facfe), Color(0xFF00f2fe)],
    [Color(0xFF43e97b), Color(0xFF38f9d7)],
    [Color(0xFFfa709a), Color(0xFFfee140)],
    [Color(0xFF30cfd0), Color(0xFF330867)],
    [Color(0xFFa18cd1), Color(0xFFfbc2eb)],
  ];

  @override
  Widget build(BuildContext context) {
    final gradient = city.isNearMe
        ? null
        : _cityGradients[city.name.hashCode.abs() % _cityGradients.length];

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
                borderRadius: BorderRadius.circular(12),
                color: city.isNearMe ? const Color(0xFF3B82F6) : null,
                gradient: city.isNearMe
                    ? null
                    : LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: gradient!,
                      ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: city.isNearMe
                  ? const Icon(
                      Icons.near_me_rounded,
                      color: Colors.white,
                      size: 28,
                    )
                  : Center(
                      child: Text(
                        city.name.substring(0, 1),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
            ),
            const SizedBox(height: 8),
            Text(
              city.name,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Color(0xFF1A1A2E),
              ),
            ),
          ],
        ),
      ),
    );
  }
}