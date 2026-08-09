"""
Central ORM model registry for Alembic autogenerate and metadata.create_all.

Import every domain model here so migrations detect all tables.
"""

from app.domains.comment.models import Comment  # noqa: F401
from app.domains.friend.models import FriendRequest, Friendship, UserBlock  # noqa: F401
from app.domains.messaging.models import (  # noqa: F401
    Conversation,
    ConversationParticipant,
    Message,
)
from app.domains.online.models import UserLastSeen  # noqa: F401
from app.domains.snap_map.models import CloseFriend, UserLocation, UserProfile  # noqa: F401
from app.domains.story.models import Story, StoryView  # noqa: F401
from app.domains.follow.models import Follow  # noqa: F401
from app.domains.gaming_booking.gc_points import GCPoints, GCPointsTransaction  # noqa: F401
from app.domains.gaming_booking.models import (  # noqa: F401
    CancellationReason,
    GamingBooking,
    GamingSlot,
    ParlourOffer,
    ParlourRating,
    UserSearchHistory,
)
from app.domains.gaming_booking.inventory_models import (  # noqa: F401
    BookingAudit,
    BookingHold,
    BookingUnitLock,
    ParlorClosure,
    ParlorHours,
    ParlorStation,
    PaymentLedger,
    ReconciliationIssue,
    WebhookEvent,
)
from app.domains.club_ops.models import (  # noqa: F401
    ClubCustomer,
    ClubCustomerNote,
    ClubPricingRule,
    ClubPromotion,
    ClubResource,
    ClubZone,
    OccupancyRollup,
)
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension  # noqa: F401
from app.domains.like.models import Like  # noqa: F401
from app.domains.notification.models import Notification  # noqa: F401
from app.domains.parlor.models import Parlor  # noqa: F401
from app.domains.post.models import Post  # noqa: F401
from app.domains.reel.models import (  # noqa: F401
    Reel,
    ReelBookmark,
    ReelComment,
    ReelReport,
    ReelView,
    UserFollow,
)
from app.domains.tournament.models import Booking, Tournament  # noqa: F401
from app.domains.dms.models import MediaAsset  # noqa: F401
from app.domains.user.models import User  # noqa: F401
from app.models.recommendation import (  # noqa: F401
    UserInteraction,
    UserInterestProfile,
    ContentEngagementStats,
    TrendingItem,
    FeedImpression,
    SearchEvent,
)