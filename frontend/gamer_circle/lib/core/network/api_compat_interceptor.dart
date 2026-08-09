import 'package:dio/dio.dart';

/// Canonicalizes client paths so the whole app hits live API routes.
///
/// Root causes this prevents:
/// 1. Accidental `/api/v1/...` when [BaseOptions.baseUrl] already ends with `/api/v1`
///    → double prefix → FastAPI 404
/// 2. Spec alias `/clubs/{id}/...` when production only mounts `/parlors/{id}/...`
///    (or clubs alias not yet deployed) → 404 on booking times, etc.
class ApiCompatInterceptor extends Interceptor {
  static final _clubsResource = RegExp(r'^/clubs/([^/]+)(/.*)?$');

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.path = canonicalizePath(options.path);
    handler.next(options);
  }

  /// Pure helper — also used by tests / call sites.
  static String canonicalizePath(String path) {
    var p = path.trim();
    if (p.isEmpty) return p;

    // Absolute URLs (presigned S3, CDN) — leave alone.
    if (p.startsWith('http://') || p.startsWith('https://')) return p;

    // Strip duplicated API prefix.
    while (p.startsWith('/api/v1/')) {
      p = p.substring('/api/v1'.length);
    }
    if (p == '/api/v1') p = '/';

    // Consumer booking/discovery: clubs == gaming_places == parlors on this API.
    final m = _clubsResource.firstMatch(p);
    if (m != null) {
      final id = m.group(1)!;
      final rest = m.group(2) ?? '';
      p = '/parlors/$id$rest';
    }

    return p;
  }
}
