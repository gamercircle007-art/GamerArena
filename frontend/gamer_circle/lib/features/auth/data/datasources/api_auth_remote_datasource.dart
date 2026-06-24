import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/auth_api_paths.dart';
import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/core/utils/phone_utils.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/models/auth_response_model.dart';

class ApiAuthRemoteDataSource implements AuthRemoteDataSource {
  final Dio _dio;

  ApiAuthRemoteDataSource(this._dio);

  String _messageFromResponse(DioException e, String fallback) {
    final data = e.response?.data;
    if (data is Map<String, dynamic>) {
      final message = data['message'];
      if (message is String && message.isNotEmpty) return message;
    }
    return fallback;
  }

  @override
  Future<void> requestLoginOtp({required String phone}) async {
    try {
      await _dio.post(
        AuthApiPaths.loginRequestOtp,
        data: {'phone_number': normalizePhoneNumber(phone)},
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw AuthException(message: 'No account found for this phone number');
      }
      throw ServerException(
        message: _messageFromResponse(e, 'Failed to send login OTP'),
        statusCode: e.response?.statusCode,
      );
    }
  }

  @override
  Future<AuthResponseModel> verifyLoginOtp({
    required String phone,
    required String otp,
  }) async {
    try {
      final response = await _dio.post(
        AuthApiPaths.loginVerifyOtp,
        data: {
          'phone_number': normalizePhoneNumber(phone),
          'otp': otp,
        },
      );
      return AuthResponseModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthException(message: 'Invalid OTP. Please try again.');
      }
      throw ServerException(
        message: _messageFromResponse(e, 'Login verification failed'),
        statusCode: e.response?.statusCode,
      );
    }
  }

  @override
  Future<void> logout({required String refreshToken}) async {
    try {
      await _dio.post(
        AuthApiPaths.logout,
        data: {'refresh_token': refreshToken},
      );
    } on DioException catch (e) {
      throw ServerException(
        message: _messageFromResponse(e, 'Logout failed'),
        statusCode: e.response?.statusCode,
      );
    }
  }

  @override
  Future<AuthResponseModel> refreshToken({required String refreshToken}) async {
    try {
      final response = await _dio.post(
        AuthApiPaths.refreshToken,
        data: {'refresh_token': refreshToken},
      );
      return AuthResponseModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthException(message: 'Session expired, please log in again');
      }
      throw ServerException(
        message: _messageFromResponse(e, 'Token refresh failed'),
        statusCode: e.response?.statusCode,
      );
    }
  }

  @override
  Future<void> sendSignupOtp({
    required String name,
    required String email,
    required String phone,
  }) async {
    try {
      await _dio.post(
        AuthApiPaths.signupRequestOtp,
        data: {
          'name': name,
          'email': email,
          'phone_number': normalizePhoneNumber(phone),
        },
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        throw AuthException(
          message: 'An account with this phone or email already exists',
        );
      }
      throw ServerException(
        message: _messageFromResponse(e, 'Failed to send OTP'),
        statusCode: e.response?.statusCode,
      );
    }
  }

  @override
  Future<AuthResponseModel> verifySignupOtp({
    required String phone,
    required String otp,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        AuthApiPaths.signupVerifyOtp,
        data: {
          'phone_number': normalizePhoneNumber(phone),
          'otp': otp,
          'password': password,
        },
      );
      return AuthResponseModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthException(message: 'Invalid OTP. Please try again.');
      }
      throw ServerException(
        message: _messageFromResponse(e, 'OTP verification failed'),
        statusCode: e.response?.statusCode,
      );
    }
  }
}