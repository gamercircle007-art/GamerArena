import 'package:dio/dio.dart';
import 'package:gamer_circle/shared/models/home_data.dart';

class HomeRepository {
  HomeRepository(this._dio);

  final Dio _dio;

  Future<HomeData> fetchHomeData({
    double? lat,
    double? lng,
    String? city,
    HomeQuickPickFilter pickFilter = HomeQuickPickFilter.recommended,
    int? radiusMeters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/home',
        queryParameters: {
          if (city != null) 'city': city,
          if (lat != null) 'lat': lat,
          if (lng != null) 'lng': lng,
          if (radiusMeters != null) 'radius': radiusMeters,
          'pick_filter': pickFilter.apiValue,
        },
        cancelToken: cancelToken,
      );
      final raw = response.data ?? {};
      return HomeData.fromApi(raw);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return HomeData.empty;
      }
      rethrow;
    }
  }
}