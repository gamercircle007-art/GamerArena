/// Amenity bitmask — keep in sync with backend `app/core/amenities.py`.
class Amenity {
  static const int ps5 = 1;
  static const int pc = 2;
  static const int vr = 4;
  static const int snooker = 8;
  static const int ac = 16;
  static const int parking = 32;
  static const int cafe = 64;

  static const Map<int, String> labels = {
    ps5: 'PS5',
    pc: 'PC',
    vr: 'VR',
    snooker: 'Snooker',
    ac: 'AC',
    parking: 'Parking',
    cafe: 'Cafe',
  };

  static List<String> namesFromMask(int mask) =>
      labels.entries.where((e) => mask & e.key != 0).map((e) => e.value).toList();

  static int maskFromNames(Iterable<String> names) {
    final lookup = {
      for (final e in labels.entries) e.value.toLowerCase(): e.key,
      'playstation': ps5,
      'pool': snooker,
      'billiards': snooker,
    };
    var mask = 0;
    for (final n in names) {
      final bit = lookup[n.trim().toLowerCase()];
      if (bit != null) mask |= bit;
    }
    return mask;
  }
}
