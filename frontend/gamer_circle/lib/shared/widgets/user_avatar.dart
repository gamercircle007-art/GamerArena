import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/shared/widgets/online_dot.dart';
import 'package:gamer_circle/shared/widgets/stories_avatar_ring.dart';

class UserAvatar extends StatelessWidget {
  const UserAvatar({
    super.key,
    this.imageUrl,
    this.name,
    this.radius = 20,
    this.showOnlineDot = false,
    this.isOnline = false,
    this.hasStory = false,
    this.allStoriesViewed = false,
    this.onTap,
  });

  final String? imageUrl;
  final String? name;
  final double radius;
  final bool showOnlineDot;
  final bool isOnline;
  final bool hasStory;
  final bool allStoriesViewed;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final initials = (name?.isNotEmpty == true)
        ? name!.trim().substring(0, 1).toUpperCase()
        : '?';

    Widget avatar;
    if (imageUrl != null && imageUrl!.isNotEmpty) {
      avatar = CircleAvatar(
        radius: radius,
        backgroundImage: CachedNetworkImageProvider(imageUrl!),
      );
    } else {
      avatar = CircleAvatar(
        radius: radius,
        backgroundColor: AppColors.primaryLight,
        child: Text(
          initials,
          style: const TextStyle(
            color: AppColors.primaryDark,
            fontWeight: FontWeight.bold,
          ),
        ),
      );
    }

    if (hasStory) {
      avatar = StoriesAvatarRing(
        hasStory: true,
        allViewed: allStoriesViewed,
        size: radius * 2 + 6,
        onTap: onTap,
        child: SizedBox(width: radius * 2, height: radius * 2, child: avatar),
      );
    } else if (onTap != null) {
      avatar = GestureDetector(onTap: onTap, child: avatar);
    }

    if (showOnlineDot) {
      return Stack(
        clipBehavior: Clip.none,
        children: [
          avatar,
          Positioned(
            bottom: 0,
            right: 0,
            child: OnlineDot(isOnline: isOnline, size: OnlineDotSize.small),
          ),
        ],
      );
    }

    return avatar;
  }
}