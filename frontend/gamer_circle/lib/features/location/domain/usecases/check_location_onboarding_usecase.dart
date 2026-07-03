import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/location/domain/repositories/location_repository.dart';

class CheckLocationOnboardingUseCase implements UseCase<bool, NoParams> {
  final LocationRepository _repository;

  CheckLocationOnboardingUseCase(this._repository);

  @override
  Future<Either<Failure, bool>> call(NoParams params) async {
    final completed = await _repository.isOnboardingCompleted();
    return Right(completed);
  }
}