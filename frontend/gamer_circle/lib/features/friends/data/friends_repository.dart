import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/messaging_api_paths.dart';
import 'package:gamer_circle/shared/models/friendship.dart';
import 'package:gamer_circle/shared/models/user.dart';

class FriendsRepository {
  FriendsRepository(this._dio);

  final Dio _dio;

  Future<void> sendFriendRequest(String userId) async {
    await _dio.post(FriendsApiPaths.request, data: {'user_id': userId});
  }

  Future<List<FriendRequest>> getIncomingRequests() async {
    final res = await _dio.get(FriendsApiPaths.requests);
    return (res.data as List<dynamic>)
        .map((e) => FriendRequest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<FriendRequest>> getSentRequests() async {
    final res = await _dio.get(FriendsApiPaths.requestsSent);
    return (res.data as List<dynamic>)
        .map((e) => FriendRequest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> acceptRequest(String requestId) async {
    await _dio.post(FriendsApiPaths.acceptRequest(requestId));
  }

  Future<void> declineRequest(String requestId) async {
    await _dio.post(FriendsApiPaths.declineRequest(requestId));
  }

  Future<void> cancelRequest(String requestId) async {
    await _dio.delete(FriendsApiPaths.cancelRequest(requestId));
  }

  Future<List<Friendship>> getFriends() async {
    final res = await _dio.get(FriendsApiPaths.friends);
    return (res.data as List<dynamic>)
        .map((e) => Friendship.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> unfriend(String userId) async {
    await _dio.delete(FriendsApiPaths.unfriend(userId));
  }

  Future<List<FriendSuggestion>> getSuggestions() async {
    final res = await _dio.get(FriendsApiPaths.suggestions);
    return (res.data as List<dynamic>)
        .map((e) => FriendSuggestion.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<AppUser>> searchUsers(String query) async {
    final res = await _dio.get(
      SocialApiPaths.searchUsers,
      queryParameters: {'q': query},
    );
    return (res.data as List<dynamic>)
        .map((e) => AppUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<int> getMutualFriendsCount(String userId) async {
    final res = await _dio.get(SocialApiPaths.mutualFriends(userId));
    final data = res.data as Map<String, dynamic>;
    return data['count'] as int? ?? 0;
  }

  Future<void> blockUser(String userId) async {
    await _dio.post(SocialApiPaths.blockUser(userId));
  }

  Future<void> unblockUser(String userId) async {
    await _dio.delete(SocialApiPaths.blockUser(userId));
  }

  Future<List<AppUser>> getBlockedUsers() async {
    final res = await _dio.get('/users/me/blocks');
    return (res.data as List<dynamic>)
        .map((e) => AppUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}