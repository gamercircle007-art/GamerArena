class NearbyParlor {
  const NearbyParlor({
    required this.id,
    required this.name,
    required this.distanceMeters,
    this.lat,
    this.lng,
    this.logoUrl,
    this.address,
    this.city,
    this.state,
    this.country,
    this.gameTypes = const [],
    this.isVerified = false,
    this.followerCount = 0,
    this.rating,
    this.phone,
    this.website,
    this.isOpen = true,
    this.images = const [],
  });

  final String id;
  final String name;
  final double distanceMeters;
  final double? lat;
  final double? lng;
  final String? logoUrl;
  final String? address;
  final String? city;
  final String? state;
  final String? country;
  final List<String> gameTypes;
  final bool isVerified;
  final int followerCount;
  final double? rating;
  final String? phone;
  final String? website;
  final bool isOpen;
  final List<String> images;

  String get displayImage => images.isNotEmpty ? images.first : (logoUrl ?? '');

  String get distanceLabel {
    if (distanceMeters < 1000) {
      return '${distanceMeters.round()} m away';
    }
    return '${(distanceMeters / 1000).toStringAsFixed(1)} km away';
  }

  String get locationLine {
    final parts = [city, state].where((e) => e != null && e.isNotEmpty).toList();
    if (parts.isNotEmpty) return parts.join(', ');
    return address ?? '';
  }

  factory NearbyParlor.fromJson(Map<String, dynamic> json) => NearbyParlor(
        id: json['id'] as String,
        name: json['name'] as String,
        distanceMeters: (json['distance_meters'] as num).toDouble(),
        lat: (json['lat'] as num?)?.toDouble(),
        lng: (json['lng'] as num?)?.toDouble(),
        logoUrl: json['logo_url'] as String?,
        address: json['address'] as String?,
        city: json['city'] as String?,
        state: json['state'] as String?,
        country: json['country'] as String?,
        gameTypes: (json['game_types'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        isVerified: json['is_verified'] as bool? ?? false,
        followerCount: json['follower_count'] as int? ?? 0,
        rating: (json['rating'] as num?)?.toDouble(),
        phone: json['phone'] as String?,
        website: json['website'] as String?,
        isOpen: json['is_open'] as bool? ?? true,
        images: (json['images'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
      );
}