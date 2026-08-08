// Club Management — pricing rule + price preview models.
//
// Mirrors `GET /club/pricing/rules` and `POST /club/pricing/preview`.
// Rates are integer paise; multipliers are basis points (10000 == 1.0x).

class PricingScope {
  PricingScope._();

  static const String club = 'club';
  static const String resourceType = 'resource_type';
  static const String zone = 'zone';
  static const String resource = 'resource';

  static const List<String> all = [club, resourceType, zone, resource];
}

/// A peak / off-peak window inside a [PricingRule].
class TimeSlab {
  const TimeSlab({
    required this.label,
    required this.start,
    required this.end,
    this.multiplierBps,
    this.flatPaise,
  });

  final String label;

  /// `HH:MM`
  final String start;

  /// `HH:MM`
  final String end;
  final int? multiplierBps;
  final int? flatPaise;

  TimeSlab copyWith({
    String? label,
    String? start,
    String? end,
    int? multiplierBps,
    int? flatPaise,
  }) =>
      TimeSlab(
        label: label ?? this.label,
        start: start ?? this.start,
        end: end ?? this.end,
        multiplierBps: multiplierBps ?? this.multiplierBps,
        flatPaise: flatPaise ?? this.flatPaise,
      );

  factory TimeSlab.fromJson(Map<String, dynamic> json) => TimeSlab(
        label: json['label'] as String? ?? 'Slab',
        start: json['start'] as String? ?? '00:00',
        end: json['end'] as String? ?? '23:59',
        multiplierBps: (json['multiplier_bps'] as num?)?.toInt(),
        flatPaise: (json['flat_paise'] as num?)?.toInt(),
      );

  Map<String, dynamic> toJson() => {
        'label': label,
        'start': start,
        'end': end,
        if (multiplierBps != null) 'multiplier_bps': multiplierBps,
        if (flatPaise != null) 'flat_paise': flatPaise,
      };
}

/// A bundle definition (e.g. "3 hour pack" for a flat price).
class PackageDef {
  const PackageDef({
    required this.label,
    required this.hours,
    required this.pricePaise,
  });

  final String label;
  final int hours;
  final int pricePaise;

  PackageDef copyWith({String? label, int? hours, int? pricePaise}) =>
      PackageDef(
        label: label ?? this.label,
        hours: hours ?? this.hours,
        pricePaise: pricePaise ?? this.pricePaise,
      );

  factory PackageDef.fromJson(Map<String, dynamic> json) => PackageDef(
        label: json['label'] as String? ?? 'Package',
        hours: (json['hours'] as num?)?.toInt() ?? 1,
        pricePaise: (json['price_paise'] as num?)?.toInt() ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'label': label,
        'hours': hours,
        'price_paise': pricePaise,
      };
}

class PricingRule {
  const PricingRule({
    required this.id,
    required this.name,
    required this.scope,
    required this.baseRatePaise,
    this.parlorId,
    this.scopeValue,
    this.timeSlabs = const [],
    this.dayOfWeekOverrides = const {},
    this.packageDefs = const [],
    this.priority = 0,
    this.validFrom,
    this.validTo,
    this.isActive = true,
  });

  final String id;
  final String name;
  final String scope;
  final int baseRatePaise;
  final String? parlorId;
  final String? scopeValue;
  final List<TimeSlab> timeSlabs;

  /// Weekday index (`"0"` == Monday) -> multiplier in basis points.
  final Map<String, int> dayOfWeekOverrides;
  final List<PackageDef> packageDefs;
  final int priority;
  final DateTime? validFrom;
  final DateTime? validTo;
  final bool isActive;

  static Map<String, int> _parseDowOverrides(dynamic raw) {
    if (raw is! Map) return const {};
    final out = <String, int>{};
    raw.forEach((key, value) {
      // Tolerates both `{"0": 12000}` and `{"0": {"multiplier_bps": 12000}}`.
      if (value is num) {
        out[key.toString()] = value.toInt();
      } else if (value is Map && value['multiplier_bps'] is num) {
        out[key.toString()] = (value['multiplier_bps'] as num).toInt();
      }
    });
    return out;
  }

