import 'package:gamer_circle/shared/models/gc_points.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

class HomeData {
  const HomeData({
    this.locationLabel = 'Select location',
    this.banners = const [],
    this.offers = const [],
    this.categories = const [],
    this.featuredParlours = const [],
    this.nearbyParlours = const [],
    this.budgetParlours = const [],
    this.gcPoints,
    this.recentSearches = const [],
  });

  final String locationLabel;
  final List<HomeBanner> banners;
  final List<HomeOffer> offers;
  final List<HomeCategory> categories;
  final List<ParlourSearchItem> featuredParlours;
  final List<ParlourSearchItem> nearbyParlours;
  final List<ParlourSearchItem> budgetParlours;
  final GcPoints? gcPoints;
  final List<String> recentSearches;

  factory HomeData.fromJson(Map<String, dynamic> json) => HomeData(
        locationLabel: json['location_label'] as String? ?? 'Select location',
        banners: (json['banners'] as List<dynamic>?)
                ?.map((e) => HomeBanner.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        offers: (json['offers'] as List<dynamic>?)
                ?.map((e) => HomeOffer.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        categories: (json['categories'] as List<dynamic>?)
                ?.map((e) => HomeCategory.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        featuredParlours: (json['featured_parlours'] as List<dynamic>?)
                ?.map(
                  (e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>),
                )
                .toList() ??
            const [],
        nearbyParlours: (json['nearby_parlours'] as List<dynamic>?)
                ?.map(
                  (e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>),
                )
                .toList() ??
            const [],
        budgetParlours: (json['budget_parlours'] as List<dynamic>?)
                ?.map(
                  (e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>),
                )
                .toList() ??
            const [],
        gcPoints: json['gc_points'] != null
            ? GcPoints.fromJson(json['gc_points'] as Map<String, dynamic>)
            : null,
        recentSearches: (json['recent_searches'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
      );

  static const empty = HomeData();

  HomeData copyWithLocationLabel(String label) => HomeData(
        locationLabel: label,
        banners: banners,
        offers: offers,
        categories: categories,
        featuredParlours: featuredParlours,
        nearbyParlours: nearbyParlours,
        budgetParlours: budgetParlours,
        gcPoints: gcPoints,
        recentSearches: recentSearches,
      );

  /// Maps backend ``GET /home`` response to [HomeData].
  factory HomeData.fromApi(Map<String, dynamic> json) {
    List<ParlourSearchItem> mapCards(List<dynamic>? list) =>
        (list ?? [])
            .map((e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>))
            .toList();

    final city = json['city'] as String?;
    return HomeData(
      locationLabel: city ?? 'Around you',
      featuredParlours: mapCards(json['featured'] as List<dynamic>?),
      nearbyParlours: mapCards(json['quick_picks'] as List<dynamic>?),
      budgetParlours: const [],
    );
  }
}

class HomeBanner {
  const HomeBanner({
    required this.id,
    required this.title,
    this.subtitle,
    this.imageUrl,
    this.actionUrl,
    this.backgroundColor,
  });

  final String id;
  final String title;
  final String? subtitle;
  final String? imageUrl;
  final String? actionUrl;
  final String? backgroundColor;

  factory HomeBanner.fromJson(Map<String, dynamic> json) => HomeBanner(
        id: json['id'] as String,
        title: json['title'] as String,
        subtitle: json['subtitle'] as String?,
        imageUrl: json['image_url'] as String?,
        actionUrl: json['action_url'] as String?,
        backgroundColor: json['background_color'] as String?,
      );
}

class HomeOffer {
  const HomeOffer({
    required this.id,
    required this.title,
    this.description,
    this.imageUrl,
    this.discountPercent,
    this.code,
  });

  final String id;
  final String title;
  final String? description;
  final String? imageUrl;
  final int? discountPercent;
  final String? code;

  factory HomeOffer.fromJson(Map<String, dynamic> json) => HomeOffer(
        id: json['id'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        imageUrl: json['image_url'] as String?,
        discountPercent: json['discount_percent'] as int?,
        code: json['code'] as String?,
      );
}

class HomeCategory {
  const HomeCategory({
    required this.id,
    required this.name,
    this.icon,
    this.filterValue,
  });

  final String id;
  final String name;
  final String? icon;
  final String? filterValue;

  factory HomeCategory.fromJson(Map<String, dynamic> json) => HomeCategory(
        id: json['id'] as String,
        name: json['name'] as String,
        icon: json['icon'] as String?,
        filterValue: json['filter_value'] as String?,
      );
}