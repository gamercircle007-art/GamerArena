import 'package:dio/dio.dart';
import 'package:gamer_circle/app/config/app_config.dart';

/// Lightweight prod connectivity check (uses /health, not /api/v1).
class ApiStatusService {
  ApiStatusService({Dio? dio}) : _dio = dio ?? Dio();

  final Dio _dio;

  /// Origin without trailing /api/v1.
  static String get apiOrigin {
    final base = AppConfig.instance.baseUrl;
    if (base.endsWith('/api/v1')) {
      return base.substring(0, base.length - '/api/v1'.length);
    }
    return base;
  }

  Future<ApiStatusResult> check({Duration timeout = const Duration(seconds: 12)}) async {
    final url = '$apiOrigin/health';
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        url,
        options: Options(
          sendTimeout: timeout,
          receiveTimeout: timeout,
          responseType: ResponseType.json,
        ),
      );
      final data = res.data ?? {};
      return ApiStatusResult(
        ok: res.statusCode == 200,
        code: 'E_OK',
        message: 'API Live (${data['service'] ?? 'ok'})',
        detail: data.toString(),
        url: url,
      );
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.sendTimeout) {
        return ApiStatusResult(
          ok: false,
          code: 'E_API_TIMEOUT',
          message:
              'Server not responding. Render gamer-circle-api may be Failed/cold.',
          detail: e.message,
          url: url,
        );
      }
      if (e.type == DioExceptionType.connectionError) {
        return ApiStatusResult(
          ok: false,
          code: 'E_API_UNREACHABLE',
          message: 'Cannot reach $url',
          detail: e.message,
          url: url,
        );
      }
      return ApiStatusResult(
        ok: false,
        code: 'E_HTTP_${e.response?.statusCode ?? 'ERR'}',
        message: e.message ?? 'API health failed',
        detail: e.response?.data?.toString(),
        url: url,
      );
    } catch (e) {
      return ApiStatusResult(
        ok: false,
        code: 'E_UNKNOWN',
        message: e.toString(),
        url: url,
      );
    }
  }
}

class ApiStatusResult {
  const ApiStatusResult({
    required this.ok,
    required this.code,
    required this.message,
    this.detail,
    this.url,
  });

  final bool ok;
  final String code;
  final String message;
  final String? detail;
  final String? url;

  String get display => ok ? message : '$code: $message';
}
