import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/location/domain/repositories/location_repository.dart';

class SkipLocationUseCase implements UseCase<void, NoParams> {
  final LocationRepository _repository;

  SkipLocationUseCase(this._repository);

  @override
  Future<Either<Failure, void>> call(NoParams params) async {
    await _repository.skipOnboarding();
    return const Right(null);
  }
}