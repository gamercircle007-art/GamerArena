import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/models/auth_response_model.dart';
import 'package:gamer_circle/features/auth/data/models/user_model.dart';

class MockAuthRemoteDataSource implements AuthRemoteDataSource {
  static const _testPhone = '9876543210';
  static const _mockOtp = '123456';

  static final Map<String, _PendingRegistration> _pendingRegistrations = {};

  @override
  Future<void> requestLoginOtp({required String phone}) async {
    await Future.delayed(const Duration(milliseconds: 800));
    if (phone != _testPhone) {
      throw AuthException(message: 'No account found for this phone number');
    }
  }

  @override
  Future<AuthResponseModel> verifyLoginOtp({
    required String phone,
    required String otp,
  }) async {
    await Future.delayed(const Duration(milliseconds: 800));

    if (otp != _mockOtp) {
      throw AuthException(message: 'Invalid OTP. Please try again.');
    }
    if (phone != _testPhone) {
      throw AuthException(message: 'No account found for this phone number');
    }

    return AuthResponseModel(
      accessToken: 'mock_access_token_login_${phone.hashCode}',
      refreshToken: 'mock_refresh_token_login_${phone.hashCode}',
      user: const UserModel(
        id: 'mock-user-001',
        email: 'test@gamercircle.com',
        name: 'TestGamer',
        phoneNumber: _testPhone,
      ),
    );
  }

  @override
  Future<void> logout({required String refreshToken}) async {
    await Future.delayed(const Duration(milliseconds: 300));
  }

  @override
  Future<AuthResponseModel> refreshToken({required String refreshToken}) async {
    throw AuthException(message: 'Token refresh not supported in mock');
  }

  @override
  Future<void> sendSignupOtp({
    required String name,
    required String email,
    required String phone,
  }) async {
    await Future.delayed(const Duration(milliseconds: 800));
    _pendingRegistrations[phone] = _PendingRegistration(
      name: name,
      email: email,
      phone: phone,
    );
  }

  @override
  Future<AuthResponseModel> verifySignupOtp({
    required String phone,
    required String otp,
    required String password,
  }) async {
    await Future.delayed(const Duration(milliseconds: 800));

    if (otp != _mockOtp) {
      throw AuthException(message: 'Invalid OTP. Please try again.');
    }

    final registration = _pendingRegistrations[phone];
    if (registration == null) {
      throw AuthException(message: 'Session expired. Please sign up again.');
    }

    _pendingRegistrations.remove(phone);

    return AuthResponseModel(
      accessToken: 'mock_access_token_${phone.hashCode}',
      refreshToken: 'mock_refresh_token_${phone.hashCode}',
      user: UserModel(
        id: 'mock-user-${phone.hashCode}',
        email: registration.email,
        name: registration.name,
        phoneNumber: registration.phone,
      ),
    );
  }
}

class _PendingRegistration {
  final String name;
  final String email;
  final String phone;
  const _PendingRegistration({
    required this.name,
    required this.email,
    required this.phone,
  });
}