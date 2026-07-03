import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/app/di/injection.dart';
import 'package:gamer_circle/core/data/reel_remote_datasource.dart';
import 'package:gamer_circle/core/data/social_remote_datasource.dart';
import 'package:gamer_circle/core/network/dio_client.dart';

final dioProvider = Provider<Dio>((ref) => getIt<DioClient>().dio);

final socialApiProvider = Provider<SocialRemoteDataSource>(
  (ref) => SocialRemoteDataSource(ref.watch(dioProvider)),
);

final reelApiProvider = Provider<ReelRemoteDataSource>(
  (ref) => ReelRemoteDataSource(ref.watch(dioProvider)),
);