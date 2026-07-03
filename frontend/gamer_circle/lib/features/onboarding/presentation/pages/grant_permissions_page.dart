import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/core/services/push_notification_service.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/app/router/router_notifier.dart';
import 'package:gamer_circle/features/location/domain/usecases/accept_location_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/skip_location_usecase.dart';
import 'package:gamer_circle/features/onboarding/data/onboarding_prefs.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/onboarding_primary_button.dart';

class GrantPermissionsPage extends ConsumerStatefulWidget {
  const GrantPermissionsPage({super.key});

  @override
  ConsumerState<GrantPermissionsPage> createState() =>
      _GrantPermissionsPageState();
}

class _GrantPermissionsPageState extends ConsumerState<GrantPermissionsPage> {
  bool _isLoading = false;

  Future<void> _onContinue() async {
    setState(() => _isLoading = true);

    final locationResult = await getIt<AcceptLocationUseCase>()(NoParams());
    locationResult.fold(
      (_) async => await getIt<SkipLocationUseCase>()(NoParams()),
      (_) {},
    );

    await PushNotificationService.instance.requestPermission();

    await getIt<OnboardingPrefs>().setOnboardingCompleted(value: true);
    await ref.read(routerNotifierProvider).refreshOnboardingState();

    if (mounted) {
      setState(() => _isLoading = false);
      context.go('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 32),
              const _PermissionsIllustration(),
              const SizedBox(height: 32),
              const Text(
                'Grant Permissions',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: OnboardingColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                height: 1,
                color: OnboardingColors.border,
              ),
              const SizedBox(height: 24),
              const _PermissionTile(
                icon: Icons.location_on_rounded,
                title: 'Location Services',
                description:
                    'Helps us suggest the best restaurants near you',
              ),
              const SizedBox(height: 20),
              const _PermissionTile(
                icon: Icons.notifications_rounded,
                title: 'Notifications',
                description:
                    "We'll inform you about your bookings and ongoing offers",
              ),
              const Spacer(),
              OnboardingPrimaryButton(
                label: 'Continue',
                isLoading: _isLoading,
                onPressed: _isLoading ? null : _onContinue,
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

class _PermissionsIllustration extends StatelessWidget {
  const _PermissionsIllustration();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 180,
      width: double.infinity,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 160,
            height: 120,
            decoration: BoxDecoration(
              color: OnboardingColors.primary,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: OnboardingColors.primary.withOpacity(0.25),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            transform: Matrix4.rotationZ(-0.08),
            child: CustomPaint(painter: _MapFoldPainter()),
          ),
          const Positioned(
            top: 24,
            child: _BadgeIcon(icon: Icons.location_on, size: 36),
          ),
          const Positioned(
            top: 16,
            right: 80,
            child: _BadgeIcon(icon: Icons.verified_user, size: 28),
          ),
          const Positioned(
            left: 72,
            top: 72,
            child: _BadgeIcon(icon: Icons.lock_outline, size: 26),
          ),
          const Positioned(
            right: 68,
            bottom: 36,
            child: _BadgeIcon(icon: Icons.settings, size: 26),
          ),
        ],
      ),
    );
  }
}

class _MapFoldPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawLine(
      Offset(size.width * 0.33, 0),
      Offset(size.width * 0.33, size.height),
      paint,
    );
    canvas.drawLine(
      Offset(size.width * 0.66, 0),
      Offset(size.width * 0.66, size.height),
      paint,
    );
    canvas.drawLine(
      Offset(0, size.height * 0.5),
      Offset(size.width, size.height * 0.5),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _BadgeIcon extends StatelessWidget {
  const _BadgeIcon({required this.icon, required this.size});

  final IconData icon;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size + 16,
      height: size + 16,
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Icon(icon, color: OnboardingColors.primary, size: size * 0.55),
    );
  }
}

class _PermissionTile extends StatelessWidget {
  const _PermissionTile({
    required this.icon,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: const BoxDecoration(
            color: OnboardingColors.permissionIconBg,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: OnboardingColors.primary, size: 24),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: OnboardingColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 14,
                  color: OnboardingColors.textSecondary,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}