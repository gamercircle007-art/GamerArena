import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/features/auth/domain/usecases/check_auth_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/logout_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/sync_location_usecase.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/onboarding/data/onboarding_prefs.dart';

final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(
    logoutUseCase: getIt<LogoutUseCase>(),
    checkAuthUseCase: getIt<CheckAuthUseCase>(),
    syncLocationUseCase: getIt<SyncLocationUseCase>(),
    onboardingPrefs: getIt<OnboardingPrefs>(),
  );
});