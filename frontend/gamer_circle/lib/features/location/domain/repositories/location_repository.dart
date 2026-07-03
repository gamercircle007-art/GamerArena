import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';

abstract interface class LocationRepository {
  Future<bool> isOnboardingCompleted();

  /// Request permission, capture GPS, and cache locally (works before login).
  Future<Either<Failure, void>> acceptLocation();

  Future<void> skipOnboarding();

  /// Upload cached coordinates after the user authenticates.
  Future<Either<Failure, void>> syncCachedLocation();
}