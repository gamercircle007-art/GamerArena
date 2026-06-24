import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/auth/domain/usecases/send_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_otp_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/signup_state.dart';

class SignUpNotifier extends StateNotifier<SignUpState> {
  final SendOtpUseCase _sendOtpUseCase;
  final VerifyOtpUseCase _verifyOtpUseCase;
  final AuthNotifier _authNotifier;

  SignUpNotifier({
    required SendOtpUseCase sendOtpUseCase,
    required VerifyOtpUseCase verifyOtpUseCase,
    required AuthNotifier authNotifier,
  })  : _sendOtpUseCase = sendOtpUseCase,
        _verifyOtpUseCase = verifyOtpUseCase,
        _authNotifier = authNotifier,
        super(const SignUpInitial());

  Future<void> sendOtp({
    required String name,
    required String email,
    required String phone,
    required String password,
  }) async {
    state = const SignUpLoading();
    final result = await _sendOtpUseCase(
      SendOtpParams(name: name, email: email, phone: phone),
    );
    state = result.fold(
      (failure) => SignUpError(failure.message),
      (_) => OtpSent(phone, password),
    );
  }

  Future<void> verifyOtp(String otp) async {
    final current = switch (state) {
      OtpSent(:final phone, :final password) => (phone, password),
      _ => null,
    };

    if (current == null) {
      state = const SignUpError('Session expired. Please sign up again.');
      return;
    }

    state = const OtpVerifying();
    final result = await _verifyOtpUseCase(
      VerifyOtpParams(
        phone: current.$1,
        otp: otp,
        password: current.$2,
      ),
    );

    result.fold(
      (failure) => state = SignUpError(failure.message),
      (user) {
        _authNotifier.setAuthenticated(user);
        state = const SignUpInitial();
      },
    );
  }

  void reset() => state = const SignUpInitial();
}