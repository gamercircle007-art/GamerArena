import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/features/auth/domain/usecases/login_with_password_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_password_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_password_state.dart';

final loginPasswordNotifierProvider =
    StateNotifierProvider<LoginPasswordNotifier, LoginPasswordState>((ref) {
  return LoginPasswordNotifier(
    loginWithPasswordUseCase: getIt<LoginWithPasswordUseCase>(),
    authNotifier: ref.read(authNotifierProvider.notifier),
  );
});