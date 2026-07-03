import 'package:shared_preferences/shared_preferences.dart';

abstract interface class LocationLocalDataSource {
  Future<bool> isOnboardingCompleted();

  Future<bool> wasLocationGranted();

  Future<void> markOnboardingCompleted({required bool granted});

  Future<void> saveLocalLocation({
    required double latitude,
    required double longitude,
    String? city,
    String? country,
  });

  Future<Map<String, dynamic>?> getLocalLocation();
}

class LocationLocalDataSourceImpl implements LocationLocalDataSource {
  static const _onboardingKey = 'location_onboarding_completed';
  static const _grantedKey = 'location_granted';
  static const _latKey = 'location_latitude';
  static const _lngKey = 'location_longitude';
  static const _cityKey = 'location_city';
  static const _countryKey = 'location_country';

  final SharedPreferences _prefs;

  LocationLocalDataSourceImpl(this._prefs);

  @override
  Future<bool> isOnboardingCompleted() async =>
      _prefs.getBool(_onboardingKey) ?? false;

  @override
  Future<bool> wasLocationGranted() async =>
      _prefs.getBool(_grantedKey) ?? false;

  @override
  Future<void> markOnboardingCompleted({required bool granted}) async {
    await _prefs.setBool(_onboardingKey, true);
    await _prefs.setBool(_grantedKey, granted);
  }

  @override
  Future<void> saveLocalLocation({
    required double latitude,
    required double longitude,
    String? city,
    String? country,
  }) async {
    await _prefs.setDouble(_latKey, latitude);
    await _prefs.setDouble(_lngKey, longitude);
    if (city != null) {
      await _prefs.setString(_cityKey, city);
    } else {
      await _prefs.remove(_cityKey);
    }
    if (country != null) {
      await _prefs.setString(_countryKey, country);
    } else {
      await _prefs.remove(_countryKey);
    }
  }

  @override
  Future<Map<String, dynamic>?> getLocalLocation() async {
    final lat = _prefs.getDouble(_latKey);
    final lng = _prefs.getDouble(_lngKey);
    if (lat == null || lng == null) return null;

    return {
      'latitude': lat,
      'longitude': lng,
      'city': _prefs.getString(_cityKey),
      'country': _prefs.getString(_countryKey),
    };
  }
}