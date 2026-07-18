import 'package:flutter/material.dart';
import 'package:visibility_detector/visibility_detector.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/features/feed/providers/ranked_feed_provider.dart';

/// Wrap feed items for auto tracking per ALG-FL04
class TrackableFeedItem extends ConsumerStatefulWidget {
  final String contentId;
  final String contentType;
  final int positionInFeed;
  final String feedType;
  final Widget child;
  final bool enableTracking;

  const TrackableFeedItem({
    super.key,
    required this.contentId,
    required this.contentType,
    required this.positionInFeed,
    required this.feedType,
    required this.child,
    this.enableTracking = true,
  });

  @override
  ConsumerState<TrackableFeedItem> createState() => _TrackableFeedItemState();
}

class _TrackableFeedItemState extends ConsumerState<TrackableFeedItem> {
  DateTime? _appearTime;
  bool _trackedView = false;
  bool _trackedDwell = false;

  @override
  Widget build(BuildContext context) {
    if (!widget.enableTracking) return widget.child;

    return VisibilityDetector(
      key: Key('track-${widget.contentType}-${widget.contentId}-${widget.positionInFeed}'),
      onVisibilityChanged: (info) {
        if (!mounted) return;
        final visible = info.visibleFraction > 0.7;

        if (visible && _appearTime == null) {
          _appearTime = DateTime.now();
          // view after 1s
          Future.delayed(const Duration(milliseconds: 1100), () {
            if (mounted && !_trackedView) {
              _trackedView = true;
              ref.read(rankedFeedProvider(widget.feedType).notifier)
                  .trackView(widget.contentId, widget.contentType, pos: widget.positionInFeed);
            }
          });
        }

        if (visible && !_trackedDwell) {
          final elapsed = _appearTime != null ? DateTime.now().difference(_appearTime!).inMilliseconds : 0;
          if (elapsed > 3000) {
            _trackedDwell = true;
            ref.read(rankedFeedProvider(widget.feedType).notifier)
                .trackDwell(widget.contentId, widget.contentType, pos: widget.positionInFeed, dur: elapsed);
          }
        }

        if (!visible && _appearTime != null) {
          final elapsed = DateTime.now().difference(_appearTime!).inMilliseconds;
          if (elapsed < 600 && !_trackedView) {
            ref.read(rankedFeedProvider(widget.feedType).notifier)
                .trackSkip(widget.contentId, widget.contentType, pos: widget.positionInFeed);
          }
          _appearTime = null;
        }
      },
      child: widget.child,
    );
  }
}
