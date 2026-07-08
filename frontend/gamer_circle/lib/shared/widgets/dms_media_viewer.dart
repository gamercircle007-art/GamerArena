import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class DmsMediaViewer extends StatelessWidget {
  const DmsMediaViewer({
    super.key,
    this.assetId,
    required this.cdnUrl,
    this.assetType = 'image',
    this.thumbnailUrl,
    this.height = 200,
    this.borderRadius = 12,
    this.onTap,
  });

  final String? assetId;
  final String cdnUrl;
  final String assetType;
  final String? thumbnailUrl;
  final double height;
  final double borderRadius;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    if (cdnUrl.isEmpty) {
      return const SizedBox.shrink();
    }

    if (assetType == 'document') {
      return _DocumentCard(cdnUrl: cdnUrl, onTap: onTap);
    }

    if (assetType == 'video') {
      return _VideoCard(
        cdnUrl: cdnUrl,
        thumbnailUrl: thumbnailUrl,
        height: height,
        borderRadius: borderRadius,
        onTap: onTap,
      );
    }

    return GestureDetector(
      onTap: onTap,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: CachedNetworkImage(
          imageUrl: cdnUrl,
          height: height,
          width: double.infinity,
          fit: BoxFit.cover,
          placeholder: (_, __) => Container(
            height: height,
            color: const Color(0xFFF0F0F0),
            child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
          ),
          errorWidget: (_, __, ___) => Container(
            height: height,
            color: const Color(0xFFF0F0F0),
            child: const Icon(Icons.broken_image_outlined),
          ),
        ),
      ),
    );
  }
}

class _VideoCard extends StatelessWidget {
  const _VideoCard({
    required this.cdnUrl,
    this.thumbnailUrl,
    required this.height,
    required this.borderRadius,
    this.onTap,
  });

  final String cdnUrl;
  final String? thumbnailUrl;
  final double height;
  final double borderRadius;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final poster = thumbnailUrl ?? cdnUrl;
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        alignment: Alignment.center,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(borderRadius),
            child: CachedNetworkImage(
              imageUrl: poster,
              height: height,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
          ),
          Container(
            width: 48,
            height: 48,
            decoration: const BoxDecoration(
              color: Colors.black54,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.play_arrow, color: Colors.white, size: 32),
          ),
        ],
      ),
    );
  }
}

class _DocumentCard extends StatelessWidget {
  const _DocumentCard({required this.cdnUrl, this.onTap});

  final String cdnUrl;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.dmBackground,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              const Icon(Icons.description_outlined, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  cdnUrl.split('/').last,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              const Text('Open', style: TextStyle(color: Colors.blue)),
            ],
          ),
        ),
      ),
    );
  }
}