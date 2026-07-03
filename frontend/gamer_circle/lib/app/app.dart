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
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      routerConfig: ref.watch(routerProvider),
      builder: (context, child) =>
          WsListener(child: child ?? const SizedBox.shrink()),
    );
  }
}
