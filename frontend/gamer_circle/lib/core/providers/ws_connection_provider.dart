import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

String wsBaseUrlFromApi(String apiBaseUrl) {
  final uri = Uri.parse(apiBaseUrl);
  final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
  return '$scheme://${uri.host}${uri.hasPort ? ':${uri.port}' : ''}';
}

/// Keeps the global WebSocket connected while the user is authenticated.
final wsConnectionProvider = Provider<void>((ref) {
  StreamSubscription<Map<String, dynamic>>? onlineSub;

  ref.onDispose(() => onlineSub?.cancel());

  ref.listen<AuthState>(authNotifierProvider, (previous, next) async {
    onlineSub?.cancel();

    if (next is AuthAuthenticated) {
      final token = await getIt<AuthLocalDataSource>().getAccessToken();
      if (token != null) {
        await WsService.instance.connect(
          baseUrl: wsBaseUrlFromApi(AppConfig.instance.baseUrl),
          token: token,
        );
        WsService.instance.subscribe('user:${next.user.id}');

        onlineSub = WsService.instance.events.listen((event) {
          final type = event['type'] as String? ?? event['event'] as String?;
          final uid = event['user_id'] as String?;
          if (uid == null) return;
          if (type == 'user_online') {
            ref.read(onlineStatusNotifierProvider.notifier).setOnline(uid, true);
          } else if (type == 'user_offline') {
            ref.read(onlineStatusNotifierProvider.notifier).setOnline(uid, false);
          }
        });
      }
    } else if (next is AuthUnauthenticated || next is AuthGuest) {
      await WsService.instance.disconnect();
    }
  }, fireImmediately: true);
});