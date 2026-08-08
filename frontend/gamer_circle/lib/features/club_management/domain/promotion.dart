// Club Management — promotion / offer model.
//
// Mirrors `GET /club/promotions`.
// `percent_bps` is basis points (10000 == 100%); flat amounts are paise.

class PromoType {
  PromoType._();

  static const String percent = 'percent';
  static const String flat = 'flat';
  static const String happyHour = 'happy_hour';
  static const String firstVisit = 'first_visit';
  static const String loyalty = 'loyalty';
  static const String code = 'code';

  static const List<String> all = [
    percent,
    flat,
    happyHour,
    firstVisit,
    loyalty,
    code,
  ];
}

class Promotion {
  const Promotion({
    required this.id,
    required this.name,
    required this.promoType,
    this.parlorId,
    this.percentBps,
    this.flatPaise,
    this.code,
    this.maxDiscountPaise,
    this.minAmountPaise,
    this.validFrom,
    this.validTo,
    this.happyHourStart,
    this.happyHourEnd,
    this.usageLimit,
    this.usedCount = 0,
    this.applicableResourceTypes = const [],
    this.minLoyaltyPoints,
    this.isActive = true,
    this.disabledByPlatform = false,
    this.disabledReason,
  });

  final String id;
  final String name;
  final String promoType;
  final String? parlorId;
  final int? percentBps;
  final int? flatPaise;
  final String? code;
  final int? maxDiscountPaise;
  final int? minAmountPaise;
  final DateTime? validFrom;
  final DateTime? validTo;

  /// `HH:MM`
  final String? happyHourStart;

  /// `HH:MM`
  final String? happyHourEnd;
  final int? usageLimit;
  final int usedCount;
  final List<String> applicableResourceTypes;
  final int? minLoyaltyPoints;
  final bool isActive;
  final bool disabledByPlatform;
  final String? disabledReason;

  /// Expired = past its validity window, or exhausted, or switched off.
  bool get isExpired {
    final to = validTo;
    if (to != null && to.isBefore(DateTime.now())) return true;
    final limit = usageLimit;
    if (limit != null && limit > 0 && usedCount >= limit) return true;
    return !isActive || disabledByPlatform;
  }

  factory Promotion.fromJson(Map<String, dynamic> json) => Promotion(
        id: json['id'] as String,
        name: json['name'] as String? ?? 'Promotion',
        promoType: json['promo_type'] as String? ?? PromoType.percent,
        parlorId: json['parlor_id'] as String?,
        percentBps: (json['percent_bps'] as num?)?.toInt(),
        flatPaise: (json['flat_paise'] as num?)?.toInt(),
        code: json['code'] as String?,
        maxDiscountPaise: (json['max_discount_paise'] as num?)?.toInt(),
        minAmountPaise: (json['min_amount_paise'] as num?)?.toInt(),
        validFrom: json['valid_from'] == null
            ? null
            : DateTime.tryParse(json['valid_from'] as String),
        validTo: json['valid_to'] == null
            ? null
            : DateTime.tryParse(json['valid_to'] as String),
        happyHourStart: json['happy_hour_start'] as String?,
        happyHourEnd: json['happy_hour_end'] as String?,
        usageLimit: (json['usage_limit'] as num?)?.toInt(),
        usedCount: (json['used_count'] as num?)?.toInt() ?? 0,
        applicableResourceTypes:
            json['applicable_resource_types'] is List
                ? (json['applicable_resource_types'] as List<dynamic>)
                    .map((e) => e.toString())
                    .toList()
                : const [],
        minLoyaltyPoints: (json['min_loyalty_points'] as num?)?.toInt(),
        isActive: json['is_active'] as bool? ?? true,
        disabledByPlatform: json['disabled_by_platform'] as bool? ?? false,
        disabledReason: json['disabled_reason'] as String?,
      );
}
