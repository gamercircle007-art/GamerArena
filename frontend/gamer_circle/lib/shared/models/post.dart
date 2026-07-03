import 'parlor.dart';
import 'tournament.dart';

class Post {
  const Post({
    required this.id,
    required this.content,
    required this.mediaUrls,
    required this.parlor,
    required this.likesCount,
    required this.commentsCount,
    required this.createdAt,
    this.tournament,
    this.isLiked = false,
  });

  final String id;
  final String content;
  final List<String> mediaUrls;
  final Parlor parlor;
  final TournamentSummary? tournament;
  final int likesCount;
  final int commentsCount;
  final bool isLiked;
  final DateTime createdAt;

  factory Post.fromJson(Map<String, dynamic> json) => Post(
        id: json['id'] as String,
        content: json['content'] as String,
        mediaUrls: (json['media_urls'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        parlor: Parlor.fromJson(json['parlor'] as Map<String, dynamic>),
        tournament: json['tournament'] != null
            ? TournamentSummary.fromJson(
                json['tournament'] as Map<String, dynamic>,
              )
            : null,
        likesCount: json['likes_count'] as int? ?? 0,
        commentsCount: json['comments_count'] as int? ?? 0,
        isLiked: json['is_liked'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'content': content,
        'media_urls': mediaUrls,
        'parlor': parlor.toJson(),
        'tournament': tournament?.toJson(),
        'likes_count': likesCount,
        'comments_count': commentsCount,
        'is_liked': isLiked,
        'created_at': createdAt.toIso8601String(),
      };

  Post copyWith({
    String? id,
    String? content,
    List<String>? mediaUrls,
    Parlor? parlor,
    TournamentSummary? tournament,
    int? likesCount,
    int? commentsCount,
    bool? isLiked,
    DateTime? createdAt,
  }) =>
      Post(
        id: id ?? this.id,
        content: content ?? this.content,
        mediaUrls: mediaUrls ?? this.mediaUrls,
        parlor: parlor ?? this.parlor,
        tournament: tournament ?? this.tournament,
        likesCount: likesCount ?? this.likesCount,
        commentsCount: commentsCount ?? this.commentsCount,
        isLiked: isLiked ?? this.isLiked,
        createdAt: createdAt ?? this.createdAt,
      );
}