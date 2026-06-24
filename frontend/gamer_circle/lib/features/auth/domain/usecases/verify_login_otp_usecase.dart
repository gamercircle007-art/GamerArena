import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class VerifyLoginOtpParams {
  final String phone;
  final String otp;

  const VerifyLoginOtpParams({required this.phone, required this.otp});
}

class VerifyLoginOtpUseCase implements UseCase<User, VerifyLoginOtpParams> {
  final AuthRepository _repository;

  VerifyLoginOtpUseCase(this._repository);

  @override
  Future<Either<Failure, User>> call(VerifyLoginOtpParams params) =>
      _repository.verifyLoginOtp(phone: params.phone, otp: params.otp);
}