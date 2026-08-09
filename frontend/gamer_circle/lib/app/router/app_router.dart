import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/router/router_notifier.dart';
import 'package:gamer_circle/features/auth/presentation/pages/login_page.dart';
import 'package:gamer_circle/features/auth/presentation/pages/otp_verification_page.dart';
import 'package:gamer_circle/features/auth/presentation/pages/signup_page.dart';
import 'package:gamer_circle/features/onboarding/presentation/pages/grant_permissions_page.dart';
import 'package:gamer_circle/features/onboarding/presentation/pages/mobile_number_page.dart';
import 'package:gamer_circle/features/onboarding/presentation/pages/mobile_otp_page.dart';
import 'package:gamer_circle/features/onboarding/presentation/pages/welcome_onboarding_page.dart';
import 'package:gamer_circle/features/admin/presentation/admin_screen.dart';
import 'package:gamer_circle/features/comments/presentation/comments_screen.dart';
import 'package:gamer_circle/features/communities/presentation/communities_screen.dart';
import 'package:gamer_circle/features/events/presentation/events_screen.dart';
import 'package:gamer_circle/features/feed/presentation/feed_screen.dart';
import 'package:gamer_circle/features/booking/presentation/book_time_screen.dart';
import 'package:gamer_circle/features/booking/presentation/booking_checkout_screen.dart';
import 'package:gamer_circle/features/booking/presentation/booking_cancelled_screen.dart';
import 'package:gamer_circle/features/booking/presentation/booking_confirmed_screen.dart';
import 'package:gamer_circle/features/booking/presentation/booking_details_view_screen.dart';
import 'package:gamer_circle/features/booking/presentation/cancellation_detail_screen.dart';
import 'package:gamer_circle/features/booking/presentation/cancellation_reason_screen.dart';
import 'package:gamer_circle/features/booking/presentation/gaming_my_bookings_screen.dart';
import 'package:gamer_circle/features/booking/presentation/booking_status_screen.dart';
import 'package:gamer_circle/features/home/presentation/home_screen.dart';

import 'package:gamer_circle/features/parlors/presentation/parlour_detail_screen.dart';
import 'package:gamer_circle/features/parlors/presentation/photo_gallery_screen.dart';
import 'package:gamer_circle/features/parlors/presentation/ratings_reviews_screen.dart';
import 'package:gamer_circle/features/parlors/presentation/search_input_screen.dart';
import 'package:gamer_circle/features/parlors/presentation/search_results_screen.dart';
import 'package:gamer_circle/features/map/presentation/discover_screen.dart';
import 'package:gamer_circle/features/discovery/presentation/discovery_page.dart';
import 'package:gamer_circle/features/friends/presentation/friend_requests_screen.dart';
import 'package:gamer_circle/features/messaging/presentation/chat_screen.dart';
import 'package:gamer_circle/features/messaging/presentation/conversations_screen.dart';
import 'package:gamer_circle/features/messaging/presentation/new_chat_screen.dart';
import 'package:gamer_circle/features/friends/presentation/find_friends_screen.dart';
import 'package:gamer_circle/features/profile/presentation/privacy_settings_screen.dart';
import 'package:gamer_circle/features/profile/presentation/public_profile_screen.dart';
import 'package:gamer_circle/features/snap_map/presentation/snap_map_screen.dart';
import 'package:gamer_circle/features/stories/presentation/story_creator.dart';
import 'package:gamer_circle/features/notifications/presentation/notifications_screen.dart';
import 'package:gamer_circle/features/parlor/presentation/owner_dashboard_screen.dart';
import 'package:gamer_circle/features/parlor/presentation/parlor_profile_screen.dart';
import 'package:gamer_circle/features/post/presentation/create_post_screen.dart';
import 'package:gamer_circle/features/create_content/presentation/add_details_screen.dart';
import 'package:gamer_circle/features/create_content/presentation/camera_screen.dart';
import 'package:gamer_circle/features/create_content/presentation/trim_preview_screen.dart';
import 'package:gamer_circle/features/profile/presentation/my_bookings_screen.dart';
import 'package:gamer_circle/features/profile/presentation/pages/profile_page.dart';
import 'package:gamer_circle/features/friends/presentation/friends_list_screen.dart';
import 'package:gamer_circle/features/profile/presentation/my_profile_screen.dart';

