import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/dm_action_tile.dart';
import 'package:gamer_circle/features/messaging/presentation/widgets/suggested_user_tile.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/messaging/providers/dm_ui_providers.dart';

/// New Message screen — matches reference Image 1 exactly:
/// - Back + "New message" title
/// - "To:" + pill search field
/// - Group chat / Create a channel / AI chats rows
/// - Suggested section + live filtered list with "x" remove buttons
/// - Special handling for Meta AI + gaming adapted contacts
class NewChatScreen extends ConsumerStatefulWidget {
  const NewChatScreen({super.key});

  @override
  ConsumerState<NewChatScreen> createState() => _NewChatScreenState();
}

class _NewChatScreenState extends ConsumerState<NewChatScreen> {
  final TextEditingController _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Live filter
    _searchCtrl.addListener(() {
      ref.read(newMessageSearchProvider.notifier).state = _searchCtrl.text;
    });
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _startChatWithUser(String userId, String name, String? avatar) async {
    try {
      final conv = await ref.read(conversationsProvider.notifier).createConversation(userId);
      if (!mounted) return;
      context.pushReplacement(
        '/messages/chat/${conv.id}',
        extra: {
          'otherUserId': userId,
          'otherUserName': name,
          'otherUserAvatar': avatar,
        },
      );
    } catch (_) {
      // Fallback demo navigation if backend not ready
      if (!mounted) return;
      context.pushReplacement(
        '/messages/chat/demo-${userId.substring(0, 6)}',
        extra: {'otherUserId': userId, 'otherUserName': name, 'otherUserAvatar': avatar},
      );
    }
  }

  void _openAIChat() {
    // Dedicated simple AI chat experience (or reuse chat screen with special handling)
    context.push(
      '/messages/chat/ai-meta',
      extra: {
        'otherUserId': 'ai-meta',
        'otherUserName': 'Meta AI',
        'otherUserAvatar': null,
      },
    );
  }

  void _showGroupOrChannelSheet({required bool isChannel}) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.dmCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _CreateGroupOrChannelSheet(isChannel: isChannel),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filtered = ref.watch(filteredSuggestedProvider);

    return Scaffold(
      backgroundColor: AppColors.dmBackground,
      appBar: AppBar(
        backgroundColor: AppColors.dmBackground,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.dmTextPrimary),
          onPressed: () => context.pop(),
        ),
        title: const Text(
          'New message',
          style: TextStyle(
            color: AppColors.dmTextPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        centerTitle: true,
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // To: label + search field
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('To:', style: TextStyle(color: AppColors.dmTextSecondary, fontSize: 15)),
                const SizedBox(height: 6),
                Container(
                  height: 46,
                  decoration: BoxDecoration(
                    color: AppColors.dmSearchBg,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  alignment: Alignment.centerLeft,
                  child: TextField(
                    controller: _searchCtrl,
                    autofocus: true,
                    style: const TextStyle(color: AppColors.dmTextPrimary, fontSize: 16),
                    decoration: const InputDecoration(
                      hintText: 'Search',
                      hintStyle: TextStyle(color: AppColors.dmTextMuted, fontSize: 16),
                      border: InputBorder.none,
                      isCollapsed: true,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Three action rows
          DmActionTile(
            icon: Icons.group_outlined,
            label: 'Group chat',
            onTap: () => _showGroupOrChannelSheet(isChannel: false),
          ),
          DmActionTile(
            icon: Icons.campaign_outlined,
            label: 'Create a channel',
            onTap: () => _showGroupOrChannelSheet(isChannel: true),
          ),
          DmActionTile(
            icon: Icons.auto_awesome_outlined,
            label: 'AI chats',
            iconColor: const Color(0xFF6C5CE7),
            onTap: _openAIChat,
          ),

          const SizedBox(height: 12),
          const Divider(height: 1, color: AppColors.dmDivider),

          // Suggested header
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 14, 16, 6),
            child: Text(
              'Suggested',
              style: TextStyle(
                color: AppColors.dmTextSecondary,
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),
          ),

          // Live filtered suggested list
          Expanded(
            child: filtered.isEmpty
                ? const Center(
                    child: Text('No matches', style: TextStyle(color: AppColors.dmTextMuted)),
                  )
                : ListView.builder(
                    itemCount: filtered.length,
                    itemBuilder: (context, index) {
                      final contact = filtered[index];
                      return SuggestedUserTile(
                        contact: contact,
                        onTap: () {
                          if (contact.isAI) {
                            _openAIChat();
                          } else {
                            _startChatWithUser(
                              contact.id,
                              contact.name,
                              contact.avatarUrl,
                            );
                          }
                        },
                        onRemove: () {
                          ref.read(suggestedNotifierProvider.notifier).remove(contact.id);
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

/// Bottom sheet for Group chat and Create channel (multi-select mock)
class _CreateGroupOrChannelSheet extends ConsumerStatefulWidget {
  const _CreateGroupOrChannelSheet({required this.isChannel});

  final bool isChannel;

  @override
  ConsumerState<_CreateGroupOrChannelSheet> createState() => _CreateGroupOrChannelSheetState();
}

class _CreateGroupOrChannelSheetState extends ConsumerState<_CreateGroupOrChannelSheet> {
  final Set<String> _selected = {};
  final List<SuggestedContact> _candidates = const [
    SuggestedContact(id: 'u1', name: 'heyitssheera', username: 'heyitssheera'),
    SuggestedContact(id: 'u2', name: 'tnu.agrwl', username: 'tnu.agrwl'),
    SuggestedContact(id: 'u5', name: 'manish kumar', username: 'lightweaver', isVerified: true),
    SuggestedContact(id: 'u7', name: 'LevelUp Lounge', username: 'levelup_parlor'),
  ];

  @override
  Widget build(BuildContext context) {
    final title = widget.isChannel ? 'Create a channel' : 'New group chat';

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
        top: 12,
        left: 16,
        right: 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.dmTextMuted,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(title, style: const TextStyle(color: AppColors.dmTextPrimary, fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(
            widget.isChannel
                ? 'Channels are broadcast style. Members can only read.'
                : 'Select friends or parlor members to chat together.',
            style: const TextStyle(color: AppColors.dmTextSecondary, fontSize: 13),
          ),
          const SizedBox(height: 16),
          ..._candidates.map((c) {
            final sel = _selected.contains(c.id);
            return CheckboxListTile(
              value: sel,
              onChanged: (v) {
                setState(() {
                  if (v == true) {
                    _selected.add(c.id);
                  } else {
                    _selected.remove(c.id);
                  }
                });
              },
              title: Text(c.name, style: const TextStyle(color: AppColors.dmTextPrimary)),
              subtitle: c.username != null ? Text('@${c.username}', style: const TextStyle(color: AppColors.dmTextMuted)) : null,
              activeColor: AppColors.dmBlue,
              contentPadding: EdgeInsets.zero,
            );
          }),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AppColors.dmBlue),
              onPressed: _selected.isEmpty
                  ? null
                  : () {
                      Navigator.pop(context);
                      // Mock success + navigate to a demo group chat
                      final names = _candidates
                          .where((c) => _selected.contains(c.id))
                          .map((c) => c.name)
                          .join(', ');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('${widget.isChannel ? 'Channel' : 'Group'} created with $names')),
                      );
                      // For demo: go back to inbox (real would create room)
                      context.pop();
                    },
              child: Text(widget.isChannel ? 'Create channel' : 'Create group'),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}