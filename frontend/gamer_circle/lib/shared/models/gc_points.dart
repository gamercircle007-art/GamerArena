class GcPoints {
  const GcPoints({
    required this.balance,
    this.lifetimeEarned = 0,
    this.lifetimeRedeemed = 0,
    this.tier = 'bronze',
    this.nextTierPoints,
    this.history = const [],
  });

  final int balance;
  final int lifetimeEarned;
  final int lifetimeRedeemed;
  final String tier;
  final int? nextTierPoints;
  final List<GcPointsTransaction> history;

  factory GcPoints.fromJson(Map<String, dynamic> json) => GcPoints(
        balance: json['balance'] as int? ?? 0,
        lifetimeEarned: json['lifetime_earned'] as int? ?? 0,
        lifetimeRedeemed: json['lifetime_redeemed'] as int? ?? 0,
        tier: json['tier'] as String? ?? 'bronze',
        nextTierPoints: json['next_tier_points'] as int?,
        history: (json['history'] as List<dynamic>?)
                ?.map(
                  (e) =>
                      GcPointsTransaction.fromJson(e as Map<String, dynamic>),
                )
                .toList() ??
            const [],
      );
}

class GcPointsTransaction {
  const GcPointsTransaction({
    required this.id,
    required this.points,
    required this.type,
    required this.description,
    required this.createdAt,
    this.bookingRef,
  });

  final String id;
  final int points;
  final String type;
  final String description;
  final DateTime createdAt;
  final String? bookingRef;

  bool get isEarned => type == 'earned' || points > 0;

  factory GcPointsTransaction.fromJson(Map<String, dynamic> json) =>
      GcPointsTransaction(
        id: json['id'] as String,
        points: json['points'] as int,
        type: json['type'] as String,
        description: json['description'] as String? ?? '',
        createdAt: DateTime.parse(json['created_at'] as String),
        bookingRef: json['booking_ref'] as String?,
      );
}