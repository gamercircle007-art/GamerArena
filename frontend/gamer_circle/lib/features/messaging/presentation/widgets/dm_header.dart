import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';

/// Custom header matching reference Image 2:
/// hamburger | username ▼ | spacer | [chart icon] pencil
class DmHeader extends ConsumerWidget {
  const DmHeader({super.key, required this.onNewMessage});

  final VoidCallback onNewMessage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider);
    String username = 'lens_by_manish';
    if (auth is AuthAuthenticated) {
      username = auth.user.username.isNotEmpty ? auth.user.username : 'lens_by_manish';
    }

    return Container(
      color: AppColors.dmBackground,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            // Hamburger (opens drawer)
            IconButton(
              icon: const Icon(Icons.menu, color: AppColors.dmTextPrimary, size: 26),
              onPressed: () => Scaffold.maybeOf(context)?.openDrawer(),
              padding: const EdgeInsets.all(4),
            ),
            const SizedBox(width: 4),
            // Username with dropdown chevron
            GestureDetector(
              onTap: () {
                // Placeholder: could open account switcher
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Account switcher (demo)')),
                );
              },
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    username,
                    style: const TextStyle(
                      color: AppColors.dmTextPrimary,
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(width: 2),
                  const Icon(Icons.keyboard_arrow_down, color: AppColors.dmTextSecondary, size: 22),
                ],
              ),
            ),
            const Spacer(),
            // Action icons (chart + pencil)
            IconButton(
              icon: const Icon(Icons.show_chart, color: AppColors.dmTextPrimary, size: 22),
              onPressed: () => context.push('/snap-map'), // repurposed as "insights" demo
              padding: const EdgeInsets.all(6),
            ),
            IconButton(
              icon: const Icon(Icons.edit_outlined, color: AppColors.dmTextPrimary, size: 22),
              onPressed: onNewMessage,
              padding: const EdgeInsets.all(6),
            ),
            const SizedBox(width: 4),
          ],
        ),
      ),
    );
  }
}
