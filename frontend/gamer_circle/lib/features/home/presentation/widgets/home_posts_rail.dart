import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/shared/models/home_data.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';
import 'package:gamer_circle/shared/widgets/verified_badge.dart';

class HomePostsRail extends StatelessWidget {
  const HomePostsRail({
    super.key,
    required this.posts,
    required this.isLoading,
    required this.onPostTap,
    required this.onSeeAllTap,
  });

  final List<HomePostItem> posts;
  final bool isLoading;
  final ValueChanged<HomePostItem> onPostTap;
  final VoidCallback onSeeAllTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 12),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'Latest posts',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: OnboardingColors.textPrimary,
                  ),
                ),
              ),
              TextButton(
                onPressed: onSeeAllTap,
                child: const Text('See all'),
              ),
            ],
          ),
        ),
        SizedBox(
          height: 280,
          child: isLoading && posts.isEmpty
              ? const Center(
                  child: CircularProgressIndicator(color: OnboardingColors.primary),
                )
              : posts.isEmpty
                  ? const Center(
                      child: Text(
                        'No posts yet',
                        style: TextStyle(color: OnboardingColors.textSecondary),
                      ),
                    )
                  : ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      itemCount: posts.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 14),
                      itemBuilder: (context, index) => _PostScrollCard(
                        post: posts[index],
                        onTap: () => onPostTap(posts[index]),
                      ),
                    ),
        ),
      ],
    );
  }
}

class _PostScrollCard extends StatelessWidget {
  const _PostScrollCard({
    required this.post,
    required this.onTap,
  });

  final HomePostItem post;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 240,
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        elevation: 2,
        shadowColor: Colors.black.withOpacity(0.08),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                child: post.coverImage != null
                    ? CachedNetworkImage(
                        imageUrl: post.coverImage!,
                        height: 150,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorWidget: (_, __, ___) => _imageFallback(),
                      )
                    : _imageFallback(),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        UserAvatar(
                          imageUrl: post.parlorLogoUrl,
                          name: post.parlorName,
                          radius: 14,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Row(
                            children: [
                              Flexible(
                                child: Text(
                                  post.parlorName,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                              if (post.parlorVerified) ...[
                                const SizedBox(width: 4),
                                const VerifiedBadge(size: 12),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      post.content,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: OnboardingColors.textSecondary,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.favorite_border, size: 14, color: OnboardingColors.textMuted),
                        const SizedBox(width: 4),
                        Text(
                          '${post.likesCount}',
                          style: const TextStyle(fontSize: 12, color: OnboardingColors.textMuted),
                        ),
                        const SizedBox(width: 12),
                        const Icon(Icons.chat_bubble_outline, size: 14, color: OnboardingColors.textMuted),
                        const SizedBox(width: 4),
                        Text(
                          '${post.commentsCount}',
                          style: const TextStyle(fontSize: 12, color: OnboardingColors.textMuted),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _imageFallback() {
    return Container(
      height: 150,
      width: double.infinity,
      color: AppColors.divider,
      child: const Icon(Icons.image_outlined, color: OnboardingColors.textSecondary, size: 40),
    );
  }
}