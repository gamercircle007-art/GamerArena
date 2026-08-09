import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/features/discovery/data/centre_summary.dart';
import 'package:gamer_circle/features/discovery/data/discovery_repository.dart';
import 'package:gamer_circle/features/discovery/presentation/centre_card.dart';
import 'package:gamer_circle/features/discovery/presentation/filter_sheet.dart';
import 'package:gamer_circle/features/discovery/presentation/filter_state.dart';

class DiscoveryListState {
  const DiscoveryListState({
    this.items = const [],
    this.loading = false,
    this.loadingMore = false,
    this.error,
    this.hasMore = false,
  });

  final List<CentreSummary> items;
  final bool loading;
  final bool loadingMore;
  final String? error;
  final bool hasMore;

  DiscoveryListState copyWith({
    List<CentreSummary>? items,
    bool? loading,
    bool? loadingMore,
    String? error,
    bool? hasMore,
    bool clearError = false,
  }) =>
      DiscoveryListState(
        items: items ?? this.items,
        loading: loading ?? this.loading,
        loadingMore: loadingMore ?? this.loadingMore,
        error: clearError ? null : (error ?? this.error),
        hasMore: hasMore ?? this.hasMore,
      );
}

class DiscoveryListNotifier extends StateNotifier<DiscoveryListState> {
  DiscoveryListNotifier(this._ref) : super(const DiscoveryListState());

  final Ref _ref;
  DiscoveryRepository get repo => _ref.read(discoveryRepositoryProvider);
  StreamSubscription<Position>? _posSub;
  Timer? _debounce;

  Future<void> bootstrap() async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      // Instant paint: last known → then medium accuracy
      Position? pos = await Geolocator.getLastKnownPosition();
      pos ??= await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
        ),
      );
      await _load(pos.latitude, pos.longitude);
      _posSub?.cancel();
      _posSub = Geolocator.getPositionStream(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          distanceFilter: 150,
        ),
      ).listen((p) {
        // Soft refresh when user moves 150m+
        _load(p.latitude, p.longitude, silent: true);
      });
    } catch (e) {
      // Fallback Delhi if GPS denied
      await _load(28.6139, 77.209);
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> _load(double lat, double lng, {bool silent = false}) async {
    if (!silent) state = state.copyWith(loading: true, clearError: true);
    final filters = _ref.read(discoveryFilterProvider);
    try {
      final page = await repo.loadFirst(lat: lat, lng: lng, filters: filters);
      state = state.copyWith(
        items: page.items,
        loading: false,
        hasMore: page.nextCursor != null,
      );
    } catch (e) {
      state = state.copyWith(loading: false, error: e.toString());
    }
  }

  void onQueryChanged(String q) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      final cur = _ref.read(discoveryFilterProvider);
      if (q == cur.query) return;
      // Require length >= 2 before network (empty clears)
      if (q.isNotEmpty && q.trim().length < 2) {
        _ref.read(discoveryFilterProvider.notifier).state =
            cur.copyWith(query: q, clearEtag: true);
        return;
      }
      _ref.read(discoveryFilterProvider.notifier).state =
          cur.copyWith(query: q, sort: q.length >= 2 ? 'relevance' : 'distance', clearEtag: true);
      refresh();
    });
  }

  Future<void> refresh() async {
    final pos = _ref.read(currentPositionProvider).valueOrNull;
    final lat = pos?.latitude ?? 28.6139;
    final lng = pos?.longitude ?? 77.209;
    await _load(lat, lng);
  }

  Future<void> loadMore() async {
    if (!state.hasMore || state.loadingMore) return;
    state = state.copyWith(loadingMore: true);
    final pos = _ref.read(currentPositionProvider).valueOrNull;
    final lat = pos?.latitude ?? 28.6139;
    final lng = pos?.longitude ?? 77.209;
    final filters = _ref.read(discoveryFilterProvider);
    try {
      final more = await repo.loadMore(lat: lat, lng: lng, filters: filters);
      state = state.copyWith(
        items: [...state.items, ...more],
        loadingMore: false,
        hasMore: repo.nextCursor != null,
      );
    } catch (_) {
      state = state.copyWith(loadingMore: false);
    }
  }

  void expandRadius() {
    final f = _ref.read(discoveryFilterProvider);
    final next = switch (f.distanceM) {
      <= 2000 => 5000,
      <= 5000 => 10000,
      <= 10000 => 25000,
      _ => 50000,
    };
    _ref.read(discoveryFilterProvider.notifier).state =
        f.copyWith(distanceM: next, clearEtag: true);
    refresh();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _posSub?.cancel();
    super.dispose();
  }
}

