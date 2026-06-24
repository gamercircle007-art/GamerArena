import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/data/models/user_model.dart';

class AuthLocalDataSourceImpl implements AuthLocalDataSource {
  final FlutterSecureStorage _storage;

  static const _kAccessToken = 'auth_access_token';
  static const _kRefreshToken = 'auth_refresh_token';
  static const _kUser = 'auth_cached_user';

  const AuthLocalDataSourceImpl(this._storage);

  @override
  Future<void> saveAccessToken(String token) async {
    try {
      await _storage.write(key: _kAccessToken, value: token);
    } catch (_) {
      throw CacheException(message: 'Failed to save access token');
    }
  }

  @override
  Future<void> saveRefreshToken(String token) async {
    try {
      await _storage.write(key: _kRefreshToken, value: token);
    } catch (_) {
      throw CacheException(message: 'Failed to save refresh token');
    }
  }

  @override
  Future<String?> getAccessToken() async {
    try {
      return await _storage.read(key: _kAccessToken);
    } catch (_) {
      throw CacheException(message: 'Failed to read access token');
    }
  }

  @override
  Future<String?> getRefreshToken() async {
    try {
      return await _storage.read(key: _kRefreshToken);
    } catch (_) {
      throw CacheException(message: 'Failed to read refresh token');
    }
  }

  @override
  Future<void> deleteTokens() async {
    try {
      await Future.wait([
        _storage.delete(key: _kAccessToken),
        _storage.delete(key: _kRefreshToken),
      ]);
    } catch (_) {
      throw CacheException(message: 'Failed to delete tokens');
    }
  }

  @override
  Future<void> saveUser(UserModel user) async {
    try {
      await _storage.write(key: _kUser, value: jsonEncode(user.toJson()));
    } catch (_) {
      throw CacheException(message: 'Failed to save user');
    }
  }

  @override
  Future<UserModel?> getCachedUser() async {
    try {
      final raw = await _storage.read(key: _kUser);
      if (raw == null) return null;
      return UserModel.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      throw CacheException(message: 'Failed to read cached user');
    }
  }

  @override
  Future<void> deleteUser() async {
    try {
      await _storage.delete(key: _kUser);
    } catch (_) {
      throw CacheException(message: 'Failed to delete user');
    }
  }

  @override
  Future<bool> hasValidToken() async {
    try {
      final token = await _storage.read(key: _kAccessToken);
      return token != null && token.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> clearAll() async {
    try {
      await Future.wait([
        _storage.delete(key: _kAccessToken),
        _storage.delete(key: _kRefreshToken),
        _storage.delete(key: _kUser),
      ]);
    } catch (_) {
      throw CacheException(message: 'Failed to clear auth data');
    }
  }
}
