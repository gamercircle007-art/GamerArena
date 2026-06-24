import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/core/network/auth_interceptor.dart';
import 'package:gamer_circle/core/network/dio_client.dart';
import 'package:gamer_circle/features/auth/data/datasources/api_auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource_impl.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/mock_auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';
import 'package:gamer_circle/features/auth/domain/usecases/check_auth_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/logout_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/request_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/send_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_otp_usecase.dart';

final getIt = GetIt.instance;

Future<void> init() async {
  getIt.registerLazySingleton<FlutterSecureStorage>(
    () => const FlutterSecureStorage(
      aOptions: AndroidOptions(encryptedSharedPreferences: true),
    ),
  );

  getIt.registerLazySingleton<AuthLocalDataSource>(
    () => AuthLocalDataSourceImpl(getIt<FlutterSecureStorage>()),
  );

  getIt.registerLazySingleton<AuthInterceptor>(
    () => AuthInterceptor(getIt<AuthLocalDataSource>()),
  );

  getIt.registerLazySingleton<DioClient>(
    () => DioClient(authInterceptor: getIt<AuthInterceptor>()),
  );

  if (AppConfig.instance.useMockApi) {
    getIt.registerLazySingleton<AuthRemoteDataSource>(
      () => MockAuthRemoteDataSource(),
    );
  } else {
    getIt.registerLazySingleton<AuthRemoteDataSource>(
      () => ApiAuthRemoteDataSource(getIt<DioClient>().dio),
    );
  }

  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(
      remoteDataSource: getIt<AuthRemoteDataSource>(),
      localDataSource: getIt<AuthLocalDataSource>(),
    ),
  );

  getIt.registerLazySingleton(() => RequestLoginOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => VerifyLoginOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => LogoutUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => CheckAuthUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => SendOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => VerifyOtpUseCase(getIt<AuthRepository>()));
}