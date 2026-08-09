"""Discovery unit tests — amenities + cursor encoding (no DB)."""

from uuid import uuid4

from app.core.amenities import Amenity, mask_from_names, names_from_mask
from app.domains.discovery.geohash import encode
from app.domains.discovery.service import decode_cursor, encode_cursor


def test_amenities_bitmask_roundtrip():
    mask = mask_from_names(["PS5", "AC", "Parking"])
    assert mask == int(Amenity.PS5 | Amenity.AC | Amenity.PARKING)
    names = names_from_mask(mask)
    assert set(names) == {"PS5", "AC", "Parking"}


def test_amenities_filter_predicate():
    club = int(Amenity.PS5 | Amenity.VR | Amenity.CAFE)
    want = int(Amenity.PS5 | Amenity.VR)
    assert (club & want) == want
    assert (club & int(Amenity.PARKING)) == 0


def test_cursor_roundtrip():
    cid = uuid4()
    cur = encode_cursor(1234.5, cid)
    score, out = decode_cursor(cur)
    assert score == 1234.5
    assert out == cid


def test_geohash_precision_6():
    # Delhi
    h = encode(28.6139, 77.209, 6)
    assert len(h) == 6
    assert h.isalnum() or all(c in "0123456789bcdefghjkmnpqrstuvwxyz" for c in h)