  factory PricingRule.fromJson(Map<String, dynamic> json) => PricingRule(
        id: json['id'] as String,
        name: json['name'] as String? ?? 'Rule',
        scope: json['scope'] as String? ?? PricingScope.club,
        baseRatePaise: (json['base_rate_paise'] as num?)?.toInt() ?? 0,
        parlorId: json['parlor_id'] as String?,
        scopeValue: json['scope_value']?.toString(),
        timeSlabs: (json['time_slabs'] as List<dynamic>? ?? const [])
            .map((e) => TimeSlab.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        dayOfWeekOverrides: _parseDowOverrides(json['day_of_week_overrides']),
        packageDefs: (json['package_defs'] as List<dynamic>? ?? const [])
            .map((e) => PackageDef.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        priority: (json['priority'] as num?)?.toInt() ?? 0,
        validFrom: json['valid_from'] == null
            ? null
            : DateTime.tryParse(json['valid_from'] as String),
        validTo: json['valid_to'] == null
            ? null
            : DateTime.tryParse(json['valid_to'] as String),
        isActive: json['is_active'] as bool? ?? true,
      );
}

class PricePerHour {
  const PricePerHour({
    required this.startTime,
    required this.ratePaise,
    this.slabLabel,
    this.dowOverride = false,
  });

  final String startTime;
  final int ratePaise;
  final String? slabLabel;
  final bool dowOverride;

  factory PricePerHour.fromJson(Map<String, dynamic> json) => PricePerHour(
        startTime: json['start_time'] as String? ?? '',
        ratePaise: (json['rate_paise'] as num?)?.toInt() ?? 0,
        slabLabel: json['slab_label'] as String?,
        dowOverride: json['dow_override'] as bool? ?? false,
      );
}

class PriceBreakdown {
  const PriceBreakdown({
    this.subtotalPaise = 0,
    this.baseRatePaise = 0,
    this.hours = 0,
    this.units = 1,
    this.source,
    this.ruleId,
    this.ruleName,
    this.packageLabel,
    this.perHour = const [],
  });

  final int subtotalPaise;
  final int baseRatePaise;
  final int hours;
  final int units;
  final String? source;
  final String? ruleId;
  final String? ruleName;
  final String? packageLabel;
  final List<PricePerHour> perHour;

  factory PriceBreakdown.fromJson(Map<String, dynamic> json) => PriceBreakdown(
        subtotalPaise: (json['subtotal_paise'] as num?)?.toInt() ?? 0,
        baseRatePaise: (json['base_rate_paise'] as num?)?.toInt() ?? 0,
        hours: (json['hours'] as num?)?.toInt() ?? 0,
        units: (json['units'] as num?)?.toInt() ?? 1,
        source: json['source'] as String?,
        ruleId: json['rule_id']?.toString(),
        ruleName: json['rule_name'] as String?,
        packageLabel: json['package_label'] as String?,
        perHour: (json['per_hour'] as List<dynamic>? ?? const [])
            .map((e) =>
                PricePerHour.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class PricePromotion {
  const PricePromotion({
    this.valid = false,
    this.discountPaise = 0,
    this.promotionId,
    this.promotionName,
    this.promoType,
    this.reason,
  });

  final bool valid;
  final int discountPaise;
  final String? promotionId;
  final String? promotionName;
  final String? promoType;
  final String? reason;

  factory PricePromotion.fromJson(Map<String, dynamic> json) => PricePromotion(
        valid: json['valid'] as bool? ?? false,
        discountPaise: (json['discount_paise'] as num?)?.toInt() ?? 0,
        promotionId: json['promotion_id']?.toString(),
        promotionName: json['promotion_name'] as String?,
        promoType: json['promo_type'] as String?,
        reason: json['reason'] as String?,
      );
}

class PricePreview {
  const PricePreview({
    required this.breakdown,
    required this.promotion,
    this.subtotalPaise = 0,
    this.discountPaise = 0,
    this.totalPaise = 0,
  });

  final PriceBreakdown breakdown;
  final PricePromotion promotion;
  final int subtotalPaise;
  final int discountPaise;
  final int totalPaise;

  factory PricePreview.fromJson(Map<String, dynamic> json) => PricePreview(
        breakdown: PriceBreakdown.fromJson(
          json['breakdown'] is Map
              ? Map<String, dynamic>.from(json['breakdown'] as Map)
              : const {},
        ),
        promotion: PricePromotion.fromJson(
          json['promotion'] is Map
              ? Map<String, dynamic>.from(json['promotion'] as Map)
              : const {},
        ),
        subtotalPaise: (json['subtotal_paise'] as num?)?.toInt() ?? 0,
        discountPaise: (json['discount_paise'] as num?)?.toInt() ?? 0,
        totalPaise: (json['total_paise'] as num?)?.toInt() ?? 0,
      );
}
