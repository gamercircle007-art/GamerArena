import 'package:dio/dio.dart';
import 'package:gamer_circle/shared/models/parlour_detail.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

class ParlorSearchRepository {
  ParlorSearchRepository(this._dio);

  final Dio _dio;

  Future<ParlourSearchResponse> searchParlours({
    required double lat,
    required double lng,
    ParlourSearchFilters filters = const ParlourSearchFilters(),
    int page = 1,
    int limit = 20,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/parlors/search',
        queryParameters: {
          'lat': lat,
          'lng': lng,
          'page': page,
          'limit': limit,
          if (filters.query.isNotEmpty) 'q': filters.query,
          if (filters.city != null) 'city': filters.city,
          if (filters.checkIn != null)
            'check_in': filters.checkIn!.toIso8601String().split('T').first,
          if (filters.checkOut != null)
            'check_out': filters.checkOut!.toIso8601String().split('T').first,
          'num_players': filters.numPlayers,
          if (filters.minPrice != null) 'min_price': filters.minPrice,
          if (filters.maxPrice != null) 'max_price': filters.maxPrice,
          if (filters.minRating != null) 'min_rating': filters.minRating,
          if (filters.gameType != null) 'game_type': filters.gameType,
          'sort_by': filters.sortBy,
          'radius': filters.radiusMeters,
          if (filters.under299) 'under_299': true,
        },
        cancelToken: cancelToken,
      );
      return ParlourSearchResponse.fromJson(response.data ?? {});
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return const ParlourSearchResponse(
          items: [],
          total: 0,
          page: 1,
          limit: 20,
          hasMore: false,
        );
      }
      rethrow;
    }
  }

  Future<ParlourDetail> fetchParlourDetail(
    String parlourId, {
    double? lat,
    double? lng,
    CancelToken? cancelToken,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/parlors/$parlourId/detail',
      queryParameters: {
        if (lat != null) 'lat': lat,
        if (lng != null) 'lng': lng,
      },
      cancelToken: cancelToken,
    );
    return ParlourDetail.fromJson(response.data ?? {});
  }

  Future<List<ParlourReview>> fetchReviews(
    String parlourId, {
    int page = 1,
    int limit = 20,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<dynamic>(
        '/parlors/$parlourId/ratings',
        queryParameters: {'page': page, 'limit': limit},
        cancelToken: cancelToken,
      );
      final data = response.data;
      final items = data is Map
          ? (data['reviews'] as List<dynamic>? ??
              data['items'] as List<dynamic>? ??
              [])
          : (data as List<dynamic>? ?? []);
      return items
          .map((e) => ParlourReview.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return [];
      rethrow;
    }
  }
}