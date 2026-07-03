abstract interface class LocationRemoteDataSource {
  Future<void> uploadLocation({
    required double latitude,
    required double longitude,
    String? city,
    String? country,
  });
}