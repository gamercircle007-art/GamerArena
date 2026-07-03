import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

final currentPositionProvider =
    AsyncNotifierProvider<CurrentPositionNotifier, Position?>(
  CurrentPositionNotifier.new,
);

class CurrentPositionNotifier extends AsyncNotifier<Position?> {
  @override
  Future<Position?> build() async => null;

  Future<Position?> requestAndFetch() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        return null;
      }
      return Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
        ),
      );
    });
    return state.valueOrNull;
  }

  void setManualPosition(double lat, double lng) {
    state = AsyncData(
      Position(
        latitude: lat,
        longitude: lng,
        timestamp: DateTime.now(),
        accuracy: 0,
        altitude: 0,
        altitudeAccuracy: 0,
        heading: 0,
        headingAccuracy: 0,
        speed: 0,
        speedAccuracy: 0,
      ),
    );
  }
}