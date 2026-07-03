import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/friends/providers/friends_provider.dart';
import 'package:gamer_circle/shared/models/user.dart';

class FindFriendsScreen extends ConsumerStatefulWidget {
  const FindFriendsScreen({super.key});

  @override
  ConsumerState<FindFriendsScreen> createState() => _FindFriendsScreenState();
}

class _FindFriendsScreenState extends ConsumerState<FindFriendsScreen> {
  final _searchCtrl = TextEditingController();
  Timer? _debounce;
  List<AppUser> _results = [];
  final Set<String> _pending = {};
  bool _searching = false;

  @override
  void dispose() {
    _searchCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearch(String q) {
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

  Future<void> _addFriend(String userId) async {
    await ref.read(friendsRepositoryProvider).sendFriendRequest(userId);
    setState(() => _pending.add(userId));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Friend request sent')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final suggestions = ref.watch(friendSuggestionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Find Friends')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              onChanged: _onSearch,
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
                      final pending = _pending.contains(u.id);
                      return ListTile(
                        leading: CircleAvatar(
                          child: Text((u.name ?? u.username ?? '?')[0].toUpperCase()),
                        ),
                        title: Text(u.name ?? u.username ?? 'User'),
                        subtitle: u.username != null ? Text('@${u.username}') : null,
                        trailing: pending
                            ? const Chip(label: Text('Pending'))
                            : FilledButton(
                                onPressed: () => _addFriend(u.id),
                                child: const Text('Add'),
                              ),
                      );
                    },
                  )
                : ListView(
                    children: [
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
                        child: Text(
                          'People you may know',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF82868B),
                          ),
                        ),
                      ),
                      ...suggestions.when(
                        data: (list) => list.map(
                          (s) => ListTile(
                            leading: CircleAvatar(
                              child: Text((s.user.name ?? '?')[0].toUpperCase()),
                            ),
                            title: Text(s.user.name ?? s.user.username ?? 'User'),
                            subtitle: Text('${s.mutualFriends} mutual friends'),
                            trailing: FilledButton(
                              onPressed: () => _addFriend(s.user.id),
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