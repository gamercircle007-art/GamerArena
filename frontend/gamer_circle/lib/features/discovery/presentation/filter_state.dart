import 'package:flutter/foundation.dart';

@immutable
class FilterState {
  const FilterState({
    this.distanceM = 5000,
    this.minRating,
    this.availableNow = false,
    this.amenitiesMask = 0,
    this.sort = 'distance',
    this.query = '',
    this.etag,
  });

  final int distanceM;
  final double? minRating;
  final bool availableNow;
  final int amenitiesMask;
  final String sort; // distance | rating | relevance
  final String query;
  final String? etag;

  int get radiusM => distanceM;

  FilterState copyWith({
    int? distanceM,
    double? minRating,
    bool? availableNow,
    int? amenitiesMask,
    String? sort,
    String? query,
    String? etag,
    bool clearMinRating = false,
    bool clearEtag = false,
  }) =>
      FilterState(
        distanceM: distanceM ?? this.distanceM,
        minRating: clearMinRating ? null : (minRating ?? this.minRating),
        availableNow: availableNow ?? this.availableNow,
        amenitiesMask: amenitiesMask ?? this.amenitiesMask,
        sort: sort ?? this.sort,
        query: query ?? this.query,
        etag: clearEtag ? null : (etag ?? this.etag),
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FilterState &&
          distanceM == other.distanceM &&
          minRating == other.minRating &&
          availableNow == other.availableNow &&
          amenitiesMask == other.amenitiesMask &&
          sort == other.sort &&
          query == other.query;

  @override
  int get hashCode => Object.hash(
        distanceM,
        minRating,
        availableNow,
        amenitiesMask,
        sort,
        query,
      );
}
