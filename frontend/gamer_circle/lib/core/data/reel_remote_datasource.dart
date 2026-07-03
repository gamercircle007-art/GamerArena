import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/reel_api_paths.dart';
import 'package:gamer_circle/shared/models/reel.dart';

class ReelRemoteDataSource {
  ReelRemoteDataSource(this._dio);
  final Dio _dio;

  Future<ReelFeedPage> fetchFeed({int page = 1, int limit = 10, String sort = 'trending'}) async {
    final res = await _dio.get(
      ReelApiPaths.feed,
      queryParameters: {'page': page, 'limit': limit, 'sort': sort},
    );
    return ReelFeedPage.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ReelFeedPage> searchReels({
    required String q,
    int page = 1,
    String sort = 'trending',
  }) async {
    final res = await _dio.get(
      ReelApiPaths.search,
      queryParameters: {'q': q, 'page': page, 'sort': sort},
    );
    return ReelFeedPage.fromJson(res.data as Map<String, dynamic>);
  }

  Future<Reel> createReel(Map<String, dynamic> body) async {
    final res = await _dio.post(ReelApiPaths.reels, data: body);
    return Reel.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> recordView(String reelId) async {
    await _dio.post(ReelApiPaths.reelView(reelId));
  }

  Future<Map<String, dynamic>> likeReel(String reelId) async {
    final res = await _dio.post(ReelApiPaths.reelLike(reelId));
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> unlikeReel(String reelId) async {
    final res = await _dio.delete(ReelApiPaths.reelLike(reelId));
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> bookmarkReel(String reelId) async {
    final res = await _dio.post(ReelApiPaths.reelBookmark(reelId));
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> shareReel(String reelId) async {
    final res = await _dio.post(ReelApiPaths.reelShare(reelId));
    return res.data as Map<String, dynamic>;
  }

  Future<List<ReelComment>> fetchComments(String reelId) async {
    final res = await _dio.get(ReelApiPaths.reelComments(reelId));
    return (res.data as List<dynamic>)
        .map((e) => ReelComment.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ReelComment> postComment(String reelId, String content, {String? parentId}) async {
    final res = await _dio.post(
      ReelApiPaths.reelComments(reelId),
      data: {
        'content': content,
        if (parentId != null) 'parent_id': parentId,
      },
    );
    return ReelComment.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<ReelComment>> fetchReplies(String commentId) async {
    final res = await _dio.get(ReelApiPaths.commentReplies(commentId));
    return (res.data as List<dynamic>)
        .map((e) => ReelComment.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Map<String, dynamic>> followUser(String userId) async {
    final res = await _dio.post(ReelApiPaths.followUser(userId));
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> unfollowUser(String userId) async {
    final res = await _dio.delete(ReelApiPaths.followUser(userId));
    return res.data as Map<String, dynamic>;
  }

  Future<void> reportReel(String reelId, String reason) async {
    await _dio.post(ReelApiPaths.reelReport(reelId), data: {'reason': reason});
  }

  Future<List<Map<String, dynamic>>> fetchDemoMusic() async {
    final res = await _dio.get(ReelApiPaths.demoMusic);
    return (res.data as List<dynamic>).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> likeComment(String commentId) async {
    final res = await _dio.post(ReelApiPaths.commentLike(commentId));
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> unlikeComment(String commentId) async {
    final res = await _dio.delete(ReelApiPaths.commentLike(commentId));
    return res.data as Map<String, dynamic>;
  }
}