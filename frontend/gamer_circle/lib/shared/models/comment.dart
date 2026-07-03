class CommentUser {
  const CommentUser({
    required this.id,
    this.name,
    this.avatarUrl,
  });

  final String id;
  final String? name;
  final String? avatarUrl;

  factory CommentUser.fromJson(Map<String, dynamic> json) => CommentUser(
        id: json['id'] as String,
        name: json['name'] as String?,
        avatarUrl: json['avatar_url'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'avatar_url': avatarUrl,
      };
}

class Comment {
  const Comment({
    required this.id,
    required this.user,
    required this.content,
    required this.likesCount,
    required this.isDeleted,
    required this.createdAt,
    this.parentId,
    this.isLiked = false,
    this.replyCount = 0,
  });

  final String id;
  final CommentUser user;
  final String content;
  final String? parentId;
  final int likesCount;
  final bool isLiked;
  final bool isDeleted;
  final int replyCount;
  final DateTime createdAt;

  factory Comment.fromJson(Map<String, dynamic> json) => Comment(
        id: json['id'] as String,
        user: CommentUser.fromJson(json['user'] as Map<String, dynamic>),
        content: json['content'] as String,
        parentId: json['parent_id'] as String?,
        likesCount: json['likes_count'] as int? ?? 0,
        isLiked: json['is_liked'] as bool? ?? false,
        isDeleted: json['is_deleted'] as bool? ?? false,
        replyCount: json['reply_count'] as int? ?? 0,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'user': user.toJson(),
        'content': content,
        'parent_id': parentId,
        'likes_count': likesCount,
        'is_liked': isLiked,
        'is_deleted': isDeleted,
        'reply_count': replyCount,
        'created_at': createdAt.toIso8601String(),
      };

  Comment copyWith({
    String? id,
    CommentUser? user,
    String? content,
    String? parentId,
    int? likesCount,
    bool? isLiked,
    bool? isDeleted,
    int? replyCount,
    DateTime? createdAt,
  }) =>
      Comment(
        id: id ?? this.id,
        user: user ?? this.user,
        content: content ?? this.content,
        parentId: parentId ?? this.parentId,
        likesCount: likesCount ?? this.likesCount,
        isLiked: isLiked ?? this.isLiked,
        isDeleted: isDeleted ?? this.isDeleted,
        replyCount: replyCount ?? this.replyCount,
        createdAt: createdAt ?? this.createdAt,
      );
}