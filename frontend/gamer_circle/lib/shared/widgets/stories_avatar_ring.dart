import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class StoriesAvatarRing extends StatelessWidget {
  const StoriesAvatarRing({
    super.key,
    required this.hasStory,
    this.allViewed = false,
    required this.child,
    this.onTap,
    this.size = 56,
  });

  final bool hasStory;
  final bool allViewed;
  final Widget child;
  final VoidCallback? onTap;
  final double size;

  @override
  Widget build(BuildContext context) {
    if (!hasStory) return GestureDetector(onTap: onTap, child: child);

    final colors = allViewed
        ? [const Color(0xFFBDBDBD), const Color(0xFF9E9E9E)]
        : [AppColors.primary, AppColors.secondary];

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        padding: const EdgeInsets.all(2.5),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(colors: colors),
        ),
        child: Container(
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white,
          ),
          padding: const EdgeInsets.all(2),
          child: ClipOval(child: child),
        ),
      ),
    );
  }
}