import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/friends/providers/friends_provider.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/shared/models/user.dart';

class NewChatScreen extends ConsumerStatefulWidget {
  const NewChatScreen({super.key});

  @override
  ConsumerState<NewChatScreen> createState() => _NewChatScreenState();
}

class _NewChatScreenState extends ConsumerState<NewChatScreen> {
  final _searchCtrl = TextEditingController();
  Timer? _debounce;
  List<AppUser> _results = [];
  bool _searching = false;

  @override
  void dispose() {
    _searchCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String q) {
    _debounce?.cancel();
    if (q.trim().isEmpty) {
      setState(() {
        _results = [];
        _searching = false;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      setState(() => _searching = true);
      try {
        final users = await ref.read(friendsRepositoryProvider).searchUsers(q.trim());
        if (mounted) setState(() => _results = users);
      } finally {
        if (mounted) setState(() => _searching = false);
      }
    });
  }

  Future<void> _startChat(String userId, String name, String? avatar) async {
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
  }

  @override
  Widget build(BuildContext context) {
    final friendsAsync = ref.watch(friendsProvider);
    final suggestionsAsync = ref.watch(friendSuggestionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('New Chat')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              onChanged: _onSearchChanged,
              decoration: InputDecoration(
                hintText: 'Search by name or username',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searching
                    ? const Padding(
                        padding: EdgeInsets.all(12),
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
          Expanded(
            child: _searchCtrl.text.isNotEmpty
                ? ListView.builder(
                    itemCount: _results.length,
                    itemBuilder: (_, i) {
                      final u = _results[i];
                      return ListTile(
                        leading: CircleAvatar(
                          child: Text((u.name ?? u.username ?? '?')[0].toUpperCase()),
                        ),
                        title: Text(u.name ?? u.username ?? 'User'),
                        subtitle: u.username != null ? Text('@${u.username}') : null,
                        onTap: () => _startChat(u.id, u.name ?? u.username ?? 'User', u.avatarUrl),
                      );
                    },
                  )
                : ListView(
                    children: [
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
                        child: Text(
                          'Friends',
                          style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF82868B)),
                        ),
                      ),
                      ...friendsAsync.when(
                        data: (friends) => friends.map(
                          (f) => ListTile(
                            leading: CircleAvatar(
                              child: Text((f.user.name ?? '?')[0].toUpperCase()),
                            ),
                            title: Text(f.user.name ?? f.user.username ?? 'Friend'),
                            onTap: () => _startChat(
                              f.user.id,
                              f.user.name ?? f.user.username ?? 'Friend',
                              f.user.avatarUrl,
                            ),
                          ),
                        ),
                        loading: () => [const Center(child: CircularProgressIndicator())],
                        error: (e, _) => [Text('Error: $e')],
                      ),
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 16, 16, 4),
                        child: Text(
                          'People you may know',
                          style: TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF82868B)),
                        ),
                      ),
                      ...suggestionsAsync.when(
                        data: (suggestions) => suggestions.map(
                          (s) => ListTile(
                            leading: CircleAvatar(
                              child: Text((s.user.name ?? '?')[0].toUpperCase()),
                            ),
                            title: Text(s.user.name ?? s.user.username ?? 'User'),
                            subtitle: Text('${s.mutualFriends} mutual friends'),
                            trailing: TextButton(
                              onPressed: () => ref
                                  .read(friendsRepositoryProvider)
                                  .sendFriendRequest(s.user.id),
                              child: const Text('Add'),
                            ),
                          ),
                        ),
                        loading: () => [const Center(child: CircularProgressIndicator())],
                        error: (e, _) => [Text('Error: $e')],
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}