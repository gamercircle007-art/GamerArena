import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class VerifyOtpParams {
  final String phone;
  final String otp;
  final String password;

  const VerifyOtpParams({
    required this.phone,
    required this.otp,
    required this.password,
  });
}

class VerifyOtpUseCase implements UseCase<User, VerifyOtpParams> {
  final AuthRepository _repository;

  VerifyOtpUseCase(this._repository);

  @override
  Future<Either<Failure, User>> call(VerifyOtpParams params) =>
      _repository.verifySignupOtp(
        phone: params.phone,
        otp: params.otp,
        password: params.password,
      );
}