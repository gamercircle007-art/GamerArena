import 'package:dio/dio.dart';
import 'package:gamer_circle/shared/models/home_data.dart';

class HomeRepository {
  HomeRepository(this._dio);

  final Dio _dio;

  Future<HomeData> fetchHomeData({
    double? lat,
    double? lng,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/home',
        queryParameters: {
          if (lat != null) 'lat': lat,
          if (lng != null) 'lng': lng,
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