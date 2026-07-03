import 'package:gamer_circle/shared/models/user.dart';

class FriendRequest {
  FriendRequest({
    required this.id,
    required this.sender,
    required this.createdAt,
    this.status = 'pending',
  });

  final String id;
  final AppUser sender;
  final DateTime createdAt;
  final String status;

  factory FriendRequest.fromJson(Map<String, dynamic> json) => FriendRequest(
        id: json['id'] as String,
        sender: AppUser.fromJson(json['sender'] as Map<String, dynamic>),
        createdAt: DateTime.parse(json['created_at'] as String),
        status: json['status'] as String? ?? 'pending',
      );
}

class Friendship {
  Friendship({
    required this.id,
    required this.user,
    required this.createdAt,
    this.isOnline = false,
  });

  final String id;
  final AppUser user;
  final DateTime createdAt;
  final bool isOnline;

  factory Friendship.fromJson(Map<String, dynamic> json) => Friendship(
        id: json['id'] as String,
        user: AppUser.fromJson(json['user'] as Map<String, dynamic>),
        createdAt: DateTime.parse(json['created_at'] as String),
        isOnline: json['is_online'] as bool? ?? false,
      );
}

class FriendSuggestion {
  FriendSuggestion({required this.user, this.mutualFriends = 0});

  final AppUser user;
  final int mutualFriends;

  factory FriendSuggestion.fromJson(Map<String, dynamic> json) => FriendSuggestion(
        user: AppUser.fromJson(json['user'] as Map<String, dynamic>),
        mutualFriends: json['mutual_friends'] as int? ?? 0,
      );
}