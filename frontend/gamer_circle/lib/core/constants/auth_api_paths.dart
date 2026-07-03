/// Central auth API path config — change endpoints here only.
class AuthApiPaths {
  AuthApiPaths._();

  // Login
  static const String loginRequestOtp = '/auth/login/request-otp';
  static const String loginVerifyOtp = '/auth/login/verify-otp';
  static const String login = '/auth/login';

  // Signup (OTP + password)
  static const String signupRequestOtp = '/auth/signup/request-otp';
  static const String signupVerifyOtp = '/auth/signup/verify-otp';

  // Session
  static const String logout = '/auth/logout';
  static const String refreshToken = '/auth/refresh-token';
  static const String me = '/auth/me';
}