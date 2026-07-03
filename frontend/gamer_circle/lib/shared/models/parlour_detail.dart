class ParlourDetail {
  const ParlourDetail({
    required this.id,
    required this.name,
    this.description,
    this.address,
    this.city,
    this.state,
    this.latitude,
    this.longitude,
    this.phone,
    this.website,
    this.rating,
    this.reviewCount = 0,
    this.isVerified = false,
    this.images = const [],
    this.amenities = const [],
    this.games = const [],
    this.offers = const [],
    this.categoryRatings = const {},
    this.openingHours,
    this.isOpen = true,
    this.distanceMeters,
    this.startingPrice,
    this.policies,
  });

  final String id;
  final String name;
  final String? description;
  final String? address;
  final String? city;
  final String? state;
  final double? latitude;
  final double? longitude;
  final String? phone;
  final String? website;
  final double? rating;
  final int reviewCount;
  final bool isVerified;
  final List<String> images;
  final List<String> amenities;
  final List<ParlourGame> games;
  final List<ParlourOffer> offers;
  final Map<String, double> categoryRatings;
  final String? openingHours;
  final bool isOpen;
  final double? distanceMeters;
  final double? startingPrice;
  final String? policies;

  String get displayImage => images.isNotEmpty ? images.first : '';

  String get locationLine {
    final parts = [city, state]
        .whereType<String>()
        .where((e) => e.isNotEmpty)
        .toList();
    if (parts.isNotEmpty) return parts.join(', ');
    return address ?? '';
  }

  factory ParlourDetail.fromJson(Map<String, dynamic> json) => ParlourDetail(
        id: json['id'] as String,
        name: json['name'] as String,
        description: json['description'] as String?,
        address: json['address'] as String?,
        city: json['city'] as String?,
        state: json['state'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble() ??
            (json['lat'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble() ??
            (json['lng'] as num?)?.toDouble(),
        phone: json['phone'] as String?,
        website: json['website'] as String?,
        rating: (json['rating'] as num?)?.toDouble(),
        reviewCount: json['review_count'] as int? ?? 0,
        isVerified: json['is_verified'] as bool? ?? false,
        images: (json['images'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        amenities: (json['amenities'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        games: (json['games'] as List<dynamic>?)
                ?.map((e) => ParlourGame.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        offers: (json['offers'] as List<dynamic>?)
                ?.map((e) => ParlourOffer.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        categoryRatings: (json['category_ratings'] as Map<String, dynamic>?)
                ?.map((k, v) => MapEntry(k, (v as num).toDouble())) ??
            const {},
        openingHours: json['opening_hours'] as String?,
        isOpen: json['is_open'] as bool? ?? true,
        distanceMeters: (json['distance_meters'] as num?)?.toDouble(),
        startingPrice: (json['starting_price'] as num?)?.toDouble() ??
            (json['price_per_hour'] as num?)?.toDouble(),
        policies: json['policies'] as String?,
      );
}

class ParlourGame {
  const ParlourGame({
    required this.id,
    required this.name,
    this.iconUrl,
    this.pricePerHour,
    this.platform,
  });

  final String id;
  final String name;
  final String? iconUrl;
  final double? pricePerHour;
  final String? platform;

  factory ParlourGame.fromJson(Map<String, dynamic> json) => ParlourGame(
        id: json['id'] as String,
        name: json['name'] as String,
        iconUrl: json['icon_url'] as String?,
        pricePerHour: (json['price_per_hour'] as num?)?.toDouble(),
        platform: json['platform'] as String?,
      );
}

class ParlourOffer {
  const ParlourOffer({
    required this.id,
    required this.title,
    this.description,
    this.discountPercent,
    this.discountAmount,
    this.code,
    this.validUntil,
  });

  final String id;
  final String title;
  final String? description;
  final int? discountPercent;
  final double? discountAmount;
  final String? code;
  final DateTime? validUntil;

  factory ParlourOffer.fromJson(Map<String, dynamic> json) => ParlourOffer(
        id: json['id'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        discountPercent: json['discount_percent'] as int?,
        discountAmount: (json['discount_amount'] as num?)?.toDouble(),
        code: json['code'] as String?,
        validUntil: json['valid_until'] != null
            ? DateTime.parse(json['valid_until'] as String)
            : null,
      );
}

class ParlourReview {
  const ParlourReview({
    required this.id,
    required this.userName,
    required this.rating,
    required this.comment,
    required this.createdAt,
    this.userAvatar,
    this.categoryRatings = const {},
  });

  final String id;
  final String userName;
  final double rating;
  final String comment;
  final DateTime createdAt;
  final String? userAvatar;
  final Map<String, double> categoryRatings;

  factory ParlourReview.fromJson(Map<String, dynamic> json) => ParlourReview(
        id: json['id'] as String,
        userName: json['user_name'] as String,
        rating: (json['rating'] as num).toDouble(),
        comment: json['comment'] as String? ?? '',
        createdAt: DateTime.parse(json['created_at'] as String),
        userAvatar: json['user_avatar'] as String?,
        categoryRatings: (json['category_ratings'] as Map<String, dynamic>?)
                ?.map((k, v) => MapEntry(k, (v as num).toDouble())) ??
            const {},
      );
}