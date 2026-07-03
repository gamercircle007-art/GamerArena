import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/user_api_paths.dart';
import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/features/location/data/datasources/location_remote_datasource.dart';

class ApiLocationRemoteDataSource implements LocationRemoteDataSource {
  final Dio _dio;

  ApiLocationRemoteDataSource(this._dio);

  @override
  Future<void> uploadLocation({
    required double latitude,
    required double longitude,
    String? city,
    String? country,
  }) async {
    try {
      await _dio.patch(
        UserApiPaths.updateLocation,
        data: {
          'latitude': latitude,
          'longitude': longitude,
          if (city != null) 'city': city,
          if (country != null) 'country': country,
        },
      );
    } on DioException catch (e) {
      final data = e.response?.data;
      final message = data is Map<String, dynamic>
          ? data['message'] as String?
          : null;
      throw ServerException(
        message: message ?? 'Failed to save location',
        statusCode: e.response?.statusCode,
      );
    }
  }
}