final discoveryListProvider =
    StateNotifierProvider<DiscoveryListNotifier, DiscoveryListState>((ref) {
  final n = DiscoveryListNotifier(ref);
  ref.listen<FilterState>(discoveryFilterProvider, (prev, next) {
    if (prev != next) n.refresh();
  });
  return n;
});

class DiscoveryPage extends ConsumerStatefulWidget {
  const DiscoveryPage({super.key});

  @override
  ConsumerState<DiscoveryPage> createState() => _DiscoveryPageState();
}

class _DiscoveryPageState extends ConsumerState<DiscoveryPage> {
  final _scroll = ScrollController();
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
    Future.microtask(() => ref.read(discoveryListProvider.notifier).bootstrap());
  }

  void _onScroll() {
    if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 400) {
      ref.read(discoveryListProvider.notifier).loadMore();
    }
  }

  @override
  void dispose() {
    _scroll.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final list = ref.watch(discoveryListProvider);
    final filters = ref.watch(discoveryFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Discover'),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () async {
              await showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                builder: (_) => const FilterSheet(),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: TextField(
              controller: _searchCtrl,
              decoration: InputDecoration(
                hintText: 'Search gaming centres',
                prefixIcon: const Icon(Icons.search),
                filled: true,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: (q) =>
                  ref.read(discoveryListProvider.notifier).onQueryChanged(q),
            ),
          ),
          // Filter chips rebuild independently of the list via select
          _FilterChipsRow(
            filters: filters,
            onChanged: (f) =>
                ref.read(discoveryFilterProvider.notifier).state = f,
          ),
          Expanded(
            child: list.loading && list.items.isEmpty
                ? const _SkeletonList()
                : list.items.isEmpty
                    ? _EmptyState(
                        radiusKm: (filters.distanceM / 1000).round(),
                        onExpand: () =>
                            ref.read(discoveryListProvider.notifier).expandRadius(),
                      )
                    : ListView.builder(
                        controller: _scroll,
                        itemExtent: kCentreCardExtent,
                        addAutomaticKeepAlives: false,
                        addRepaintBoundaries: true,
                        itemCount: list.items.length + (list.loadingMore ? 1 : 0),
                        itemBuilder: (context, i) {
                          if (i >= list.items.length) {
                            return const SizedBox(
                              height: 48,
                              child: Center(
                                child: SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                ),
                              ),
                            );
                          }
                          final c = list.items[i];
                          return CentreCard(
                            centre: c,
                            onTap: () => context.push('/parlour/${c.id}'),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

class _FilterChipsRow extends StatelessWidget {
  const _FilterChipsRow({required this.filters, required this.onChanged});

  final FilterState filters;
  final ValueChanged<FilterState> onChanged;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          for (final m in const [2000, 5000, 10000, 25000])
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text('${m ~/ 1000} km'),
                selected: filters.distanceM == m,
                onSelected: (_) => onChanged(filters.copyWith(distanceM: m, clearEtag: true)),
              ),
            ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: const Text('4.0+'),
              selected: filters.minRating == 4.0,
              onSelected: (on) => onChanged(
                filters.copyWith(
                  minRating: on ? 4.0 : null,
                  clearMinRating: !on,
                  clearEtag: true,
                ),
              ),
            ),
          ),
          FilterChip(
            label: const Text('Available now'),
            selected: filters.availableNow,
            selectedColor: const Color(0xFFDCFCE7),
            onSelected: (on) =>
                onChanged(filters.copyWith(availableNow: on, clearEtag: true)),
          ),
        ],
      ),
    );
  }
}

class _SkeletonList extends StatelessWidget {
  const _SkeletonList();

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemExtent: kCentreCardExtent,
      itemCount: 6,
      itemBuilder: (_, __) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            Container(
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                color: const Color(0xFFE5E7EB),
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(height: 14, width: double.infinity, color: const Color(0xFFE5E7EB)),
                  const SizedBox(height: 8),
                  Container(height: 12, width: 120, color: const Color(0xFFE5E7EB)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.radiusKm, required this.onExpand});

  final int radiusKm;
  final VoidCallback onExpand;

  @override
  Widget build(BuildContext context) {
    final next = radiusKm < 5
        ? 5
        : radiusKm < 10
            ? 10
            : radiusKm < 25
                ? 25
                : 50;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.sports_esports_outlined, size: 48, color: Color(0xFF9CA3AF)),
            const SizedBox(height: 12),
            Text(
              'No centres within ${radiusKm}km',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: onExpand,
              style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
              child: Text('Expand radius to ${next}km'),
            ),
          ],
        ),
      ),
    );
  }
}
