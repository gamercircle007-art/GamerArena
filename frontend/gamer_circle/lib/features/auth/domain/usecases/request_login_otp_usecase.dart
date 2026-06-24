import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/core/usecases/usecase.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class RequestLoginOtpParams {
  final String phone;
  const RequestLoginOtpParams({required this.phone});
}

class RequestLoginOtpUseCase implements UseCase<void, RequestLoginOtpParams> {
  final AuthRepository _repository;

  RequestLoginOtpUseCase(this._repository);

  @override
  Future<Either<Failure, void>> call(RequestLoginOtpParams params) =>
      _repository.requestLoginOtp(phone: params.phone);
}