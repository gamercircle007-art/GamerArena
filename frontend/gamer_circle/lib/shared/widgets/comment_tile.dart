import 'package:flutter/material.dart';
import 'package:gamer_circle/shared/models/comment.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class CommentTile extends StatelessWidget {
  const CommentTile({
    super.key,
    required this.comment,
    this.indent = 0,
    this.onLike,
    this.onReply,
    this.onViewReplies,
  });

  final Comment comment;
  final double indent;
  final VoidCallback? onLike;
  final VoidCallback? onReply;
  final VoidCallback? onViewReplies;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(left: indent, right: 16, top: 8, bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          UserAvatar(
            imageUrl: comment.user.avatarUrl,
            name: comment.user.name,
            radius: 16,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  comment.user.name ?? 'Gamer',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                Text(comment.content),
                const SizedBox(height: 6),
                Row(
                  children: [
                    if (onLike != null)
                      TextButton(
                        onPressed: onLike,
                        child: Text(comment.isLiked ? 'Liked' : 'Like'),
                      ),
                    if (onReply != null)
                      TextButton(onPressed: onReply, child: const Text('Reply')),
                    if (comment.replyCount > 0 && onViewReplies != null)
                      TextButton(
                        onPressed: onViewReplies,
                        child: Text('View ${comment.replyCount} replies'),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}