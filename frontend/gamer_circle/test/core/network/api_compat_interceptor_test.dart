import 'package:flutter_test/flutter_test.dart';
import 'package:gamer_circle/core/network/api_compat_interceptor.dart';

void main() {
  group('ApiCompatInterceptor.canonicalizePath', () {
    test('strips duplicated /api/v1 prefix', () {
      expect(
        ApiCompatInterceptor.canonicalizePath('/api/v1/posts'),
        '/posts',
      );
      expect(
        ApiCompatInterceptor.canonicalizePath('/api/v1/api/v1/posts'),
        '/posts',
      );
    });

    test('rewrites clubs availability to parlors', () {
      expect(
        ApiCompatInterceptor.canonicalizePath(
          '/clubs/abc-123/availability',
        ),
        '/parlors/abc-123/availability',
      );
    });

    test('leaves absolute upload URLs alone', () {
      const url = 'https://cdn.example.com/upload';
      expect(ApiCompatInterceptor.canonicalizePath(url), url);
    });

    test('leaves canonical parlor paths alone', () {
      expect(
        ApiCompatInterceptor.canonicalizePath('/parlors/abc/availability'),
        '/parlors/abc/availability',
      );
    });
  });
}
