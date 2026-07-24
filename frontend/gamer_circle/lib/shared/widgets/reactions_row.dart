import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class ReactionsRow extends StatelessWidget {
  const ReactionsRow({
    super.key,
    required this.reactions,
    this.onEmojiTap,
    this.myUserId,
  });

  final Map<String, dynamic> reactions;
  final void Function(String emoji)? onEmojiTap;
  final String? myUserId;

  @override
  Widget build(BuildContext context) {
    if (reactions.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Wrap(
        spacing: 6,
        children: reactions.entries.map((entry) {
          final emoji = entry.key;
          final users = entry.value;
          final count = users is List ? users.length : 1;
          final mine = users is List && myUserId != null && users.contains(myUserId);

          return GestureDetector(
            onTap: () => onEmojiTap?.call(emoji),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: mine
                    ? AppColors.primary.withOpacity(0.15)
                    : Colors.grey.shade200,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: mine ? AppColors.primary : Colors.transparent,
                ),
              ),
              child: Text('$emoji $count', style: const TextStyle(fontSize: 12)),
            ),
          );
        }).toList(),
      ),
    );
  }
}