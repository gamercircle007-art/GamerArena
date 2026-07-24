import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/home/providers/home_provider.dart';
import 'package:gamer_circle/features/home/providers/selected_location_provider.dart';

Future<void> showLocationPickerSheet(BuildContext context, WidgetRef ref) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (ctx) => const _LocationPickerSheet(),
  );
}

class _LocationPickerSheet extends ConsumerStatefulWidget {
  const _LocationPickerSheet();

  @override
  ConsumerState<_LocationPickerSheet> createState() =>
      _LocationPickerSheetState();
}

class _LocationPickerSheetState extends ConsumerState<_LocationPickerSheet> {
  final _searchController = TextEditingController();
  bool _isFetchingGps = false;
  bool _isSearching = false;
  String? _error;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _onUseCurrentLocation() async {
    setState(() {
      _isFetchingGps = true;
      _error = null;
    });

    final error =
        await ref.read(selectedLocationProvider.notifier).useCurrentLocation();

    if (!mounted) return;

    if (error == null) {
      await ref.read(homeProvider.notifier).refresh();
      Navigator.pop(context);
    } else {
      setState(() {
        _isFetchingGps = false;
        _error = error;
      });
    }
  }

  Future<void> _onSearch() async {
    setState(() {
      _isSearching = true;
      _error = null;
    });

    final error = await ref
        .read(selectedLocationProvider.notifier)
        .setManualLocation(_searchController.text);

    if (!mounted) return;

    if (error == null) {
      await ref.read(homeProvider.notifier).refresh();
      Navigator.pop(context);
    } else {
      setState(() {
        _isSearching = false;
        _error = error;
      });
    }
  }

  Future<void> _onSelectPreset(SelectedLocation preset) async {
    setState(() => _error = null);
    await ref.read(selectedLocationProvider.notifier).selectPreset(preset);
    await ref.read(homeProvider.notifier).refresh();
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final selected = ref.watch(selectedLocationProvider).valueOrNull;

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 12,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: OnboardingColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Select your location',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: OnboardingColors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            selected?.label ?? 'Choose where you want to explore',
            style: const TextStyle(
              fontSize: 13,
              color: OnboardingColors.textSecondary,
            ),
          ),
          const SizedBox(height: 20),
          Material(
            color: OnboardingColors.permissionIconBg,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              onTap: _isFetchingGps ? null : _onUseCurrentLocation,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: OnboardingColors.primary.withOpacity(0.12),
                        shape: BoxShape.circle,
                      ),
                      child: _isFetchingGps
                          ? const Padding(
                              padding: EdgeInsets.all(10),
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: OnboardingColors.primary,
                              ),
                            )
                          : const Icon(
                              Icons.my_location,
                              color: OnboardingColors.primary,
                            ),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Use current location',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 15,
                              color: OnboardingColors.textPrimary,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Detect automatically using GPS',
                            style: TextStyle(
                              fontSize: 12,
                              color: OnboardingColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.chevron_right,
                      color: OnboardingColors.textSecondary,
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _searchController,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _onSearch(),
            decoration: InputDecoration(
              hintText: 'Search city, area or landmark',
              prefixIcon: const Icon(Icons.search, color: OnboardingColors.textSecondary),
              suffixIcon: _isSearching
                  ? const Padding(
                      padding: EdgeInsets.all(12),
                      child: SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : IconButton(
                      icon: const Icon(Icons.arrow_forward),
                      color: OnboardingColors.primary,
                      onPressed: _onSearch,
                    ),
              filled: true,
              fillColor: AppColors.backgroundLight,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(
              _error!,
              style: const TextStyle(
                color: OnboardingColors.payBillRed,
                fontSize: 13,
              ),
            ),
          ],
          const SizedBox(height: 20),
          const Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Popular areas',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: OnboardingColors.textPrimary,
              ),
            ),
          ),
          const SizedBox(height: 8),
          ...popularLocations.map(
            (loc) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(
                Icons.location_on_outlined,
                color: OnboardingColors.primary,
                size: 22,
              ),
              title: Text(
                loc.label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              trailing: selected?.label == loc.label
                  ? const Icon(Icons.check, color: OnboardingColors.primary, size: 20)
                  : null,
              onTap: () => _onSelectPreset(loc),
            ),
          ),
        ],
      ),
    );
  }
}