import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/profile/providers/profile_provider.dart';

class PrivacySettingsScreen extends ConsumerStatefulWidget {
  const PrivacySettingsScreen({super.key});

  @override
  ConsumerState<PrivacySettingsScreen> createState() => _PrivacySettingsScreenState();
}

class _PrivacySettingsScreenState extends ConsumerState<PrivacySettingsScreen> {
  bool _isPrivate = false;
  String _onlineStatus = 'friends';
  String _locationPrivacy = 'friends';
  String _allowMessages = 'friends';
  String _storiesPrivacy = 'friends';
  bool _allowFriendRequests = true;
  bool _ghostMode = false;
  List<dynamic> _blocked = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final auth = ref.read(authNotifierProvider);
      final blocked = await ref.read(profileRepositoryProvider).getBlockedUsers();
      if (auth is AuthAuthenticated) {
        final profile = await ref.read(profileRepositoryProvider).getMyProfile(auth.user.id);
        setState(() {
          _blocked = blocked;
          _isPrivate = profile.isPrivate;
          _allowMessages = 'friends';
        });
      } else {
        setState(() => _blocked = blocked);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _saveProfile() async {
    await ref.read(profileRepositoryProvider).updateProfile({
      'is_private': _isPrivate,
      'allow_messages_from': _allowMessages,
      'show_online_status': _onlineStatus,
      'allow_friend_requests': _allowFriendRequests,
      'stories_privacy': _storiesPrivacy,
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Privacy settings saved')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy'),
        actions: [
          TextButton(onPressed: _saveProfile, child: const Text('Save')),
        ],
      ),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Private Account'),
            subtitle: const Text('Only friends can see your posts'),
            value: _isPrivate,
            onChanged: (v) => setState(() => _isPrivate = v),
          ),
          const Divider(),
          _PrivacyTile(
            title: 'Online Status',
            value: _onlineStatus,
            options: const ['everyone', 'friends', 'nobody'],
            onChanged: (v) async {
              setState(() => _onlineStatus = v);
              await ref.read(profileRepositoryProvider).updateStatusPrivacy(v);
            },
          ),
          _PrivacyTile(
            title: 'Location on Map',
            value: _locationPrivacy,
            options: const ['everyone', 'friends', 'nobody'],
            onChanged: (v) async {
              setState(() => _locationPrivacy = v);
              await ref.read(profileRepositoryProvider).updateLocationPrivacy(v);
            },
          ),
          SwitchListTile(
            title: const Text('Ghost Mode'),
            subtitle: const Text('Hide from Snap Map'),
            value: _ghostMode,
            onChanged: (v) async {
              setState(() => _ghostMode = v);
              await ref.read(locationRepositoryProvider).toggleGhostMode(v);
            },
          ),
          _PrivacyTile(
            title: 'Stories',
            value: _storiesPrivacy,
            options: const ['everyone', 'friends', 'close_friends'],
            onChanged: (v) => setState(() => _storiesPrivacy = v),
          ),
          _PrivacyTile(
            title: 'Direct Messages',
            value: _allowMessages,
            options: const ['everyone', 'friends', 'nobody'],
            onChanged: (v) => setState(() => _allowMessages = v),
          ),
          SwitchListTile(
            title: const Text('Allow Friend Requests'),
            value: _allowFriendRequests,
            onChanged: (v) => setState(() => _allowFriendRequests = v),
          ),
          const Divider(),
          const ListTile(
            title: Text('Blocked Users'),
            subtitle: Text('Tap to unblock'),
          ),
          ..._blocked.map(
            (u) => ListTile(
              title: Text(u.name ?? u.username ?? 'User'),
              trailing: TextButton(
                onPressed: () async {
                  await ref.read(profileRepositoryProvider).unblockUser(u.id);
                  await _load();
                },
                child: const Text('Unblock'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PrivacyTile extends StatelessWidget {
  const _PrivacyTile({
    required this.title,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  final String title;
  final String value;
  final List<String> options;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(title),
      subtitle: Text(value),
      trailing: DropdownButton<String>(
        value: value,
        items: options
            .map((o) => DropdownMenuItem(value: o, child: Text(o)))
            .toList(),
        onChanged: (v) {
          if (v != null) onChanged(v);
        },
      ),
    );
  }
}