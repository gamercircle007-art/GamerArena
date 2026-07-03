import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/features/home/data/home_repository.dart';
import 'package:gamer_circle/shared/models/gc_points.dart';
import 'package:gamer_circle/shared/models/home_data.dart';

final homeRepositoryProvider = Provider<HomeRepository>((ref) {
  return HomeRepository(ref.watch(dioProvider));
});

class HomeState {
  const HomeState({
    this.data = HomeData.empty,
    this.isLoading = false,
    this.error,
    this.locationDenied = false,
  });

  final HomeData data;
  final bool isLoading;
  final String? error;
  final bool locationDenied;

  HomeState copyWith({
    HomeData? data,
    bool? isLoading,
    String? error,
    bool? locationDenied,
    bool clearError = false,
  }) =>
      HomeState(
        data: data ?? this.data,
        isLoading: isLoading ?? this.isLoading,
        error: clearError ? null : (error ?? this.error),
        locationDenied: locationDenied ?? this.locationDenied,
      );
}

final homeProvider = NotifierProvider<HomeNotifier, HomeState>(HomeNotifier.new);

class HomeNotifier extends Notifier<HomeState> {
  CancelToken? _cancelToken;

  @override
  HomeState build() => const HomeState();

  HomeRepository get _repo => ref.read(homeRepositoryProvider);

  Future<void> load() async {
    _cancelToken?.cancel();
    _cancelToken = CancelToken();
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final pos = ref.read(currentPositionProvider).valueOrNull ??
          await ref.read(currentPositionProvider.notifier).requestAndFetch();

      if (pos == null) {
        state = state.copyWith(
          isLoading: false,
          locationDenied: true,
          data: const HomeData(
            locationLabel: 'Khora Colony, Ghaziabad',
            gcPoints: GcPoints(balance: 200, lifetimeEarned: 200),
          ),
        );
        return;
      }

      final data = await _repo.fetchHomeData(
        lat: pos.latitude,
        lng: pos.longitude,
        cancelToken: _cancelToken,
      );
      state = state.copyWith(
        data: data,
        isLoading: false,
        locationDenied: false,
        clearError: true,
      );
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      state = state.copyWith(
        isLoading: false,
        error: e.message ?? 'Failed to load home',
        data: HomeData.empty,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
        data: HomeData.empty,
      );
    }
  }

  Future<void> refresh() => load();
}