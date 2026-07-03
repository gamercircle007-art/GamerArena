class Parlor {
  const Parlor({
    required this.id,
    required this.name,
    this.logoUrl,
    this.isVerified = false,
    this.description,
    this.address,
    this.gameTypes = const [],
    this.followerCount = 0,
    this.postCount = 0,
    this.isFollowing = false,
    this.rating,
    this.phone,
    this.website,
    this.latitude,
    this.longitude,
  });

  final String id;
  final String name;
  final String? logoUrl;
  final bool isVerified;
  final String? description;
  final String? address;
  final List<String> gameTypes;
  final int followerCount;
  final int postCount;
  final bool isFollowing;
  final double? rating;
  final String? phone;
  final String? website;
  final double? latitude;
  final double? longitude;

  factory Parlor.fromJson(Map<String, dynamic> json) => Parlor(
        id: json['id'] as String,
        name: json['name'] as String,
        logoUrl: json['logo_url'] as String?,
        isVerified: json['is_verified'] as bool? ?? false,
        description: json['description'] as String?,
        address: json['address'] as String?,
        gameTypes: (json['game_types'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        followerCount: json['follower_count'] as int? ?? 0,
        postCount: json['post_count'] as int? ?? 0,
        isFollowing: json['is_following'] as bool? ?? false,
        rating: (json['rating'] as num?)?.toDouble(),
        phone: json['phone'] as String?,
        website: json['website'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'logo_url': logoUrl,
        'is_verified': isVerified,
        'description': description,
        'address': address,
        'game_types': gameTypes,
        'follower_count': followerCount,
        'post_count': postCount,
        'is_following': isFollowing,
      };

  Parlor copyWith({
    String? id,
    String? name,
    String? logoUrl,
    bool? isVerified,
    String? description,
    String? address,
    List<String>? gameTypes,
    int? followerCount,
    int? postCount,
    bool? isFollowing,
  }) =>
      Parlor(
        id: id ?? this.id,
        name: name ?? this.name,
        logoUrl: logoUrl ?? this.logoUrl,
        isVerified: isVerified ?? this.isVerified,
        description: description ?? this.description,
        address: address ?? this.address,
        gameTypes: gameTypes ?? this.gameTypes,
        followerCount: followerCount ?? this.followerCount,
        postCount: postCount ?? this.postCount,
        isFollowing: isFollowing ?? this.isFollowing,
      );
}