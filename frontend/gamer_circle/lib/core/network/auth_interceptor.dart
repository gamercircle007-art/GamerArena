import 'dart:async';

import 'package:dio/dio.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/core/constants/auth_api_paths.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/data/models/user_model.dart';

/// Attaches Bearer access tokens and silently refreshes on 401.
///
/// Access JWTs expire in ~30 minutes on the API. Without refresh, screens like
/// Messages show raw DioException 401 while the UI still thinks the user is
/// logged in (cached local session).
class AuthInterceptor extends Interceptor {
  AuthInterceptor(this._localDataSource);

  final AuthLocalDataSource _localDataSource;

  /// Wired by [AuthNotifier] so UI returns to login when refresh fails.
  void Function()? onUnauthorized;

  /// Set by [DioClient] after the main Dio instance is created (for retries).
  Dio? dio;

  /// Bare client for refresh — avoids interceptor recursion.
  late final Dio _refreshDio = Dio(
    BaseOptions(
      baseUrl: AppConfig.instance.baseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 20),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  Completer<bool>? _refreshLock;

  static const _noRefreshPaths = <String>{
    AuthApiPaths.login,
    AuthApiPaths.loginRequestOtp,
    AuthApiPaths.loginVerifyOtp,
    AuthApiPaths.signupRequestOtp,
    AuthApiPaths.signupVerifyOtp,
    AuthApiPaths.refreshToken,
    AuthApiPaths.logout,
  };

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _localDataSource.getAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401) {
      handler.next(err);
      return;
    }

    final path = err.requestOptions.path;
    if (_noRefreshPaths.any(path.contains)) {
      handler.next(err);
      return;
    }

    // Already retried once — don't loop.
    if (err.requestOptions.extra['auth_retried'] == true) {
      await _forceLogout();
      handler.next(err);
      return;
    }

    final refreshed = await _refreshTokens();
    if (!refreshed || dio == null) {
      await _forceLogout();
      handler.next(err);
      return;
    }

    try {
      final token = await _localDataSource.getAccessToken();
      final req = err.requestOptions;
      req.headers['Authorization'] = 'Bearer $token';
      req.extra['auth_retried'] = true;
      final response = await dio!.fetch<dynamic>(req);
      handler.resolve(response);
    } catch (e) {
      if (e is DioException) {
        handler.next(e);
      } else {
        handler.next(err);
      }
    }
  }

  Future<bool> _refreshTokens() async {
    if (_refreshLock != null) {
      return _refreshLock!.future;
    }
    final lock = Completer<bool>();
    _refreshLock = lock;

    try {
      final refresh = await _localDataSource.getRefreshToken();
      if (refresh == null || refresh.isEmpty) {
        lock.complete(false);
        return false;
      }

      final res = await _refreshDio.post<Map<String, dynamic>>(
        AuthApiPaths.refreshToken,
        data: {'refresh_token': refresh},
      );
      final data = res.data;
      if (data == null) {
        lock.complete(false);
        return false;
      }

      final access = data['access_token'] as String?;
      final newRefresh = data['refresh_token'] as String?;
      if (access == null || newRefresh == null) {
        lock.complete(false);
        return false;
      }

      await _localDataSource.saveAccessToken(access);
      await _localDataSource.saveRefreshToken(newRefresh);

      final userJson = data['user'];
      if (userJson is Map<String, dynamic>) {
        await _localDataSource.saveUser(UserModel.fromJson(userJson));
      }

      lock.complete(true);
      return true;
    } catch (_) {
      lock.complete(false);
      return false;
    } finally {
      _refreshLock = null;
    }
  }

  Future<void> _forceLogout() async {
    await _localDataSource.clearAll();
    onUnauthorized?.call();
  }
}
