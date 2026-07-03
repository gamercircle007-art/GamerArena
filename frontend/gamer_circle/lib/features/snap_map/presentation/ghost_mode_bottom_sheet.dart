import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/snap_map/providers/snap_map_provider.dart';

class GhostModeBottomSheet extends ConsumerWidget {
  const GhostModeBottomSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ghost = ref.watch(ghostModeProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.visibility_off, color: Color(0xFF7367F0)),
              const SizedBox(width: 8),
              Text(
                'Ghost Mode',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'While in ghost mode, you won\'t appear on others\' maps. '
            'Friends can still message you.',
            style: TextStyle(color: Color(0xFF82868B)),
          ),
          const SizedBox(height: 16),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(ghost ? 'Ghost Mode ON' : 'Show on Map'),
            subtitle: Text(ghost ? 'Hidden from friends' : 'Visible to friends'),
            value: ghost,
            onChanged: (_) => ref.read(ghostModeProvider.notifier).toggle(),
          ),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: () => Navigator.pop(context),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(48),
              backgroundColor: const Color(0xFF7367F0),
            ),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }
}