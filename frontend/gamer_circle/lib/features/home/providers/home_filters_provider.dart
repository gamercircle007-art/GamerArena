import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/shared/models/home_data.dart';

/// `null` means the Nearby chip is selected (GPS / selected location).
final homeSelectedCityProvider = StateProvider<HomeCityItem?>((ref) => null);

final homeQuickPickFilterProvider =
    StateProvider<HomeQuickPickFilter>((ref) => HomeQuickPickFilter.recommended);

/// Distance filter for the all-parlors list on home (`null` = nearest, no radius cap).
enum HomeRadiusFilter {
  nearest,
  within2km,
  within5km,
  within10km,
  within20km,
}

extension HomeRadiusFilterX on HomeRadiusFilter {
  String get label => switch (this) {
        HomeRadiusFilter.nearest => 'Nearest',
        HomeRadiusFilter.within2km => 'Within 2 km',
        HomeRadiusFilter.within5km => 'Within 5 km',
        HomeRadiusFilter.within10km => 'Within 10 km',
        HomeRadiusFilter.within20km => 'Within 20 km',
      };

  /// Backend `radius` query param in meters; `null` returns all sorted by distance.
  int? get radiusMeters => switch (this) {
        HomeRadiusFilter.nearest => null,
        HomeRadiusFilter.within2km => 2000,
        HomeRadiusFilter.within5km => 5000,
        HomeRadiusFilter.within10km => 10000,
        HomeRadiusFilter.within20km => 20000,
      };
}

final homeRadiusFilterProvider =
    StateProvider<HomeRadiusFilter>((ref) => HomeRadiusFilter.nearest);

const fallbackHomeCities = [
  HomeCityItem(
    name: 'Delhi',
    imageUrl: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400',
    latitude: 28.6139,
    longitude: 77.2090,
  ),
  HomeCityItem(
    name: 'Mumbai',
    imageUrl: 'https://images.unsplash.com/photo-1566552881560-0be862a7c445?w=400',
    latitude: 19.0760,
    longitude: 72.8777,
  ),
  HomeCityItem(
    name: 'Hyderabad',
    imageUrl: 'https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=400',
    latitude: 17.3850,
    longitude: 78.4867,
  ),
  HomeCityItem(
    name: 'Bangalore',
    imageUrl: 'https://images.unsplash.com/photo-1596176530730-7c8049bedb1b?w=400',
    latitude: 12.9716,
    longitude: 77.5946,
  ),
  HomeCityItem(
    name: 'Chennai',
    imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400',
    latitude: 13.0827,
    longitude: 80.2707,
  ),
  HomeCityItem(
    name: 'Goa',
    imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf10e873?w=400',
    latitude: 15.2993,
    longitude: 74.1240,
  ),
  HomeCityItem(
    name: 'Pune',
    imageUrl: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=400',
    latitude: 18.5204,
    longitude: 73.8567,
  ),
  HomeCityItem(
    name: 'Kolkata',
    imageUrl: 'https://images.unsplash.com/photo-1558430322-d7feda25f6b8?w=400',
    latitude: 22.5726,
    longitude: 88.3639,
  ),
  HomeCityItem(
    name: 'Ahmedabad',
    imageUrl: 'https://images.unsplash.com/photo-1599669306557-8a1e1a5730b0?w=400',
    latitude: 23.0225,
    longitude: 72.5714,
  ),
  HomeCityItem(
    name: 'Jaipur',
    imageUrl: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400',
    latitude: 26.9124,
    longitude: 75.7873,
  ),
  HomeCityItem(
    name: 'Lucknow',
    imageUrl: 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400',
    latitude: 26.8467,
    longitude: 80.9462,
  ),
  HomeCityItem(
    name: 'Noida',
    imageUrl: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400',
    latitude: 28.5355,
    longitude: 77.3910,
  ),
  HomeCityItem(
    name: 'Gurgaon',
    imageUrl: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400',
    latitude: 28.4595,
    longitude: 77.0266,
  ),
  HomeCityItem(
    name: 'Chandigarh',
    imageUrl: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=400',
    latitude: 30.7333,
    longitude: 76.7794,
  ),
  HomeCityItem(
    name: 'Kochi',
    imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf10e873?w=400',
    latitude: 9.9312,
    longitude: 76.2673,
  ),
  HomeCityItem(
    name: 'Indore',
    imageUrl: 'https://images.unsplash.com/photo-1596176530730-7c8049bedb1b?w=400',
    latitude: 22.7196,
    longitude: 75.8577,
  ),
  HomeCityItem(
    name: 'Surat',
    imageUrl: 'https://images.unsplash.com/photo-1566552881560-0be862a7c445?w=400',
    latitude: 21.1702,
    longitude: 72.8311,
  ),
  HomeCityItem(
    name: 'Bhopal',
    imageUrl: 'https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=400',
    latitude: 23.2599,
    longitude: 77.4126,
  ),
  HomeCityItem(
    name: 'Patna',
    imageUrl: 'https://images.unsplash.com/photo-1558430322-d7feda25f6b8?w=400',
    latitude: 25.5941,
    longitude: 85.1376,
  ),
  HomeCityItem(
    name: 'Guwahati',
    imageUrl: 'https://images.unsplash.com/photo-1512343879784-a960bf10e873?w=400',
    latitude: 26.1445,
    longitude: 91.7362,
  ),
];