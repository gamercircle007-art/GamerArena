import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/exceptions.dart';
import 'package:gamer_circle/core/errors/failures.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/models/auth_response_model.dart';
import 'package:gamer_circle/features/auth/domain/entities/user.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;
  final AuthLocalDataSource _localDataSource;

  AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required AuthLocalDataSource localDataSource,
  })  : _remoteDataSource = remoteDataSource,
        _localDataSource = localDataSource;

  Future<void> _persistSession(AuthResponseModel response) async {
    await _localDataSource.saveAccessToken(response.accessToken);
    await _localDataSource.saveRefreshToken(response.refreshToken);
    await _localDataSource.saveUser(response.user);
  }

  @override
  Future<Either<Failure, void>> requestLoginOtp({required String phone}) async {
    try {
      await _remoteDataSource.requestLoginOtp(phone: phone);
      return const Right(null);
    } on AuthException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    }
  }

  @override
  Future<Either<Failure, User>> loginWithPassword({
    required String username,
    required String password,
  }) async {
    try {
      final response = await _remoteDataSource.loginWithPassword(
        username: username,
        password: password,
      );
      await _persistSession(response);
      return Right(response.user.toEntity());
    } on AuthException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    } on CacheException catch (e) {
      return Left(CacheFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, User>> verifyLoginOtp({
    required String phone,
    required String otp,
  }) async {
    try {
      final response = await _remoteDataSource.verifyLoginOtp(
        phone: phone,
        otp: otp,
      );
      await _persistSession(response);
      return Right(response.user.toEntity());
    } on AuthException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    } on CacheException catch (e) {
      return Left(CacheFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> logout() async {
    try {
      final refreshToken = await _localDataSource.getRefreshToken();
      if (refreshToken != null) {
        await _remoteDataSource.logout(refreshToken: refreshToken);
      }
      await _localDataSource.clearAll();
      return const Right(null);
    } on AuthException catch (e) {
      await _localDataSource.clearAll();
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (_) {
      await _localDataSource.clearAll();
      return const Right(null);
    } on CacheException catch (e) {
      return Left(CacheFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, User>> checkAuth() async {
    try {
      final hasToken = await _localDataSource.hasValidToken();
      if (!hasToken) {
        return const Left(AuthFailure(message: 'No active session'));
      }
      final userModel = await _localDataSource.getCachedUser();
      if (userModel == null) {
        return const Left(AuthFailure(message: 'No cached user found'));
      }
      return Right(userModel.toEntity());
    } on CacheException catch (e) {
      return Left(CacheFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> sendSignupOtp({
    required String name,
    required String username,
    required String email,
    required String phone,
  }) async {
    try {
      await _remoteDataSource.sendSignupOtp(
        name: name,
        username: username,
        email: email,
        phone: phone,
      );
      return const Right(null);
    } on AuthException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    }
  }

  @override
  Future<Either<Failure, User>> verifySignupOtp({
    required String phone,
    required String otp,
    required String password,
  }) async {
    try {
      final response = await _remoteDataSource.verifySignupOtp(
        phone: phone,
        otp: otp,
        password: password,
      );
      await _persistSession(response);
      return Right(response.user.toEntity());
    } on AuthException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message, code: e.statusCode));
    } on CacheException catch (e) {
      return Left(CacheFailure(message: e.message));
    }
  }
}