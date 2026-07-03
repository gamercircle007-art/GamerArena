import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/core/providers/location_provider.dart';
import 'package:gamer_circle/features/home/data/home_repository.dart';
import 'package:gamer_circle/features/home/providers/selected_location_provider.dart';
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
      final selectedLocation =
          await ref.read(selectedLocationProvider.future);

      ref.read(currentPositionProvider.notifier).setManualPosition(
            selectedLocation.latitude,
            selectedLocation.longitude,
          );

      final data = await _repo.fetchHomeData(
        lat: selectedLocation.latitude,
        lng: selectedLocation.longitude,
        cancelToken: _cancelToken,
      );
      state = state.copyWith(
        data: data.copyWithLocationLabel(selectedLocation.label),
        isLoading: false,
        locationDenied: false,
        clearError: true,
      );
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      final selectedLocation =
          ref.read(selectedLocationProvider).valueOrNull ??
              SelectedLocation.defaultLocation;
      state = state.copyWith(
        isLoading: false,
        error: e.message ?? 'Failed to load home',
        data: HomeData.empty.copyWithLocationLabel(selectedLocation.label),
      );
    } catch (e) {
      final selectedLocation =
          ref.read(selectedLocationProvider).valueOrNull ??
              SelectedLocation.defaultLocation;
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
        data: HomeData.empty.copyWithLocationLabel(selectedLocation.label),
      );
    }
  }

  Future<void> refresh() => load();
}