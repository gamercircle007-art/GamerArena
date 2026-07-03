class ConversationParticipant {
  ConversationParticipant({
    required this.id,
    this.name,
    this.username,
    this.avatarUrl,
    this.isOnline = false,
  });

  final String id;
  final String? name;
  final String? username;
  final String? avatarUrl;
  final bool isOnline;

  factory ConversationParticipant.fromJson(Map<String, dynamic> json) =>
      ConversationParticipant(
        id: json['id'] as String,
        name: json['name'] as String?,
        username: json['username'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        isOnline: json['is_online'] as bool? ?? false,
      );
}

class Conversation {
  Conversation({
    required this.id,
    this.type = 'direct',
    this.isEphemeral = false,
    this.theme = 'default',
    this.emoji,
    this.lastMessageAt,
    this.lastMessagePreview,
    this.unreadCount = 0,
    this.participants = const [],
    required this.createdAt,
  });

  final String id;
  final String type;
  final bool isEphemeral;
  final String theme;
  final String? emoji;
  final DateTime? lastMessageAt;
  final String? lastMessagePreview;
  final int unreadCount;
  final List<ConversationParticipant> participants;
  final DateTime createdAt;

  ConversationParticipant? otherParticipant(String myId) {
    for (final p in participants) {
      if (p.id != myId) return p;
    }
    return participants.isNotEmpty ? participants.first : null;
  }

  factory Conversation.fromJson(Map<String, dynamic> json) {
    final parts = json['participants'] as List<dynamic>? ?? [];
    return Conversation(
      id: json['id'] as String,
      type: json['type'] as String? ?? 'direct',
      isEphemeral: json['is_ephemeral'] as bool? ?? false,
      theme: json['theme'] as String? ?? 'default',
      emoji: json['emoji'] as String?,
      lastMessageAt: json['last_message_at'] != null
          ? DateTime.parse(json['last_message_at'] as String)
          : null,
      lastMessagePreview: json['last_message_preview'] as String?,
      unreadCount: json['unread_count'] as int? ?? 0,
      participants: parts
          .map((e) => ConversationParticipant.fromJson(e as Map<String, dynamic>))
          .toList(),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Conversation copyWith({
    String? lastMessagePreview,
    DateTime? lastMessageAt,
    int? unreadCount,
    List<ConversationParticipant>? participants,
  }) =>
      Conversation(
        id: id,
        type: type,
        isEphemeral: isEphemeral,
        theme: theme,
        emoji: emoji,
        lastMessageAt: lastMessageAt ?? this.lastMessageAt,
        lastMessagePreview: lastMessagePreview ?? this.lastMessagePreview,
        unreadCount: unreadCount ?? this.unreadCount,
        participants: participants ?? this.participants,
        createdAt: createdAt,
      );
}