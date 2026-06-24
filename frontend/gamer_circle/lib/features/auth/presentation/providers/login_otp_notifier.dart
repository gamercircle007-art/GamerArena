import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/auth/domain/usecases/request_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';

class LoginOtpNotifier extends StateNotifier<LoginOtpState> {
  final RequestLoginOtpUseCase _requestLoginOtpUseCase;
  final VerifyLoginOtpUseCase _verifyLoginOtpUseCase;
  final AuthNotifier _authNotifier;

  LoginOtpNotifier({
    required RequestLoginOtpUseCase requestLoginOtpUseCase,
    required VerifyLoginOtpUseCase verifyLoginOtpUseCase,
    required AuthNotifier authNotifier,
  })  : _requestLoginOtpUseCase = requestLoginOtpUseCase,
        _verifyLoginOtpUseCase = verifyLoginOtpUseCase,
        _authNotifier = authNotifier,
        super(const LoginOtpInitial());

  Future<void> requestOtp(String phone) async {
    state = const LoginOtpSending();
    final result = await _requestLoginOtpUseCase(
      RequestLoginOtpParams(phone: phone),
    );
    state = result.fold(
      (failure) => LoginOtpError(failure.message),
      (_) => LoginOtpSent(phone),
    );
  }

  Future<void> verifyOtp(String otp) async {
    final phone = switch (state) {
      LoginOtpSent(:final phone) => phone,
      LoginOtpError(:final phone?) => phone,
      _ => null,
    };

    if (phone == null) {
      state = const LoginOtpError('Session expired. Enter your phone again.');
      return;
    }

    state = LoginOtpVerifying(phone);
    final result = await _verifyLoginOtpUseCase(
      VerifyLoginOtpParams(phone: phone, otp: otp),
    );

    result.fold(
      (failure) => state = LoginOtpError(failure.message, phone: phone),
      (user) {
        _authNotifier.setAuthenticated(user);
        state = const LoginOtpInitial();
      },
    );
  }

  void reset() => state = const LoginOtpInitial();
}