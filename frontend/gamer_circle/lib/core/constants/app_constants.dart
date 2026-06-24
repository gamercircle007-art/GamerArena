class AppConstants {
  static const String appName = 'GamerCircle';

  /// Paythan backend API (local dev). Override via --dart-define=API_BASE_URL=...
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  /// Flutter web dev server port (must match scripts/run_frontend.sh).
  static const int webPort = 8080;

  static const int apiTimeout = 30000;

  /// Dev OTP shown in UI when backend OTP_DEV_BYPASS_CODE is set.
  static const String devOtpBypass = '123456';
}