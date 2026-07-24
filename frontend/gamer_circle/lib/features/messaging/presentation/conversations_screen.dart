import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/dm_chat_list_tile.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/dm_header.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/dm_note_card.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/dm_tab_bar.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/dm_ui_providers.dart';
import 'package:gamer_circle/features/messaging/providers/messages_provider.dart'; // for userOnlineStatusProvider

/// Main DM Inbox screen — redesigned to be pixel-close to the reference Instagram DM list (Image 2).
/// Fully dark, responsive, uses existing Riverpod + go_router + real conversations.
class ConversationsScreen extends ConsumerStatefulWidget {
  const ConversationsScreen({super.key});

  @override
  ConsumerState<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends ConsumerState<ConversationsScreen> {
  final TextEditingController _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Live search — once in initState (never in build; that stacked listeners).
    _searchCtrl.addListener(() {
      ref.read(dmInboxSearchProvider.notifier).state = _searchCtrl.text;
    });
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _openNewMessage() {
    context.push('/messages/new');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authNotifierProvider);
    final isGuest = auth is AuthGuest || auth is AuthUnauthenticated;
    final myId = auth is AuthAuthenticated ? auth.user.id : null;

    final convsAsync = ref.watch(conversationsProvider);
    final notes = ref.watch(dmNotesProvider);
    final ({DmTab tab, String query}) tabAndQuery = ref.watch(dmTabAndQueryProvider);

    // No nested drawer — hamburger uses MainShellScaffold's AppDrawer.
    return Scaffold(
      backgroundColor: AppColors.dmBackground,
      body: SafeArea(
        child: Column(
          children: [
            // Custom header (username + pencil action)
            DmHeader(onNewMessage: _openNewMessage),

            // Search bar — "Search or ask Meta AI"
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
              child: Container(
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.dmSearchBg,
                  borderRadius: BorderRadius.circular(22),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    const Icon(Icons.search, color: AppColors.dmTextSecondary, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _searchCtrl,
                        style: const TextStyle(color: AppColors.dmTextPrimary, fontSize: 15),
                        decoration: const InputDecoration(
                          hintText: 'Search or ask Meta AI',
                          hintStyle: TextStyle(color: AppColors.dmTextSecondary, fontSize: 15),
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: EdgeInsets.zero,
                        ),
                        textInputAction: TextInputAction.search,
                      ),
                    ),
                    if (_searchCtrl.text.isNotEmpty)
                      GestureDetector(
                        onTap: () {
                          _searchCtrl.clear();
                          ref.read(dmInboxSearchProvider.notifier).state = '';
                        },
                        child: const Icon(Icons.close, size: 18, color: AppColors.dmTextSecondary),
                      ),
                  ],
                ),
              ),
            ),

            // Horizontal Notes / Parlor Highlights row (exactly like reference)
            SizedBox(
              height: 102,
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                scrollDirection: Axis.horizontal,
                itemCount: notes.length,
                separatorBuilder: (_, __) => const SizedBox(width: 12),
                itemBuilder: (context, index) {
                  final note = notes[index];
                  return DmNoteCard(
                    note: note,
                    onTap: () {
                      // Demo: open a relevant parlor or story-like flow
                      context.push('/discover');
                    },
                  );
                },
              ),
            ),

            const SizedBox(height: 4),

            // Tabs: Primary (with badge), Requests, General
            const DmTabBar(),

            const Divider(height: 1, color: AppColors.dmDivider),

