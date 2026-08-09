import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/amenities.dart';
import 'package:gamer_circle/features/discovery/presentation/filter_state.dart';

final discoveryFilterProvider =
    StateProvider<FilterState>((ref) => const FilterState());

class FilterSheet extends ConsumerWidget {
  const FilterSheet({super.key});

  static const _distances = [2000, 5000, 10000, 25000];
  static const _ratings = [3.5, 4.0, 4.5];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final f = ref.watch(discoveryFilterProvider);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Filters', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            Text('Distance', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: _distances.map((m) {
                final selected = f.distanceM == m;
                return ChoiceChip(
                  label: Text(m >= 1000 ? '${m ~/ 1000} km' : '$m m'),
                  selected: selected,
                  onSelected: (_) => ref.read(discoveryFilterProvider.notifier).state =
                      f.copyWith(distanceM: m, clearEtag: true),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            Text('Rating', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: _ratings.map((r) {
                final selected = f.minRating == r;
                return ChoiceChip(
                  label: Text('$r+'),
                  selected: selected,
                  onSelected: (on) => ref.read(discoveryFilterProvider.notifier).state =
                      f.copyWith(
                        minRating: on ? r : null,
                        clearMinRating: !on,
                        clearEtag: true,
                      ),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Available now'),
              value: f.availableNow,
              activeThumbColor: AppColors.primary,
              onChanged: (v) => ref.read(discoveryFilterProvider.notifier).state =
                  f.copyWith(availableNow: v, clearEtag: true),
            ),
            const SizedBox(height: 8),
            Text('Amenities', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: Amenity.labels.entries.map((e) {
                final on = f.amenitiesMask & e.key != 0;
                return FilterChip(
                  label: Text(e.value),
                  selected: on,
                  onSelected: (sel) {
                    final mask = sel
                        ? (f.amenitiesMask | e.key)
                        : (f.amenitiesMask & ~e.key);
                    ref.read(discoveryFilterProvider.notifier).state =
                        f.copyWith(amenitiesMask: mask, clearEtag: true);
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Apply'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
