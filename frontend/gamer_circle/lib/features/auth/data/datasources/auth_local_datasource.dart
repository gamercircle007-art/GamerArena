import 'package:gamer_circle/features/auth/data/models/user_model.dart';

abstract interface class AuthLocalDataSource {
  Future<void> saveAccessToken(String token);
  Future<void> saveRefreshToken(String token);
  Future<String?> getAccessToken();
  Future<String?> getRefreshToken();
  Future<void> deleteTokens();

  Future<void> saveUser(UserModel user);
  Future<UserModel?> getCachedUser();
  Future<void> deleteUser();

  Future<bool> hasValidToken();
  Future<void> clearAll();
}
