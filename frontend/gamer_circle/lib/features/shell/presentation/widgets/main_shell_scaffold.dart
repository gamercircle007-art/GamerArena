import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';

class MainShellScaffold extends ConsumerWidget {
  const MainShellScaffold({super.key, required this.child});

  final Widget child;

  int _indexForLocation(String location) {
    if (location.startsWith('/events')) return 4;
    if (location.startsWith('/store')) return 3;
    if (location.startsWith('/feed') || location.startsWith('/reels')) return 1;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = _indexForLocation(location);

    return Scaffold(
      body: child,
      extendBody: true,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 12,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: SizedBox(
            height: 64,
            child: Row(
              children: [
                _NavItem(
                  icon: Icons.home_rounded,
                  label: 'HOME',
                  selected: index == 0,
                  onTap: () => context.go('/'),
                ),
                _NavItem(
                  icon: Icons.workspace_premium_outlined,
                  label: 'PRIME',
                  selected: index == 1,
                  onTap: () => context.go('/feed'),
                ),
                Expanded(
                  child: Center(
                    child: _PayBillButton(
                      onTap: () => context.push('/search-input'),
                    ),
                  ),
                ),
                _NavItem(
                  icon: Icons.credit_card_outlined,
                  label: 'CARD',
                  selected: index == 3,
                  onTap: () => context.go('/store'),
                ),
                _NavItem(
                  icon: Icons.confirmation_number_outlined,
                  label: 'EVENTS',
                  selected: index == 4,
                  badge: 'NEW!',
                  onTap: () => context.go('/events'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
    this.badge,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final String? badge;

  @override
  Widget build(BuildContext context) {
    final color = selected ? OnboardingColors.primary : OnboardingColors.textMuted;

    return Expanded(
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  icon,
                  color: color,
                  size: 24,
                ),
                if (badge != null)
                  Positioned(
                    right: -18,
                    top: -8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: OnboardingColors.payBillRed,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        badge!,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 7,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: color,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PayBillButton extends StatelessWidget {
  const _PayBillButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Transform.translate(
      offset: const Offset(0, -16),
      child: Material(
        color: OnboardingColors.payBillRed,
        shape: const CircleBorder(),
        elevation: 6,
        shadowColor: OnboardingColors.payBillRed.withOpacity(0.4),
        child: InkWell(
          onTap: onTap,
          customBorder: const CircleBorder(),
          child: const SizedBox(
            width: 56,
            height: 56,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.receipt_long, color: Colors.white, size: 22),
                SizedBox(height: 2),
                Text(
                  'Pay Bill',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 8,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}