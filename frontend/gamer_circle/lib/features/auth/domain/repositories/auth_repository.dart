import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';

abstract interface class AuthRepository {
  Future<Either<Failure, void>> requestLoginOtp({required String phone});

  Future<Either<Failure, User>> verifyLoginOtp({
    required String phone,
    required String otp,
  });

  Future<Either<Failure, void>> logout();

  Future<Either<Failure, User>> checkAuth();

  Future<Either<Failure, void>> sendSignupOtp({
    required String name,
    required String email,
    required String phone,
  });

  Future<Either<Failure, User>> verifySignupOtp({
    required String phone,
    required String otp,
    required String password,
  });
}