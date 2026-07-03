import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/services/location_service.dart';
import 'package:gamer_circle/features/location/data/datasources/location_local_datasource.dart';
import 'package:gamer_circle/features/location/data/datasources/location_remote_datasource.dart';
import 'package:gamer_circle/features/location/domain/repositories/location_repository.dart';

class LocationRepositoryImpl implements LocationRepository {
  final LocationLocalDataSource _localDataSource;
  final LocationRemoteDataSource _remoteDataSource;
  final LocationService _locationService;

  LocationRepositoryImpl({
    required LocationLocalDataSource localDataSource,
    required LocationRemoteDataSource remoteDataSource,
    required LocationService locationService,
  })  : _localDataSource = localDataSource,
        _remoteDataSource = remoteDataSource,
        _locationService = locationService;

  @override
  Future<bool> isOnboardingCompleted() =>
      _localDataSource.isOnboardingCompleted();

  @override
  Future<Either<Failure, void>> acceptLocation() async {
    try {
      final access = await _locationService.requestAccess();
      if (access != LocationAccessResult.granted) {
        return Left(
          AuthFailure(
            message: switch (access) {
              LocationAccessResult.serviceDisabled =>
                'Location services are turned off. Enable them in settings.',
              LocationAccessResult.deniedForever =>
                'Location permission denied. Enable it in app settings.',
              _ => 'Location permission was not granted.',
            },
          ),
        );
      }

      final deviceLocation = await _locationService.fetchCurrentLocation();

      await _localDataSource.saveLocalLocation(
        latitude: deviceLocation.latitude,
        longitude: deviceLocation.longitude,
        city: deviceLocation.city,
        country: deviceLocation.country,
      );
      await _localDataSource.markOnboardingCompleted(granted: true);

      return const Right(null);
    } catch (_) {
      return const Left(
        AuthFailure(message: 'Could not determine your location.'),
      );
    }
  }

  @override
  Future<void> skipOnboarding() async {
    await _localDataSource.markOnboardingCompleted(granted: false);
  }

  @override
  Future<Either<Failure, void>> syncCachedLocation() async {
    final granted = await _localDataSource.wasLocationGranted();
    if (!granted) return const Right(null);

    final cached = await _localDataSource.getLocalLocation();
    if (cached == null) return const Right(null);

    try {
      await _remoteDataSource.uploadLocation(
        latitude: cached['latitude'] as double,
        longitude: cached['longitude'] as double,
        city: cached['city'] as String?,
        country: cached['country'] as String?,
      );
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    }
  }
}