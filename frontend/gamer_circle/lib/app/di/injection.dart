import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:gamer_circle/app/config/app_config.dart';
import 'package:gamer_circle/core/network/auth_interceptor.dart';
import 'package:gamer_circle/core/network/dio_client.dart';
import 'package:gamer_circle/core/services/location_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:gamer_circle/features/location/data/datasources/api_location_remote_datasource.dart';
import 'package:gamer_circle/features/location/data/datasources/location_local_datasource.dart';
import 'package:gamer_circle/features/location/data/datasources/location_remote_datasource.dart';
import 'package:gamer_circle/features/location/data/datasources/mock_location_remote_datasource.dart';
import 'package:gamer_circle/features/location/data/repositories/location_repository_impl.dart';
import 'package:gamer_circle/features/location/domain/repositories/location_repository.dart';
import 'package:gamer_circle/features/location/domain/usecases/accept_location_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/check_location_onboarding_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/skip_location_usecase.dart';
import 'package:gamer_circle/features/location/domain/usecases/sync_location_usecase.dart';
import 'package:gamer_circle/features/auth/data/datasources/api_auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_local_datasource_impl.dart';
import 'package:gamer_circle/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/datasources/mock_auth_remote_datasource.dart';
import 'package:gamer_circle/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:gamer_circle/features/auth/domain/repositories/auth_repository.dart';
import 'package:gamer_circle/features/auth/domain/usecases/check_auth_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/login_with_password_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/logout_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/request_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/send_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_login_otp_usecase.dart';
import 'package:gamer_circle/features/auth/domain/usecases/verify_otp_usecase.dart';
import 'package:gamer_circle/features/onboarding/data/onboarding_prefs.dart';

final getIt = GetIt.instance;

Future<void> init() async {
  final sharedPreferences = await SharedPreferences.getInstance();
  getIt.registerLazySingleton<SharedPreferences>(() => sharedPreferences);

  getIt.registerLazySingleton<OnboardingPrefs>(
    () => OnboardingPrefs(getIt<SharedPreferences>()),
  );

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

  getIt.registerLazySingleton(() => LoginWithPasswordUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => RequestLoginOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => VerifyLoginOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => LogoutUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => CheckAuthUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => SendOtpUseCase(getIt<AuthRepository>()));
  getIt.registerLazySingleton(() => VerifyOtpUseCase(getIt<AuthRepository>()));

  getIt.registerLazySingleton<LocationService>(() => LocationService());

  getIt.registerLazySingleton<LocationLocalDataSource>(
    () => LocationLocalDataSourceImpl(getIt<SharedPreferences>()),
  );

  if (AppConfig.instance.useMockApi) {
    getIt.registerLazySingleton<LocationRemoteDataSource>(
      () => MockLocationRemoteDataSource(),
    );
  } else {
    getIt.registerLazySingleton<LocationRemoteDataSource>(
      () => ApiLocationRemoteDataSource(getIt<DioClient>().dio),
    );
  }

  getIt.registerLazySingleton<LocationRepository>(
    () => LocationRepositoryImpl(
      localDataSource: getIt<LocationLocalDataSource>(),
      remoteDataSource: getIt<LocationRemoteDataSource>(),
      locationService: getIt<LocationService>(),
    ),
  );

  getIt.registerLazySingleton(
    () => CheckLocationOnboardingUseCase(getIt<LocationRepository>()),
  );
  getIt.registerLazySingleton(
    () => AcceptLocationUseCase(getIt<LocationRepository>()),
  );
  getIt.registerLazySingleton(
    () => SkipLocationUseCase(getIt<LocationRepository>()),
  );
  getIt.registerLazySingleton(
    () => SyncLocationUseCase(getIt<LocationRepository>()),
  );
}