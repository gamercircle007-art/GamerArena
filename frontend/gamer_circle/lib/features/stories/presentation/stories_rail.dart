import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/stories/presentation/story_viewer.dart';
import 'package:gamer_circle/features/stories/providers/stories_provider.dart';
import 'package:gamer_circle/shared/models/story.dart';
import 'package:gamer_circle/shared/widgets/stories_avatar_ring.dart';

class StoriesRail extends ConsumerWidget {
  const StoriesRail({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final feedAsync = ref.watch(storiesFeedProvider);
    final auth = ref.watch(authNotifierProvider);
    final myId = auth is AuthAuthenticated ? auth.user.id : null;
    final myName = auth is AuthAuthenticated ? auth.user.username : 'You';

    return SizedBox(
      height: 108,
      child: feedAsync.when(
        loading: () => const Center(
          child: SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
        error: (_, __) => _buildRail(
          context,
          groups: const [],
          myId: myId,
          myName: myName,
        ),
        data: (groups) => _buildRail(
          context,
          groups: groups,
          myId: myId,
          myName: myName,
        ),
      ),
    );
  }

  Widget _buildRail(
    BuildContext context, {
    required List<StoryGroup> groups,
    String? myId,
    required String myName,
  }) {
    StoryGroup? myGroup;
    if (myId != null) {
      for (final g in groups) {
        if (g.userId == myId) {
          myGroup = g;
          break;
        }
      }
    }
    final friendGroups = myId != null
        ? groups.where((g) => g.userId != myId).toList()
        : groups;

    return ListView.separated(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: 1 + friendGroups.length,
      separatorBuilder: (_, __) => const SizedBox(width: 12),
      itemBuilder: (_, i) {
        if (i == 0) {
          final hasStory = myGroup != null && myGroup.stories.isNotEmpty;
          return _StoryBubble(
            label: 'Your Story',
            name: myName,
            avatarUrl: myGroup?.userAvatar,
            hasStory: hasStory,
            allViewed: false,
            showAdd: !hasStory,
            onTap: () {
              if (hasStory && myGroup != null) {
                final group = myGroup;
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => StoryViewer(
                      groups: [group],
                      initialGroupIndex: 0,
                    ),
                  ),
                );
              } else {
                context.push('/story/create');
              }
            },
          );
        }

        final group = friendGroups[i - 1];
        final name = group.userName ?? 'Story';
        return _StoryBubble(
          label: name,
          name: name,
          avatarUrl: group.userAvatar,
          hasStory: group.stories.isNotEmpty,
          allViewed: group.allViewed,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => StoryViewer(
                  groups: friendGroups,
                  initialGroupIndex: i - 1,
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _StoryBubble extends StatelessWidget {
  const _StoryBubble({
    required this.label,
    required this.name,
    this.avatarUrl,
    required this.hasStory,
    this.allViewed = false,
    this.showAdd = false,
    this.onTap,
  });

  final String label;
  final String name;
  final String? avatarUrl;
  final bool hasStory;
  final bool allViewed;
  final bool showAdd;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 72,
        child: Column(
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                StoriesAvatarRing(
                  hasStory: hasStory,
                  allViewed: allViewed,
                  size: 56,
                  child: CircleAvatar(
                    radius: 24,
                    backgroundColor: AppColors.primary.withOpacity(0.1),
                    backgroundImage:
                        avatarUrl != null ? NetworkImage(avatarUrl!) : null,
                    child: avatarUrl == null
                        ? Text(
                            name.isNotEmpty ? name[0].toUpperCase() : '?',
                            style: const TextStyle(color: AppColors.primary),
                          )
                        : null,
                  ),
                ),
                if (showAdd)
                  const Positioned(
                    bottom: -2,
                    right: -2,
                    child: CircleAvatar(
                      radius: 10,
                      backgroundColor: AppColors.primary,
                      child: Icon(Icons.add, size: 14, color: Colors.white),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}