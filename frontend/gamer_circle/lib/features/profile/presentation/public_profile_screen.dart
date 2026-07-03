import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/messages_provider.dart';
import 'package:gamer_circle/features/profile/data/profile_repository.dart';
import 'package:gamer_circle/features/profile/providers/profile_provider.dart';
import 'package:gamer_circle/shared/widgets/online_dot.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class PublicProfileScreen extends ConsumerWidget {
  const PublicProfileScreen({super.key, required this.userId});

  final String userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(publicProfileProvider(userId));
    final isOnline = ref.watch(userOnlineStatusProvider(userId));

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (profile) {
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Center(
                child: Stack(
                  children: [
                    UserAvatar(
                      name: profile.name ?? profile.username,
                      imageUrl: profile.avatarUrl,
                      radius: 48,
                    ),
                    Positioned(
                      bottom: 4,
                      right: 4,
                      child: OnlineDot(isOnline: isOnline || profile.isOnline),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          profile.name ?? 'User',
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        if (profile.isPrivate) ...[
                          const SizedBox(width: 6),
                          const Icon(Icons.lock, size: 16, color: Colors.grey),
                        ],
                      ],
                    ),
                    if (profile.username != null)
                      Text('@${profile.username}', style: const TextStyle(color: Colors.grey)),
                    if (isOnline || profile.isOnline)
                      const Text('Active now', style: TextStyle(color: Colors.green, fontSize: 12))
                    else
                      const SizedBox(height: 4),
                  ],
                ),
              ),
              if (profile.bio != null) ...[
                const SizedBox(height: 12),
                Text(profile.bio!, textAlign: TextAlign.center),
              ],
              if (profile.gameTags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  alignment: WrapAlignment.center,
                  children: profile.gameTags
                      .map((t) => Chip(label: Text(t), backgroundColor: const Color(0xFFF0EFFF)))
                      .toList(),
                ),
              ],
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _Stat(label: 'Friends', value: '${profile.friendsCount}'),
                  _Stat(label: 'Followers', value: '${profile.followersCount}'),
                  _Stat(label: 'Following', value: '${profile.followingCount}'),
                ],
              ),
              if (profile.mutualFriendsCount > 0) ...[
                const SizedBox(height: 8),
                Text(
                  '${profile.mutualFriendsCount} mutual friends',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Color(0xFF82868B)),
                ),
              ],
              const SizedBox(height: 20),
              _ActionButtons(profile: profile, userId: userId),
              if (profile.isPrivate && !profile.isFriend)
                const Padding(
                  padding: EdgeInsets.only(top: 24),
                  child: Text(
                    'This account is private. Add friend to see posts.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF82868B)),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: Color(0xFF82868B), fontSize: 12)),
      ],
    );
  }
}

class _ActionButtons extends ConsumerWidget {
  const _ActionButtons({required this.profile, required this.userId});

  final PublicProfile profile;
  final String userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (profile.isFriend) {
      return Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: () {},
              child: const Text('Friends ✓'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: FilledButton(
              onPressed: () => _message(context, ref),
              child: const Text('Message'),
            ),
          ),
        ],
      );
    }

    if (profile.friendRequestSent) {
      return Row(
        children: [
          Expanded(child: OutlinedButton(onPressed: null, child: const Text('Request Sent'))),
          const SizedBox(width: 8),
          Expanded(
            child: FilledButton(onPressed: () => _message(context, ref), child: const Text('Message')),
          ),
        ],
      );
    }

    return Row(
      children: [
        Expanded(
          child: FilledButton(
            onPressed: () async {
              await ref.read(friendsRepositoryProvider).sendFriendRequest(userId);
              ref.invalidate(publicProfileProvider(userId));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Friend request sent')),
                );
              }
            },
            child: const Text('Add Friend'),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: OutlinedButton(
            onPressed: () => _message(context, ref),
            child: const Text('Message'),
          ),
        ),
      ],
    );
  }

  Future<void> _message(BuildContext context, WidgetRef ref) async {
    final conv = await ref.read(conversationsProvider.notifier).createConversation(userId);
    if (!context.mounted) return;
    context.push(
      '/messages/chat/${conv.id}',
      extra: {
        'otherUserId': userId,
        'otherUserName': profile.name ?? profile.username ?? 'User',
        'otherUserAvatar': profile.avatarUrl,
      },
    );
  }
}