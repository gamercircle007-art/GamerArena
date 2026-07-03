class ReelUser {
  const ReelUser({
    required this.id,
    this.username,
    this.name,
    this.avatarUrl,
    this.followersCount = 0,
    this.followingCount = 0,
    this.isFollowing = false,
  });

  final String id;
  final String? username;
  final String? name;
  final String? avatarUrl;
  final int followersCount;
  final int followingCount;
  final bool isFollowing;

  String get displayName => username ?? name ?? 'Gamer';

  factory ReelUser.fromJson(Map<String, dynamic> json) => ReelUser(
        id: json['id'] as String,
        username: json['username'] as String?,
        name: json['name'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        followersCount: json['followers_count'] as int? ?? 0,
        followingCount: json['following_count'] as int? ?? 0,
        isFollowing: json['is_following'] as bool? ?? false,
      );
}

class Reel {
  const Reel({
    required this.id,
    required this.user,
    required this.videoUrl,
    this.thumbnailUrl,
    this.coverUrl,
    this.caption,
    this.hashtags = const [],
    this.location,
    this.durationSeconds,
    this.aspectRatio = '9:16',
    this.filterName = 'normal',
    this.musicTitle,
    this.privacy = 'public',
    this.likesCount = 0,
    this.commentsCount = 0,
    this.viewsCount = 0,
    this.sharesCount = 0,
    this.bookmarksCount = 0,
    this.isLiked = false,
    this.isBookmarked = false,
    this.createdAt,
  });

  final String id;
  final ReelUser user;
  final String videoUrl;
  final String? thumbnailUrl;
  final String? coverUrl;
  final String? caption;
  final List<String> hashtags;
  final String? location;
  final int? durationSeconds;
  final String aspectRatio;
  final String filterName;
  final String? musicTitle;
  final String privacy;
  final int likesCount;
  final int commentsCount;
  final int viewsCount;
  final int sharesCount;
  final int bookmarksCount;
  final bool isLiked;
  final bool isBookmarked;
  final DateTime? createdAt;

  Reel copyWith({
    bool? isLiked,
    int? likesCount,
    bool? isBookmarked,
    int? bookmarksCount,
    int? viewsCount,
    int? commentsCount,
    ReelUser? user,
  }) {
    return Reel(
      id: id,
      user: user ?? this.user,
      videoUrl: videoUrl,
      thumbnailUrl: thumbnailUrl,
      coverUrl: coverUrl,
      caption: caption,
      hashtags: hashtags,
      location: location,
      durationSeconds: durationSeconds,
      aspectRatio: aspectRatio,
      filterName: filterName,
      musicTitle: musicTitle,
      privacy: privacy,
      likesCount: likesCount ?? this.likesCount,
      commentsCount: commentsCount ?? this.commentsCount,
      viewsCount: viewsCount ?? this.viewsCount,
      sharesCount: sharesCount,
      bookmarksCount: bookmarksCount ?? this.bookmarksCount,
      isLiked: isLiked ?? this.isLiked,
      isBookmarked: isBookmarked ?? this.isBookmarked,
      createdAt: createdAt,
    );
  }

  factory Reel.fromJson(Map<String, dynamic> json) => Reel(
        id: json['id'] as String,
        user: ReelUser.fromJson(json['user'] as Map<String, dynamic>),
        videoUrl: json['video_url'] as String,
        thumbnailUrl: json['thumbnail_url'] as String?,
        coverUrl: json['cover_url'] as String?,
        caption: json['caption'] as String?,
        hashtags: (json['hashtags'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        location: json['location'] as String?,
        durationSeconds: json['duration_seconds'] as int?,
        aspectRatio: json['aspect_ratio'] as String? ?? '9:16',
        filterName: json['filter_name'] as String? ?? 'normal',
        musicTitle: json['music_title'] as String?,
        privacy: json['privacy'] as String? ?? 'public',
        likesCount: json['likes_count'] as int? ?? 0,
        commentsCount: json['comments_count'] as int? ?? 0,
        viewsCount: json['views_count'] as int? ?? 0,
        sharesCount: json['shares_count'] as int? ?? 0,
        bookmarksCount: json['bookmarks_count'] as int? ?? 0,
        isLiked: json['is_liked'] as bool? ?? false,
        isBookmarked: json['is_bookmarked'] as bool? ?? false,
        createdAt: json['created_at'] != null
            ? DateTime.tryParse(json['created_at'] as String)
            : null,
      );
}

class ReelFeedPage {
  const ReelFeedPage({
    required this.items,
    required this.page,
    required this.hasMore,
  });

  final List<Reel> items;
  final int page;
  final bool hasMore;

  factory ReelFeedPage.fromJson(Map<String, dynamic> json) => ReelFeedPage(
        items: (json['items'] as List<dynamic>)
            .map((e) => Reel.fromJson(e as Map<String, dynamic>))
            .toList(),
        page: json['page'] as int? ?? 1,
        hasMore: json['has_more'] as bool? ?? false,
      );
}

class ReelComment {
  const ReelComment({
    required this.id,
    required this.user,
    required this.content,
    this.parentId,
    this.likesCount = 0,
    this.isLiked = false,
    this.isPinned = false,
    this.replyCount = 0,
    this.createdAt,
  });

  final String id;
  final ReelUser user;
  final String content;
  final String? parentId;
  final int likesCount;
  final bool isLiked;
  final bool isPinned;
  final int replyCount;
  final DateTime? createdAt;

  factory ReelComment.fromJson(Map<String, dynamic> json) => ReelComment(
        id: json['id'] as String,
        user: ReelUser.fromJson(json['user'] as Map<String, dynamic>),
        content: json['content'] as String,
        parentId: json['parent_id'] as String?,
        likesCount: json['likes_count'] as int? ?? 0,
        isLiked: json['is_liked'] as bool? ?? false,
        isPinned: json['is_pinned'] as bool? ?? false,
        replyCount: json['reply_count'] as int? ?? 0,
        createdAt: json['created_at'] != null
            ? DateTime.tryParse(json['created_at'] as String)
            : null,
      );
}