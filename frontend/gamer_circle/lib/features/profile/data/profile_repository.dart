import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/messaging_api_paths.dart';
import 'package:gamer_circle/shared/models/online_status.dart';
import 'package:gamer_circle/shared/models/user.dart';


class PublicProfile {
  PublicProfile({
    required this.id,
    this.name,
    this.username,
    this.avatarUrl,
    this.bio,
    this.gameTags = const [],
    this.city,
    this.isPrivate = false,
    this.friendsCount = 0,
    this.followersCount = 0,
    this.followingCount = 0,
    this.isFriend = false,
    this.friendRequestSent = false,
    this.friendRequestReceived = false,
    this.isOnline = false,
    this.mutualFriendsCount = 0,
  });

  final String id;
  final String? name;
  final String? username;
  final String? avatarUrl;
  final String? bio;
  final List<String> gameTags;
  final String? city;
  final bool isPrivate;
  final int friendsCount;
  final int followersCount;
  final int followingCount;
  final bool isFriend;
  final bool friendRequestSent;
  final bool friendRequestReceived;
  final bool isOnline;
  final int mutualFriendsCount;

  factory PublicProfile.fromJson(Map<String, dynamic> json) => PublicProfile(
        id: json['id'] as String,
        name: json['name'] as String?,
        username: json['username'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        bio: json['bio'] as String?,
        gameTags: (json['game_tags'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        city: json['city'] as String?,
        isPrivate: json['is_private'] as bool? ?? false,
        friendsCount: json['friends_count'] as int? ?? 0,
        followersCount: json['followers_count'] as int? ?? 0,
        followingCount: json['following_count'] as int? ?? 0,
        isFriend: json['is_friend'] as bool? ?? false,
        friendRequestSent: json['friend_request_sent'] as bool? ?? false,
        friendRequestReceived: json['friend_request_received'] as bool? ?? false,
        isOnline: json['is_online'] as bool? ?? false,
        mutualFriendsCount: json['mutual_friends_count'] as int? ?? 0,
      );
}

class ProfileRepository {
  ProfileRepository(this._dio);

  final Dio _dio;

  Future<PublicProfile> getUserProfile(String userId) async {
    final res = await _dio.get(SocialApiPaths.userProfile(userId));
    return PublicProfile.fromJson(res.data as Map<String, dynamic>);
  }

  Future<PublicProfile> getMyProfile(String userId) async {
    return getUserProfile(userId);
  }

  Future<OnlineStatus> getUserStatus(String userId) async {
    final res = await _dio.get(SocialApiPaths.userStatus(userId));
    return OnlineStatus.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> updateProfile(Map<String, dynamic> data) async {
    await _dio.put(SocialApiPaths.myProfile, data: data);
  }

  Future<void> updateStatusPrivacy(String showTo) async {
    await _dio.put(SocialApiPaths.statusPrivacy, data: {'show_to': showTo});
  }

  Future<void> updateLocationPrivacy(String privacy) async {
    await _dio.put(SocialApiPaths.locationPrivacy, data: {'privacy': privacy});
  }

  Future<Map<String, dynamic>> getQrCode() async {
    final res = await _dio.get(SocialApiPaths.qrCode);
    return res.data as Map<String, dynamic>;
  }

  Future<List<AppUser>> getBlockedUsers() async {
    final res = await _dio.get('/users/me/blocks');
    return (res.data as List<dynamic>)
        .map((e) => AppUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> unblockUser(String userId) async {
    await _dio.delete(SocialApiPaths.blockUser(userId));
  }
}