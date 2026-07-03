class Message {
  Message({
    required this.id,
    required this.conversationId,
    required this.senderId,
    this.senderName,
    this.senderAvatar,
    this.content,
    this.messageType = 'text',
    this.mediaUrl,
    this.thumbnailUrl,
    this.durationSeconds,
    this.isEphemeral = false,
    this.ephemeralDuration = 10,
    this.viewedAt,
    this.replyToId,
    this.locationLat,
    this.locationLng,
    this.stickerId,
    this.reactions = const {},
    this.isDeleted = false,
    required this.createdAt,
    this.isMine = false,
    this.status = 'sent',
  });

  final String id;
  final String conversationId;
  final String senderId;
  final String? senderName;
  final String? senderAvatar;
  final String? content;
  final String messageType;
  final String? mediaUrl;
  final String? thumbnailUrl;
  final int? durationSeconds;
  final bool isEphemeral;
  final int ephemeralDuration;
  final DateTime? viewedAt;
  final String? replyToId;
  final double? locationLat;
  final double? locationLng;
  final String? stickerId;
  final Map<String, dynamic> reactions;
  final bool isDeleted;
  final DateTime createdAt;
  final bool isMine;
  final String status;

  factory Message.fromJson(Map<String, dynamic> json, {String? myId}) {
    final reactionsRaw = json['reactions'];
    return Message(
      id: json['id'] as String,
      conversationId: json['conversation_id'] as String,
      senderId: json['sender_id'] as String,
      senderName: json['sender_name'] as String?,
      senderAvatar: json['sender_avatar'] as String?,
      content: json['content'] as String?,
      messageType: json['message_type'] as String? ?? 'text',
      mediaUrl: json['media_url'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      durationSeconds: json['duration_seconds'] as int?,
      isEphemeral: json['is_ephemeral'] as bool? ?? false,
      ephemeralDuration: json['ephemeral_duration'] as int? ?? 10,
      viewedAt: json['viewed_at'] != null
          ? DateTime.parse(json['viewed_at'] as String)
          : null,
      replyToId: json['reply_to_id'] as String?,
      locationLat: (json['location_lat'] as num?)?.toDouble(),
      locationLng: (json['location_lng'] as num?)?.toDouble(),
      stickerId: json['sticker_id'] as String?,
      reactions: reactionsRaw is Map<String, dynamic>
          ? reactionsRaw
          : (reactionsRaw is Map ? Map<String, dynamic>.from(reactionsRaw) : {}),
      isDeleted: json['is_deleted'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      isMine: myId != null && json['sender_id'] == myId,
    );
  }

  Message copyWith({
    String? status,
    Map<String, dynamic>? reactions,
    DateTime? viewedAt,
    bool? isDeleted,
  }) =>
      Message(
        id: id,
        conversationId: conversationId,
        senderId: senderId,
        senderName: senderName,
        senderAvatar: senderAvatar,
        content: content,
        messageType: messageType,
        mediaUrl: mediaUrl,
        thumbnailUrl: thumbnailUrl,
        durationSeconds: durationSeconds,
        isEphemeral: isEphemeral,
        ephemeralDuration: ephemeralDuration,
        viewedAt: viewedAt ?? this.viewedAt,
        replyToId: replyToId,
        locationLat: locationLat,
        locationLng: locationLng,
        stickerId: stickerId,
        reactions: reactions ?? this.reactions,
        isDeleted: isDeleted ?? this.isDeleted,
        createdAt: createdAt,
        isMine: isMine,
        status: status ?? this.status,
      );
}