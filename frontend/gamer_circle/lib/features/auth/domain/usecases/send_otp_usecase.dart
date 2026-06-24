import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class SendOtpParams {
  final String name;
  final String email;
  final String phone;

  const SendOtpParams({
    required this.name,
    required this.email,
    required this.phone,
  });
}

class SendOtpUseCase implements UseCase<void, SendOtpParams> {
  final AuthRepository _repository;

  SendOtpUseCase(this._repository);

  @override
  Future<Either<Failure, void>> call(SendOtpParams params) =>
      _repository.sendSignupOtp(
        name: params.name,
        email: params.email,
        phone: params.phone,
      );
}