import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class CheckAuthUseCase implements UseCase<User, NoParams> {
  final AuthRepository _repository;

  CheckAuthUseCase(this._repository);

  @override
  Future<Either<Failure, User>> call(NoParams params) =>
      _repository.checkAuth();
}
