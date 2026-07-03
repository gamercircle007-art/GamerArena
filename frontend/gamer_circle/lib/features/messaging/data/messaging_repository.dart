import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/messaging_api_paths.dart';
import 'package:gamer_circle/shared/models/conversation.dart';
import 'package:gamer_circle/shared/models/message.dart';

class MessagingRepository {
  MessagingRepository(this._dio);

  final Dio _dio;

  Future<List<Conversation>> getConversations() async {
    final res = await _dio.get(MessagingApiPaths.conversations);
    final list = res.data as List<dynamic>;
    return list
        .map((e) => Conversation.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Conversation> findOrCreateDm(String userId) async {
    final res = await _dio.post(
      MessagingApiPaths.findOrCreate,
      data: {'user_id': userId},
    );
    return Conversation.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Message>> getMessages(
    String conversationId, {
    int limit = 30,
    String? beforeId,
    String? myId,
  }) async {
    final res = await _dio.get(
      MessagingApiPaths.messages(conversationId),
      queryParameters: {
        'limit': limit,
        if (beforeId != null) 'before_id': beforeId,
      },
    );
    final list = res.data as List<dynamic>;
    return list
        .map((e) => Message.fromJson(e as Map<String, dynamic>, myId: myId))
        .toList();
  }

  Future<Message> sendMessage(
    String conversationId, {
    required String? content,
    String messageType = 'text',
    String? mediaUrl,
    String? replyToId,
    bool isEphemeral = false,
    String? myId,
  }) async {
    final res = await _dio.post(
      MessagingApiPaths.messages(conversationId),
      data: {
        if (content != null) 'content': content,
        'message_type': messageType,
        if (mediaUrl != null) 'media_url': mediaUrl,
        if (replyToId != null) 'reply_to_id': replyToId,
        'is_ephemeral': isEphemeral,
      },
    );
    return Message.fromJson(res.data as Map<String, dynamic>, myId: myId);
  }

  Future<void> addReaction(
    String conversationId,
    String messageId,
    String emoji,
  ) async {
    await _dio.post(
      MessagingApiPaths.messageReact(conversationId, messageId),
      data: {'emoji': emoji},
    );
  }

  Future<void> deleteMessage(String conversationId, String messageId) async {
    await _dio.delete(
      MessagingApiPaths.messageDelete(conversationId, messageId),
    );
  }

  Future<List<Message>> getMedia(String conversationId, {String? myId}) async {
    final res = await _dio.get(MessagingApiPaths.media(conversationId));
    final list = res.data as List<dynamic>;
    return list
        .map((e) => Message.fromJson(e as Map<String, dynamic>, myId: myId))
        .toList();
  }

  Future<void> markDelivered(String conversationId, String messageId) async {
    await _dio.put(MessagingApiPaths.messageDelivered(conversationId, messageId));
  }

  Future<void> markEphemeralViewed(String conversationId, String messageId) async {
    await _dio.put(MessagingApiPaths.messageViewed(conversationId, messageId));
  }
}