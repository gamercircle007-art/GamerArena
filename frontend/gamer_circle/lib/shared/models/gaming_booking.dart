class GamingBooking {
  const GamingBooking({
    required this.id,
    required this.bookingRef,
    required this.userId,
    required this.parlourId,
    this.parlourName,
    this.parlourImage,
    this.parlourAddress,
    this.slotId,
    this.offerId,
    this.guestName,
    this.numPlayers = 1,
    this.slotDate,
    this.startTime,
    this.endTime,
    this.hoursBooked,
    this.pricePerHour,
    this.totalPrice,
    this.taxAmount,
    this.discountAmount = 0,
    this.finalPrice,
    this.paymentMode = 'pay_at_parlor',
    this.paymentStatus = 'pending',
    this.paymentId,
    this.bookingStatus = 'confirmed',
    this.cancellationReason,
    this.cancellationDetail,
    this.cancelledAt,
    this.refundAmount = 0,
    this.refundStatus,
    this.freeCancellationBefore,
    this.isNonRefundable = false,
    this.gcPointsEarned = 0,
    this.contactEmail,
    this.contactPhone,
    this.gstin,
    required this.createdAt,
  });

  final String id;
  final String bookingRef;
  final String userId;
  final String parlourId;
  final String? parlourName;
  final String? parlourImage;
  final String? parlourAddress;
  final String? slotId;
  final String? offerId;
  final String? guestName;
  final int numPlayers;
  final DateTime? slotDate;
  final String? startTime;
  final String? endTime;
  final double? hoursBooked;
  final double? pricePerHour;
  final double? totalPrice;
  final double? taxAmount;
  final double discountAmount;
  final double? finalPrice;
  final String paymentMode;
  final String paymentStatus;
  final String? paymentId;
  final String bookingStatus;
  final String? cancellationReason;
  final String? cancellationDetail;
  final DateTime? cancelledAt;
  final double refundAmount;
  final String? refundStatus;
  final DateTime? freeCancellationBefore;
  final bool isNonRefundable;
  final int gcPointsEarned;
  final String? contactEmail;
  final String? contactPhone;
  final String? gstin;
  final DateTime createdAt;

  bool get isConfirmed =>
      bookingStatus == 'confirmed' && cancelledAt == null;
  bool get isCancelled => bookingStatus == 'cancelled' || cancelledAt != null;
  bool get isUpcoming {
    if (slotDate == null) return bookingStatus == 'confirmed';
    final now = DateTime.now();
    return slotDate!.isAfter(DateTime(now.year, now.month, now.day)) ||
        (slotDate!.year == now.year &&
            slotDate!.month == now.month &&
            slotDate!.day == now.day);
  }

  factory GamingBooking.fromJson(Map<String, dynamic> json) => GamingBooking(
        id: json['id'] as String,
        bookingRef: json['booking_ref'] as String,
        userId: json['user_id'] as String,
        parlourId: json['parlour_id'] as String,
        parlourName: json['parlour_name'] as String?,
        parlourImage: json['parlour_image'] as String?,
        parlourAddress: json['parlour_address'] as String?,
        slotId: json['slot_id'] as String?,
        offerId: json['offer_id'] as String?,
        guestName: json['guest_name'] as String?,
        numPlayers: json['num_players'] as int? ?? 1,
        slotDate: json['slot_date'] != null
            ? DateTime.parse(json['slot_date'] as String)
            : null,
        startTime: json['start_time'] as String?,
        endTime: json['end_time'] as String?,
        hoursBooked: (json['hours_booked'] as num?)?.toDouble(),
        pricePerHour: (json['price_per_hour'] as num?)?.toDouble(),
        totalPrice: (json['total_price'] as num?)?.toDouble(),
        taxAmount: (json['tax_amount'] as num?)?.toDouble(),
        discountAmount: (json['discount_amount'] as num?)?.toDouble() ?? 0,
        finalPrice: (json['final_price'] as num?)?.toDouble(),
        paymentMode: json['payment_mode'] as String? ?? 'pay_at_parlor',
        paymentStatus: json['payment_status'] as String? ?? 'pending',
        paymentId: json['payment_id'] as String?,
        bookingStatus: json['booking_status'] as String? ?? 'confirmed',
        cancellationReason: json['cancellation_reason'] as String?,
        cancellationDetail: json['cancellation_detail'] as String?,
        cancelledAt: json['cancelled_at'] != null
            ? DateTime.parse(json['cancelled_at'] as String)
            : null,
        refundAmount: (json['refund_amount'] as num?)?.toDouble() ?? 0,
        refundStatus: json['refund_status'] as String?,
        freeCancellationBefore: json['free_cancellation_before'] != null
            ? DateTime.parse(json['free_cancellation_before'] as String)
            : null,
        isNonRefundable: json['is_non_refundable'] as bool? ?? false,
        gcPointsEarned: json['gc_points_earned'] as int? ?? 0,
        contactEmail: json['contact_email'] as String?,
        contactPhone: json['contact_phone'] as String?,
        gstin: json['gstin'] as String?,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'booking_ref': bookingRef,
        'user_id': userId,
        'parlour_id': parlourId,
        'parlour_name': parlourName,
        'slot_id': slotId,
        'offer_id': offerId,
        'guest_name': guestName,
        'num_players': numPlayers,
        'slot_date': slotDate?.toIso8601String().split('T').first,
        'start_time': startTime,
        'end_time': endTime,
        'hours_booked': hoursBooked,
        'price_per_hour': pricePerHour,
        'total_price': totalPrice,
        'tax_amount': taxAmount,
        'discount_amount': discountAmount,
        'final_price': finalPrice,
        'payment_mode': paymentMode,
        'payment_status': paymentStatus,
        'payment_id': paymentId,
        'booking_status': bookingStatus,
        'cancellation_reason': cancellationReason,
        'cancellation_detail': cancellationDetail,
        'cancelled_at': cancelledAt?.toIso8601String(),
        'refund_amount': refundAmount,
        'refund_status': refundStatus,
        'free_cancellation_before': freeCancellationBefore?.toIso8601String(),
        'is_non_refundable': isNonRefundable,
        'gc_points_earned': gcPointsEarned,
        'contact_email': contactEmail,
        'contact_phone': contactPhone,
        'gstin': gstin,
        'created_at': createdAt.toIso8601String(),
      };
}

class GamingSlot {
  const GamingSlot({
    required this.id,
    required this.parlourId,
    required this.slotDate,
    required this.startTime,
    required this.endTime,
    required this.pricePerHour,
    this.originalPrice,
    this.maxPlayers = 1,
    this.currentBookings = 0,
    this.isAvailable = true,
    this.gameName,
  });

  final String id;
  final String parlourId;
  final DateTime slotDate;
  final String startTime;
  final String endTime;
  final double pricePerHour;
  final double? originalPrice;
  final int maxPlayers;
  final int currentBookings;
  final bool isAvailable;
  final String? gameName;

  factory GamingSlot.fromJson(Map<String, dynamic> json) => GamingSlot(
        id: json['id'] as String,
        parlourId: json['parlour_id'] as String,
        slotDate: DateTime.parse(json['slot_date'] as String),
        startTime: json['start_time'] as String,
        endTime: json['end_time'] as String,
        pricePerHour: (json['price_per_hour'] as num).toDouble(),
        originalPrice: (json['original_price'] as num?)?.toDouble(),
        maxPlayers: json['max_players'] as int? ?? 1,
        currentBookings: json['current_bookings'] as int? ?? 0,
        isAvailable: json['is_available'] as bool? ?? true,
        gameName: json['game_name'] as String?,
      );
}