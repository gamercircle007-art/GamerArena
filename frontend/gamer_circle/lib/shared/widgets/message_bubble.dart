import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/shared/models/message.dart';

class MessageBubble extends StatelessWidget {
  const MessageBubble({
    super.key,
    required this.message,
    this.onReplyTap,
    this.onLongPress,
  });

  final Message message;
  final VoidCallback? onReplyTap;
  final VoidCallback? onLongPress;

  @override
  Widget build(BuildContext context) {
    final isMine = message.isMine;
    final align = isMine ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final bg = isMine ? const Color(0xFF7367F0) : Colors.white;
    final fg = isMine ? Colors.white : const Color(0xFF5E5873);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: align,
        children: [
          GestureDetector(
            onLongPress: onLongPress,
            onTap: message.isEphemeral && message.viewedAt == null ? onReplyTap : null,
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: bg,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isMine ? 16 : 4),
                  bottomRight: Radius.circular(isMine ? 4 : 16),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 4,
                    offset: const Offset(0, 1),
                  ),
                ],
              ),
              child: _buildContent(fg),
            ),
          ),
          if (isMine)
            Padding(
              padding: const EdgeInsets.only(top: 2, right: 4),
              child: Text(
                message.status == 'sending' ? '✓' : '✓✓',
                style: TextStyle(
                  fontSize: 10,
                  color: message.status == 'sending'
                      ? Colors.grey
                      : const Color(0xFF7367F0),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildContent(Color fg) {
    if (message.isDeleted) {
      return Text('Message deleted', style: TextStyle(color: fg.withOpacity(0.7), fontStyle: FontStyle.italic));
    }
    if (message.isEphemeral && message.viewedAt == null) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.local_fire_department, color: fg, size: 16),
          const SizedBox(width: 6),
          Text('Tap to view', style: TextStyle(color: fg, fontWeight: FontWeight.w500)),
        ],
      );
    }
    if (message.messageType == 'image' && message.mediaUrl != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: message.mediaUrl!,
          width: 200,
          fit: BoxFit.cover,
        ),
      );
    }
    return Text(
      message.content ?? '',
      style: TextStyle(color: fg, fontSize: 14),
    );
  }
}