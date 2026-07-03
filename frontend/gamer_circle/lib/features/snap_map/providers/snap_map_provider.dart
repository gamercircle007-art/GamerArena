import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:gamer_circle/core/network/ws_service.dart';
import 'package:gamer_circle/core/providers/messaging_providers.dart';
import 'package:gamer_circle/shared/models/snap_map_user.dart';
import 'package:latlong2/latlong.dart';

class FriendsOnMapNotifier extends AsyncNotifier<List<SnapMapUser>> {
  StreamSubscription<Map<String, dynamic>>? _wsSub;

  @override
  Future<List<SnapMapUser>> build() async {
    ref.onDispose(() => _wsSub?.cancel());
    _listenLocationUpdates();
    return ref.read(locationRepositoryProvider).getFriendsOnMap();
  }

  void _listenLocationUpdates() {
    _wsSub = WsService.instance.events.listen((event) {
      final type = event['type'] as String?;
      if (type != 'location_update') return;
      final userId = event['user_id'] as String?;
      final lat = (event['lat'] as num?)?.toDouble();
      final lng = (event['lng'] as num?)?.toDouble();
      if (userId == null || lat == null || lng == null) return;

      final current = state.valueOrNull ?? [];
      final idx = current.indexWhere((u) => u.userId == userId);
      if (idx < 0) return;

      final updated = SnapMapUser(
        userId: userId,
        name: current[idx].name,
        avatarUrl: current[idx].avatarUrl,
        lat: lat,
        lng: lng,
        distanceKm: current[idx].distanceKm,
        updatedAt: DateTime.now(),
      );
      final list = [...current];
      list[idx] = updated;
      state = AsyncData(list);
    });
  }

  Future<void> refresh() async {
    state = AsyncData(await ref.read(locationRepositoryProvider).getFriendsOnMap());
  }
}

final friendsOnMapProvider =
    AsyncNotifierProvider<FriendsOnMapNotifier, List<SnapMapUser>>(
  FriendsOnMapNotifier.new,
);

class GhostModeNotifier extends Notifier<bool> {
  @override
  bool build() => false;

  Future<void> toggle() async {
    final next = !state;
    await ref.read(locationRepositoryProvider).toggleGhostMode(next);
    state = next;
  }

  Future<void> load() async {
    // Ghost mode status loaded on first map open via API if needed
  }
}

final ghostModeProvider = NotifierProvider<GhostModeNotifier, bool>(
  GhostModeNotifier.new,
);

final myLocationProvider = StateProvider<LatLng?>((ref) => null);

Future<void> startLocationUpdates(WidgetRef ref) async {
  final enabled = await Geolocator.isLocationServiceEnabled();
  if (!enabled) return;

  var permission = await Geolocator.checkPermission();
  if (permission == LocationPermission.denied) {
    permission = await Geolocator.requestPermission();
  }
  if (permission == LocationPermission.denied ||
      permission == LocationPermission.deniedForever) {
    return;
  }

  Future<void> sync(Position pos) async {
    ref.read(myLocationProvider.notifier).state =
        LatLng(pos.latitude, pos.longitude);
    await ref.read(locationRepositoryProvider).updateLocation(
          lat: pos.latitude,
          lng: pos.longitude,
          accuracy: pos.accuracy,
        );
  }

  final current = await Geolocator.getCurrentPosition();
  await sync(current);

  Timer.periodic(const Duration(minutes: 5), (_) async {
    final pos = await Geolocator.getCurrentPosition();
    await sync(pos);
  });
}