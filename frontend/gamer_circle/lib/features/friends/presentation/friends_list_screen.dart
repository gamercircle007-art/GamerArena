import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/friends/providers/friends_provider.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/messages_provider.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class FriendsListScreen extends ConsumerWidget {
  const FriendsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final friendsAsync = ref.watch(friendsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Friends'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add_outlined),
            onPressed: () => context.push('/find-friends'),
          ),
        ],
      ),
      body: friendsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (friends) {
          if (friends.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.people_outline, size: 64, color: Colors.grey.shade400),
                  const SizedBox(height: 12),
                  const Text('No friends yet'),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: () => context.push('/find-friends'),
                    child: const Text('Find Friends'),
                  ),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(friendsProvider),
            child: ListView.separated(
              itemCount: friends.length,
              separatorBuilder: (_, __) => const Divider(height: 1, indent: 72),
              itemBuilder: (_, i) {
                final f = friends[i];
                final isOnline = ref.watch(userOnlineStatusProvider(f.user.id));
                return ListTile(
                  leading: UserAvatar(
                    name: f.user.name ?? f.user.username,
                    imageUrl: f.user.avatarUrl,
                    radius: 24,
                    showOnlineDot: true,
                    isOnline: isOnline,
                    onTap: () => context.push('/profile/${f.user.id}'),
                  ),
                  title: Text(f.user.name ?? f.user.username ?? 'User'),
                  subtitle: Text(isOnline ? 'Active now' : 'Offline'),
                  trailing: IconButton(
                    icon: const Icon(Icons.chat_bubble_outline),
                    onPressed: () async {
                      final conv = await ref
                          .read(conversationsProvider.notifier)
                          .createConversation(f.user.id);
                      if (!context.mounted) return;
                      context.push(
                        '/messages/chat/${conv.id}',
                        extra: {
                          'otherUserId': f.user.id,
                          'otherUserName': f.user.name ?? f.user.username ?? 'User',
                          'otherUserAvatar': f.user.avatarUrl,
                        },
                      );
                    },
                  ),
                  onTap: () => context.push('/profile/${f.user.id}'),
                );
              },
            ),
          );
        },
      ),
    );
  }
}