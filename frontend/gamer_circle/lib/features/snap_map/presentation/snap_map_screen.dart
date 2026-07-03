import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/features/messaging/providers/conversations_provider.dart';
import 'package:gamer_circle/features/snap_map/presentation/ghost_mode_bottom_sheet.dart';
import 'package:gamer_circle/features/snap_map/providers/snap_map_provider.dart';
import 'package:gamer_circle/shared/models/snap_map_user.dart';
import 'package:gamer_circle/shared/widgets/map_user_marker.dart';
import 'package:latlong2/latlong.dart';

class SnapMapScreen extends ConsumerStatefulWidget {
  const SnapMapScreen({super.key});

  @override
  ConsumerState<SnapMapScreen> createState() => _SnapMapScreenState();
}

class _SnapMapScreenState extends ConsumerState<SnapMapScreen> {
  final _mapController = MapController();

  @override
  void initState() {
    super.initState();
    Future.microtask(() => startLocationUpdates(ref));
    ref.read(friendsOnMapProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context) {
    final friendsAsync = ref.watch(friendsOnMapProvider);
    final myLoc = ref.watch(myLocationProvider);
    final ghost = ref.watch(ghostModeProvider);

    final center = myLoc ??
        (friendsAsync.valueOrNull?.isNotEmpty == true
            ? LatLng(
                friendsAsync.valueOrNull!.first.lat,
                friendsAsync.valueOrNull!.first.lng,
              )
            : const LatLng(28.6139, 77.2090));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Snap Map'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(friendsOnMapProvider.notifier).refresh(),
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(initialCenter: center, initialZoom: 12),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.gamercircle.app',
              ),
              if (myLoc != null)
                MarkerLayer(
                  markers: [
                    Marker(
                      point: myLoc,
                      width: 16,
                      height: 16,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.blue,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                        ),
                      ),
                    ),
                  ],
                ),
              MarkerLayer(
                markers: (friendsAsync.valueOrNull ?? []).map((f) {
                  return Marker(
                    point: LatLng(f.lat, f.lng),
                    width: 48,
                    height: 48,
                    child: MapUserMarker(
                      avatarUrl: f.avatarUrl,
                      name: f.name,
                      onTap: () => _showUserSheet(f),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),
          friendsAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (_, __) => const SizedBox.shrink(),
            data: (_) => const SizedBox.shrink(),
          ),
          Positioned(
            right: 16,
            bottom: 24,
            child: Column(
              children: [
                if (myLoc != null)
                  FloatingActionButton.small(
                    heroTag: 'center',
                    onPressed: () => _mapController.move(myLoc, 14),
                    child: const Icon(Icons.my_location),
                  ),
                const SizedBox(height: 8),
                FloatingActionButton(
                  heroTag: 'ghost',
                  onPressed: () => showModalBottomSheet(
                    context: context,
                    builder: (_) => const GhostModeBottomSheet(),
                  ),
                  backgroundColor: ghost ? Colors.grey.shade700 : Colors.white,
                  child: Icon(
                    Icons.visibility_off,
                    color: ghost ? Colors.white : const Color(0xFF5E5873),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showUserSheet(SnapMapUser user) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            MapUserMarker(avatarUrl: user.avatarUrl, name: user.name, size: 64),
            const SizedBox(height: 8),
            Text(
              user.name ?? 'User',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            if (user.distanceKm != null) Text('${user.distanceKm} km away'),
            Text(
              'Updated ${_timeAgo(user.updatedAt)}',
              style: const TextStyle(color: Color(0xFF82868B), fontSize: 12),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      context.push('/profile/${user.userId}');
                    },
                    child: const Text('View Profile'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(
                    onPressed: () async {
                      Navigator.pop(context);
                      final conv = await ref
                          .read(conversationsProvider.notifier)
                          .createConversation(user.userId);
                      if (!context.mounted) return;
                      context.push(
                        '/messages/chat/${conv.id}',
                        extra: {
                          'otherUserId': user.userId,
                          'otherUserName': user.name ?? 'User',
                          'otherUserAvatar': user.avatarUrl,
                        },
                      );
                    },
                    child: const Text('Message'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _timeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    return '${diff.inHours}h ago';
  }
}