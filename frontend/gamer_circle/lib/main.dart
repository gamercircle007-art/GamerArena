import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/app.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  AppConfig(
    flavor: Flavor.dev,
    baseUrl: AppConstants.baseUrl,
    useMockApi: false,
  );

  await init();

  runApp(
    const ProviderScope(
      child: GamerCircleApp(),
    ),
  );
}
