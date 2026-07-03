import 'parlor.dart';

class TournamentSummary {
  const TournamentSummary({required this.id, required this.title});

  final String id;
  final String title;

  factory TournamentSummary.fromJson(Map<String, dynamic> json) =>
      TournamentSummary(
        id: json['id'] as String,
        title: json['title'] as String,
      );

  Map<String, dynamic> toJson() => {'id': id, 'title': title};
}

class Tournament {
  const Tournament({
    required this.id,
    required this.parlorId,
    required this.title,
    required this.gameType,
    required this.format,
    required this.startTime,
    required this.endTime,
    required this.totalSlots,
    required this.bookedSlots,
    required this.entryFee,
    required this.status,
    this.prizes,
    this.rules,
    this.isBookedByMe = false,
    this.parlor,
  });

  final String id;
  final String parlorId;
  final String title;
  final String gameType;
  final String format;
  final DateTime startTime;
  final DateTime endTime;
  final int totalSlots;
  final int bookedSlots;
  final double entryFee;
  final String status;
  final Map<String, dynamic>? prizes;
  final String? rules;
  final bool isBookedByMe;
  final Parlor? parlor;

  int get slotsLeft => totalSlots - bookedSlots;
  bool get isFull => bookedSlots >= totalSlots;

  factory Tournament.fromJson(Map<String, dynamic> json) => Tournament(
        id: json['id'] as String,
        parlorId: json['parlor_id'] as String,
        title: json['title'] as String,
        gameType: json['game_type'] as String,
        format: json['format'] as String,
        startTime: DateTime.parse(json['start_time'] as String),
        endTime: DateTime.parse(json['end_time'] as String),
        totalSlots: json['total_slots'] as int,
        bookedSlots: json['booked_slots'] as int,
        entryFee: double.parse(json['entry_fee'].toString()),
        status: json['status'] as String,
        prizes: json['prizes'] as Map<String, dynamic>?,
        rules: json['rules'] as String?,
        isBookedByMe: json['is_booked_by_me'] as bool? ?? false,
        parlor: json['parlor'] != null
            ? Parlor.fromJson(json['parlor'] as Map<String, dynamic>)
            : null,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'parlor_id': parlorId,
        'title': title,
        'game_type': gameType,
        'format': format,
        'start_time': startTime.toIso8601String(),
        'end_time': endTime.toIso8601String(),
        'total_slots': totalSlots,
        'booked_slots': bookedSlots,
        'entry_fee': entryFee,
        'status': status,
        'prizes': prizes,
        'rules': rules,
        'is_booked_by_me': isBookedByMe,
        'parlor': parlor?.toJson(),
      };

  Tournament copyWith({
    String? id,
    String? parlorId,
    String? title,
    String? gameType,
    String? format,
    DateTime? startTime,
    DateTime? endTime,
    int? totalSlots,
    int? bookedSlots,
    double? entryFee,
    String? status,
    Map<String, dynamic>? prizes,
    String? rules,
    bool? isBookedByMe,
    Parlor? parlor,
  }) =>
      Tournament(
        id: id ?? this.id,
        parlorId: parlorId ?? this.parlorId,
        title: title ?? this.title,
        gameType: gameType ?? this.gameType,
        format: format ?? this.format,
        startTime: startTime ?? this.startTime,
        endTime: endTime ?? this.endTime,
        totalSlots: totalSlots ?? this.totalSlots,
        bookedSlots: bookedSlots ?? this.bookedSlots,
        entryFee: entryFee ?? this.entryFee,
        status: status ?? this.status,
        prizes: prizes ?? this.prizes,
        rules: rules ?? this.rules,
        isBookedByMe: isBookedByMe ?? this.isBookedByMe,
        parlor: parlor ?? this.parlor,
      );
}