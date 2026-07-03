import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/messages_provider.dart';
import 'package:gamer_circle/features/stories/providers/stories_provider.dart';
import 'package:gamer_circle/shared/widgets/social_top_bar.dart';
import 'package:gamer_circle/shared/widgets/stories_avatar_ring.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';
import 'package:intl/intl.dart';

class ConversationsScreen extends ConsumerStatefulWidget {
  const ConversationsScreen({super.key});

  @override
  ConsumerState<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends ConsumerState<ConversationsScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final convsAsync = ref.watch(conversationsProvider);
    final auth = ref.watch(authNotifierProvider);
    final myId = auth is AuthAuthenticated ? auth.user.id : null;
    final myStoriesAsync = ref.watch(myStoriesProvider);
    final hasMyStory = myStoriesAsync.valueOrNull?.isNotEmpty ?? false;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F8F8),
      appBar: AppBar(
        title: const Text('Messages'),
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF5E5873),
        elevation: 0,
        actions: const [
          SocialTopBarActions(),
          SizedBox(width: 4),
        ],
      ),
      body: convsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (convs) {
          final filtered = _query.isEmpty
              ? convs
              : convs.where((c) {
                  if (myId == null) return true;
                  final other = c.otherParticipant(myId);
                  final name = other?.name ?? other?.username ?? '';
                  return name.toLowerCase().contains(_query.toLowerCase());
                }).toList();

          return RefreshIndicator(
            onRefresh: () => ref.read(conversationsProvider.notifier).refresh(),
            child: ListView(
              children: [
                if (auth is AuthAuthenticated) ...[
                  ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    leading: StoriesAvatarRing(
                      hasStory: hasMyStory,
                      allViewed: false,
                      size: 58,
                      onTap: () => context.push('/story/create'),
                      child: UserAvatar(
                        name: auth.user.username,
                        imageUrl: auth.user.avatarUrl,
                        radius: 24,
                        showOnlineDot: true,
                        isOnline: true,
                      ),
                    ),
                    title: const Text('Your Story', style: TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: Text(hasMyStory ? 'Tap to view or add' : 'Tap to add a story'),
                    onTap: () => context.push('/story/create'),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: 'Search conversations...',
                        prefixIcon: const Icon(Icons.search, size: 20),
                        filled: true,
                        fillColor: Colors.white,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: const EdgeInsets.symmetric(vertical: 0),
                      ),
                      onChanged: (v) => setState(() => _query = v),
                    ),
                  ),
                  const Divider(height: 1),
                ],
                if (filtered.isEmpty)
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Center(
                      child: Column(
                        children: [
                          Icon(Icons.chat_bubble_outline, size: 48, color: Colors.grey.shade400),
                          const SizedBox(height: 12),
                          Text(_query.isEmpty ? 'No messages yet' : 'No matches'),
                          if (_query.isEmpty) ...[
                            const SizedBox(height: 12),
                            FilledButton(
                              onPressed: () => context.push('/messages/new'),
                              child: const Text('Start a chat'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  )
                else
                  ...filtered.map((conv) {
                    final other = myId != null ? conv.otherParticipant(myId) : null;
                    final name = other?.name ?? other?.username ?? 'Chat';
                    final isOnline = other != null
                        ? ref.watch(userOnlineStatusProvider(other.id))
                        : false;

                    return Column(
                      children: [
                        ListTile(
                          onTap: () {
                            if (other != null) {
                              context.push(
                                '/messages/chat/${conv.id}',
                                extra: {
                                  'otherUserId': other.id,
                                  'otherUserName': name,
                                  'otherUserAvatar': other.avatarUrl,
                                },
                              );
                            }
                          },
                          leading: UserAvatar(
                            name: name,
                            imageUrl: other?.avatarUrl,
                            radius: 26,
                            showOnlineDot: other != null,
                            isOnline: isOnline,
                            onTap: other != null
                                ? () => context.push('/profile/${other.id}')
                                : null,
                          ),
                          title: Text(
                            name,
                            style: TextStyle(
                              fontWeight: conv.unreadCount > 0 ? FontWeight.w700 : FontWeight.w500,
                            ),
                          ),
                          subtitle: Text(
                            conv.isEphemeral
                                ? '🔥 ${conv.lastMessagePreview ?? "Ephemeral"}'
                                : (conv.lastMessagePreview ?? 'No messages'),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              if (conv.lastMessageAt != null)
                                Text(
                                  DateFormat('HH:mm').format(conv.lastMessageAt!.toLocal()),
                                  style: const TextStyle(fontSize: 11, color: Color(0xFF82868B)),
                                ),
                              if (conv.unreadCount > 0) ...[
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF7367F0),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    '${conv.unreadCount}',
                                    style: const TextStyle(color: Colors.white, fontSize: 11),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                        const Divider(height: 1, indent: 72),
                      ],
                    );
                  }),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/messages/new'),
        backgroundColor: const Color(0xFF7367F0),
        child: const Icon(Icons.edit_outlined),
      ),
    );
  }
}