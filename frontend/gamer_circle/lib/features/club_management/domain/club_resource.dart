// Club Management — inventory models (zones + per-unit resources).
//
// Mirrors `GET /club/zones` and `GET /club/resources`.
// Money is always integer paise (never a double) per the build spec.

/// Allowed `resource_type` values from the backend enum.
class ClubResourceType {
  ClubResourceType._();

  static const String seat = 'seat';
  static const String pc = 'pc';
  static const String console = 'console';
  static const String ps5 = 'ps5';
  static const String pool = 'pool';
  static const String vr = 'vr';
  static const String other = 'other';

  static const List<String> all = [seat, pc, console, ps5, pool, vr, other];
}

/// Allowed `status` values from the backend enum.
class ClubResourceStatus {
  ClubResourceStatus._();

  static const String available = 'available';
  static const String occupied = 'occupied';
  static const String reserved = 'reserved';
  static const String maintenance = 'maintenance';
  static const String offline = 'offline';

  static const List<String> all = [
    available,
    occupied,
    reserved,
    maintenance,
    offline,
  ];
}

class ClubZone {
  const ClubZone({
    required this.id,
    required this.parlorId,
    required this.name,
    this.description,
    this.sortOrder = 0,
    this.isActive = true,
    this.resourceCount = 0,
  });

  final String id;
  final String parlorId;
  final String name;
  final String? description;
  final int sortOrder;
  final bool isActive;
  final int resourceCount;

  factory ClubZone.fromJson(Map<String, dynamic> json) => ClubZone(
        id: json['id'] as String,
        parlorId: json['parlor_id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        description: json['description'] as String?,
        sortOrder: json['sort_order'] as int? ?? 0,
        isActive: json['is_active'] as bool? ?? true,
        resourceCount: json['resource_count'] as int? ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'parlor_id': parlorId,
        'name': name,
        'description': description,
        'sort_order': sortOrder,
        'is_active': isActive,
        'resource_count': resourceCount,
      };
}

class ClubResource {
  const ClubResource({
    required this.id,
    required this.parlorId,
    required this.label,
    required this.resourceType,
    required this.status,
    this.zoneId,
    this.zoneName,
    this.specs = const {},
    this.hourlyRateOverridePaise,
    this.layoutX,
    this.layoutY,
    this.statusNote,
    this.isActive = true,
  });

  final String id;
  final String parlorId;
  final String label;
  final String resourceType;
  final String status;
  final String? zoneId;
  final String? zoneName;
  final Map<String, dynamic> specs;
  final int? hourlyRateOverridePaise;
  final int? layoutX;
  final int? layoutY;
  final String? statusNote;
  final bool isActive;

  bool get isBusy =>
      status == ClubResourceStatus.occupied ||
      status == ClubResourceStatus.reserved;

  ClubResource copyWith({
    String? label,
    String? resourceType,
    String? status,
    String? zoneId,
    String? zoneName,
    Map<String, dynamic>? specs,
    int? hourlyRateOverridePaise,
    int? layoutX,
    int? layoutY,
    String? statusNote,
    bool? isActive,
  }) =>
      ClubResource(
        id: id,
        parlorId: parlorId,
        label: label ?? this.label,
        resourceType: resourceType ?? this.resourceType,
        status: status ?? this.status,
        zoneId: zoneId ?? this.zoneId,
        zoneName: zoneName ?? this.zoneName,
        specs: specs ?? this.specs,
        hourlyRateOverridePaise:
            hourlyRateOverridePaise ?? this.hourlyRateOverridePaise,
        layoutX: layoutX ?? this.layoutX,
        layoutY: layoutY ?? this.layoutY,
        statusNote: statusNote ?? this.statusNote,
        isActive: isActive ?? this.isActive,
      );

  factory ClubResource.fromJson(Map<String, dynamic> json) => ClubResource(
        id: json['id'] as String,
        parlorId: json['parlor_id'] as String? ?? '',
        label: json['label'] as String? ?? '',
        resourceType:
            json['resource_type'] as String? ?? ClubResourceType.other,
        status: json['status'] as String? ?? ClubResourceStatus.available,
        zoneId: json['zone_id'] as String?,
        zoneName: json['zone_name'] as String?,
        specs: json['specs'] is Map
            ? Map<String, dynamic>.from(json['specs'] as Map)
            : const {},
        hourlyRateOverridePaise: json['hourly_rate_override_paise'] as int?,
        layoutX: json['layout_x'] as int?,
        layoutY: json['layout_y'] as int?,
        statusNote: json['status_note'] as String?,
        isActive: json['is_active'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'parlor_id': parlorId,
        'label': label,
        'resource_type': resourceType,
        'status': status,
        'zone_id': zoneId,
        'zone_name': zoneName,
        'specs': specs,
        'hourly_rate_override_paise': hourlyRateOverridePaise,
        'layout_x': layoutX,
        'layout_y': layoutY,
        'status_note': statusNote,
        'is_active': isActive,
      };
}
