import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';

class DeviceLocation {
  final double latitude;
  final double longitude;
  final String? city;
  final String? country;

  const DeviceLocation({
    required this.latitude,
    required this.longitude,
    this.city,
    this.country,
  });
}

enum LocationAccessResult {
  granted,
  denied,
  deniedForever,
  serviceDisabled,
}

class LocationService {
  Future<LocationAccessResult> requestAccess() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationAccessResult.serviceDisabled;
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    return switch (permission) {
      LocationPermission.always ||
      LocationPermission.whileInUse =>
        LocationAccessResult.granted,
      LocationPermission.deniedForever => LocationAccessResult.deniedForever,
      _ => LocationAccessResult.denied,
    };
  }

  Future<DeviceLocation> fetchCurrentLocation() async {
    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: Duration(seconds: 15),
      ),
    );

    String? city;
    String? country;

    try {
      final placemarks = await placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );
      if (placemarks.isNotEmpty) {
        final place = placemarks.first;
        city = place.locality?.trim().isNotEmpty == true
            ? place.locality
            : place.subAdministrativeArea;
        country = place.isoCountryCode;
      }
    } catch (_) {
      // Reverse geocoding is best-effort; coordinates are still valid.
    }

    return DeviceLocation(
      latitude: position.latitude,
      longitude: position.longitude,
      city: city,
      country: country,
    );
  }

  Future<DeviceLocation?> getCurrentLocation() async {
    final access = await requestAccess();
    if (access != LocationAccessResult.granted) {
      return null;
    }
    return fetchCurrentLocation();
  }
}