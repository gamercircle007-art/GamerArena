class ParlourSearchItem {
  const ParlourSearchItem({
    required this.id,
    required this.name,
    this.imageUrl,
    this.address,
    this.city,
    this.state,
    this.rating,
    this.reviewCount = 0,
    this.distanceMeters,
    this.startingPrice,
    this.originalPrice,
    this.isVerified = false,
    this.isOpen = true,
    this.gameTypes = const [],
    this.offerText,
    this.discountPercent,
  });

  final String id;
  final String name;
  final String? imageUrl;
  final String? address;
  final String? city;
  final String? state;
  final double? rating;
  final int reviewCount;
  final double? distanceMeters;
  final double? startingPrice;
  final double? originalPrice;
  final bool isVerified;
  final bool isOpen;
  final List<String> gameTypes;
  final String? offerText;
  final int? discountPercent;

  String get distanceLabel {
    final d = distanceMeters;
    if (d == null) return '';
    if (d < 1000) return '${d.round()} m';
    return '${(d / 1000).toStringAsFixed(1)} km';
  }

  String get locationLine {
    final parts = [city, state]
        .whereType<String>()
        .where((e) => e.isNotEmpty)
        .toList();
    if (parts.isNotEmpty) return parts.join(', ');
    return address ?? '';
  }

  factory ParlourSearchItem.fromJson(Map<String, dynamic> json) =>
      ParlourSearchItem(
        id: json['id'] as String,
        name: json['name'] as String,
        imageUrl: json['image_url'] as String? ?? json['logo_url'] as String?,
        address: json['address'] as String?,
        city: json['city'] as String?,
        state: json['state'] as String?,
        rating: (json['rating'] as num?)?.toDouble(),
        reviewCount: json['review_count'] as int? ?? 0,
        distanceMeters: (json['distance_meters'] as num?)?.toDouble(),
        startingPrice: (json['starting_price'] as num?)?.toDouble() ??
            (json['price_per_hour'] as num?)?.toDouble(),
        originalPrice: (json['original_price'] as num?)?.toDouble(),
        isVerified: json['is_verified'] as bool? ?? false,
        isOpen: json['is_open'] as bool? ?? true,
        gameTypes: (json['game_types'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        offerText: json['offer_text'] as String?,
        discountPercent: json['discount_percent'] as int?,
      );
}

class ParlourSearchResponse {
  const ParlourSearchResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.limit,
    required this.hasMore,
  });

  final List<ParlourSearchItem> items;
  final int total;
  final int page;
  final int limit;
  final bool hasMore;

  factory ParlourSearchResponse.fromJson(Map<String, dynamic> json) =>
      ParlourSearchResponse(
        items: (json['items'] as List<dynamic>? ?? [])
            .map((e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        total: json['total'] as int? ?? 0,
        page: json['page'] as int? ?? 1,
        limit: json['limit'] as int? ?? 20,
        hasMore: json['has_more'] as bool? ?? false,
      );
}

class ParlourSearchFilters {
  const ParlourSearchFilters({
    this.query = '',
    this.city,
    this.checkIn,
    this.checkOut,
    this.numPlayers = 1,
    this.minPrice,
    this.maxPrice,
    this.minRating,
    this.gameType,
    this.sortBy = 'relevance',
    this.radiusMeters = 10000,
    this.under299 = false,
  });

  final String query;
  final String? city;
  final DateTime? checkIn;
  final DateTime? checkOut;
  final int numPlayers;
  final double? minPrice;
  final double? maxPrice;
  final double? minRating;
  final String? gameType;
  final String sortBy;
  final int radiusMeters;
  final bool under299;

  ParlourSearchFilters copyWith({
    String? query,
    String? city,
    DateTime? checkIn,
    DateTime? checkOut,
    int? numPlayers,
    double? minPrice,
    double? maxPrice,
    double? minRating,
    String? gameType,
    String? sortBy,
    int? radiusMeters,
    bool? under299,
    bool clearCity = false,
    bool clearMinRating = false,
    bool clearGameType = false,
    bool clearMinPrice = false,
    bool clearMaxPrice = false,
  }) =>
      ParlourSearchFilters(
        query: query ?? this.query,
        city: clearCity ? null : (city ?? this.city),
        checkIn: checkIn ?? this.checkIn,
        checkOut: checkOut ?? this.checkOut,
        numPlayers: numPlayers ?? this.numPlayers,
        minPrice: clearMinPrice ? null : (minPrice ?? this.minPrice),
        maxPrice: clearMaxPrice ? null : (maxPrice ?? this.maxPrice),
        minRating: clearMinRating ? null : (minRating ?? this.minRating),
        gameType: clearGameType ? null : (gameType ?? this.gameType),
        sortBy: sortBy ?? this.sortBy,
        radiusMeters: radiusMeters ?? this.radiusMeters,
        under299: under299 ?? this.under299,
      );
}