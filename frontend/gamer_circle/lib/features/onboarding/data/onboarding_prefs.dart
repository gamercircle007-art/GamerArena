import 'package:shared_preferences/shared_preferences.dart';

class OnboardingPrefs {
  OnboardingPrefs(this._prefs);

  final SharedPreferences _prefs;

  static const _onboardingCompletedKey = 'app_onboarding_completed';
  static const _guestModeKey = 'is_guest_mode';

  Future<bool> isOnboardingCompleted() async =>
      _prefs.getBool(_onboardingCompletedKey) ?? false;

  Future<bool> isGuestMode() async => _prefs.getBool(_guestModeKey) ?? false;

  Future<void> setOnboardingCompleted({required bool value}) async {
    await _prefs.setBool(_onboardingCompletedKey, value);
  }

  Future<void> setGuestMode({required bool value}) async {
    await _prefs.setBool(_guestModeKey, value);
  }

  Future<void> enterGuestMode() async {
    await setGuestMode(value: true);
    await setOnboardingCompleted(value: true);
  }

  Future<void> clearGuestMode() async {
    await setGuestMode(value: false);
  }
}