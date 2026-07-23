class AppConstants {
  static const String appName = 'GamerCircle';

  /// Production API (Render).
  static const String renderBaseUrl =
      'https://gamer-circle-api.onrender.com/api/v1';

  /// Local backend override.
  static const String localBaseUrl = 'http://localhost:8000/api/v1';

  /// API base including `/api/v1`.
  ///
  /// Default = Render production.
  /// Local: `--dart-define=API_BASE_URL=http://localhost:8000/api/v1`
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: renderBaseUrl,
  );

  /// `dev` | `staging` | `prod` — release APK uses prod.
  static const String appFlavor = String.fromEnvironment(
    'APP_FLAVOR',
    defaultValue: 'prod',
  );

  static const int webPort = 8080;

  /// Render free tier cold start — 60s connect/receive.
  static const int apiTimeout = 60000;

  /// Only shown in non-release UI when backend still has OTP_DEV_BYPASS.
  static const String devOtpBypass = '123456';

  static bool get isProdFlavor => appFlavor == 'prod';
}
