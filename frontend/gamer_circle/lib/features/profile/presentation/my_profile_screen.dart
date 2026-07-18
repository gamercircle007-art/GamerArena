import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/features/profile/data/profile_repository.dart';
import 'package:gamer_circle/features/profile/providers/profile_provider.dart';
import 'package:gamer_circle/features/stories/providers/stories_provider.dart';
import 'package:gamer_circle/shared/widgets/stories_avatar_ring.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:gamer_circle/core/services/dms_service.dart';

class MyProfileScreen extends ConsumerWidget {
  const MyProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider);
    if (auth is! AuthAuthenticated) {
      return Scaffold(
        appBar: AppBar(title: const Text('Profile')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.person_outline, size: 64, color: Colors.grey),
                const SizedBox(height: 12),
                const Text('Sign in to view your profile'),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => context.go('/login'),
                  child: const Text('Login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final userId = auth.user.id;
    final profileAsync = ref.watch(publicProfileProvider(userId));
    final myStoriesAsync = ref.watch(myStoriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.push('/privacy-settings'),
          ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Could not load profile:\n$e', textAlign: TextAlign.center),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () => ref.invalidate(publicProfileProvider(userId)),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
        data: (profile) {
          final hasStory = myStoriesAsync.valueOrNull?.isNotEmpty ?? false;
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 100),
            children: [
              Center(
                child: Stack(
                  alignment: Alignment.bottomRight,
                  children: [
                    StoriesAvatarRing(
                      hasStory: hasStory,
                      allViewed: false,
                      size: 108,
                      onTap: () => _changeAvatar(context, ref, userId),
                      child: UserAvatar(
                        name: profile.name ?? profile.username,
                        imageUrl: profile.avatarUrl,
                        radius: 48,
                        showOnlineDot: true,
                        isOnline: true,
                      ),
                    ),
                    Material(
                      color: AppColors.primary,
                      shape: const CircleBorder(),
                      child: InkWell(
                        customBorder: const CircleBorder(),
                        onTap: () => _changeAvatar(context, ref, userId),
                        child: const Padding(
                          padding: EdgeInsets.all(6),
                          child: Icon(
                            Icons.camera_alt,
                            size: 16,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Column(
                  children: [
                    Text(
                      profile.name ?? profile.username ?? 'User',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    if (profile.username != null)
                      Text('@${profile.username}', style: const TextStyle(color: Colors.grey)),
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
                      .map((t) => Chip(label: Text(t), backgroundColor: AppColors.primaryLight))
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
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _showEditSheet(context, ref, profile),
                      icon: const Icon(Icons.edit_outlined),
                      label: const Text('Edit Profile'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () => _showQrSheet(context, ref, userId, profile.username),
                      icon: const Icon(Icons.qr_code),
                      label: const Text('Share'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ListTile(
                leading: const Icon(Icons.people_outline),
                title: const Text('Friends'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('/friends-list'),
              ),
              ListTile(
                leading: const Icon(Icons.privacy_tip_outlined),
                title: const Text('Privacy Settings'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('/privacy-settings'),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _changeAvatar(BuildContext context, WidgetRef ref, String userId) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 800,
      maxHeight: 800,
    );
    if (pickedFile == null) return;
    final file = File(pickedFile.path);
    try {
      final dms = ref.read(dmsServiceProvider);
      final result = await dms.uploadFile(
        file: file,
        assetType: 'image',
        fileType: 'image/jpeg',
        context: 'profile',
        contextId: userId,
      );
      await ref.read(profileRepositoryProvider).updateProfile({
        'avatar_url': result.cdnUrl,
      });
      ref.invalidate(publicProfileProvider(userId));
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile picture updated')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Upload failed: $e')),
        );
      }
    }
  }

  Future<void> _showQrSheet(
    BuildContext context,
    WidgetRef ref,
    String userId,
    String? username,
  ) async {
    final qr = await ref.read(profileRepositoryProvider).getQrCode();
    final qrData = qr['qr_data'] as String? ?? 'gamer-circle://profile/$userId';
    if (!context.mounted) return;
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              username != null ? '@$username' : 'My Profile',
              style: Theme.of(ctx).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            QrImageView(data: qrData, size: 200),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () {
                Share.share('Add me on Gamer Circle: $qrData');
              },
              icon: const Icon(Icons.share),
              label: const Text('Share Profile'),
            ),
          ],
        ),
      ),
    );
  }

  void _showEditSheet(BuildContext context, WidgetRef ref, PublicProfile profile) {
    final bioCtrl = TextEditingController(text: profile.bio ?? '');
    final cityCtrl = TextEditingController(text: profile.city ?? '');
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Edit Profile', style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 16),
            TextField(
              controller: bioCtrl,
              decoration: const InputDecoration(labelText: 'Bio'),
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: cityCtrl,
              decoration: const InputDecoration(labelText: 'City'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () async {
                await ref.read(profileRepositoryProvider).updateProfile({
                  'bio': bioCtrl.text.trim(),
                  'city': cityCtrl.text.trim(),
                });
                ref.invalidate(publicProfileProvider(profile.id));
                if (ctx.mounted) Navigator.pop(ctx);
              },
              child: const Text('Save'),
            ),
          ],
        ),
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
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
      ],
    );
  }
}