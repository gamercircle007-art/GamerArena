// Club Management — revenue + occupancy analytics models.
//
// Mirrors `GET /club/revenue/summary` and the `/club/occupancy/*` endpoints.
// All money is integer paise; all ratios arrive as basis points (10000 == 100%).

class RevenueRange {
  RevenueRange._();

  static const String today = 'today';
  static const String week = 'week';
  static const String month = 'month';

  static const List<String> all = [today, week, month];
}

class RevenueByResourceType {
  const RevenueByResourceType({
    required this.resourceType,
    this.grossPaise = 0,
    this.bookingCount = 0,
  });

  final String resourceType;
  final int grossPaise;
  final int bookingCount;

  factory RevenueByResourceType.fromJson(Map<String, dynamic> json) =>
      RevenueByResourceType(
        resourceType: json['resource_type'] as String? ?? 'other',
        grossPaise: (json['gross_paise'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
      );
}

class RevenueByPaymentMethod {
  const RevenueByPaymentMethod({
    required this.paymentMethod,
    this.grossPaise = 0,
    this.bookingCount = 0,
  });

  final String paymentMethod;
  final int grossPaise;
  final int bookingCount;

  factory RevenueByPaymentMethod.fromJson(Map<String, dynamic> json) =>
      RevenueByPaymentMethod(
        paymentMethod: json['payment_method'] as String? ?? 'unknown',
        grossPaise: (json['gross_paise'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
      );
}

class RevenueDailyPoint {
  const RevenueDailyPoint({
    required this.date,
    this.grossPaise = 0,
    this.netPaise = 0,
    this.bookingCount = 0,
  });

  final String date;
  final int grossPaise;
  final int netPaise;
  final int bookingCount;

  factory RevenueDailyPoint.fromJson(Map<String, dynamic> json) =>
      RevenueDailyPoint(
        date: json['date'] as String? ?? '',
        grossPaise: (json['gross_paise'] as num?)?.toInt() ?? 0,
        netPaise: (json['net_paise'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
      );
}

class RevenueSummary {
  const RevenueSummary({
    required this.range,
    this.fromDate,
    this.toDate,
    this.grossPaise = 0,
    this.commissionPaise = 0,
    this.netPaise = 0,
    this.discountPaise = 0,
    this.bookingCount = 0,
    this.completedCount = 0,
    this.cancelledCount = 0,
    this.noShowCount = 0,
    this.avgSessionPaise = 0,
    this.byResourceType = const [],
    this.byPaymentMethod = const [],
    this.daily = const [],
  });

  final String range;
  final String? fromDate;
  final String? toDate;
  final int grossPaise;
  final int commissionPaise;
  final int netPaise;
  final int discountPaise;
  final int bookingCount;
  final int completedCount;
  final int cancelledCount;
  final int noShowCount;
  final int avgSessionPaise;
  final List<RevenueByResourceType> byResourceType;
  final List<RevenueByPaymentMethod> byPaymentMethod;
  final List<RevenueDailyPoint> daily;

  bool get isEmpty => bookingCount == 0 && grossPaise == 0;

  factory RevenueSummary.fromJson(Map<String, dynamic> json) => RevenueSummary(
        range: json['range'] as String? ?? RevenueRange.today,
        fromDate: json['from_date'] as String?,
        toDate: json['to_date'] as String?,
        grossPaise: (json['gross_paise'] as num?)?.toInt() ?? 0,
        commissionPaise: (json['commission_paise'] as num?)?.toInt() ?? 0,
        netPaise: (json['net_paise'] as num?)?.toInt() ?? 0,
        discountPaise: (json['discount_paise'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
        completedCount: (json['completed_count'] as num?)?.toInt() ?? 0,
        cancelledCount: (json['cancelled_count'] as num?)?.toInt() ?? 0,
        noShowCount: (json['no_show_count'] as num?)?.toInt() ?? 0,
        avgSessionPaise: (json['avg_session_paise'] as num?)?.toInt() ?? 0,
        byResourceType:
            (json['by_resource_type'] as List<dynamic>? ?? const [])
                .map((e) => RevenueByResourceType.fromJson(
                    Map<String, dynamic>.from(e as Map)))
                .toList(),
        byPaymentMethod:
            (json['by_payment_method'] as List<dynamic>? ?? const [])
                .map((e) => RevenueByPaymentMethod.fromJson(
                    Map<String, dynamic>.from(e as Map)))
                .toList(),
        daily: (json['daily'] as List<dynamic>? ?? const [])
            .map((e) =>
                RevenueDailyPoint.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class OccupancyPoint {
  const OccupancyPoint({
    required this.bucketStart,
    this.occupiedMinutes = 0,
    this.capacityMinutes = 0,
    this.utilizationBps = 0,
    this.bookingCount = 0,
    this.revenuePaise = 0,
  });

  final String bucketStart;
  final int occupiedMinutes;
  final int capacityMinutes;
  final int utilizationBps;
  final int bookingCount;
  final int revenuePaise;

  factory OccupancyPoint.fromJson(Map<String, dynamic> json) => OccupancyPoint(
        bucketStart: json['bucket_start']?.toString() ?? '',
        occupiedMinutes: (json['occupied_minutes'] as num?)?.toInt() ?? 0,
        capacityMinutes: (json['capacity_minutes'] as num?)?.toInt() ?? 0,
        utilizationBps: (json['utilization_bps'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
        revenuePaise: (json['revenue_paise'] as num?)?.toInt() ?? 0,
      );
}

class OccupancyTimeseries {
  const OccupancyTimeseries({
    this.fromDate,
    this.toDate,
    this.grain,
    this.points = const [],
  });

  final String? fromDate;
  final String? toDate;
  final String? grain;
  final List<OccupancyPoint> points;

  factory OccupancyTimeseries.fromJson(Map<String, dynamic> json) =>
      OccupancyTimeseries(
        fromDate: json['from_date'] as String?,
        toDate: json['to_date'] as String?,
        grain: json['grain'] as String?,
        points: (json['points'] as List<dynamic>? ?? const [])
            .map((e) =>
                OccupancyPoint.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class HeatmapCell {
  const HeatmapCell({
    required this.weekday,
    required this.hour,
    this.occupiedMinutes = 0,
    this.capacityMinutes = 0,
    this.utilizationBps = 0,
    this.bookingCount = 0,
  });

  /// 0 == Monday (Asia/Kolkata business week, per the backend rollup).
  final int weekday;
  final int hour;
  final int occupiedMinutes;
  final int capacityMinutes;
  final int utilizationBps;
  final int bookingCount;

  factory HeatmapCell.fromJson(Map<String, dynamic> json) => HeatmapCell(
        weekday: (json['weekday'] as num?)?.toInt() ?? 0,
        hour: (json['hour'] as num?)?.toInt() ?? 0,
        occupiedMinutes: (json['occupied_minutes'] as num?)?.toInt() ?? 0,
        capacityMinutes: (json['capacity_minutes'] as num?)?.toInt() ?? 0,
        utilizationBps: (json['utilization_bps'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
      );
}

class OccupancyHeatmap {
  const OccupancyHeatmap({this.fromDate, this.toDate, this.cells = const []});

  final String? fromDate;
  final String? toDate;
  final List<HeatmapCell> cells;

  factory OccupancyHeatmap.fromJson(Map<String, dynamic> json) =>
      OccupancyHeatmap(
        fromDate: json['from_date'] as String?,
        toDate: json['to_date'] as String?,
        cells: (json['cells'] as List<dynamic>? ?? const [])
            .map((e) =>
                HeatmapCell.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class UtilizationRow {
  const UtilizationRow({
    required this.label,
    this.grain,
    this.grainKey,
    this.occupiedMinutes = 0,
    this.capacityMinutes = 0,
    this.utilizationBps = 0,
    this.bookingCount = 0,
    this.revenuePaise = 0,
  });

  final String label;
  final String? grain;
  final String? grainKey;
  final int occupiedMinutes;
  final int capacityMinutes;
  final int utilizationBps;
  final int bookingCount;
  final int revenuePaise;

  factory UtilizationRow.fromJson(Map<String, dynamic> json) => UtilizationRow(
        label: json['label'] as String? ??
            json['grain_key']?.toString() ??
            'Unknown',
        grain: json['grain'] as String?,
        grainKey: json['grain_key']?.toString(),
        occupiedMinutes: (json['occupied_minutes'] as num?)?.toInt() ?? 0,
        capacityMinutes: (json['capacity_minutes'] as num?)?.toInt() ?? 0,
        utilizationBps: (json['utilization_bps'] as num?)?.toInt() ?? 0,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
        revenuePaise: (json['revenue_paise'] as num?)?.toInt() ?? 0,
      );
}

class UtilizationReport {
  const UtilizationReport({this.fromDate, this.toDate, this.grain, this.rows = const []});

  final String? fromDate;
  final String? toDate;
  final String? grain;
  final List<UtilizationRow> rows;

  factory UtilizationReport.fromJson(Map<String, dynamic> json) =>
      UtilizationReport(
        fromDate: json['from_date'] as String?,
        toDate: json['to_date'] as String?,
        grain: json['grain'] as String?,
        rows: (json['rows'] as List<dynamic>? ?? const [])
            .map((e) =>
                UtilizationRow.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class NoShowByResourceType {
  const NoShowByResourceType({
    required this.resourceType,
    this.bookingCount = 0,
    this.noShowCount = 0,
    this.noShowRateBps = 0,
  });

  final String resourceType;
  final int bookingCount;
  final int noShowCount;
  final int noShowRateBps;

  factory NoShowByResourceType.fromJson(Map<String, dynamic> json) =>
      NoShowByResourceType(
        resourceType: json['resource_type'] as String? ?? 'other',
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
        noShowCount: (json['no_show_count'] as num?)?.toInt() ?? 0,
        noShowRateBps: (json['no_show_rate_bps'] as num?)?.toInt() ?? 0,
      );
}

class NoShowRate {
  const NoShowRate({
    this.fromDate,
    this.toDate,
    this.bookingCount = 0,
    this.noShowCount = 0,
    this.noShowRateBps = 0,
    this.byResourceType = const [],
  });

  final String? fromDate;
  final String? toDate;
  final int bookingCount;
  final int noShowCount;
  final int noShowRateBps;
  final List<NoShowByResourceType> byResourceType;

  factory NoShowRate.fromJson(Map<String, dynamic> json) => NoShowRate(
        fromDate: json['from_date'] as String?,
        toDate: json['to_date'] as String?,
        bookingCount: (json['booking_count'] as num?)?.toInt() ?? 0,
        noShowCount: (json['no_show_count'] as num?)?.toInt() ?? 0,
        noShowRateBps: (json['no_show_rate_bps'] as num?)?.toInt() ?? 0,
        byResourceType:
            (json['by_resource_type'] as List<dynamic>? ?? const [])
                .map((e) => NoShowByResourceType.fromJson(
                    Map<String, dynamic>.from(e as Map)))
                .toList(),
      );
}
