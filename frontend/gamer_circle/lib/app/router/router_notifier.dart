import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/location/domain/usecases/check_location_onboarding_usecase.dart';
import 'package:gamer_circle/features/onboarding/data/onboarding_prefs.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;

  bool? _onboardingCompleted;
  bool? _permissionsCompleted;

  RouterNotifier(this._ref) {
    _loadPrefs();
    _ref.listen<AuthState>(
      authNotifierProvider,
      (_, __) => notifyListeners(),
    );
  }

  Future<void> _loadPrefs() async {
    final prefs = getIt<OnboardingPrefs>();
    _onboardingCompleted = await prefs.isOnboardingCompleted();

    final permResult =
        await getIt<CheckLocationOnboardingUseCase>()(NoParams());
    _permissionsCompleted = permResult.fold((_) => true, (v) => v);

    notifyListeners();
  }

  Future<void> refreshOnboardingState() async {
    await _loadPrefs();
  }

  bool _isOnboardingRoute(String location) =>
      location == '/onboarding' ||
      location == '/mobile-number' ||
      location == '/mobile-otp' ||
      location == '/permissions';

  bool _isAuthRoute(String location) => location.startsWith('/login');

  bool _isProtectedRoute(String location) =>
      location.startsWith('/profile') ||
      location.startsWith('/messages/chat') ||
      location == '/messages/new' ||
      location.startsWith('/my-bookings') ||
      location.startsWith('/gaming-bookings') ||
      location.startsWith('/owner-dashboard') ||
      location.startsWith('/create-post') ||
      location.startsWith('/create-reel') ||
      location.startsWith('/create-tournament') ||
      location.startsWith('/admin');

  String? redirect(BuildContext context, GoRouterState state) {
    final authState = _ref.read(authNotifierProvider);
    final location = state.matchedLocation;

    if (authState is AuthInitial || authState is AuthLoading) return null;
    if (_onboardingCompleted == null || _permissionsCompleted == null) {
      return null;
    }

    if (!_onboardingCompleted! && !_isOnboardingRoute(location)) {
      return '/onboarding';
    }

    if (_onboardingCompleted! &&
        (location == '/onboarding' || location == '/mobile-number')) {
      return '/';
    }

    return switch (authState) {
      AuthAuthenticated() => _redirectAuthenticated(location),
      AuthGuest() => _redirectGuest(location),
      AuthUnauthenticated() => _redirectUnauthenticated(location),
      AuthError() =>
        _isOnboardingRoute(location) ? null : '/onboarding',
      _ => null,
    };
  }

  String? _redirectAuthenticated(String location) {
    if (!_permissionsCompleted! &&
        location != '/permissions' &&
        location != '/mobile-otp') {
      return '/permissions';
    }

    if (location.startsWith('/login') ||
        location == '/onboarding' ||
        location == '/mobile-number') {
      return '/';
    }

    return null;
  }

  String? _redirectGuest(String location) {
    if (location == '/onboarding' || location == '/mobile-number') {
      return '/';
    }
    if (_isAuthRoute(location)) return null;
    if (_isProtectedRoute(location)) return '/login';
    return null;
  }

  String? _redirectUnauthenticated(String location) {
    if (_isOnboardingRoute(location) || _isAuthRoute(location)) return null;

    if (_isProtectedRoute(location)) {
      return '/login';
    }

    return null;
  }
}

final routerNotifierProvider = ChangeNotifierProvider<RouterNotifier>(
  (ref) => RouterNotifier(ref),
);