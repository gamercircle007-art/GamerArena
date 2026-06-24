import 'package:dartz/dartz.dart';
import 'package:gamer_circle/core/errors/failures.dart';

abstract class UseCase<Type, Params> {
  Future<Either<Failure, Type>> call(Params params);
}

class NoParams {}
