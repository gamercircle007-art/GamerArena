import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/features/location/data/datasources/location_local_datasource.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SelectedLocation {
  const SelectedLocation({
    required this.label,
    required this.latitude,
    required this.longitude,
    this.isGpsBased = false,
  });

  final String label;
  final double latitude;
  final double longitude;
  final bool isGpsBased;

  static const defaultLocation = SelectedLocation(
    label: 'Khora Colony, Ghaziabad',
    latitude: 28.6692,
    longitude: 77.4538,
  );
}

final selectedLocationProvider =
    AsyncNotifierProvider<SelectedLocationNotifier, SelectedLocation>(
  SelectedLocationNotifier.new,
);

class SelectedLocationNotifier extends AsyncNotifier<SelectedLocation> {
  static const _labelKey = 'selected_location_label';
  static const _latKey = 'selected_location_lat';
  static const _lngKey = 'selected_location_lng';
  static const _isGpsKey = 'selected_location_is_gps';

  void _schedulePositionSync(double lat, double lng) {
    Future.microtask(() {
      ref.read(currentPositionProvider.notifier).setManualPosition(lat, lng);
    });
  }

  @override
  Future<SelectedLocation> build() async {
    final prefs = getIt<SharedPreferences>();
    final label = prefs.getString(_labelKey);
    final lat = prefs.getDouble(_latKey);
    final lng = prefs.getDouble(_lngKey);

    if (label != null && lat != null && lng != null) {
      _schedulePositionSync(lat, lng);
      return SelectedLocation(
        label: label,
        latitude: lat,
        longitude: lng,
        isGpsBased: prefs.getBool(_isGpsKey) ?? false,
      );
    }

    final cached = await getIt<LocationLocalDataSource>().getLocalLocation();
    if (cached != null) {
      final city = cached['city'] as String?;
      final lat = cached['latitude'] as double;
      final lng = cached['longitude'] as double;
      _schedulePositionSync(lat, lng);
      return SelectedLocation(
        label: city ?? 'Around you',
        latitude: lat,
        longitude: lng,
        isGpsBased: true,
      );
    }

    const fallback = SelectedLocation.defaultLocation;
    _schedulePositionSync(fallback.latitude, fallback.longitude);
    return fallback;
  }

  Future<void> _persist(SelectedLocation location) async {
    final prefs = getIt<SharedPreferences>();
    await prefs.setString(_labelKey, location.label);
    await prefs.setDouble(_latKey, location.latitude);
    await prefs.setDouble(_lngKey, location.longitude);
    await prefs.setBool(_isGpsKey, location.isGpsBased);

    await getIt<LocationLocalDataSource>().saveLocalLocation(
      latitude: location.latitude,
      longitude: location.longitude,
      city: location.label,
    );

    _schedulePositionSync(location.latitude, location.longitude);
    state = AsyncData(location);
  }

  Future<String?> useCurrentLocation() async {
    state = const AsyncLoading();

    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        state = AsyncData(state.valueOrNull ?? SelectedLocation.defaultLocation);
        return 'Location services are disabled. Enable GPS in settings.';
      }

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        state = AsyncData(state.valueOrNull ?? SelectedLocation.defaultLocation);
        return 'Location permission denied. Enable it in app settings.';
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 15),
        ),
      );

      String label = 'Around you';
      try {
        final placemarks = await placemarkFromCoordinates(
          position.latitude,
          position.longitude,
        );
        if (placemarks.isNotEmpty) {
          final place = placemarks.first;
          final locality = place.locality?.trim();
          final subAdmin = place.subAdministrativeArea?.trim();
          final parts = [locality, subAdmin]
              .whereType<String>()
              .where((e) => e.isNotEmpty)
              .toSet()
              .toList();
          if (parts.isNotEmpty) {
            label = parts.join(', ');
          }
        }
      } catch (_) {}

      final location = SelectedLocation(
        label: label,
        latitude: position.latitude,
        longitude: position.longitude,
        isGpsBased: true,
      );
      await _persist(location);
      return null;
    } catch (e) {
      state = AsyncData(state.valueOrNull ?? SelectedLocation.defaultLocation);
      return 'Could not fetch current location. Try again.';
    }
  }

  Future<String?> setManualLocation(String query) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return 'Enter a city or area name';

    state = const AsyncLoading();
    try {
      final locations = await locationFromAddress('$trimmed, India');
      if (locations.isEmpty) {
        state = AsyncData(state.valueOrNull ?? SelectedLocation.defaultLocation);
        return 'Could not find "$trimmed". Try another area.';
      }

      final loc = locations.first;
      final location = SelectedLocation(
        label: trimmed,
        latitude: loc.latitude,
        longitude: loc.longitude,
      );
      await _persist(location);
      return null;
    } catch (_) {
      state = AsyncData(state.valueOrNull ?? SelectedLocation.defaultLocation);
      return 'Could not find "$trimmed". Try another area.';
    }
  }

  Future<String?> selectPreset(SelectedLocation preset) async {
    await _persist(preset);
    return null;
  }
}

const popularLocations = [
  SelectedLocation(
    label: 'Khora Colony, Ghaziabad',
    latitude: 28.6692,
    longitude: 77.4538,
  ),
  SelectedLocation(
    label: 'Indirapuram, Ghaziabad',
    latitude: 28.6415,
    longitude: 77.3714,
  ),
  SelectedLocation(
    label: 'Vaishali, Ghaziabad',
    latitude: 28.6506,
    longitude: 77.3412,
  ),
  SelectedLocation(
    label: 'Noida Sector 18',
    latitude: 28.5709,
    longitude: 77.3245,
  ),
  SelectedLocation(
    label: 'Connaught Place, Delhi',
    latitude: 28.6315,
    longitude: 77.2167,
  ),
];