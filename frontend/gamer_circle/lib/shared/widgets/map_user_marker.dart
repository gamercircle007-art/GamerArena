import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/shared/widgets/online_dot.dart';
import 'package:gamer_circle/shared/widgets/stories_avatar_ring.dart';

class MapUserMarker extends StatelessWidget {
  const MapUserMarker({
    super.key,
    this.avatarUrl,
    this.name,
    this.isOnline = false,
    this.hasStory = false,
    this.allStoriesViewed = false,
    this.onTap,
    this.size = 44,
  });

  final String? avatarUrl;
  final String? name;
  final bool isOnline;
  final bool hasStory;
  final bool allStoriesViewed;
  final VoidCallback? onTap;
  final double size;

  @override
  Widget build(BuildContext context) {
    final avatar = Stack(
      clipBehavior: Clip.none,
      children: [
        StoriesAvatarRing(
          hasStory: hasStory,
          allViewed: allStoriesViewed,
          size: size,
          child: Container(
            width: size - 6,
            height: size - 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
              color: AppColors.primary.withOpacity(0.1),
            ),
            child: ClipOval(
              child: avatarUrl != null
                  ? CachedNetworkImage(imageUrl: avatarUrl!, fit: BoxFit.cover)
                  : Center(
                      child: Text(
                        (name?.isNotEmpty == true ? name![0] : '?').toUpperCase(),
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
            ),
          ),
        ),
        if (isOnline)
          const Positioned(
            bottom: 0,
            right: 0,
            child: OnlineDot(isOnline: true),
          ),
      ],
    );

    return GestureDetector(onTap: onTap, child: avatar);
  }
}