            // Chat list
            Expanded(
              child: isGuest
                  ? _GuestMessagingPrompt(onLogin: () => context.go('/login'))
                  : RefreshIndicator(
                      color: AppColors.dmBlue,
                      backgroundColor: AppColors.dmCard,
                      onRefresh: () => ref.read(conversationsProvider.notifier).refresh(),
                      child: convsAsync.when(
                        loading: () => const Center(
                          child: CircularProgressIndicator(color: AppColors.dmBlue),
                        ),
                        error: (e, _) => Center(
                          child: Text('Failed to load chats: $e',
                              style: const TextStyle(color: AppColors.dmTextSecondary)),
                        ),
                        data: (convs) {
                          // Apply tab + search filter client-side (real data + demo rules)
                          final q = tabAndQuery.query;
                          final tab = tabAndQuery.tab;

                          final filtered = convs.where((c) {
                            // Tab logic (demo)
                            bool tabOk = true;
                            final unread = c.unreadCount;
                            if (tab == DmTab.primary) {
                              tabOk = unread > 0 || c.lastMessageAt != null;
                            } else if (tab == DmTab.requests) {
                              tabOk = (c.type) == 'request';
                            } // general = all remaining

                            if (!tabOk) return false;

                            if (q.isNotEmpty && myId != null) {
                              final other = c.otherParticipant(myId);
                              final name = (other?.name ?? other?.username ?? '').toLowerCase();
                              final preview = (c.lastMessagePreview ?? '').toLowerCase();
                              if (!name.contains(q) && !preview.contains(q)) return false;
                            }
                            return true;
                          }).toList();

                          if (filtered.isEmpty) {
                            return _EmptyState(onStartChat: _openNewMessage);
                          }

                          return ListView.builder(
                            physics: const AlwaysScrollableScrollPhysics(),
                            itemCount: filtered.length,
                            itemBuilder: (context, index) {
                              final conv = filtered[index];
                              final other = myId != null ? conv.otherParticipant(myId) : null;
                              final isOnline = other != null
                                  ? ref.watch(userOnlineStatusProvider(other.id))
                                  : false;

                              return Column(
                                children: [
                                  DmChatListTile(
                                    conversation: conv,
                                    myId: myId,
                                    isOnline: isOnline,
                                    onTap: () {
                                      if (other != null) {
                                        context.push(
                                          '/messages/chat/${conv.id}',
                                          extra: {
                                            'otherUserId': other.id,
                                            'otherUserName': other.name ?? other.username ?? 'Chat',
                                            'otherUserAvatar': other.avatarUrl,
                                          },
                                        );
                                      }
                                    },
                                  ),
                                  if (index != filtered.length - 1)
                                    const Divider(
                                      height: 1,
                                      indent: 70,
                                      endIndent: 16,
                                      color: AppColors.dmDivider,
                                    ),
                                ],
                              );
                            },
                          );
                        },
                      ),
                    ),
            ),
          ],
        ),
      ),

      // Keep FAB as secondary access (hidden on new/chat by shell)
      floatingActionButton: isGuest
          ? null
          : FloatingActionButton(
              onPressed: _openNewMessage,
              backgroundColor: AppColors.dmBlue,
              child: const Icon(Icons.edit_outlined, color: Colors.white),
            ),
    );
  }
}

class _GuestMessagingPrompt extends StatelessWidget {
  const _GuestMessagingPrompt({required this.onLogin});

  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.chat_bubble_outline, size: 64, color: AppColors.dmTextMuted),
            const SizedBox(height: 16),
            const Text(
              'Sign in to view your messages',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.dmTextPrimary),
            ),
            const SizedBox(height: 8),
            const Text(
              'Message friends, parlors & join tournament chats.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.dmTextSecondary),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: onLogin,
              style: FilledButton.styleFrom(backgroundColor: AppColors.dmBlue),
              child: const Text('Login to continue'),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onStartChat});

  final VoidCallback onStartChat;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.forum_outlined, size: 56, color: AppColors.dmTextMuted),
            const SizedBox(height: 16),
            const Text('No chats yet', style: TextStyle(color: AppColors.dmTextPrimary, fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            const Text(
              'Start a conversation with friends or a parlor.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.dmTextSecondary),
            ),
            const SizedBox(height: 20),
            OutlinedButton(
              onPressed: onStartChat,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.dmBlue,
                side: const BorderSide(color: AppColors.dmBlue),
              ),
              child: const Text('New message'),
            ),
          ],
        ),
      ),
    );
  }
}

