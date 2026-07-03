import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

class ProfileMenuButton extends ConsumerWidget {
  const ProfileMenuButton({
    super.key,
    required this.displayName,
  });

  final String displayName;

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
              backgroundColor: OnboardingColors.primary,
            ),
            child: const Text('Log out'),
          ),
        ],
      ),
    );

    if (confirmed != true || !context.mounted) return;

    await ref.read(authNotifierProvider.notifier).logout();

    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Logged out successfully'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      context.go('/');
    }
  }

  void _requireLogin(BuildContext context, WidgetRef ref, String destination) {
    final auth = ref.read(authNotifierProvider);
    if (auth is AuthGuest || auth is AuthUnauthenticated) {
      showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Login required'),
          content: Text(
            'Please sign in to access ${destination.toLowerCase()}.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.pop(ctx);
                context.go('/mobile-number');
              },
              style: FilledButton.styleFrom(
                backgroundColor: OnboardingColors.primary,
              ),
              child: const Text('Login'),
            ),
          ],
        ),
      );
      return;
    }
    context.push(destination);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider);
    final isGuest = auth is AuthGuest || auth is AuthUnauthenticated;
    final isLoggingOut = auth is AuthLoading;
    final initial =
        displayName.isNotEmpty ? displayName[0].toUpperCase() : 'G';

    return PopupMenuButton<_ProfileMenuAction>(
      offset: const Offset(0, 44),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      onSelected: (action) {
        switch (action) {
          case _ProfileMenuAction.login:
            context.go('/mobile-number');
          case _ProfileMenuAction.profileSettings:
            if (isGuest) {
              _requireLogin(context, ref, 'Profile Settings');
            } else {
              context.push('/settings');
            }
          case _ProfileMenuAction.saved:
            if (isGuest) {
              _requireLogin(context, ref, 'Saved');
            } else {
              context.push('/saved');
            }
          case _ProfileMenuAction.myProfile:
            if (isGuest) {
              _requireLogin(context, ref, 'Profile');
            } else {
              context.push('/profile');
            }
          case _ProfileMenuAction.logout:
            _onLogout(context, ref);
        }
      },
      itemBuilder: (context) => [
        PopupMenuItem(
          enabled: false,
          height: 48,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                displayName,
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 14,
                  color: OnboardingColors.textPrimary,
                ),
              ),
              Text(
                isGuest ? 'Guest account' : 'Signed in',
                style: const TextStyle(
                  fontSize: 12,
                  color: OnboardingColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        const PopupMenuDivider(),
        if (isGuest)
          const PopupMenuItem(
            value: _ProfileMenuAction.login,
            child: _MenuRow(
              icon: Icons.login,
              label: 'Login',
              color: OnboardingColors.primary,
            ),
          ),
        const PopupMenuItem(
          value: _ProfileMenuAction.profileSettings,
          child: _MenuRow(
            icon: Icons.settings_outlined,
            label: 'Profile Settings',
          ),
        ),
        const PopupMenuItem(
          value: _ProfileMenuAction.saved,
          child: _MenuRow(
            icon: Icons.bookmark_outline,
            label: 'Saved',
          ),
        ),
        if (!isGuest) ...[
          const PopupMenuItem(
            value: _ProfileMenuAction.myProfile,
            child: _MenuRow(
              icon: Icons.person_outline,
              label: 'My Profile',
            ),
          ),
          const PopupMenuDivider(),
          PopupMenuItem(
            value: _ProfileMenuAction.logout,
            enabled: !isLoggingOut,
            child: _MenuRow(
              icon: Icons.logout,
              label: isLoggingOut ? 'Logging out...' : 'Logout',
              color: OnboardingColors.payBillRed,
            ),
          ),
        ],
      ],
      child: CircleAvatar(
        radius: 16,
        backgroundColor: OnboardingColors.textPrimary,
        child: Text(
          initial,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 13,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

enum _ProfileMenuAction {
  login,
  profileSettings,
  saved,
  myProfile,
  logout,
}

class _MenuRow extends StatelessWidget {
  const _MenuRow({
    required this.icon,
    required this.label,
    this.color = OnboardingColors.textPrimary,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: color),
        const SizedBox(width: 12),
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: color,
          ),
        ),
      ],
    );
  }
}