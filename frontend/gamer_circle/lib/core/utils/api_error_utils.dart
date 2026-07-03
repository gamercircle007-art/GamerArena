import 'package:dio/dio.dart';

/// Extract a user-facing message from Paythan API error responses.
String messageFromDioException(DioException e, String fallback) {
  final data = e.response?.data;
  if (data is! Map<String, dynamic>) return fallback;

  final message = data['message'];
  if (message is String && message.isNotEmpty && message != 'Invalid request') {
    return message;
  }

  final details = data['details'];
  if (details is List && details.isNotEmpty) {
    final first = details.first;
    if (first is Map<String, dynamic>) {
      final field = first['loc'] is List ? (first['loc'] as List).last : null;
      final detail = first['msg']?.toString();
      if (field == 'password') {
        return 'Password must be at least 6 characters and include '
            'uppercase, lowercase, and a number';
      }
      if (detail != null && detail.isNotEmpty) {
        return field != null && field != 'body' ? '$field: $detail' : detail;
      }
    }
  }

  return fallback;
}