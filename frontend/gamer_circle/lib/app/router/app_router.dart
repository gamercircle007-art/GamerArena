import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/router/router_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/pages/login_page.dart';
import 'package:gamer_circle/features/auth/presentation/pages/otp_verification_page.dart';
import 'package:gamer_circle/features/auth/presentation/pages/signup_page.dart';
import 'package:gamer_circle/features/feed/presentation/pages/feed_page.dart';
import 'package:gamer_circle/features/profile/presentation/pages/profile_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final notifier = ref.watch(routerNotifierProvider);
  return GoRouter(
    initialLocation: '/login',
    refreshListenable: notifier,
    redirect: notifier.redirect,
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginPage(),
        routes: [
          GoRoute(
            path: 'signup',
            builder: (context, state) => const SignUpPage(),
            routes: [
              GoRoute(
                path: 'verify-otp',
                builder: (context, state) => const OtpVerificationPage(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => const FeedPage(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfilePage(),
      ),
    ],
  );
});
