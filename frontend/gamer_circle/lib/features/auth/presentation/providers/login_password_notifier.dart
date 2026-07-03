import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/auth/domain/usecases/login_with_password_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/login_password_state.dart';

class LoginPasswordNotifier extends StateNotifier<LoginPasswordState> {
  final LoginWithPasswordUseCase _loginWithPasswordUseCase;
  final AuthNotifier _authNotifier;

  LoginPasswordNotifier({
    required LoginWithPasswordUseCase loginWithPasswordUseCase,
    required AuthNotifier authNotifier,
  })  : _loginWithPasswordUseCase = loginWithPasswordUseCase,
        _authNotifier = authNotifier,
        super(const LoginPasswordInitial());

  Future<void> login({
    required String username,
    required String password,
  }) async {
    state = const LoginPasswordLoading();
    final result = await _loginWithPasswordUseCase(
      LoginWithPasswordParams(username: username, password: password),
    );

    result.fold(
      (failure) => state = LoginPasswordError(failure.message),
      (user) {
        _authNotifier.setAuthenticated(user);
        state = const LoginPasswordInitial();
      },
    );
  }

  void reset() => state = const LoginPasswordInitial();
}