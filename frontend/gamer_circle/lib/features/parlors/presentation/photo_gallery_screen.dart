import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:photo_view/photo_view.dart';
import 'package:photo_view/photo_view_gallery.dart';

class PhotoGalleryScreen extends StatefulWidget {
  const PhotoGalleryScreen({
    super.key,
    required this.images,
    this.initialIndex = 0,
  });

  final List<String> images;
  final int initialIndex;

  @override
  State<PhotoGalleryScreen> createState() => _PhotoGalleryScreenState();
}

class _PhotoGalleryScreenState extends State<PhotoGalleryScreen> {
  late final PageController _controller;
  late int _index;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
    _controller = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final images = widget.images;
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text('${_index + 1} / ${images.length}'),
      ),
      body: images.isEmpty
          ? const Center(
              child: Text(
                'No photos available',
                style: TextStyle(color: Colors.white70),
              ),
            )
          : PhotoViewGallery.builder(
              pageController: _controller,
              itemCount: images.length,
              onPageChanged: (i) => setState(() => _index = i),
              builder: (_, i) => PhotoViewGalleryPageOptions(
                imageProvider: CachedNetworkImageProvider(images[i]),
                minScale: PhotoViewComputedScale.contained,
                maxScale: PhotoViewComputedScale.covered * 2,
                heroAttributes: PhotoViewHeroAttributes(tag: images[i]),
              ),
              loadingBuilder: (_, __) => const Center(
                child: CircularProgressIndicator(color: BookingColors.oyoRed),
              ),
            ),
    );
  }
}