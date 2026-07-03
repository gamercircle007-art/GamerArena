import 'package:gamer_circle/features/location/data/datasources/location_remote_datasource.dart';

class MockLocationRemoteDataSource implements LocationRemoteDataSource {
  @override
  Future<void> uploadLocation({
    required double latitude,
    required double longitude,
    String? city,
    String? country,
  }) async {
    await Future.delayed(const Duration(milliseconds: 400));
  }
}