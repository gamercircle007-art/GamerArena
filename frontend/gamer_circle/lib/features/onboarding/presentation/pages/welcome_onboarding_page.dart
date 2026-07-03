import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/app/router/router_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/continue_as_guest_button.dart';
import 'package:gamer_circle/features/onboarding/presentation/widgets/onboarding_primary_button.dart';

class WelcomeOnboardingPage extends ConsumerWidget {
  const WelcomeOnboardingPage({super.key});

  Future<void> _continueAsGuest(BuildContext context, WidgetRef ref) async {
    await ref.read(authNotifierProvider.notifier).continueAsGuest();
    await ref.read(routerNotifierProvider).refreshOnboardingState();
    if (context.mounted) context.go('/');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: OnboardingColors.welcomeGradient,
        ),
        child: SafeArea(
          child: Stack(
            children: [
              const _ConcentricCircles(),
              const _FloatingIcons(),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  children: [
                    const SizedBox(height: 8),
                    ContinueAsGuestButton(
                      pillStyle: true,
                      onPressed: () => _continueAsGuest(context, ref),
                    ),
                    const Spacer(flex: 2),
                    const Text(
                      'Book exclusive\nevents',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.w800,
                        height: 1.15,
                        color: OnboardingColors.primary,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const Spacer(flex: 3),
                    OnboardingPrimaryButton(
                      label: 'Get Started',
                      onPressed: () => context.go('/mobile-number'),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConcentricCircles extends StatelessWidget {
  const _ConcentricCircles();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: CustomPaint(
        size: const Size(400, 400),
        painter: _CirclePainter(),
      ),
    );
  }
}

class _CirclePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    for (var i = 4; i >= 1; i--) {
      final paint = Paint()
        ..color = OnboardingColors.primary.withOpacity(0.03 * i)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1;
      canvas.drawCircle(center, 40.0 * i * 1.8, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _FloatingIcons extends StatelessWidget {
  const _FloatingIcons();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final w = constraints.maxWidth;
        final h = constraints.maxHeight;
        return Stack(
          children: [
            _IconBubble(
              left: w * 0.06,
              top: h * 0.14,
              size: 52,
              emoji: '🪩',
              rotation: -0.15,
            ),
            _IconBubble(
              right: w * 0.05,
              top: h * 0.12,
              size: 48,
              emoji: '🎫',
              rotation: 0.2,
            ),
            _IconBubble(
              left: w * 0.22,
              top: h * 0.22,
              size: 40,
              emoji: '🏷️',
              rotation: -0.1,
            ),
            _IconBubble(
              right: w * 0.18,
              top: h * 0.28,
              size: 44,
              emoji: '⚡',
              rotation: 0.15,
            ),
            _IconBubble(
              left: w * 0.08,
              top: h * 0.42,
              size: 46,
              emoji: '🍾',
              rotation: 0.1,
            ),
            _IconBubble(
              right: w * 0.06,
              top: h * 0.44,
              size: 42,
              emoji: '🎁',
              rotation: -0.2,
            ),
            _IconBubble(
              left: w * 0.28,
              bottom: h * 0.28,
              size: 48,
              emoji: '📍',
              rotation: 0.05,
            ),
            _IconBubble(
              right: w * 0.2,
              bottom: h * 0.26,
              size: 46,
              emoji: '☕',
              rotation: -0.12,
            ),
            _IconBubble(
              left: w * 0.42,
              bottom: h * 0.22,
              size: 50,
              emoji: '🍽️',
              rotation: 0.08,
            ),
          ],
        );
      },
    );
  }
}

class _IconBubble extends StatelessWidget {
  const _IconBubble({
    this.left,
    this.right,
    this.top,
    this.bottom,
    required this.size,
    required this.emoji,
    this.rotation = 0,
  });

  final double? left;
  final double? right;
  final double? top;
  final double? bottom;
  final double size;
  final String emoji;
  final double rotation;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      right: right,
      top: top,
      bottom: bottom,
      child: Transform.rotate(
        angle: rotation * math.pi,
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: Colors.white,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.08),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          alignment: Alignment.center,
          child: Text(emoji, style: TextStyle(fontSize: size * 0.45)),
        ),
      ),
    );
  }
}