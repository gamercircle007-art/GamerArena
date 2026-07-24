import 'package:gamer_circle/shared/models/gc_points.dart';
import 'package:gamer_circle/shared/models/parlour_search.dart';

enum HomeQuickPickFilter { recommended, pastStays, recentlyViewed }

extension HomeQuickPickFilterX on HomeQuickPickFilter {
  String get apiValue => switch (this) {
        HomeQuickPickFilter.recommended => 'recommended',
        HomeQuickPickFilter.pastStays => 'past_stays',
        HomeQuickPickFilter.recentlyViewed => 'recently_viewed',
      };

  String get label => switch (this) {
        HomeQuickPickFilter.recommended => 'Recommended',
        HomeQuickPickFilter.pastStays => 'Past stays',
        HomeQuickPickFilter.recentlyViewed => 'Recently Viewed',
      };

  static HomeQuickPickFilter fromApi(String? value) => switch (value) {
        'past_stays' => HomeQuickPickFilter.pastStays,
        'recently_viewed' => HomeQuickPickFilter.recentlyViewed,
        _ => HomeQuickPickFilter.recommended,
      };
}

class HomeData {
  const HomeData({
    this.locationLabel = 'Select location',
    this.banners = const [],
    this.offers = const [],
    this.categories = const [],
    this.featuredParlours = const [],
    this.quickPickParlours = const [],
    this.allParlours = const [],
    this.nearbyParlours = const [],
    this.budgetParlours = const [],
    this.gcPoints,
    this.recentSearches = const [],
    this.cities = const [],
    this.pickFilter = HomeQuickPickFilter.recommended,
    this.nearbyCount = 0,
    this.posts = const [],
  });

  final String locationLabel;
  final List<HomeBanner> banners;
  final List<HomeOffer> offers;
  final List<HomeCategory> categories;
  final List<ParlourSearchItem> featuredParlours;
  final List<ParlourSearchItem> quickPickParlours;
  final List<ParlourSearchItem> allParlours;
  final List<ParlourSearchItem> nearbyParlours;
  final List<ParlourSearchItem> budgetParlours;
  final GcPoints? gcPoints;
  final List<String> recentSearches;
  final List<HomeCityItem> cities;
  final HomeQuickPickFilter pickFilter;
  final int nearbyCount;
  final List<HomePostItem> posts;

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
        quickPickParlours: quickPickParlours,
        allParlours: allParlours,
        nearbyParlours: nearbyParlours,
        budgetParlours: budgetParlours,
        gcPoints: gcPoints,
        recentSearches: recentSearches,
        cities: cities,
        pickFilter: pickFilter,
        nearbyCount: nearbyCount,
        posts: posts,
      );

  /// Maps backend ``GET /home`` response to [HomeData].
  factory HomeData.fromApi(Map<String, dynamic> json) {
    List<ParlourSearchItem> mapCards(List<dynamic>? list) =>
        (list ?? [])
            .map((e) => ParlourSearchItem.fromJson(e as Map<String, dynamic>))
            .toList();

    final featured = mapCards(json['featured'] as List<dynamic>?);
    final quickPicks = mapCards(json['quick_picks'] as List<dynamic>?);
    final nearbyParlors = mapCards(json['nearby_parlors'] as List<dynamic>?);
    final allParlours = nearbyParlors.isNotEmpty
        ? nearbyParlors
        : quickPicks.isNotEmpty
            ? quickPicks
            : featured;

    final city = json['city'] as String?;
    return HomeData(
      locationLabel: city ?? 'Around you',
      featuredParlours: featured,
      quickPickParlours: quickPicks,
      allParlours: allParlours,
      nearbyParlours: allParlours,
      budgetParlours: const [],
      cities: (json['cities'] as List<dynamic>?)
              ?.map((e) => HomeCityItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      pickFilter: HomeQuickPickFilterX.fromApi(json['pick_filter'] as String?),
      nearbyCount: json['nearby_count'] as int? ?? 0,
      posts: (json['posts'] as List<dynamic>?)
              ?.map((e) => HomePostItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}

class HomePostItem {
  const HomePostItem({
    required this.id,
    required this.content,
    required this.parlorId,
    required this.parlorName,
    this.mediaUrls = const [],
    this.parlorLogoUrl,
    this.parlorVerified = false,
    this.likesCount = 0,
    this.commentsCount = 0,
    required this.createdAt,
  });

  final String id;
  final String content;
  final List<String> mediaUrls;
  final String parlorId;
  final String parlorName;
  final String? parlorLogoUrl;
  final bool parlorVerified;
  final int likesCount;
  final int commentsCount;
  final DateTime createdAt;

  String? get coverImage =>
      mediaUrls.isNotEmpty ? mediaUrls.first : parlorLogoUrl;

  factory HomePostItem.fromJson(Map<String, dynamic> json) => HomePostItem(
        id: json['id'] as String,
        content: json['content'] as String,
        mediaUrls: (json['media_urls'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            const [],
        parlorId: json['parlor_id'] as String,
        parlorName: json['parlor_name'] as String,
        parlorLogoUrl: json['parlor_logo_url'] as String?,
        parlorVerified: json['parlor_verified'] as bool? ?? false,
        likesCount: json['likes_count'] as int? ?? 0,
        commentsCount: json['comments_count'] as int? ?? 0,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class HomeCityItem {
  const HomeCityItem({
    required this.name,
    this.parlourCount = 0,
    this.imageUrl,
    this.latitude,
    this.longitude,
  });

  final String name;
  final int parlourCount;
  final String? imageUrl;
  final double? latitude;
  final double? longitude;

  factory HomeCityItem.fromJson(Map<String, dynamic> json) => HomeCityItem(
        name: json['name'] as String,
        parlourCount: json['parlour_count'] as int? ?? 0,
        imageUrl: json['image_url'] as String?,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
      );
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