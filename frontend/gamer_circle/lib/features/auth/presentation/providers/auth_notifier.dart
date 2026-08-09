import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/network/auth_interceptor.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/usecases/check_auth_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/logout_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/location/domain/usecases/skip_location_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/sync_location_usecase.dart';
import 'package:gamer_circle/features/onboarding/data/onboarding_prefs.dart';

class AuthNotifier extends StateNotifier<AuthState> {
  final LogoutUseCase _logoutUseCase;
  final CheckAuthUseCase _checkAuthUseCase;
  final SyncLocationUseCase _syncLocationUseCase;
  final OnboardingPrefs _onboardingPrefs;

  AuthNotifier({
    required LogoutUseCase logoutUseCase,
    required CheckAuthUseCase checkAuthUseCase,
    required SyncLocationUseCase syncLocationUseCase,
    required OnboardingPrefs onboardingPrefs,
  })  : _logoutUseCase = logoutUseCase,
        _checkAuthUseCase = checkAuthUseCase,
        _syncLocationUseCase = syncLocationUseCase,
        _onboardingPrefs = onboardingPrefs,
        super(const AuthInitial()) {
    // When refresh fails, interceptor clears tokens — mirror that in UI state.
    getIt<AuthInterceptor>().onUnauthorized = onSessionExpired;
    checkAuthStatus();
  }

  void onSessionExpired() {
    WsService.instance.disconnect();
    if (state is AuthUnauthenticated) return;
    state = const AuthUnauthenticated();
  }

  Future<void> _syncCachedLocation() async {
    await _syncLocationUseCase(NoParams());
  }

  Future<void> checkAuthStatus() async {
    state = const AuthLoading();
    final result = await _checkAuthUseCase(NoParams());
    await result.fold(
      (_) async {
        if (await _onboardingPrefs.isGuestMode()) {
          state = const AuthGuest();
        } else {
          state = const AuthUnauthenticated();
        }
      },
      (user) async {
        await _onboardingPrefs.clearGuestMode();
        await _onboardingPrefs.setOnboardingCompleted(value: true);
        state = AuthAuthenticated(user);
        _syncCachedLocation();
      },
    );
  }

  Future<void> logout() async {
    state = const AuthLoading();
    await WsService.instance.disconnect();
    final result = await _logoutUseCase(NoParams());
    await result.fold(
      (failure) async {
        state = AuthError(failure.message);
      },
      (_) async {
        await _onboardingPrefs.clearGuestMode();
        state = const AuthUnauthenticated();
      },
    );
  }

  void setAuthenticated(User user) {
    _onboardingPrefs.clearGuestMode();
    state = AuthAuthenticated(user);
    _syncCachedLocation();
  }

  Future<void> continueAsGuest() async {
    await getIt<SkipLocationUseCase>()(NoParams());
    await _onboardingPrefs.enterGuestMode();
    state = const AuthGuest();
  }

}