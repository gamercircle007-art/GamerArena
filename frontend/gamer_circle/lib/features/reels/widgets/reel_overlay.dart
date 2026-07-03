import 'package:flutter/material.dart';
import 'package:gamer_circle/shared/models/reel.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class ReelOverlay extends StatelessWidget {
  const ReelOverlay({
    super.key,
    required this.reel,
    required this.onLike,
    required this.onComment,
    required this.onShare,
    required this.onBookmark,
    required this.onFollow,
    required this.onMore,
    this.showHeart = false,
  });

  final Reel reel;
  final VoidCallback onLike;
  final VoidCallback onComment;
  final VoidCallback onShare;
  final VoidCallback onBookmark;
  final VoidCallback onFollow;
  final VoidCallback onMore;
  final bool showHeart;

  String _formatCount(int n) {
    if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}M';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return '$n';
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        if (showHeart)
          const Center(
            child: Icon(Icons.favorite, color: Colors.red, size: 96),
          ),
        Positioned(
          left: 16,
          right: 80,
          bottom: 24,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  UserAvatar(
                    name: reel.user.displayName,
                    imageUrl: reel.user.avatarUrl,
                    radius: 18,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    reel.user.displayName,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (!reel.user.isFollowing)
                    GestureDetector(
                      onTap: onFollow,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.white),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          'Follow',
                          style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700),
                        ),
                      ),
                    ),
                ],
              ),
              if (reel.caption != null && reel.caption!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  reel.caption!,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                ),
              ],
              if (reel.hashtags.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  reel.hashtags.map((h) => '#$h').join(' '),
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
              if (reel.musicTitle != null) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.music_note, color: Colors.white, size: 14),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        reel.musicTitle!,
                        style: const TextStyle(color: Colors.white, fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 4),
              Text(
                '${_formatCount(reel.viewsCount)} views',
                style: const TextStyle(color: Colors.white60, fontSize: 12),
              ),
            ],
          ),
        ),
        Positioned(
          right: 12,
          bottom: 40,
          child: Column(
            children: [
              _ActionButton(
                icon: reel.isLiked ? Icons.favorite : Icons.favorite_border,
                label: _formatCount(reel.likesCount),
                color: reel.isLiked ? Colors.red : Colors.white,
                onTap: onLike,
              ),
              const SizedBox(height: 20),
              _ActionButton(
                icon: Icons.mode_comment_outlined,
                label: _formatCount(reel.commentsCount),
                onTap: onComment,
              ),
              const SizedBox(height: 20),
              _ActionButton(
                icon: Icons.share_outlined,
                label: _formatCount(reel.sharesCount),
                onTap: onShare,
              ),
              const SizedBox(height: 20),
              _ActionButton(
                icon: reel.isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                label: _formatCount(reel.bookmarksCount),
                onTap: onBookmark,
              ),
              const SizedBox(height: 20),
              _ActionButton(icon: Icons.more_vert, label: '', onTap: onMore),
            ],
          ),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.color = Colors.white,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Icon(icon, color: color, size: 30),
          if (label.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ],
      ),
    );
  }
}