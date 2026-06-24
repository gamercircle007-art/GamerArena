import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;

  RouterNotifier(this._ref) {
    _ref.listen<AuthState>(
      authNotifierProvider,
      (_, __) => notifyListeners(),
    );
  }

  String? redirect(BuildContext context, GoRouterState state) {
    final authState = _ref.read(authNotifierProvider);
    // All auth-related routes are nested under /login
    final isAuthRoute = state.matchedLocation.startsWith('/login');

    return switch (authState) {
      AuthInitial() => null,
      AuthLoading() => null,
      AuthAuthenticated() => isAuthRoute ? '/' : null,
      AuthUnauthenticated() => isAuthRoute ? null : '/login',
      AuthError() => isAuthRoute ? null : '/login',
    };
  }
}

final routerNotifierProvider = ChangeNotifierProvider<RouterNotifier>(
  (ref) => RouterNotifier(ref),
);
