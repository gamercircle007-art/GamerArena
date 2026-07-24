import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_state.dart';
import 'package:gamer_circle/shared/widgets/user_avatar.dart';

class UserProfileScreen extends ConsumerWidget {
  const UserProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider);
    final user = auth is AuthAuthenticated ? auth.user : null;

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: user == null
          ? const Center(child: Text('Not logged in'))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Row(
                  children: [
                    UserAvatar(name: user.username, imageUrl: user.avatarUrl, radius: 36),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(user.username,
                              style: Theme.of(context).textTheme.titleLarge),
                          Text(user.email),
                        ],
                      ),
                    ),
                    TextButton(onPressed: () => context.push('/profile/edit'), child: const Text('Edit')),
                  ],
                ),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: () => context.push('/create-reel'),
                  icon: const Icon(Icons.video_call_outlined),
                  label: const Text('Upload Reel'),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(48),
                    backgroundColor: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 24),
                const Text('Followed Parlors', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(
                  height: 100,
                  child: FutureBuilder(
                    future: ref.read(socialApiProvider).fetchFollowing(),
                    builder: (context, snap) {
                      if (!snap.hasData) return const Center(child: CircularProgressIndicator());
                      final list = snap.data!;
                      return ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: list.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, i) => Chip(label: Text(list[i].name)),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 16),
                ListTile(
                  title: const Text('My Bookings'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/my-bookings'),
                ),
              ],
            ),
    );
  }
}