import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geocoding/geocoding.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/shared/models/nearby_parlor.dart';

const kRadiusOptions = <int>[5000, 10000, 25000, 50000];

class ParlorSearchFilters {
  const ParlorSearchFilters({
    this.query = '',
    this.radiusMeters = 10000,
    this.minRating,
    this.openNow = false,
    this.city,
    this.state,
    this.gameType,
  });

  final String query;
  final int radiusMeters;
  final double? minRating;
  final bool openNow;
  final String? city;
  final String? state;
  final String? gameType;

  ParlorSearchFilters copyWith({
    String? query,
    int? radiusMeters,
    double? minRating,
    bool? openNow,
    String? city,
    String? state,
    String? gameType,
    bool clearMinRating = false,
    bool clearCity = false,
    bool clearState = false,
    bool clearGameType = false,
  }) {
    return ParlorSearchFilters(
      query: query ?? this.query,
      radiusMeters: radiusMeters ?? this.radiusMeters,
      minRating: clearMinRating ? null : (minRating ?? this.minRating),
      openNow: openNow ?? this.openNow,
      city: clearCity ? null : (city ?? this.city),
      state: clearState ? null : (state ?? this.state),
      gameType: clearGameType ? null : (gameType ?? this.gameType),
    );
  }
}

class ParlorSearchState {
  const ParlorSearchState({
    this.filters = const ParlorSearchFilters(),
    this.parlors = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.isSearching = false,
    this.hasMore = false,
    this.page = 1,
    this.total = 0,
    this.error,
    this.locationDenied = false,
  });

  final ParlorSearchFilters filters;
  final List<NearbyParlor> parlors;
  final bool isLoading;
  final bool isLoadingMore;
  final bool isSearching;
  final bool hasMore;
  final int page;
  final int total;
  final String? error;
  final bool locationDenied;

  ParlorSearchState copyWith({
    ParlorSearchFilters? filters,
    List<NearbyParlor>? parlors,
    bool? isLoading,
    bool? isLoadingMore,
    bool? isSearching,
    bool? hasMore,
    int? page,
    int? total,
    String? error,
    bool? locationDenied,
    bool clearError = false,
  }) {
    return ParlorSearchState(
      filters: filters ?? this.filters,
      parlors: parlors ?? this.parlors,
      isLoading: isLoading ?? this.isLoading,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      isSearching: isSearching ?? this.isSearching,
      hasMore: hasMore ?? this.hasMore,
      page: page ?? this.page,
      total: total ?? this.total,
      error: clearError ? null : (error ?? this.error),
      locationDenied: locationDenied ?? this.locationDenied,
    );
  }
}

final parlorSearchProvider =
    NotifierProvider<ParlorSearchNotifier, ParlorSearchState>(
  ParlorSearchNotifier.new,
);

class ParlorSearchNotifier extends Notifier<ParlorSearchState> {
  Timer? _debounce;
  CancelToken? _cancelToken;
  final _cache = <String, ParlorSearchState>{};

  @override
  ParlorSearchState build() => const ParlorSearchState();

  String _cacheKey(ParlorSearchFilters filters, int page) =>
      '${filters.radiusMeters}|${filters.query}|${filters.minRating}|'
      '${filters.openNow}|${filters.city}|${filters.state}|'
      '${filters.gameType}|$page';

  Future<void> initialize() async {
    state = state.copyWith(isLoading: true, clearError: true);
    final pos = await ref.read(currentPositionProvider.notifier).requestAndFetch();
    if (pos == null) {
      state = state.copyWith(
        isLoading: false,
        locationDenied: true,
        parlors: const [],
      );
      return;
    }
    state = state.copyWith(locationDenied: false);
    await _fetch(page: 1, showLoading: true);
  }

  Future<void> refresh() async {
    _cache.clear();
    final pos = ref.read(currentPositionProvider).valueOrNull ??
        await ref.read(currentPositionProvider.notifier).requestAndFetch();
    if (pos == null) {
      state = state.copyWith(locationDenied: true, parlors: const []);
      return;
    }
    state = state.copyWith(locationDenied: false);
    await _fetch(page: 1, showLoading: true);
  }

  void setQuery(String query) {
    state = state.copyWith(
      filters: state.filters.copyWith(query: query),
      isSearching: true,
    );
    _debounceSearch();
  }

  void updateFilters(ParlorSearchFilters filters) {
    state = state.copyWith(filters: filters);
    _debounceSearch();
  }

  void _debounceSearch() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      _fetch(page: 1, showLoading: false);
    });
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    await _fetch(page: state.page + 1, showLoading: false, append: true);
  }

  Future<void> setManualCity(String city) async {
    state = state.copyWith(
      filters: state.filters.copyWith(city: city, clearState: true),
      isLoading: true,
      clearError: true,
    );
    try {
      final locations = await locationFromAddress('$city, India');
      if (locations.isNotEmpty) {
        final loc = locations.first;
        ref
            .read(currentPositionProvider.notifier)
            .setManualPosition(loc.latitude, loc.longitude);
        state = state.copyWith(locationDenied: false);
        await _fetch(page: 1, showLoading: true);
        return;
      }
      state = state.copyWith(
        isLoading: false,
        error: 'Could not find location for $city',
      );
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        error: 'Could not find location for $city',
      );
    }
  }

  Future<void> _fetch({
    required int page,
    required bool showLoading,
    bool append = false,
  }) async {
    final pos = ref.read(currentPositionProvider).valueOrNull;
    if (pos == null) {
      state = state.copyWith(
        isLoading: false,
        isSearching: false,
        locationDenied: true,
      );
      return;
    }

    final filters = state.filters;
    final cacheKey = _cacheKey(filters, page);
    if (!append && _cache.containsKey(cacheKey)) {
      final cached = _cache[cacheKey]!;
      state = state.copyWith(
        parlors: cached.parlors,
        hasMore: cached.hasMore,
        page: cached.page,
        total: cached.total,
        isLoading: false,
        isSearching: false,
        isLoadingMore: false,
        clearError: true,
      );
      return;
    }

    _cancelToken?.cancel();
    _cancelToken = CancelToken();

    state = state.copyWith(
      isLoading: showLoading && !append,
      isLoadingMore: append,
      isSearching: !showLoading && !append,
      clearError: true,
    );

    try {
      final response = await ref.read(socialApiProvider).searchParlors(
            lat: pos.latitude,
            lng: pos.longitude,
            radius: filters.radiusMeters.toDouble(),
            q: filters.query.isEmpty ? null : filters.query,
            minRating: filters.minRating,
            openNow: filters.openNow ? true : null,
            city: filters.city,
            state: filters.state,
            gameType: filters.gameType,
            page: page,
            cancelToken: _cancelToken,
          );

      final parlors = append
          ? [...state.parlors, ...response.items]
          : response.items;

      final next = state.copyWith(
        parlors: parlors,
        hasMore: response.hasMore,
        page: response.page,
        total: response.total,
        isLoading: false,
        isLoadingMore: false,
        isSearching: false,
        clearError: true,
      );
      state = next;
      if (!append) {
        _cache[cacheKey] = next;
      }
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        isSearching: false,
        error: e.message ?? 'Search failed',
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        isSearching: false,
        error: e.toString(),
      );
    }
  }
}