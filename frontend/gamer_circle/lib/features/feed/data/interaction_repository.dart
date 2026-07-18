import 'package:dio/dio.dart';

/// Interaction + ranked feed API client per ALG-FL02
class InteractionRepository {
  final Dio _dio;

  InteractionRepository(this._dio);

  Future<void> track({
    required String contentId,
    required String contentType,
    required String action,
    int? viewDurationMs,
    String? source,
    int? positionInFeed,
    double? userLat,
    double? userLng,
  }) async {
    try {
      await _dio.post('/interactions/track', data: {
        'content_type': contentType,
        'content_id': contentId,
        'action': action,
        if (viewDurationMs != null) 'view_duration_ms': viewDurationMs,
        if (source != null) 'source': source,
        if (positionInFeed != null) 'position_in_feed': positionInFeed,
        if (userLat != null) 'user_lat': userLat,
        if (userLng != null) 'user_lng': userLng,
      });
    } catch (_) {
      // fire-and-forget: never break UI
    }
  }

  Future<Map<String, dynamic>> getRankedFeed({
    String feedType = 'home',
    int page = 1,
    int limit = 20,
    double? lat,
    double? lng,
  }) async {
    final res = await _dio.get('/feed/ranked', queryParameters: {
      'feed_type': feedType,
      'page': page,
      'limit': limit,
      if (lat != null) 'lat': lat,
      if (lng != null) 'lng': lng,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getReelsFeed({int page = 1, int limit = 20}) async {
    final res = await _dio.get('/feed/reels', queryParameters: {'page': page, 'limit': limit});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getTrending({String window = '6h', String? gameType}) async {
    final res = await _dio.get('/feed/trending', queryParameters: {
      'window': window,
      if (gameType != null) 'game_type': gameType,
    });
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getDiscover({int page = 1, int limit = 20}) async {
    final res = await _dio.get('/feed/discover', queryParameters: {'page': page, 'limit': limit});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getMyInterests() async {
    final res = await _dio.get('/users/me/interests');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> smartSearch(String q, {int limit = 20}) async {
    final res = await _dio.get('/search/smart', queryParameters: {'q': q, 'limit': limit});
    return res.data as Map<String, dynamic>;
  }
}
