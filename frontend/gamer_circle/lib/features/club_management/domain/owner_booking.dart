// Club Management — owner-side booking models.
//
// Mirrors `GET /club/bookings` and `GET /club/live`.
// Amounts are integer paise.

class OwnerBookingStatus {
  OwnerBookingStatus._();

  static const String paymentPending = 'payment_pending';
  static const String confirmed = 'confirmed';
  static const String checkedIn = 'checked_in';
  static const String completed = 'completed';
  static const String cancelled = 'cancelled';
  static const String noShow = 'no_show';
}

class OwnerBooking {
  const OwnerBooking({
    required this.id,
    required this.bookingRef,
    required this.bookingStatus,
    this.parlourId,
    this.userId,
    this.resourceId,
    this.resourceLabel,
    this.clubCustomerId,
    this.customerName,
    this.contactPhone,
    this.stationType,
    this.slotDate,
    this.startTime,
    this.endTime,
    this.durationHours = 1,
    this.units = 1,
    this.paymentStatus,
    this.paymentMode,
    this.amountPaise = 0,
    this.clubDiscountPaise = 0,
    this.commissionPaise = 0,
    this.isWalkIn = false,
    this.checkedInAt,
    this.checkedOutAt,
    this.extendedHours = 0,
    this.noShowAt,
    this.cancellationReason,
    this.createdAt,
  });

  final String id;
  final String bookingRef;
  final String bookingStatus;
  final String? parlourId;
  final String? userId;
  final String? resourceId;
  final String? resourceLabel;
  final String? clubCustomerId;
  final String? customerName;
  final String? contactPhone;
  final String? stationType;
  final DateTime? slotDate;
  final String? startTime;
  final String? endTime;
  final int durationHours;
  final int units;
  final String? paymentStatus;
  final String? paymentMode;
  final int amountPaise;
  final int clubDiscountPaise;
  final int commissionPaise;
  final bool isWalkIn;
  final DateTime? checkedInAt;
  final DateTime? checkedOutAt;
  final int extendedHours;
  final DateTime? noShowAt;
  final String? cancellationReason;
  final DateTime? createdAt;

  bool get canConfirm => bookingStatus == OwnerBookingStatus.paymentPending;
  bool get canCheckIn =>
      checkedInAt == null &&
      (bookingStatus == OwnerBookingStatus.confirmed ||
          bookingStatus == OwnerBookingStatus.paymentPending);
  bool get canCheckOut => checkedInAt != null && checkedOutAt == null;
  bool get isClosed =>
      bookingStatus == OwnerBookingStatus.cancelled ||
      bookingStatus == OwnerBookingStatus.completed ||
      bookingStatus == OwnerBookingStatus.noShow;

  /// `HH:MM` sort/group key, safe when the API omits `start_time`.
  String get timeKey => (startTime ?? '00:00').padRight(5).substring(0, 5);

  static DateTime? _date(dynamic value) =>
      value == null ? null : DateTime.tryParse(value as String);

  factory OwnerBooking.fromJson(Map<String, dynamic> json) => OwnerBooking(
        id: json['id'] as String,
        bookingRef: json['booking_ref'] as String? ?? '',
        bookingStatus:
            json['booking_status'] as String? ?? OwnerBookingStatus.confirmed,
        parlourId: json['parlour_id'] as String?,
        userId: json['user_id'] as String?,
        resourceId: json['resource_id'] as String?,
        resourceLabel: json['resource_label'] as String?,
        clubCustomerId: json['club_customer_id'] as String?,
        customerName: json['customer_name'] as String?,
        contactPhone: json['contact_phone'] as String?,
        stationType: json['station_type'] as String?,
        slotDate: _date(json['slot_date']),
        startTime: json['start_time'] as String?,
        endTime: json['end_time'] as String?,
        durationHours: (json['duration_hours'] as num?)?.toInt() ?? 1,
        units: (json['units'] as num?)?.toInt() ?? 1,
        paymentStatus: json['payment_status'] as String?,
        paymentMode: json['payment_mode'] as String?,
        amountPaise: (json['amount_paise'] as num?)?.toInt() ?? 0,
        clubDiscountPaise:
            (json['club_discount_paise'] as num?)?.toInt() ?? 0,
        commissionPaise: (json['commission_paise'] as num?)?.toInt() ?? 0,
        isWalkIn: json['is_walk_in'] as bool? ?? false,
        checkedInAt: _date(json['checked_in_at']),
        checkedOutAt: _date(json['checked_out_at']),
        extendedHours: (json['extended_hours'] as num?)?.toInt() ?? 0,
        noShowAt: _date(json['no_show_at']),
        cancellationReason: json['cancellation_reason'] as String?,
        createdAt: _date(json['created_at']),
      );
}

class LiveOccupant {
  const LiveOccupant({
    required this.bookingId,
    required this.bookingRef,
    this.resourceId,
    this.resourceLabel,
    this.resourceType,
    this.customerName,
    this.contactPhone,
    this.checkedInAt,
    this.endsAt,
    this.minutesRemaining = 0,
    this.isOverdue = false,
    this.units = 1,
    this.amountPaise = 0,
  });

  final String bookingId;
  final String bookingRef;
  final String? resourceId;
  final String? resourceLabel;
  final String? resourceType;
  final String? customerName;
  final String? contactPhone;
  final DateTime? checkedInAt;
  final DateTime? endsAt;
  final int minutesRemaining;
  final bool isOverdue;
  final int units;
  final int amountPaise;

  factory LiveOccupant.fromJson(Map<String, dynamic> json) => LiveOccupant(
        bookingId: json['booking_id'] as String? ?? json['id'] as String? ?? '',
        bookingRef: json['booking_ref'] as String? ?? '',
        resourceId: json['resource_id'] as String?,
        resourceLabel: json['resource_label'] as String?,
        resourceType: json['resource_type'] as String?,
        customerName: json['customer_name'] as String?,
        contactPhone: json['contact_phone'] as String?,
        checkedInAt: json['checked_in_at'] == null
            ? null
            : DateTime.tryParse(json['checked_in_at'] as String),
        endsAt: json['ends_at'] == null
            ? null
            : DateTime.tryParse(json['ends_at'] as String),
        minutesRemaining: (json['minutes_remaining'] as num?)?.toInt() ?? 0,
        isOverdue: json['is_overdue'] as bool? ?? false,
        units: (json['units'] as num?)?.toInt() ?? 1,
        amountPaise: (json['amount_paise'] as num?)?.toInt() ?? 0,
      );
}
