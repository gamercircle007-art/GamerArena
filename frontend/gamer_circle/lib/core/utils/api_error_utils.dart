import 'package:dio/dio.dart';
import 'package:gamer_circle/app/config/app_config.dart';

/// Extract a user-facing message from API error responses.
///
/// Prefixed with stable codes (E_*) so logs/screenshots are AI-debuggable.
String messageFromDioException(DioException e, String fallback) {
  final base = AppConfig.instance.baseUrl;

  switch (e.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return 'E_API_TIMEOUT: Server not responding at $base. '
          'Render free tier may be cold/Failed — wait 60s or use password login.';
    case DioExceptionType.connectionError:
      return 'E_API_UNREACHABLE: Cannot reach $base. '
          'Check internet, or Render Dashboard (gamer-circle-api must be Live).';
    case DioExceptionType.badCertificate:
      return 'E_TLS: HTTPS certificate error talking to $base.';
    case DioExceptionType.cancel:
      return 'E_CANCELLED: Request was cancelled.';
    case DioExceptionType.badResponse:
    case DioExceptionType.unknown:
    default:
      break;
  }

  final status = e.response?.statusCode;
  final data = e.response?.data;
  if (data is Map) {
    final map = Map<String, dynamic>.from(data);
    final message = map['message']?.toString();
    final code = map['error']?.toString();
    if (message != null &&
        message.isNotEmpty &&
        message != 'Invalid request') {
      final prefix = code != null && code.isNotEmpty ? 'E_API_$code: ' : '';
      return '$prefix$message';
    }

    final details = map['details'];
    if (details is List && details.isNotEmpty) {
      final first = details.first;
      if (first is Map) {
        final field =
            first['loc'] is List ? (first['loc'] as List).last : null;
        final detail = first['msg']?.toString();
        if (field == 'password') {
          return 'E_VALIDATION: Password must be at least 6 characters and '
              'include uppercase, lowercase, and a number';
        }
        if (detail != null && detail.isNotEmpty) {
          return field != null && field != 'body'
              ? 'E_VALIDATION: $field: $detail'
              : 'E_VALIDATION: $detail';
        }
      }
    }
  }

  if (status != null) {
    return 'E_HTTP_$status: $fallback';
  }
  return 'E_UNKNOWN: $fallback';
}