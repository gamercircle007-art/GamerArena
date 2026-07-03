import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geocoding/geocoding.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/features/parlors/data/parlor_search_repository.dart';
import 'package:gamer_circle/shared/models/parlour_detail.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

final parlorSearchRepositoryProvider = Provider<ParlorSearchRepository>((ref) {
  return ParlorSearchRepository(ref.watch(dioProvider));
});

class ParlourSearchState {
  const ParlourSearchState({
    this.filters = const ParlourSearchFilters(),
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = false,
    this.page = 1,
    this.total = 0,
    this.error,
    this.locationDenied = false,
  });

  final ParlourSearchFilters filters;
  final List<ParlourSearchItem> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final int total;
  final String? error;
  final bool locationDenied;

  ParlourSearchState copyWith({
    ParlourSearchFilters? filters,
    List<ParlourSearchItem>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    int? total,
    String? error,
    bool? locationDenied,
    bool clearError = false,
  }) =>
      ParlourSearchState(
        filters: filters ?? this.filters,
        items: items ?? this.items,
        isLoading: isLoading ?? this.isLoading,
        isLoadingMore: isLoadingMore ?? this.isLoadingMore,
        hasMore: hasMore ?? this.hasMore,
        page: page ?? this.page,
        total: total ?? this.total,
        error: clearError ? null : (error ?? this.error),
        locationDenied: locationDenied ?? this.locationDenied,
      );
}

final parlourSearchProvider =
    NotifierProvider<ParlourSearchNotifier, ParlourSearchState>(
  ParlourSearchNotifier.new,
);

class ParlourSearchNotifier extends Notifier<ParlourSearchState> {
  Timer? _debounce;
  CancelToken? _cancelToken;

  @override
  ParlourSearchState build() => const ParlourSearchState();

  ParlorSearchRepository get _repo => ref.read(parlorSearchRepositoryProvider);

  Future<void> initialize({ParlourSearchFilters? initialFilters}) async {
    if (initialFilters != null) {
      state = state.copyWith(filters: initialFilters);
    }
    state = state.copyWith(isLoading: true, clearError: true);
    final pos = await ref.read(currentPositionProvider.notifier).requestAndFetch();
    if (pos == null) {
      state = state.copyWith(
        isLoading: false,
        locationDenied: true,
        items: const [],
      );
      return;
    }
    await _fetch(page: 1, showLoading: true);
  }

  void setQuery(String query) {
    state = state.copyWith(
      filters: state.filters.copyWith(query: query),
    );
    _debounceSearch();
  }

  void updateFilters(ParlourSearchFilters filters) {
    state = state.copyWith(filters: filters);
    _debounceSearch();
  }

  void _debounceSearch() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      _fetch(page: 1, showLoading: false);
    });
  }

  Future<void> refresh() async {
    final pos = ref.read(currentPositionProvider).valueOrNull ??
        await ref.read(currentPositionProvider.notifier).requestAndFetch();
    if (pos == null) {
      state = state.copyWith(locationDenied: true, items: const []);
      return;
    }
    await _fetch(page: 1, showLoading: true);
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore) return;
    await _fetch(page: state.page + 1, showLoading: false, append: true);
  }

  Future<void> setManualCity(String city) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final locations = await locationFromAddress('$city, India');
      if (locations.isNotEmpty) {
        final loc = locations.first;
        ref
            .read(currentPositionProvider.notifier)
            .setManualPosition(loc.latitude, loc.longitude);
        state = state.copyWith(
          filters: state.filters.copyWith(city: city),
          locationDenied: false,
        );
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
        locationDenied: true,
      );
      return;
    }

    _cancelToken?.cancel();
    _cancelToken = CancelToken();

    state = state.copyWith(
      isLoading: showLoading && !append,
      isLoadingMore: append,
      clearError: true,
    );

    try {
      final response = await _repo.searchParlours(
        lat: pos.latitude,
        lng: pos.longitude,
        filters: state.filters,
        page: page,
        cancelToken: _cancelToken,
      );

      final items = append ? [...state.items, ...response.items] : response.items;
      state = state.copyWith(
        items: items,
        hasMore: response.hasMore,
        page: response.page,
        total: response.total,
        isLoading: false,
        isLoadingMore: false,
        locationDenied: false,
        clearError: true,
      );
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        error: e.message ?? 'Search failed',
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        isLoadingMore: false,
        error: e.toString(),
      );
    }
  }
}

final parlourDetailProvider = FutureProvider.family<ParlourDetail, String>(
  (ref, parlourId) async {
    final pos = ref.read(currentPositionProvider).valueOrNull;
    return ref.read(parlorSearchRepositoryProvider).fetchParlourDetail(
          parlourId,
          lat: pos?.latitude,
          lng: pos?.longitude,
        );
  },
);

final parlourReviewsProvider =
    FutureProvider.family<List<ParlourReview>, String>(
  (ref, parlourId) async {
    return ref.read(parlorSearchRepositoryProvider).fetchReviews(parlourId);
  },
);