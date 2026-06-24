import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/features/auth/domain/usecases/request_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_otp_state.dart';

final loginOtpNotifierProvider =
    StateNotifierProvider<LoginOtpNotifier, LoginOtpState>((ref) {
  return LoginOtpNotifier(
    requestLoginOtpUseCase: getIt<RequestLoginOtpUseCase>(),
    verifyLoginOtpUseCase: getIt<VerifyLoginOtpUseCase>(),
    authNotifier: ref.read(authNotifierProvider.notifier),
  );
});