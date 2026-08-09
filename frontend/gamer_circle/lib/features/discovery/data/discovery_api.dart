import 'dart:async';

import 'package:dio/dio.dart';
import 'package:gamer_circle/features/discovery/data/centre_summary.dart';
import 'package:gamer_circle/features/discovery/presentation/filter_state.dart';

class DiscoveryApi {
  DiscoveryApi(this._dio);

  final Dio _dio;
  CancelToken? _searchToken;

  Future<DiscoveryPage> fetchCentres({
    required double lat,
    required double lng,
    required FilterState filters,
    String? cursor,
  }) async {
    // Cancel prior search keystroke request
    _searchToken?.cancel('superseded');
    _searchToken = CancelToken();

    final q = filters.query.trim();
    final response = await _dio.get<Map<String, dynamic>>(
      '/discovery/centres',
      queryParameters: {
        'lat': lat,
        'lng': lng,
        'radius_m': filters.radiusM,
        'sort': filters.sort,
        'limit': 20,
        if (cursor != null) 'cursor': cursor,
        if (q.length >= 2) 'q': q,
        if (filters.minRating != null) 'min_rating': filters.minRating,
        if (filters.availableNow) 'available_now': true,
        if (filters.amenitiesMask != 0) 'amenities_mask': filters.amenitiesMask,
      },
      options: Options(
        receiveTimeout: const Duration(seconds: 6),
        sendTimeout: const Duration(seconds: 4),
        headers: {
          if (filters.etag != null) 'If-None-Match': '"${filters.etag}"',
        },
        validateStatus: (s) => s != null && (s < 400 || s == 304),
      ),
      cancelToken: _searchToken,
    );

    if (response.statusCode == 304) {
      return DiscoveryPage(items: const [], nextCursor: null, radiusM: filters.radiusM);
    }
    final data = response.data ?? {};
    return DiscoveryPage.fromJson(data);
  }
}
