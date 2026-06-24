import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/features/auth/domain/usecases/send_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_otp_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/signup_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/signup_state.dart';

final signUpNotifierProvider =
    StateNotifierProvider<SignUpNotifier, SignUpState>((ref) {
  return SignUpNotifier(
    sendOtpUseCase: getIt<SendOtpUseCase>(),
    verifyOtpUseCase: getIt<VerifyOtpUseCase>(),
    authNotifier: ref.read(authNotifierProvider.notifier),
  );
});