import 'package:gamer_circle/features/reels/presentation/create_reel_screen.dart';
import 'package:gamer_circle/features/reels/presentation/reel_comments_screen.dart';
import 'package:gamer_circle/features/reels/presentation/reel_search_screen.dart';
import 'package:gamer_circle/features/reels/presentation/reels_screen.dart';
import 'package:gamer_circle/features/saved/presentation/pages/saved_page.dart';
import 'package:gamer_circle/features/settings/presentation/settings_screen.dart';

import 'package:gamer_circle/features/shell/presentation/widgets/main_shell_scaffold.dart';
import 'package:gamer_circle/features/store/presentation/pages/store_page.dart';
import 'package:gamer_circle/features/tournament/presentation/create_tournament_screen.dart';
import 'package:gamer_circle/features/tournament/presentation/tournament_chat_screen.dart';
import 'package:gamer_circle/features/tournament/presentation/tournament_detail_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final notifier = ref.watch(routerNotifierProvider);
  return GoRouter(
    initialLocation: '/onboarding',
    refreshListenable: notifier,
    redirect: notifier.redirect,
    routes: [
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const WelcomeOnboardingPage(),
      ),
      GoRoute(
        path: '/mobile-number',
        builder: (context, state) => const MobileNumberPage(),
      ),
      GoRoute(
        path: '/mobile-otp',
        builder: (context, state) => MobileOtpPage(
          phone: state.extra as String? ?? '',
        ),
      ),
      GoRoute(
        path: '/permissions',
        builder: (context, state) => const GrantPermissionsPage(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginPage(),
        routes: [
          GoRoute(
            path: 'signup',
            builder: (context, state) => const SignUpPage(),
            routes: [
              GoRoute(
                path: 'verify-otp',
                builder: (context, state) => const OtpVerificationPage(),
              ),
            ],
          ),
        ],
      ),
      ShellRoute(
        builder: (context, state, child) => MainShellScaffold(child: child),
        routes: [
          GoRoute(
            path: '/home-booking',
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/gaming-bookings',
            builder: (context, state) => const GamingMyBookingsScreen(),
          ),
          GoRoute(
            path: '/search-results',
            builder: (context, state) => const SearchResultsScreen(),
          ),
          GoRoute(
            path: '/search-input',
            builder: (context, state) => const SearchInputScreen(),
          ),
          GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
          GoRoute(path: '/feed', builder: (context, state) => const FeedScreen()),
          GoRoute(path: '/reels', builder: (context, state) => const ReelsScreen()),
          GoRoute(path: '/discover', builder: (context, state) => const DiscoveryPage()),
          GoRoute(path: '/discover/map', builder: (context, state) => const DiscoverScreen()),
          GoRoute(
            path: '/notifications',
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(path: '/snap-map', builder: (context, state) => const SnapMapScreen()),
          GoRoute(
            path: '/messages',
            builder: (context, state) => const ConversationsScreen(),
            routes: [
              GoRoute(
                path: 'new',
                builder: (context, state) => const NewChatScreen(),
              ),
              GoRoute(
                path: 'chat/:id',
                builder: (context, state) {
                  final extra = state.extra as Map<String, dynamic>? ?? {};
                  return ChatScreen(
                    conversationId: state.pathParameters['id']!,
                    otherUserId: extra['otherUserId'] as String? ?? '',
                    otherUserName: extra['otherUserName'] as String? ?? 'Chat',
                    otherUserAvatar: extra['otherUserAvatar'] as String?,
                  );
                },
              ),
            ],
          ),
          GoRoute(path: '/profile', builder: (context, state) => const MyProfileScreen()),
          GoRoute(path: '/store', builder: (context, state) => const StorePage()),
          GoRoute(path: '/events', builder: (context, state) => const EventsScreen()),
        ],
      ),
      GoRoute(path: '/profile/legacy', builder: (context, state) => const ProfilePage()),
      GoRoute(path: '/my-bookings', builder: (context, state) => const MyBookingsScreen()),
      GoRoute(
        path: '/parlour/:id',
        builder: (context, state) => ParlourDetailScreen(
          parlourId: state.pathParameters['id']!,
        ),
        routes: [
          GoRoute(
            path: 'detail',
            builder: (context, state) => ParlourDetailScreen(
              parlourId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: 'book',
            builder: (context, state) {
              final extra = state.extra as Map<String, dynamic>? ?? {};
              return BookTimeScreen(
                parlorId: state.pathParameters['id']!,
                parlorName: extra['name'] as String?,
                parlorImage: extra['image'] as String?,
              );
            },
          ),
          GoRoute(
            path: 'checkout',
            builder: (context, state) => BookingCheckoutScreen(
              parlorId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: 'gallery',
            builder: (context, state) {
              final images = state.extra as List<String>? ?? [];
              return PhotoGalleryScreen(images: images);
            },
          ),
        ],
      ),
      GoRoute(
        path: '/booking/confirm',
        builder: (context, state) => BookingConfirmedScreen(
          booking: state.extra,
        ),
      ),
      GoRoute(
        path: '/booking/status/:id',
        builder: (context, state) {
          final extra = state.extra;
          final mock = extra is Map && extra['mockMode'] == true;
          return BookingStatusScreen(
            bookingId: state.pathParameters['id']!,
            mockMode: mock,
          );
        },
      ),
      GoRoute(
        path: '/booking/:id/details',
        builder: (context, state) => BookingDetailsViewScreen(
          bookingId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/booking/:id/cancel-reason',
        builder: (context, state) => CancellationReasonScreen(
          bookingId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/booking/:id/cancel-detail',
        builder: (context, state) => CancellationDetailScreen(
          bookingId: state.pathParameters['id']!,
          reason: state.extra as String?,
        ),
      ),
      GoRoute(
        path: '/booking/:id/cancelled',
        builder: (context, state) => BookingCancelledScreen(
          bookingId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/ratings/:parlourId',
        builder: (context, state) => RatingsReviewsScreen(
          parlourId: state.pathParameters['parlourId']!,
        ),
      ),
      GoRoute(path: '/owner-dashboard', builder: (context, state) => const OwnerDashboardScreen()),
      GoRoute(path: '/create-post', builder: (context, state) => const CreatePostScreen()),
      GoRoute(path: '/create-reel', builder: (context, state) => const CreateReelScreen()),
      GoRoute(
        path: '/create/add-details',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>? ?? {};
          return AddDetailsScreen(
            postType: extra['postType'] as String? ?? 'post',
            videoUrl: extra['videoUrl'] as String?,
            durationSeconds: extra['duration'] as int?,
          );
        },
      ),
      GoRoute(
        path: '/create/camera',
        builder: (context, state) {
          final mode = state.extra as String? ?? 'short';
          return CameraScreen(mode: mode);
        },
      ),
      GoRoute(
        path: '/create/trim',
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>? ?? {};
          return TrimPreviewScreen(
            videoPath: extra['videoPath'] as String? ?? '',
            maxDuration: extra['maxDuration'] as int? ?? 60,
          );
        },
      ),
      GoRoute(path: '/reels/search', builder: (context, state) => const ReelSearchScreen()),
      GoRoute(
        path: '/reels/:id/comments',
        builder: (context, state) => ReelCommentsScreen(
          reelId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(path: '/create-tournament', builder: (context, state) => const CreateTournamentScreen()),
      GoRoute(
        path: '/tournaments/:id',
        builder: (context, state) => TournamentDetailScreen(
          tournamentId: state.pathParameters['id']!,
        ),
        routes: [
          GoRoute(
            path: 'chat',
            builder: (context, state) => TournamentChatScreen(
              tournamentId: state.pathParameters['id']!,
            ),
          ),
        ],
      ),

      GoRoute(path: '/friends-list', builder: (context, state) => const FriendsListScreen()),
      GoRoute(
        path: '/friend-requests',
        builder: (context, state) => const FriendRequestsScreen(),
      ),

      GoRoute(
        path: '/find-friends',
        builder: (context, state) => const FindFriendsScreen(),
      ),
      GoRoute(
        path: '/story/create',
        builder: (context, state) => const StoryCreator(),
      ),
      GoRoute(
        path: '/profile/:userId',
        builder: (context, state) => PublicProfileScreen(
          userId: state.pathParameters['userId']!,
        ),
      ),
      GoRoute(
        path: '/privacy-settings',
        builder: (context, state) => const PrivacySettingsScreen(),
      ),
      GoRoute(path: '/admin', builder: (context, state) => const AdminScreen()),
      GoRoute(
        path: '/parlors/:id',
        builder: (context, state) => ParlorProfileScreen(
          parlorId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(
        path: '/posts/:id/comments',
        builder: (context, state) => CommentsScreen(
          postId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(path: '/saved', builder: (context, state) => const SavedPage()),
      GoRoute(
        path: '/communities',
        builder: (context, state) => const CommunitiesScreen(),
      ),
      GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
    ],
  );
});