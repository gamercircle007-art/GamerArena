import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/shared/models/conversation.dart';
import 'package:gamer_circle/shared/models/message.dart';

class ConversationsNotifier extends AsyncNotifier<List<Conversation>> {
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  Future<List<Conversation>> build() async {
    ref.onDispose(() => _wsSub?.cancel());
    _listenWs();
    return ref.read(messagingRepositoryProvider).getConversations();
  }

  void _listenWs() {
    _wsSub?.cancel();
    _wsSub = WsService.instance.events.listen((event) {
      final type = event['type'] as String? ?? event['event'] as String?;
      if (type != 'new_message') {
        final payload = event['payload'];
        if (payload is! Map<String, dynamic> || payload['type'] != 'new_message') {
          return;
        }
        _handleNewMessage(payload);
        return;
      }
      _handleNewMessage(event);
    });
  }

  void _handleNewMessage(Map<String, dynamic> event) {
    final convId = event['conversation_id'] as String?;
    final msgRaw = event['message'];
    if (convId == null || msgRaw is! Map<String, dynamic>) return;

    final auth = ref.read(authNotifierProvider);
    final myId = auth is AuthAuthenticated ? auth.user.id : null;
    final msg = Message.fromJson(msgRaw, myId: myId);

    final current = state.valueOrNull ?? [];
    final idx = current.indexWhere((c) => c.id == convId);
    if (idx >= 0) {
      final conv = current[idx];
      final updated = conv.copyWith(
        lastMessagePreview: msg.isEphemeral ? '🔥 Ephemeral message' : (msg.content ?? 'Media'),
        lastMessageAt: msg.createdAt,
        unreadCount: conv.unreadCount + 1,
      );
      final list = [...current]..removeAt(idx);
      state = AsyncData([updated, ...list]);
    } else {
      ref.invalidateSelf();
    }
  }

  Future<Conversation> createConversation(String userId) async {
    final conv = await ref.read(messagingRepositoryProvider).findOrCreateDm(userId);
    final current = state.valueOrNull ?? [];
    state = AsyncData([conv, ...current.where((c) => c.id != conv.id)]);
    return conv;
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = AsyncData(await ref.read(messagingRepositoryProvider).getConversations());
  }
}

final conversationsProvider =
    AsyncNotifierProvider<ConversationsNotifier, List<Conversation>>(
  ConversationsNotifier.new,
);

final unreadCountProvider = Provider<int>((ref) {
  final convs = ref.watch(conversationsProvider).valueOrNull ?? [];
  return convs.fold(0, (sum, c) => sum + c.unreadCount);
});