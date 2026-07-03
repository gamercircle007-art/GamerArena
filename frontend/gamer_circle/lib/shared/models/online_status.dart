class OnlineStatus {
  OnlineStatus({
    required this.userId,
    this.isOnline = false,
    this.lastSeenAt,
    this.lastSeenDisplay,
  });

  final String userId;
  final bool isOnline;
  final DateTime? lastSeenAt;
  final String? lastSeenDisplay;

  factory OnlineStatus.fromJson(Map<String, dynamic> json) => OnlineStatus(
        userId: json['user_id'] as String,
        isOnline: json['is_online'] as bool? ?? false,
        lastSeenAt: json['last_seen_at'] != null
            ? DateTime.parse(json['last_seen_at'] as String)
            : null,
        lastSeenDisplay: json['last_seen_display'] as String?,
      );

  String get displayText {
    if (isOnline) return 'Active now';
    if (lastSeenDisplay != null && lastSeenDisplay!.isNotEmpty) {
      return lastSeenDisplay!;
    }
    if (lastSeenAt == null) return '';
    final diff = DateTime.now().difference(lastSeenAt!);
    if (diff.inMinutes < 60) return 'Active ${diff.inMinutes}m ago';
    if (diff.inHours < 24) return 'Active ${diff.inHours}h ago';
    return 'Active yesterday';
  }
}