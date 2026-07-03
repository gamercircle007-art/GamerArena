class UserLocation {
  UserLocation({
    required this.userId,
    required this.lat,
    required this.lng,
    this.accuracy,
    this.ghostMode = false,
    this.locationPrivacy = 'friends',
    this.updatedAt,
  });

  final String userId;
  final double lat;
  final double lng;
  final double? accuracy;
  final bool ghostMode;
  final String locationPrivacy;
  final DateTime? updatedAt;

  factory UserLocation.fromJson(Map<String, dynamic> json) => UserLocation(
        userId: json['user_id'] as String,
        lat: (json['lat'] as num? ?? json['latitude'] as num).toDouble(),
        lng: (json['lng'] as num? ?? json['longitude'] as num).toDouble(),
        accuracy: (json['accuracy'] as num?)?.toDouble(),
        ghostMode: json['ghost_mode'] as bool? ?? false,
        locationPrivacy: json['location_privacy'] as String? ?? 'friends',
        updatedAt: json['updated_at'] != null
            ? DateTime.parse(json['updated_at'] as String)
            : null,
      );
}