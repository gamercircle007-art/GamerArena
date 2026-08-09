import 'package:dio/dio.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/core/constants/app_constants.dart';
import 'package:gamer_circle/core/network/api_compat_interceptor.dart';
import 'package:gamer_circle/core/network/auth_interceptor.dart';

class DioClient {
  late final Dio _dio;

  DioClient({AuthInterceptor? authInterceptor}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.instance.baseUrl,
        connectTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
        receiveTimeout: const Duration(milliseconds: AppConstants.apiTimeout),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Path rewrite FIRST so auth + logs see the final route.
    final interceptors = <Interceptor>[
      ApiCompatInterceptor(),
    ];
    if (AppConfig.instance.enableHttpLogs) {
      interceptors.add(
        LogInterceptor(
          request: true,
          requestBody: true,
          responseBody: true,
          error: true,
        ),
      );
    }
    if (authInterceptor != null) {
      authInterceptor.dio = _dio;
      interceptors.add(authInterceptor);
    }
    _dio.interceptors.addAll(interceptors);
  }

  Dio get dio => _dio;
}
