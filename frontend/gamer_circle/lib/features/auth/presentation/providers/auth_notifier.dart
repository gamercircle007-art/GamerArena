import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/usecases/check_auth_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/logout_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

class AuthNotifier extends StateNotifier<AuthState> {
  final LogoutUseCase _logoutUseCase;
  final CheckAuthUseCase _checkAuthUseCase;

  AuthNotifier({
    required LogoutUseCase logoutUseCase,
    required CheckAuthUseCase checkAuthUseCase,
  })  : _logoutUseCase = logoutUseCase,
        _checkAuthUseCase = checkAuthUseCase,
        super(const AuthInitial()) {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    state = const AuthLoading();
    final result = await _checkAuthUseCase(NoParams());
    state = result.fold(
      (_) => const AuthUnauthenticated(),
      (user) => AuthAuthenticated(user),
    );
  }

  Future<void> logout() async {
    state = const AuthLoading();
    final result = await _logoutUseCase(NoParams());
    state = result.fold(
      (failure) => AuthError(failure.message),
      (_) => const AuthUnauthenticated(),
    );
  }

  void setAuthenticated(User user) => state = AuthAuthenticated(user);
}