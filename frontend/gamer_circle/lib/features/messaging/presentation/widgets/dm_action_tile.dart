import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

/// The three action rows at top of New Message (Group chat / Create channel / AI chats)
class DmActionTile extends StatelessWidget {
  const DmActionTile({
    super.key,
    required this.icon,
    required this.label,
    required this.onTap,
    this.iconColor = AppColors.dmTextPrimary,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color iconColor;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: AppColors.dmPillBg,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: iconColor, size: 22), // const not possible due to runtime icon
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  color: AppColors.dmTextPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: AppColors.dmTextSecondary,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}
