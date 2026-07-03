import 'package:gamer_circle/features/auth/data/models/auth_response_model.dart';

abstract interface class AuthRemoteDataSource {
  Future<void> requestLoginOtp({required String phone});

  Future<AuthResponseModel> verifyLoginOtp({
    required String phone,
    required String otp,
  });

  Future<AuthResponseModel> loginWithPassword({
    required String username,
    required String password,
  });

  Future<void> logout({required String refreshToken});

  Future<AuthResponseModel> refreshToken({required String refreshToken});

  Future<void> sendSignupOtp({
    required String name,
    required String username,
    required String email,
    required String phone,
  });

  Future<AuthResponseModel> verifySignupOtp({
    required String phone,
    required String otp,
    required String password,
  });
}