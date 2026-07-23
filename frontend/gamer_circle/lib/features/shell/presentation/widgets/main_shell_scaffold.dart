import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/shell/presentation/widgets/app_drawer.dart';

class MainShellScaffold extends ConsumerWidget {
  const MainShellScaffold({super.key, required this.child});

  final Widget child;

  static const _tabs = <_ShellTab>[
    _ShellTab(
      path: '/',
      icon: Icons.home_outlined,
      selectedIcon: Icons.home_rounded,
      label: 'HOME',
    ),
    _ShellTab(
      path: '/reels',
      icon: Icons.play_circle_outline_rounded,
      selectedIcon: Icons.play_circle_rounded,
      label: 'REELS',
    ),
    _ShellTab(
      path: '/search-input',
      icon: Icons.search_rounded,
      selectedIcon: Icons.search_rounded,
      label: 'SEARCH',
    ),
    _ShellTab(
      path: '/gaming-bookings',
      icon: Icons.calendar_month_outlined,
      selectedIcon: Icons.calendar_month,
      label: 'BOOKING',
    ),
    _ShellTab(
      path: '/messages',
      icon: Icons.chat_bubble_outline_rounded,
      selectedIcon: Icons.chat_bubble_rounded,
      label: 'MESSAGES',
    ),
    _ShellTab(
      path: '/profile',
      icon: Icons.person_outline_rounded,
      selectedIcon: Icons.person_rounded,
      label: 'PROFILE',
    ),
  ];

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

  void _goTab(BuildContext context, String path) {
    final current = GoRouterState.of(context).matchedLocation;
    if (path == '/') {
      if (current == '/' || current == '/home-booking') return;
      context.go('/');
      return;
    }
    if (current == path) return;
    context.go(path);
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
          : Material(
              color: AppColors.surface,
              elevation: 8,
              shadowColor: Colors.black26,
              child: SafeArea(
                top: false,
                child: SizedBox(
                  height: 64,
                  child: Stack(
                    clipBehavior: Clip.none,
                    alignment: Alignment.bottomCenter,
                    children: [
                      Positioned.fill(
                        child: Row(
                          children: [
                            for (var i = 0; i < 3; i++)
                              Expanded(
                                child: _NavItem(
                                  icon: index == i
                                      ? _tabs[i].selectedIcon
                                      : _tabs[i].icon,
                                  label: _tabs[i].label,
                                  selected: index == i,
                                  onTap: () => _goTab(context, _tabs[i].path),
                                ),
                              ),
                            const SizedBox(width: 56),
                            for (var i = 3; i < 6; i++)
                              Expanded(
                                child: _NavItem(
                                  icon: index == i
                                      ? _tabs[i].selectedIcon
                                      : _tabs[i].icon,
                                  label: _tabs[i].label,
                                  selected: index == i,
                                  badgeCount:
                                      i == 4 ? unreadMessages : 0,
                                  onTap: () => _goTab(context, _tabs[i].path),
                                ),
                              ),
                          ],
                        ),
                      ),
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

class _ShellTab {
  const _ShellTab({
    required this.path,
    required this.icon,
    required this.selectedIcon,
    required this.label,
  });

  final String path;
  final IconData icon;
  final IconData selectedIcon;
  final String label;
}

/// Raised + control for Post / Short / Video / Live.
class _PlusButton extends StatelessWidget {
  const _PlusButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.primary,
      shape: const CircleBorder(),
      elevation: 4,
      shadowColor: Colors.black38,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: const SizedBox(
          width: 52,
          height: 52,
          child: Icon(Icons.add, color: Colors.white, size: 30),
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

    // Parent Row already wraps each item in Expanded.
    // Fill the entire cell so taps are reliable on small screens.
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        child: SizedBox.expand(
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
                        padding: const EdgeInsets.symmetric(
                          horizontal: 5,
                          vertical: 1,
                        ),
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
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  color: color,
                  letterSpacing: 0.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
