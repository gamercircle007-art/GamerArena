import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/features/home/data/home_repository.dart';
import 'package:gamer_circle/features/home/providers/home_filters_provider.dart';
import 'package:gamer_circle/features/home/providers/selected_location_provider.dart';
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
      final selectedCity = ref.read(homeSelectedCityProvider);
      final pickFilter = ref.read(homeQuickPickFilterProvider);
      final radiusFilter = ref.read(homeRadiusFilterProvider);
      final selectedLocation =
          await ref.read(selectedLocationProvider.future);

      double? lat;
      double? lng;
      String? city;
      String locationLabel = selectedLocation.label;

      if (selectedCity != null) {
        city = selectedCity.name;
        locationLabel = selectedCity.name;
        lat = selectedCity.latitude ?? selectedLocation.latitude;
        lng = selectedCity.longitude ?? selectedLocation.longitude;
      } else {
        lat = selectedLocation.latitude;
        lng = selectedLocation.longitude;
      }

      final data = await _repo.fetchHomeData(
        lat: lat,
        lng: lng,
        city: city,
        pickFilter: pickFilter,
        radiusMeters: radiusFilter.radiusMeters,
        cancelToken: _cancelToken,
      );
      state = state.copyWith(
        data: data.copyWithLocationLabel(locationLabel),
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
      final message = e is StateError || e.toString().contains('Assertion failed')
          ? 'Failed to load home data. Pull to refresh.'
          : e.toString();
      state = state.copyWith(
        isLoading: false,
        error: message,
        data: HomeData.empty.copyWithLocationLabel(selectedLocation.label),
      );
    }
  }

  Future<void> refresh() => load();
}