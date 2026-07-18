import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/shell/presentation/widgets/app_drawer.dart';

class MainShellScaffold extends ConsumerWidget {
  const MainShellScaffold({super.key, required this.child});

  final Widget child;

  int _indexForLocation(String location) {
    if (location.startsWith('/profile')) return 5;
    if (location.startsWith('/messages')) return 4;
    if (location.startsWith('/gaming-bookings') ||
        location.startsWith('/my-bookings')) {
      return 3;
    }
    if (location.startsWith('/search-input') ||
        location.startsWith('/search-results')) {
      return 2;
    }
    if (location.startsWith('/feed') || location.startsWith('/reels')) return 1;
    return 0;
  }

  bool _shouldHideNavBar(String location) {
    return location.startsWith('/messages/chat') || location == '/messages/new';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = _indexForLocation(location);
    final hideNavBar = _shouldHideNavBar(location);
    final unreadMessages = ref.watch(unreadCountProvider);

    return Scaffold(
      drawer: hideNavBar ? null : const AppDrawer(),
      body: child,
      extendBody: true,
      bottomNavigationBar: hideNavBar
          ? null
          : Container(
              decoration: BoxDecoration(
                color: AppColors.surface,
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
                  child: Stack(
                    clipBehavior: Clip.none,
                    alignment: Alignment.bottomCenter,
                    children: [
                      // Base row of nav items (reserve center space for the +)
                      Positioned.fill(
                        child: Row(
                          children: [
                            Expanded(
                              child: _NavItem(
                                icon: Icons.home_rounded,
                                label: 'HOME',
                                selected: index == 0,
                                onTap: () => context.go('/'),
                              ),
                            ),
                            Expanded(
                              child: _NavItem(
                                icon: Icons.play_circle_outline_rounded,
                                label: 'REELS',
                                selected: index == 1,
                                onTap: () => context.go('/reels'),
                              ),
                            ),
                            Expanded(
                              child: _NavItem(
                                icon: Icons.search_rounded,
                                label: 'SEARCH',
                                selected: index == 2,
                                onTap: () => context.go('/search-input'),
                              ),
                            ),
                            const SizedBox(width: 56),
                            Expanded(
                              child: _NavItem(
                                icon: Icons.calendar_month_outlined,
                                label: 'BOOKING',
                                selected: index == 3,
                                onTap: () => context.go('/gaming-bookings'),
                              ),
                            ),
                            Expanded(
                              child: _NavItem(
                                icon: Icons.chat_bubble_outline_rounded,
                                label: 'MESSAGES',
                                selected: index == 4,
                                badgeCount: unreadMessages,
                                onTap: () => context.go('/messages'),
                              ),
                            ),
                            Expanded(
                              child: _NavItem(
                                icon: Icons.person_outline_rounded,
                                label: 'PROFILE',
                                selected: index == 5,
                                onTap: () => context.go('/profile'),
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Prominent + button in lower navbar (raised like YouTube/Instagram) for Post/Short/Video/Live
                      Positioned(
                        bottom: 12,
                        child: _PlusButton(
                          onTap: () => context.push('/create-post'),
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

/// Special + button placed in the lower navbar (YouTube-style) for adding posts, shorts, videos, live.
class _PlusButton extends StatelessWidget {
  const _PlusButton({required this.onTap, super.key});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: BoxDecoration(
          color: AppColors.primary,
          shape: BoxShape.circle,
          boxShadow: const [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 6,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: const Icon(
          Icons.add,
          color: Colors.white,
          size: 30,
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
    this.badgeCount = 0,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final int badgeCount;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.primary : AppColors.textSecondaryLight;

    return Expanded(
      child: InkWell(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(icon, color: color, size: 24),
                if (badgeCount > 0)
                  Positioned(
                    right: -10,
                    top: -6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.error,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      constraints: const BoxConstraints(minWidth: 16),
                      child: Text(
                        badgeCount > 99 ? '99+' : '$badgeCount',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 9,
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