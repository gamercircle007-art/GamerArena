class SnapMapUser {
  SnapMapUser({
    required this.userId,
    this.name,
    this.avatarUrl,
    required this.lat,
    required this.lng,
    this.distanceKm,
    required this.updatedAt,
  });

  final String userId;
  final String? name;
  final String? avatarUrl;
  final double lat;
  final double lng;
  final double? distanceKm;
  final DateTime updatedAt;

  factory SnapMapUser.fromJson(Map<String, dynamic> json) => SnapMapUser(
        userId: json['user_id'] as String,
        name: json['name'] as String?,
        avatarUrl: json['avatar_url'] as String?,
        lat: (json['lat'] as num).toDouble(),
        lng: (json['lng'] as num).toDouble(),
        distanceKm: (json['distance_km'] as num?)?.toDouble(),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}