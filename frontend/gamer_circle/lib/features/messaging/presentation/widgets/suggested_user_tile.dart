import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/messaging/providers/dm_ui_providers.dart';

/// Single row in the "Suggested" list of New Message screen.
/// Matches exact reference: avatar + name (+ verified) + username-ish + trailing X button.
class SuggestedUserTile extends StatelessWidget {
  const SuggestedUserTile({
    super.key,
    required this.contact,
    required this.onTap,
    required this.onRemove,
  });

  final SuggestedContact contact;
  final VoidCallback onTap;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final hasAvatar = contact.avatarUrl != null && contact.avatarUrl!.isNotEmpty;

    Widget avatar;
    if (contact.isAI) {
      // Purple flower / Meta AI style icon (as in screenshot)
      avatar = Container(
        width: 48,
        height: 48,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            colors: [Color(0xFF6C5CE7), Color(0xFFA29BFE)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: const Center(
          child: Text(
            'AI',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: 14,
              letterSpacing: 0.5,
            ),
          ),
        ),
      );
    } else if (hasAvatar) {
      avatar = CircleAvatar(
        radius: 24,
        backgroundImage: NetworkImage(contact.avatarUrl!),
      );
    } else {
      avatar = CircleAvatar(
        radius: 24,
        backgroundColor: AppColors.dmPillBg,
        child: Text(
          contact.name.isNotEmpty ? contact.name[0].toUpperCase() : '?',
          style: const TextStyle(color: AppColors.dmTextPrimary, fontWeight: FontWeight.w600),
        ),
      );
    }

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            avatar,
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          contact.name,
                          style: const TextStyle(
                            color: AppColors.dmTextPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (contact.isVerified) ...[
                        const SizedBox(width: 4),
                        const Icon(Icons.verified, size: 16, color: AppColors.dmBlue),
                      ],
                    ],
                  ),
                  if (contact.username != null && contact.username!.isNotEmpty)
                    Text(
                      contact.username!.startsWith('@') ? contact.username! : '@${contact.username}',
                      style: const TextStyle(
                        color: AppColors.dmTextSecondary,
                        fontSize: 14,
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Exact "x" button from screenshot
            IconButton(
              onPressed: onRemove,
              icon: const Icon(Icons.close, size: 20),
              color: AppColors.dmTextSecondary,
              padding: const EdgeInsets.all(6),
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              splashRadius: 20,
            ),
          ],
        ),
      ),
    );
  }
}
