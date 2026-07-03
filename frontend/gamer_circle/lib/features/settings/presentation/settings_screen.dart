import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/auth/presentation/providers/auth_providers.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Push notifications'),
            subtitle: const Text('Tournament updates and booking alerts'),
            value: true,
            onChanged: (_) {},
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.event_seat_outlined),
            title: const Text('My Bookings'),
            onTap: () => context.push('/my-bookings'),
          ),
          ListTile(
            leading: const Icon(Icons.dashboard_outlined),
            title: const Text('Owner Dashboard'),
            onTap: () => context.push('/owner-dashboard'),
          ),
          ListTile(
            leading: const Icon(Icons.chat_bubble_outline),
            title: const Text('Messages'),
            onTap: () => context.push('/messages'),
          ),
          ListTile(
            leading: const Icon(Icons.people_outline),
            title: const Text('Friend Requests'),
            onTap: () => context.push('/friend-requests'),
          ),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Privacy'),
            onTap: () => context.push('/privacy-settings'),
          ),
          ListTile(
            leading: const Icon(Icons.admin_panel_settings_outlined),
            title: const Text('Admin Panel'),
            onTap: () => context.push('/admin'),
          ),
          ListTile(
            leading: const Icon(Icons.storefront_outlined),
            title: const Text('Store'),
            onTap: () => context.push('/store'),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Log out', style: TextStyle(color: Colors.red)),
            onTap: () => ref.read(authNotifierProvider.notifier).logout(),
          ),
        ],
      ),
    );
  }
}