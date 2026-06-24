enum Flavor { dev, staging, prod }

class AppConfig {
  final Flavor flavor;
  final String baseUrl;
  final bool useMockApi;

  static AppConfig? _instance;

  AppConfig._internal({
    required this.flavor,
    required this.baseUrl,
    required this.useMockApi,
  });

  factory AppConfig({
    required Flavor flavor,
    required String baseUrl,
    bool useMockApi = false,
  }) {
    _instance ??= AppConfig._internal(
      flavor: flavor,
      baseUrl: baseUrl,
      useMockApi: useMockApi,
    );
    return _instance!;
  }

  static AppConfig get instance => _instance!;

  bool get isDev => flavor == Flavor.dev;
}