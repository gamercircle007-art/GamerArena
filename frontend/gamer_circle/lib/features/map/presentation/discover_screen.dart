import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/shared/models/nearby_parlor.dart';
import 'package:latlong2/latlong.dart';

class DiscoverScreen extends ConsumerStatefulWidget {
  const DiscoverScreen({super.key});

  @override
  ConsumerState<DiscoverScreen> createState() => _DiscoverScreenState();
}

class _DiscoverScreenState extends ConsumerState<DiscoverScreen> {
  bool _listView = false;
  double _radius = 5000;
  String? _gameType;
  List<NearbyParlor> _parlors = [];
  bool _loading = false;

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      var pos = ref.read(currentPositionProvider).valueOrNull;
      pos ??= await ref.read(currentPositionProvider.notifier).requestAndFetch();
      if (pos == null) return;
      final data = await ref.read(socialApiProvider).nearbyParlors(
            lat: pos.latitude,
            lng: pos.longitude,
            radius: _radius,
            gameType: _gameType,
          );
      setState(() => _parlors = data);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _setGameType(String? type) {
    setState(() => _gameType = _gameType == type ? null : type);
    _load();
  }

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  LatLng _markerPoint(NearbyParlor parlor, LatLng fallback) {
    if (parlor.lat != null && parlor.lng != null) {
      return LatLng(parlor.lat!, parlor.lng!);
    }
    return fallback;
  }

  @override
  Widget build(BuildContext context) {
    final pos = ref.watch(currentPositionProvider).valueOrNull;
    final center = pos != null ? LatLng(pos.latitude, pos.longitude) : const LatLng(28.6, 77.2);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Discover'),
        actions: [
          IconButton(
            icon: Icon(_listView ? Icons.map : Icons.list),
            onPressed: () => setState(() => _listView = !_listView),
          ),
        ],
      ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('BGMI'),
                  selected: _gameType == 'BGMI',
                  onSelected: (_) => _setGameType('BGMI'),
                ),
                FilterChip(
                  label: const Text('Valorant'),
                  selected: _gameType == 'Valorant',
                  onSelected: (_) => _setGameType('Valorant'),
                ),
                SizedBox(
                  width: 180,
                  child: Slider(
                    value: _radius,
                    min: 1000,
                    max: 20000,
                    label: '${(_radius / 1000).round()}km',
                    onChanged: (v) => setState(() => _radius = v),
                    onChangeEnd: (_) => _load(),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _listView
                    ? ListView.builder(
                        itemCount: _parlors.length,
                        itemBuilder: (context, i) {
                          final p = _parlors[i];
                          return ListTile(
                            leading: p.logoUrl != null
                                ? ClipRRect(
                                    borderRadius: BorderRadius.circular(8),
                                    child: Image.network(
                                      p.logoUrl!,
                                      width: 48,
                                      height: 48,
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, __, ___) =>
                                          const Icon(Icons.videogame_asset),
                                    ),
                                  )
                                : const Icon(Icons.videogame_asset),
                            title: Text(p.name),
                            subtitle: Text(
                              [
                                if (p.rating != null) '★ ${p.rating!.toStringAsFixed(1)}',
                                p.distanceLabel,
                                if (!p.isOpen) 'Closed',
                                if (p.city != null) p.city!,
                              ].join(' · '),
                            ),
                            onTap: () => context.push('/parlors/${p.id}'),
                          );
                        },
                      )
                    : FlutterMap(
                        options: MapOptions(initialCenter: center, initialZoom: 13),
                        children: [
                          TileLayer(
                            urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                          ),
                          MarkerLayer(
                            markers: _parlors.map((p) {
                              return Marker(
                                point: _markerPoint(p, center),
                                width: 40,
                                height: 40,
                                child: GestureDetector(
                                  onTap: () => _showSheet(p),
                                  child: const Icon(
                                    Icons.location_pin,
                                    color: AppColors.primary,
                                    size: 36,
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  void _showSheet(NearbyParlor parlor) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(parlor.name, style: Theme.of(context).textTheme.titleLarge),
            if (parlor.rating != null) Text('★ ${parlor.rating!.toStringAsFixed(1)}'),
            if (parlor.address != null) Text(parlor.address!),
            if (parlor.phone != null) Text(parlor.phone!),
            Text('${parlor.distanceMeters.round()} meters away'),
            if (parlor.gameTypes.isNotEmpty)
              Wrap(
                spacing: 6,
                children: parlor.gameTypes.map((g) => Chip(label: Text(g))).toList(),
              ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () {
                Navigator.pop(ctx);
                context.push('/parlors/${parlor.id}');
              },
              child: const Text('View Profile'),
            ),
          ],
        ),
      ),
    );
  }
}