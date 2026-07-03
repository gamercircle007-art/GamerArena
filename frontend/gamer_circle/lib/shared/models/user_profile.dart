class UserProfile {
  UserProfile({
    required this.userId,
    this.bio,
    this.gameTags = const [],
    this.website,
    this.isPrivate = false,
    this.allowMessagesFrom = 'friends',
    this.showOnlineStatus = 'friends',
    this.allowFriendRequests = true,
    this.city,
    this.storiesPrivacy = 'friends',
  });

  final String userId;
  final String? bio;
  final List<String> gameTags;
  final String? website;
  final bool isPrivate;
  final String allowMessagesFrom;
  final String showOnlineStatus;
  final bool allowFriendRequests;
  final String? city;
  final String storiesPrivacy;

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        userId: json['user_id'] as String? ?? json['id'] as String,
        bio: json['bio'] as String?,
        gameTags: (json['game_tags'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        website: json['website'] as String?,
        isPrivate: json['is_private'] as bool? ?? false,
        allowMessagesFrom: json['allow_messages_from'] as String? ?? 'friends',
        showOnlineStatus: json['show_online_status'] as String? ?? 'friends',
        allowFriendRequests: json['allow_friend_requests'] as bool? ?? true,
        city: json['city'] as String?,
        storiesPrivacy: json['stories_privacy'] as String? ?? 'friends',
      );

  Map<String, dynamic> toJson() => {
        'bio': bio,
        'game_tags': gameTags,
        'website': website,
        'is_private': isPrivate,
        'allow_messages_from': allowMessagesFrom,
        'show_online_status': showOnlineStatus,
        'allow_friend_requests': allowFriendRequests,
        'city': city,
      };
}