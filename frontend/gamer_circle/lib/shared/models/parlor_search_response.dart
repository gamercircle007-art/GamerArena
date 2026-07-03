import 'package:gamer_circle/shared/models/nearby_parlor.dart';

class ParlorSearchResponse {
  const ParlorSearchResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.limit,
    required this.hasMore,
  });

  final List<NearbyParlor> items;
  final int total;
  final int page;
  final int limit;
  final bool hasMore;

  factory ParlorSearchResponse.fromJson(Map<String, dynamic> json) =>
      ParlorSearchResponse(
        items: (json['items'] as List<dynamic>)
            .map((e) => NearbyParlor.fromJson(e as Map<String, dynamic>))
            .toList(),
        total: json['total'] as int? ?? 0,
        page: json['page'] as int? ?? 1,
        limit: json['limit'] as int? ?? 20,
        hasMore: json['has_more'] as bool? ?? false,
      );
}