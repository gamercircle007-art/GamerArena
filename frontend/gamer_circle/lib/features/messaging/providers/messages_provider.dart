import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/shared/models/message.dart';

class MessagesNotifier extends FamilyAsyncNotifier<List<Message>, String> {
  StreamSubscription<Map<String, dynamic>>? _wsSub;
  String? _oldestId;
  bool _hasMore = true;

  @override
  Future<List<Message>> build(String arg) async {
    ref.onDispose(() {
      _wsSub?.cancel();
      WsService.instance.unsubscribe('conversation:$arg');
    });

    WsService.instance.subscribe('conversation:$arg');
    _listenWs(arg);

    final myId = _myId();
    final messages = await ref.read(messagingRepositoryProvider).getMessages(
          arg,
          myId: myId,
        );
    if (messages.isNotEmpty) _oldestId = messages.last.id;
    return messages;
  }

  String? _myId() {
    final auth = ref.read(authNotifierProvider);
    return auth is AuthAuthenticated ? auth.user.id : null;
  }

  void _listenWs(String conversationId) {
    _wsSub?.cancel();
    _wsSub = WsService.instance.events.listen((event) {
      Map<String, dynamic> data = event;
      if (event['payload'] is Map<String, dynamic>) {
        data = event['payload'] as Map<String, dynamic>;
      }

      if (data['type'] == 'typing_start' &&
          data['conversation_id'] == conversationId) {
        final uid = data['user_id'] as String?;
        if (uid != null && uid != _myId()) {
          ref.read(typingUsersProvider(conversationId).notifier).state = {uid};
        }
        return;
      }
      if (data['type'] == 'typing_stop' &&
          data['conversation_id'] == conversationId) {
        ref.read(typingUsersProvider(conversationId).notifier).state = {};
        return;
      }

      if (data['type'] == 'message_read' && data['conversation_id'] == conversationId) {
        final msgId = data['message_id'] as String?;
        if (msgId == null) return;
        final current = state.valueOrNull ?? [];
        state = AsyncData(
          current.map((m) {
            if (m.id == msgId && m.isMine) {
              return m.copyWith(status: 'read');
            }
            return m;
          }).toList(),
        );
        return;
      }

      if (data['type'] == 'message_deleted' && data['conversation_id'] == conversationId) {
        final msgId = data['message_id'] as String?;
        if (msgId == null) return;
        final current = state.valueOrNull ?? [];
        state = AsyncData(current.where((m) => m.id != msgId).toList());
        return;
      }

      if (data['type'] == 'ephemeral_viewed') {
        final msgId = data['message_id'] as String?;
        if (msgId == null) return;
        final current = state.valueOrNull ?? [];
        state = AsyncData(
          current.map((m) {
            if (m.id == msgId) {
              return m.copyWith(viewedAt: DateTime.now());
            }
            return m;
          }).toList(),
        );
        return;
      }

      if (data['type'] != 'new_message') return;
      if (data['conversation_id'] != conversationId) return;

      final msgRaw = data['message'];
      if (msgRaw is! Map<String, dynamic>) return;
      final msg = Message.fromJson(msgRaw, myId: _myId());
      final current = state.valueOrNull ?? [];
      if (current.any((m) => m.id == msg.id)) return;
      state = AsyncData([msg, ...current]);

      if (!msg.isMine) {
        ref.read(messagingRepositoryProvider).markDelivered(conversationId, msg.id);
      }
    });
  }

  Future<void> addReaction(String messageId, String emoji) async {
    await ref.read(messagingRepositoryProvider).addReaction(arg, messageId, emoji);
    final current = state.valueOrNull ?? [];
    state = AsyncData(
      current.map((m) {
        if (m.id != messageId) return m;
        final reactions = Map<String, dynamic>.from(m.reactions);
        final users = List<dynamic>.from(reactions[emoji] as List<dynamic>? ?? []);
        final myId = _myId();
        if (myId != null && !users.contains(myId)) users.add(myId);
        reactions[emoji] = users;
        return m.copyWith(reactions: reactions);
      }).toList(),
    );
  }

  Future<void> deleteMessage(String messageId) async {
    await ref.read(messagingRepositoryProvider).deleteMessage(arg, messageId);
    final current = state.valueOrNull ?? [];
    state = AsyncData(current.where((m) => m.id != messageId).toList());
  }

  Future<void> loadMore() async {
    if (!_hasMore || _oldestId == null) return;
    final more = await ref.read(messagingRepositoryProvider).getMessages(
          arg,
          beforeId: _oldestId,
          myId: _myId(),
        );
    if (more.isEmpty) {
      _hasMore = false;
      return;
    }
    _oldestId = more.last.id;
    final current = state.valueOrNull ?? [];
    state = AsyncData([...current, ...more]);
  }

  Future<void> sendMessage({
    required String content,
    String messageType = 'text',
    String? replyToId,
    bool isEphemeral = false,
  }) async {
    final myId = _myId();
    final optimistic = Message(
      id: 'temp-${DateTime.now().millisecondsSinceEpoch}',
      conversationId: arg,
      senderId: myId ?? '',
      content: content,
      messageType: messageType,
      isEphemeral: isEphemeral,
      createdAt: DateTime.now(),
      isMine: true,
      status: 'sending',
    );
    final current = state.valueOrNull ?? [];
    state = AsyncData([optimistic, ...current]);

    try {
      final sent = await ref.read(messagingRepositoryProvider).sendMessage(
            arg,
            content: content,
            messageType: messageType,
            replyToId: replyToId,
            isEphemeral: isEphemeral,
            myId: myId,
          );
      final updated = [
        sent,
        ...current.where((m) => m.id != optimistic.id),
      ];
      state = AsyncData(updated);
    } catch (e) {
      state = AsyncData(current);
      rethrow;
    }
  }

  void markAllRead() {
    final messages = state.valueOrNull;
    WsService.instance.sendAction('mark_read', {
      'conversation_id': arg,
      if (messages != null && messages.isNotEmpty)
        'last_message_id': messages.first.id,
    });
  }
}

final messagesProvider =
    AsyncNotifierProvider.family<MessagesNotifier, List<Message>, String>(
  MessagesNotifier.new,
);

final typingUsersProvider = StateProvider.family<Set<String>, String>(
  (ref, _) => <String>{},
);

final userOnlineStatusProvider = Provider.family<bool, String>((ref, userId) {
  final map = ref.watch(onlineStatusNotifierProvider);
  return map[userId] ?? WsService.instance.isUserOnline(userId);
});