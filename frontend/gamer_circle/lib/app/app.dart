import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/router/app_router.dart';
import 'package:gamer_circle/app/theme/app_theme.dart';
import 'package:gamer_circle/core/widgets/ws_listener.dart';
class GamerCircleApp extends ConsumerWidget {
  const GamerCircleApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'GamerCircle',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      // Force light so system dark mode does not paint black input fills
      // on white auth/onboarding screens (text becomes invisible).
      themeMode: ThemeMode.light,
      routerConfig: ref.watch(routerProvider),
      builder: (context, child) =>
          WsListener(child: child ?? const SizedBox.shrink()),
    );
  }
}
