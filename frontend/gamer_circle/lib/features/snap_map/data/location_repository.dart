import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/messaging_api_paths.dart';
import 'package:gamer_circle/shared/models/snap_map_user.dart';

class LocationRepository {
  LocationRepository(this._dio);

  final Dio _dio;

  Future<void> updateLocation({
    required double lat,
    required double lng,
    double? accuracy,
  }) async {
    await _dio.put(SocialApiPaths.locationUpdate, data: {
      'lat': lat,
      'lng': lng,
      if (accuracy != null) 'accuracy': accuracy,
    });
  }

  Future<void> toggleGhostMode(bool enabled) async {
    await _dio.put(SocialApiPaths.ghostMode, data: {'enabled': enabled});
  }

  Future<List<SnapMapUser>> getFriendsOnMap() async {
    final res = await _dio.get(SocialApiPaths.friendsMap);
    return (res.data as List<dynamic>)
        .map((e) => SnapMapUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}