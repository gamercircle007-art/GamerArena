import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/app.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final flavor = _flavorFromDefine(AppConstants.appFlavor);

  AppConfig(
    flavor: flavor,
    baseUrl: AppConstants.baseUrl,
    useMockApi: false,
  );

  // Status bar: light content on dark brand bars
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  await init();

  if (kReleaseMode) {
    debugPrint = (String? message, {int? wrapWidth}) {};
  }

  runApp(
    const ProviderScope(
      child: GamerCircleApp(),
    ),
  );
}

Flavor _flavorFromDefine(String raw) {
  switch (raw.toLowerCase()) {
    case 'prod':
    case 'production':
      return Flavor.prod;
    case 'staging':
      return Flavor.staging;
    default:
      return Flavor.dev;
  }
}
