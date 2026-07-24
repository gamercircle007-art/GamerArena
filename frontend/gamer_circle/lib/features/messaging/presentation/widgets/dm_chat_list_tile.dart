import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/shared/models/conversation.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';
import 'package:intl/intl.dart';

/// Custom list tile for the main DM inbox list. Matches reference visuals:
/// avatar (with optional ring/dot), title+preview, time, trailing blue dot or status.
class DmChatListTile extends StatelessWidget {
  const DmChatListTile({
    super.key,
    required this.conversation,
    required this.myId,
    required this.onTap,
    this.isOnline = false,
  });

  final Conversation conversation;
  final String? myId;
  final VoidCallback onTap;
  final bool isOnline;

  @override
  Widget build(BuildContext context) {
    final other = myId != null ? conversation.otherParticipant(myId!) : null;
    final name = other?.name ?? other?.username ?? 'Chat';
    final avatarUrl = other?.avatarUrl;
    final hasUnread = conversation.unreadCount > 0;
    final time = conversation.lastMessageAt != null
        ? DateFormat('h:mm a').format(conversation.lastMessageAt!.toLocal()).toLowerCase()
        : '';

    // Demo "last message" enhancement for visual match
    String preview = conversation.lastMessagePreview ?? 'No messages yet';
    if (preview.length > 48) preview = '${preview.substring(0, 45)}...';

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Leading avatar + online
            UserAvatar(
              name: name,
              imageUrl: avatarUrl,
              radius: 26,
              showOnlineDot: other != null,
              isOnline: isOnline,
            ),
            const SizedBox(width: 14),
            // Title + subtitle
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: AppColors.dmTextPrimary,
                            fontWeight: hasUnread ? FontWeight.w700 : FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                      ),
                      // small gaming emoji or badge example
                      if (conversation.emoji != null && conversation.emoji!.isNotEmpty) ...[
                        const SizedBox(width: 4),
                        Text(conversation.emoji!, style: const TextStyle(fontSize: 14)),
                      ],
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    preview,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: hasUnread ? AppColors.dmTextPrimary : AppColors.dmTextSecondary,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Trailing time + unread / status
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (time.isNotEmpty)
                  Text(
                    time,
                    style: const TextStyle(
                      color: AppColors.dmTextMuted,
                      fontSize: 12,
                    ),
                  ),
                const SizedBox(height: 6),
                if (hasUnread)
                  Container(
                    width: 10,
                    height: 10,
                    decoration: const BoxDecoration(
                      color: AppColors.dmBlue,
                      shape: BoxShape.circle,
                    ),
                  )
                else
                  Text(
                    'Seen',
                    style: TextStyle(
                      color: AppColors.dmTextMuted,
                      fontSize: 11,
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
