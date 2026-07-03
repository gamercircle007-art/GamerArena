import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/social_api_paths.dart';
import 'package:gamer_circle/shared/models/booking.dart';
import 'package:gamer_circle/shared/models/comment.dart';
import 'package:gamer_circle/shared/models/nearby_parlor.dart';
import 'package:gamer_circle/shared/models/parlor_search_response.dart';
import 'package:gamer_circle/shared/models/notification.dart';
import 'package:gamer_circle/shared/models/parlor.dart';
import 'package:gamer_circle/shared/models/post.dart';
import 'package:gamer_circle/shared/models/tournament.dart';

class SocialRemoteDataSource {
  SocialRemoteDataSource(this._dio);
  final Dio _dio;

  Future<List<dynamic>> fetchFeed({required int page, int limit = 20}) async {
    final res = await _dio.get(
      SocialApiPaths.feed,
      queryParameters: {'page': page, 'limit': limit},
    );
    return (res.data['items'] as List<dynamic>? ?? []);
  }

  Future<List<Map<String, dynamic>>> fetchStoreCatalog() async {
    final res = await _dio.get(SocialApiPaths.store);
    final items = res.data['items'] as List<dynamic>? ?? [];
    return items.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Post> fetchPost(String id) async {
    final res = await _dio.get(SocialApiPaths.post(id));
    return Post.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Post> createPost(Map<String, dynamic> body) async {
    final res = await _dio.post(SocialApiPaths.posts, data: body);
    return Post.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Post>> fetchParlorPosts(String parlorId, {int page = 1}) async {
    final res = await _dio.get(
      SocialApiPaths.parlorPosts(parlorId),
      queryParameters: {'page': page, 'limit': 20},
    );
    return (res.data as List<dynamic>)
        .map((e) => Post.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Tournament> fetchTournament(String id) async {
    final res = await _dio.get(SocialApiPaths.tournament(id));
    return Tournament.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Tournament> createTournament(Map<String, dynamic> body) async {
    final res = await _dio.post(SocialApiPaths.tournaments, data: body);
    return Tournament.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Booking> bookSlot(String tournamentId) async {
    final res = await _dio.post(SocialApiPaths.bookTournament(tournamentId));
    return Booking.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Booking>> fetchMyBookings({bool? upcoming}) async {
    final res = await _dio.get(
      SocialApiPaths.myBookings,
      queryParameters: upcoming == null ? null : {'upcoming': upcoming},
    );
    return (res.data as List<dynamic>)
        .map((e) => Booking.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Comment>> fetchComments(String postId) async {
    final res = await _dio.get(SocialApiPaths.postComments(postId));
    return (res.data as List<dynamic>)
        .map((e) => Comment.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Comment> addComment(String postId, String content, {String? parentId}) async {
    final res = await _dio.post(
      SocialApiPaths.postComments(postId),
      data: {'content': content, if (parentId != null) 'parent_id': parentId},
    );
    return Comment.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Parlor> fetchParlor(String id) async {
    final res = await _dio.get(SocialApiPaths.parlor(id));
    return Parlor.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Parlor>> fetchFollowing() async {
    final res = await _dio.get(SocialApiPaths.myFollowing);
    return (res.data as List<dynamic>)
        .map((e) => Parlor.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> followParlor(String parlorId) async {
    await _dio.post(SocialApiPaths.follows, data: {'parlor_id': parlorId});
  }

  Future<void> unfollowParlor(String parlorId) async {
    await _dio.delete(SocialApiPaths.unfollow(parlorId));
  }

  Future<void> like(String type, String id) async {
    await _dio.post(SocialApiPaths.likes, data: {'target_type': type, 'target_id': id});
  }

  Future<void> unlike(String type, String id) async {
    await _dio.delete(SocialApiPaths.unlike(type, id));
  }

  Future<List<AppNotification>> fetchNotifications({bool? isRead}) async {
    final res = await _dio.get(
      SocialApiPaths.notifications,
      queryParameters: isRead == null ? null : {'is_read': isRead},
    );
    return (res.data as List<dynamic>)
        .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<int> unreadCount() async {
    final res = await _dio.get(SocialApiPaths.notificationsUnread);
    return res.data['count'] as int? ?? 0;
  }

  Future<void> markRead(String id) async {
    await _dio.put(SocialApiPaths.notificationRead(id));
  }

  Future<List<NearbyParlor>> nearbyParlors({
    required double lat,
    required double lng,
    double radius = 5000,
    String? gameType,
  }) async {
    final res = await _dio.get(
      SocialApiPaths.nearbyParlors,
      queryParameters: {
        'lat': lat,
        'lng': lng,
        'radius': radius,
        if (gameType != null) 'game_type': gameType,
      },
    );
    return (res.data as List<dynamic>)
        .map((e) => NearbyParlor.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ParlorSearchResponse> searchParlors({
    required double lat,
    required double lng,
    double radius = 5000,
    String? q,
    double? minRating,
    bool? openNow,
    String? city,
    String? state,
    String? gameType,
    int page = 1,
    int limit = 20,
    CancelToken? cancelToken,
  }) async {
    final res = await _dio.get(
      SocialApiPaths.searchParlors,
      queryParameters: {
        'lat': lat,
        'lng': lng,
        'radius': radius,
        'page': page,
        'limit': limit,
        if (q != null && q.isNotEmpty) 'q': q,
        if (minRating != null) 'min_rating': minRating,
        if (openNow == true) 'open_now': true,
        if (city != null && city.isNotEmpty) 'city': city,
        if (state != null && state.isNotEmpty) 'state': state,
        if (gameType != null && gameType.isNotEmpty) 'game_type': gameType,
      },
      cancelToken: cancelToken,
    );
    return ParlorSearchResponse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> uploadToPresignedUrl({
    required String uploadUrl,
    required List<int> bytes,
    required String contentType,
  }) async {
    await _dio.put(
      uploadUrl,
      data: bytes,
      options: Options(
        headers: {'Content-Type': contentType},
        contentType: contentType,
      ),
    );
  }

  Future<Map<String, dynamic>> presignedUrl(String fileType, String purpose) async {
    final res = await _dio.post(
      SocialApiPaths.presignedUrl,
      data: {'file_type': fileType, 'purpose': purpose},
    );
    return res.data as Map<String, dynamic>;
  }

  Future<List<Tournament>> fetchParlorTournaments(String parlorId) async {
    final res = await _dio.get(SocialApiPaths.parlorTournaments(parlorId));
    return (res.data as List<dynamic>)
        .map((e) => Tournament.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> fetchAnalytics() async {
    final res = await _dio.get(SocialApiPaths.parlorAnalytics);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> fetchRazorpayConfig() async {
    final res = await _dio.get(SocialApiPaths.razorpayConfig);
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createBookingPaymentOrder(String bookingId) async {
    final res = await _dio.post(SocialApiPaths.bookingPaymentOrder(bookingId));
    return res.data as Map<String, dynamic>;
  }

  Future<Booking> verifyBookingPayment(
    String bookingId, {
    required String orderId,
    required String paymentId,
    required String signature,
  }) async {
    final res = await _dio.post(
      SocialApiPaths.bookingPaymentVerify(bookingId),
      data: {
        'order_id': orderId,
        'payment_id': paymentId,
        'signature': signature,
      },
    );
    return Booking.fromJson(res.data as Map<String, dynamic>);
  }
}