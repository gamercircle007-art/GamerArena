import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/features/messaging/providers/dm_ui_providers.dart';

/// Horizontal note/highlight card matching the IG DM "notes" row style.
/// Adapted for Paythan gaming/parlor context.
class DmNoteCard extends StatelessWidget {
  const DmNoteCard({
    super.key,
    required this.note,
    this.onTap,
  });

  final DmNote note;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 78,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.dmDivider, width: 1.5),
              ),
              child: ClipOval(
                child: Image.network(
                  note.imageUrl,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    color: AppColors.dmPillBg,
                    alignment: Alignment.center,
                    child: Text(
                      note.emoji ?? '🎮',
                      style: const TextStyle(fontSize: 26),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              note.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.dmTextPrimary,
                fontWeight: FontWeight.w500,
              ),
            ),
            if (note.subtitle != null)
              Text(
                note.subtitle!,
                maxLines: 1,
                style: const TextStyle(
                  fontSize: 10,
                  color: AppColors.dmTextMuted,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
