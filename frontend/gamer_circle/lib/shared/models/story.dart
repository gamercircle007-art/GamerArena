class Story {
  Story({
    required this.id,
    required this.userId,
    required this.mediaUrl,
    required this.mediaType,
    this.durationSeconds = 5,
    this.caption,
    this.privacy = 'friends',
    this.viewCount = 0,
    required this.expiresAt,
    required this.createdAt,
    this.viewed = false,
  });

  final String id;
  final String userId;
  final String mediaUrl;
  final String mediaType;
  final int durationSeconds;
  final String? caption;
  final String privacy;
  final int viewCount;
  final DateTime expiresAt;
  final DateTime createdAt;
  final bool viewed;

  factory Story.fromJson(Map<String, dynamic> json) => Story(
        id: json['id'] as String,
        userId: json['user_id'] as String,
        mediaUrl: json['media_url'] as String,
        mediaType: json['media_type'] as String,
        durationSeconds: json['duration_seconds'] as int? ?? 5,
        caption: json['caption'] as String?,
        privacy: json['privacy'] as String? ?? 'friends',
        viewCount: json['view_count'] as int? ?? 0,
        expiresAt: DateTime.parse(json['expires_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        viewed: json['viewed'] as bool? ?? false,
      );
}

class StoryViewEntry {
  StoryViewEntry({
    required this.viewerId,
    this.viewerName,
    this.viewerAvatar,
    required this.viewedAt,
  });

  final String viewerId;
  final String? viewerName;
  final String? viewerAvatar;
  final DateTime viewedAt;

  factory StoryViewEntry.fromJson(Map<String, dynamic> json) => StoryViewEntry(
        viewerId: json['user_id'] as String? ?? json['viewer_id'] as String,
        viewerName: json['name'] as String? ?? json['viewer_name'] as String?,
        viewerAvatar: json['avatar_url'] as String? ?? json['viewer_avatar'] as String?,
        viewedAt: DateTime.parse(json['viewed_at'] as String),
      );
}

class StoryGroup {
  StoryGroup({
    required this.userId,
    this.userName,
    this.userAvatar,
    this.allViewed = false,
    this.stories = const [],
  });

  final String userId;
  final String? userName;
  final String? userAvatar;
  final bool allViewed;
  final List<Story> stories;

  factory StoryGroup.fromJson(Map<String, dynamic> json) {
    final storiesRaw = json['stories'] as List<dynamic>? ?? [];
    return StoryGroup(
      userId: json['user_id'] as String,
      userName: json['user_name'] as String?,
      userAvatar: json['user_avatar'] as String?,
      allViewed: json['all_viewed'] as bool? ?? false,
      stories: storiesRaw
          .map((e) => Story.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}