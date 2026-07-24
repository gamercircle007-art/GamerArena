import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

class AppDrawer extends ConsumerWidget {
  const AppDrawer({super.key});

  Future<void> _onLogout(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Log out?'),
        content: const Text('You will need to sign in again to continue.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
            ),
            child: const Text('Log out'),
          ),
        ],
      ),
    );

    if (confirmed != true || !context.mounted) return;

    Navigator.pop(context);
    await ref.read(authNotifierProvider.notifier).logout();
  }

  void _navigate(BuildContext context, String path) {
    Navigator.pop(context);
    if (GoRouterState.of(context).matchedLocation != path) {
      context.go(path);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final isLoggingOut = authState is AuthLoading;

    final username = switch (authState) {
      AuthAuthenticated(:final user) => user.username,
      _ => 'Gamer',
    };
    final email = switch (authState) {
      AuthAuthenticated(:final user) => user.email,
      _ => '',
    };

    return Drawer(
      backgroundColor: AppColors.surface,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [AppColors.primary, AppColors.secondary],
                ),
              ),
              child: Row(
                children: [
                  Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.white.withOpacity(0.2),
                      border: Border.all(color: Colors.white, width: 2),
                    ),
                    child: Center(
                      child: Text(
                        username.isNotEmpty
                            ? username[0].toUpperCase()
                            : 'G',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          username,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (email.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          Text(
                            email,
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.85),
                              fontSize: 13,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  _DrawerTile(
                    icon: Icons.home_outlined,
                    label: 'Home',
                    onTap: () => _navigate(context, '/'),
                  ),
                  _DrawerTile(
                    icon: Icons.dynamic_feed_outlined,
                    label: 'Feed',
                    onTap: () => _navigate(context, '/feed'),
                  ),
                  _DrawerTile(
                    icon: Icons.map_outlined,
                    label: 'Discover',
                    onTap: () => _navigate(context, '/discover'),
                  ),
                  _DrawerTile(
                    icon: Icons.notifications_outlined,
                    label: 'Notifications',
                    onTap: () => _navigate(context, '/notifications'),
                  ),
                  _DrawerTile(
                    icon: Icons.chat_bubble_outline,
                    label: 'Messages',
                    onTap: () => _navigate(context, '/messages'),
                  ),
                  _DrawerTile(
                    icon: Icons.person_outline,
                    label: 'Profile',
                    onTap: () => _navigate(context, '/profile'),
                  ),
                  _DrawerTile(
                    icon: Icons.event_seat_outlined,
                    label: 'My Bookings',
                    onTap: () => _navigate(context, '/gaming-bookings'),
                  ),
                  _DrawerTile(
                    icon: Icons.bookmark_outline,
                    label: 'Saved',
                    onTap: () => _navigate(context, '/saved'),
                  ),
                  _DrawerTile(
                    icon: Icons.storefront_outlined,
                    label: 'Store',
                    onTap: () => _navigate(context, '/store'),
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                    child: Divider(color: AppColors.borderLight),
                  ),
                  _DrawerTile(
                    icon: Icons.groups_outlined,
                    label: 'Communities',
                    onTap: () => _navigate(context, '/communities'),
                  ),
                  _DrawerTile(
                    icon: Icons.event_outlined,
                    label: 'Events',
                    onTap: () => _navigate(context, '/events'),
                  ),
                  _DrawerTile(
                    icon: Icons.settings_outlined,
                    label: 'Settings',
                    onTap: () => _navigate(context, '/settings'),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: AppColors.borderLight),
            ListTile(
              leading: isLoggingOut
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.logout, color: AppColors.error),
              title: Text(
                isLoggingOut ? 'Logging out...' : 'Log out',
                style: const TextStyle(
                  color: AppColors.error,
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: isLoggingOut ? null : () => _onLogout(context, ref),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}

class _DrawerTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _DrawerTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(
        label,
        style: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w500,
          color: AppColors.textPrimaryLight,
        ),
      ),
      onTap: onTap,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
    );
  }
}