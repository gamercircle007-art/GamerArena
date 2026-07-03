import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/notification_badge_provider.dart';
import 'package:gamer_circle/core/providers/ws_connection_provider.dart';
import 'package:gamer_circle/core/services/push_notification_service.dart';

/// Global WebSocket listener: maintains connection and routes notification taps.
class WsListener extends ConsumerStatefulWidget {
  const WsListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<WsListener> createState() => _WsListenerState();
}

class _WsListenerState extends ConsumerState<WsListener> {
  StreamSubscription<Map<String, dynamic>>? _subscription;

  @override
  void initState() {
    super.initState();
    PushNotificationService.instance.initialize();
    _subscription = WsService.instance.events.listen(_onEvent);
  }

  void _onEvent(Map<String, dynamic> event) {
    if (event['event'] != 'notification') return;
    final payload = event['payload'];
    if (payload is! Map<String, dynamic>) return;
    final title = payload['title'] as String? ?? 'Notification';
    final body = payload['body'] as String? ?? '';
    final data = payload['data'];
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$title${body.isNotEmpty ? ': $body' : ''}'),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'View',
          onPressed: () => _navigateFromNotification(data),
        ),
      ),
    );
  }

  void _navigateFromNotification(dynamic data) {
    if (data is! Map<String, dynamic>) {
      context.push('/notifications');
      return;
    }
    final type = data['type'] as String?;
    switch (type) {
      case 'new_message':
        final convId = data['conversation_id'] as String?;
        if (convId != null) {
          context.push('/messages/chat/$convId');
        } else {
          context.push('/messages');
        }
      case 'friend_request':
        context.push('/friend-requests');
      case 'new_story':
        context.push('/feed');
      default:
        context.push('/notifications');
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(wsConnectionProvider);
    ref.watch(unreadNotificationCountProvider);
    return widget.child;
  }
}