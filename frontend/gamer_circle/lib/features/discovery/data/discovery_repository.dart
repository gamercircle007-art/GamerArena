import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/discovery/data/centre_summary.dart';
import 'package:gamer_circle/features/discovery/data/discovery_api.dart';
import 'package:gamer_circle/features/discovery/presentation/filter_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

final discoveryApiProvider = Provider<DiscoveryApi>((ref) {
  return DiscoveryApi(ref.watch(dioProvider));
});

/// Stale-while-revalidate local cache (SharedPreferences; Hive-ready key shape).
class DiscoveryLocalCache {
  static String key(double lat, double lng, FilterState f) {
    // geohash6 approx via rounded coords (~1.2km)
    final gh = '${(lat * 100).round()}_${(lng * 100).round()}';
    return 'discovery_cache:$gh:${f.radiusM}:${f.sort}:${f.query}:'
        '${f.minRating}:${f.availableNow}:${f.amenitiesMask}';
  }

  static Future<DiscoveryPage?> read(String k) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(k);
    if (raw == null) return null;
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      final ts = map['_ts'] as int? ?? 0;
      if (DateTime.now().millisecondsSinceEpoch - ts > 60000) {
        await prefs.remove(k);
        return null;
      }
      return DiscoveryPage.fromJson(map);
    } catch (_) {
      return null;
    }
  }

  static Future<void> write(String k, DiscoveryPage page) async {
    final prefs = await SharedPreferences.getInstance();
    final map = {
      'items': page.items
          .map(
            (e) => {
              'id': e.id,
              'name': e.name,
              'thumb_url': e.thumbUrl,
              'rating_score': e.ratingScore,
              'review_count': e.reviewCount,
              'available_now': e.availableNow,
              'amenities_mask': e.amenitiesMask,
              'price_paise': e.pricePaise,
              'distance_m': e.distanceM,
              'lat': e.lat,
              'lng': e.lng,
            },
          )
          .toList(),
      'next_cursor': page.nextCursor,
      'radius_m': page.radiusM,
      '_ts': DateTime.now().millisecondsSinceEpoch,
    };
    await prefs.setString(k, jsonEncode(map));
  }
}

class DiscoveryRepository {
  DiscoveryRepository(this._api);

  final DiscoveryApi _api;
  String? _nextCursor;
  bool _loadingMore = false;

  String? get nextCursor => _nextCursor;

  Future<DiscoveryPage> loadFirst({
    required double lat,
    required double lng,
    required FilterState filters,
  }) async {
    _nextCursor = null;
    _loadingMore = false;
    final cacheKey = DiscoveryLocalCache.key(lat, lng, filters);
    final cached = await DiscoveryLocalCache.read(cacheKey);

    final page = await _api.fetchCentres(
      lat: lat,
      lng: lng,
      filters: filters,
    );
    // Empty 304 → keep cache if any
    if (page.items.isEmpty && cached != null) {
      _nextCursor = cached.nextCursor;
      return cached;
    }
    _nextCursor = page.nextCursor;
    await DiscoveryLocalCache.write(cacheKey, page);
    return page;
  }

  Future<List<CentreSummary>> loadMore({
    required double lat,
    required double lng,
    required FilterState filters,
  }) async {
    if (_nextCursor == null || _loadingMore) return const [];
    _loadingMore = true;
    try {
      final page = await _api.fetchCentres(
        lat: lat,
        lng: lng,
        filters: filters,
        cursor: _nextCursor,
      );
      _nextCursor = page.nextCursor;
      return page.items;
    } finally {
      _loadingMore = false;
    }
  }
}

final discoveryRepositoryProvider = Provider<DiscoveryRepository>((ref) {
  return DiscoveryRepository(ref.watch(discoveryApiProvider));
});
