class Booking {
  const Booking({
    required this.id,
    required this.tournamentId,
    required this.userId,
    required this.slotNumber,
    required this.status,
    required this.paymentStatus,
    required this.createdAt,
  });

  final String id;
  final String tournamentId;
  final String userId;
  final int slotNumber;
  final String status;
  final String paymentStatus;
  final DateTime createdAt;

  factory Booking.fromJson(Map<String, dynamic> json) => Booking(
        id: json['id'] as String,
        tournamentId: json['tournament_id'] as String,
        userId: json['user_id'] as String,
        slotNumber: json['slot_number'] as int,
        status: json['status'] as String,
        paymentStatus: json['payment_status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'tournament_id': tournamentId,
        'user_id': userId,
        'slot_number': slotNumber,
        'status': status,
        'payment_status': paymentStatus,
        'created_at': createdAt.toIso8601String(),
      };

  Booking copyWith({
    String? id,
    String? tournamentId,
    String? userId,
    int? slotNumber,
    String? status,
    String? paymentStatus,
    DateTime? createdAt,
  }) =>
      Booking(
        id: id ?? this.id,
        tournamentId: tournamentId ?? this.tournamentId,
        userId: userId ?? this.userId,
        slotNumber: slotNumber ?? this.slotNumber,
        status: status ?? this.status,
        paymentStatus: paymentStatus ?? this.paymentStatus,
        createdAt: createdAt ?? this.createdAt,
      );
}