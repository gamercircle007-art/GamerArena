import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/dm_ui_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Segmented style tabs: Primary (with badge), Requests, General
/// Matches the screenshot pill + red dot aesthetic.
class DmTabBar extends ConsumerWidget {
  const DmTabBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(dmSelectedTabProvider);
    final unread = ref.watch(unreadCountProvider); // reuse global

    Widget buildTab(DmTab tab, String label, {int? badge}) {
      final isSel = selected == tab;
      return Expanded(
        child: GestureDetector(
          onTap: () => ref.read(dmSelectedTabProvider.notifier).state = tab,
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            padding: const EdgeInsets.symmetric(vertical: 8),
            decoration: BoxDecoration(
              color: isSel ? AppColors.dmPillBg : Colors.transparent,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (badge != null && badge > 0) ...[
                  Container(
                    width: 7,
                    height: 7,
                    decoration: const BoxDecoration(
                      color: AppColors.dmRed,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                ],
                Text(
                  badge != null && badge > 0 ? '$label $badge' : label,
                  style: TextStyle(
                    color: isSel ? AppColors.dmTextPrimary : AppColors.dmTextSecondary,
                    fontWeight: isSel ? FontWeight.w600 : FontWeight.w500,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      color: AppColors.dmBackground,
      child: Row(
        children: [
          buildTab(DmTab.primary, 'Primary', badge: unread > 0 ? unread : null),
          buildTab(DmTab.requests, 'Requests'),
          buildTab(DmTab.general, 'General'),
        ],
      ),
    );
  }
}
