class AppConstants {
  static const String appName = 'GamerCircle';

  /// Backend API base (includes `/api/v1`).
  ///
  /// - Local default: `http://localhost:8000/api/v1`
  /// - Render staging: pass at build/run time:
  ///   `--dart-define=API_BASE_URL=https://gamer-circle-api.onrender.com/api/v1`
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  /// Render-hosted API (used by release APK scripts / docs).
  static const String renderBaseUrl =
      'https://gamer-circle-api.onrender.com/api/v1';

  /// Flutter web dev server port (must match scripts/run_frontend.sh).
  static const int webPort = 8080;

  static const int apiTimeout = 30000;

  /// Dev OTP shown in UI when backend OTP_DEV_BYPASS_CODE is set.
  static const String devOtpBypass = '123456';
}