import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class LoginWithPasswordParams {
  final String username;
  final String password;

  const LoginWithPasswordParams({
    required this.username,
    required this.password,
  });
}

class LoginWithPasswordUseCase
    implements UseCase<User, LoginWithPasswordParams> {
  final AuthRepository _repository;

  LoginWithPasswordUseCase(this._repository);

  @override
  Future<Either<Failure, User>> call(LoginWithPasswordParams params) =>
      _repository.loginWithPassword(
        username: params.username,
        password: params.password,
      );
}