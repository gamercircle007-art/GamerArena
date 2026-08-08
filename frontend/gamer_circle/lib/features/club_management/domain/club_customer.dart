// Club Management — per-club CRM models.
//
// Mirrors `GET /club/customers` and `GET /club/customers/{id}`.
// Spend is integer paise (`total_spend_rupees` from the API is display sugar
// and is deliberately ignored in favour of the paise value).

import 'package:gamer_circle/features/club_management/domain/owner_booking.dart';

class ClubCustomer {
  const ClubCustomer({
    required this.id,
    required this.displayName,
    this.parlorId,
    this.userId,
    this.phone,
    this.visitCount = 0,
    this.totalSpendPaise = 0,
    this.lastVisitAt,
    this.loyaltyPoints = 0,
    this.tags = const [],
    this.notes,
    this.isBanned = false,
    this.banReason,
    this.platformFlagged = false,
  });

  final String id;
  final String displayName;
  final String? parlorId;
  final String? userId;
  final String? phone;
  final int visitCount;
  final int totalSpendPaise;
  final DateTime? lastVisitAt;
  final int loyaltyPoints;
  final List<String> tags;
  final String? notes;
  final bool isBanned;
  final String? banReason;
  final bool platformFlagged;

  ClubCustomer copyWith({
    List<String>? tags,
    bool? isBanned,
    String? banReason,
    String? notes,
  }) =>
      ClubCustomer(
        id: id,
        displayName: displayName,
        parlorId: parlorId,
        userId: userId,
        phone: phone,
        visitCount: visitCount,
        totalSpendPaise: totalSpendPaise,
        lastVisitAt: lastVisitAt,
        loyaltyPoints: loyaltyPoints,
        tags: tags ?? this.tags,
        notes: notes ?? this.notes,
        isBanned: isBanned ?? this.isBanned,
        banReason: banReason ?? this.banReason,
        platformFlagged: platformFlagged,
      );

  factory ClubCustomer.fromJson(Map<String, dynamic> json) => ClubCustomer(
        id: json['id'] as String,
        displayName: json['display_name'] as String? ?? 'Guest',
        parlorId: json['parlor_id'] as String?,
        userId: json['user_id'] as String?,
        phone: json['phone'] as String?,
        visitCount: (json['visit_count'] as num?)?.toInt() ?? 0,
        totalSpendPaise: (json['total_spend_paise'] as num?)?.toInt() ?? 0,
        lastVisitAt: json['last_visit_at'] == null
            ? null
            : DateTime.tryParse(json['last_visit_at'] as String),
        loyaltyPoints: (json['loyalty_points'] as num?)?.toInt() ?? 0,
        tags: json['tags'] is List
            ? (json['tags'] as List<dynamic>)
                .map((e) => e.toString())
                .toList()
            : const [],
        notes: json['notes'] as String?,
        isBanned: json['is_banned'] as bool? ?? false,
        banReason: json['ban_reason'] as String?,
        platformFlagged: json['platform_flagged'] as bool? ?? false,
      );
}

class ClubCustomerNote {
  const ClubCustomerNote({
    required this.id,
    required this.body,
    this.authorId,
    this.createdAt,
  });

  final String id;
  final String body;
  final String? authorId;
  final DateTime? createdAt;

  factory ClubCustomerNote.fromJson(Map<String, dynamic> json) =>
      ClubCustomerNote(
        id: json['id'] as String? ?? '',
        body: json['body'] as String? ?? '',
        authorId: json['author_id'] as String?,
        createdAt: json['created_at'] == null
            ? null
            : DateTime.tryParse(json['created_at'] as String),
      );
}

/// Envelope returned by `GET /club/customers/{id}`.
class ClubCustomerDetail {
  const ClubCustomerDetail({
    required this.customer,
    this.recentBookings = const [],
    this.noteHistory = const [],
  });

  final ClubCustomer customer;
  final List<OwnerBooking> recentBookings;
  final List<ClubCustomerNote> noteHistory;

  factory ClubCustomerDetail.fromJson(Map<String, dynamic> json) {
    final rawCustomer = json['customer'] is Map
        ? Map<String, dynamic>.from(json['customer'] as Map)
        : json;
    final bookings = json['recent_bookings'] as List<dynamic>? ?? const [];
    final notes = json['note_history'] as List<dynamic>? ?? const [];
    return ClubCustomerDetail(
      customer: ClubCustomer.fromJson(rawCustomer),
      recentBookings: bookings
          .map((e) => OwnerBooking.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      noteHistory: notes
          .map((e) =>
              ClubCustomerNote.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
    );
  }
}

/// Paginated envelope returned by `GET /club/customers`.
class ClubCustomerPage {
  const ClubCustomerPage({
    this.items = const [],
    this.total = 0,
    this.limit = 20,
    this.offset = 0,
  });

  final List<ClubCustomer> items;
  final int total;
  final int limit;
  final int offset;

  bool get hasMore => offset + items.length < total;

  factory ClubCustomerPage.fromJson(Map<String, dynamic> json) {
    final items = json['items'] as List<dynamic>? ?? const [];
    return ClubCustomerPage(
      items: items
          .map((e) => ClubCustomer.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      total: (json['total'] as num?)?.toInt() ?? items.length,
      limit: (json['limit'] as num?)?.toInt() ?? 20,
      offset: (json['offset'] as num?)?.toInt() ?? 0,
    );
  }
}
