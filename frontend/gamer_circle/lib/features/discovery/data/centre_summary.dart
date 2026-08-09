/// Compact discovery list DTO — hand-written fromJson (hot path).
class CentreSummary {
  const CentreSummary({
    required this.id,
    required this.name,
    required this.distanceM,
    this.thumbUrl,
    this.ratingScore = 0,
    this.reviewCount = 0,
    this.availableNow = false,
    this.amenitiesMask = 0,
    this.pricePaise,
    this.lat,
    this.lng,
  });

  final String id;
  final String name;
  final String? thumbUrl;
  final double ratingScore;
  final int reviewCount;
  final bool availableNow;
  final int amenitiesMask;
  final int? pricePaise;
  final int distanceM;
  final double? lat;
  final double? lng;

  String get distanceLabel {
    if (distanceM < 1000) return '$distanceM m';
    return '${(distanceM / 1000).toStringAsFixed(1)} km';
  }

  String? get priceLabel {
    final p = pricePaise;
    if (p == null) return null;
    final rupees = p / 100;
    if (rupees == rupees.roundToDouble()) return '₹${rupees.toInt()}/hr';
    return '₹${rupees.toStringAsFixed(0)}/hr';
  }

  factory CentreSummary.fromJson(Map<String, dynamic> json) => CentreSummary(
        id: json['id'].toString(),
        name: json['name'] as String? ?? '',
        thumbUrl: json['thumb_url'] as String?,
        ratingScore: (json['rating_score'] as num?)?.toDouble() ?? 0,
        reviewCount: (json['review_count'] as num?)?.toInt() ?? 0,
        availableNow: json['available_now'] as bool? ?? false,
        amenitiesMask: (json['amenities_mask'] as num?)?.toInt() ?? 0,
        pricePaise: (json['price_paise'] as num?)?.toInt(),
        distanceM: (json['distance_m'] as num?)?.toInt() ?? 0,
        lat: (json['lat'] as num?)?.toDouble(),
        lng: (json['lng'] as num?)?.toDouble(),
      );
}

class DiscoveryPage {
  const DiscoveryPage({
    required this.items,
    this.nextCursor,
    this.radiusM = 5000,
  });

  final List<CentreSummary> items;
  final String? nextCursor;
  final int radiusM;

  factory DiscoveryPage.fromJson(Map<String, dynamic> json) => DiscoveryPage(
        items: (json['items'] as List<dynamic>? ?? [])
            .map((e) => CentreSummary.fromJson(e as Map<String, dynamic>))
            .toList(),
        nextCursor: json['next_cursor'] as String?,
        radiusM: (json['radius_m'] as num?)?.toInt() ?? 5000,
      );
}
