import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:file_picker/file_picker.dart' as file_picker;
import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/constants/onboarding_colors.dart';
import 'package:gamer_circle/core/services/dms_service.dart';
import 'package:gamer_circle/shared/models/media_asset.dart';
import 'package:image_picker/image_picker.dart';

class DmsUploadWidget extends ConsumerStatefulWidget {
  const DmsUploadWidget({
    super.key,
    required this.context,
    required this.allowedTypes,
    required this.onUploaded,
    this.contextId,
    this.existingCdnUrl,
    this.onRemoved,
    this.height = 180,
    this.showPreview = true,
    this.placeholder,
  });

  final String context;
  final List<String> allowedTypes;
  final void Function(DmsUploadResult result) onUploaded;
  final String? contextId;
  final String? existingCdnUrl;
  final VoidCallback? onRemoved;
  final double height;
  final bool showPreview;
  final Widget? placeholder;

  @override
  ConsumerState<DmsUploadWidget> createState() => _DmsUploadWidgetState();
}

class _DmsUploadWidgetState extends ConsumerState<DmsUploadWidget> {
  double? _progress;
  bool _uploading = false;
  String? _previewPath;
  String? _cdnUrl;
  String? _error;

  Future<void> _pickAndUpload() async {
    File? file;
    String? mimeType;
    String assetType = widget.allowedTypes.first;

    if (widget.allowedTypes.contains('image') &&
        !widget.allowedTypes.contains('video') &&
        !widget.allowedTypes.contains('document')) {
      final picked = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );
      if (picked == null) return;
      file = File(picked.path);
      mimeType = 'image/jpeg';
      assetType = 'image';
    } else if (widget.allowedTypes.contains('video')) {
      final picked = await ImagePicker().pickVideo(source: ImageSource.gallery);
      if (picked == null) return;
      file = File(picked.path);
      mimeType = 'video/mp4';
      assetType = 'video';
    } else {
      // Use alias to ensure resolution for FilePicker.platform in all analyzer contexts
      final result = await file_picker.FilePicker.platform.pickFiles(
        type: file_picker.FileType.custom,
        allowedExtensions: const ['pdf', 'doc', 'docx', 'txt', 'jpg', 'png'],
      );
      if (result == null || result.files.isEmpty) return;
      final pickedPath = result.files.first.path;
      if (pickedPath == null) return;
      file = File(pickedPath);
      final ext = result.files.first.extension?.toLowerCase();
      mimeType = ext == 'pdf' ? 'application/pdf' : 'image/jpeg';
      assetType = ext == 'pdf' ? 'document' : 'image';
    }

    setState(() {
      _uploading = true;
      _error = null;
      _previewPath = file!.path;
      _progress = 0;
    });

    try {
      final result = await ref.read(dmsServiceProvider).uploadFile(
            file: file,
            assetType: assetType,
            fileType: mimeType!,
            context: widget.context,
            contextId: widget.contextId,
            onProgress: (p) => setState(() => _progress = p),
          );
      setState(() {
        _cdnUrl = result.cdnUrl;
        _uploading = false;
        _progress = null;
      });
      widget.onUploaded(result);
    } catch (e) {
      setState(() {
        _error = 'Upload failed. Tap to retry.';
        _uploading = false;
        _progress = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayUrl = _cdnUrl ?? widget.existingCdnUrl;

    return GestureDetector(
      onTap: _uploading ? null : _pickAndUpload,
      child: Container(
        height: widget.height,
        decoration: BoxDecoration(
          color: AppColors.dmBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _error != null ? Colors.red : const Color(0xFFE0E0E0),
          ),
        ),
        child: _uploading
            ? _UploadingState(progress: _progress ?? 0)
            : displayUrl != null && widget.showPreview
                ? _PreviewState(
                    cdnUrl: displayUrl,
                    localPath: _previewPath,
                    onRemove: widget.onRemoved == null
                        ? null
                        : () {
                            setState(() => _cdnUrl = null);
                            widget.onRemoved?.call();
                          },
                  )
                : _EmptyState(
                    allowedTypes: widget.allowedTypes,
                    error: _error,
                    placeholder: widget.placeholder,
                  ),
      ),
    );
  }
}

class _UploadingState extends StatelessWidget {
  const _UploadingState({required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        CircularProgressIndicator(
          value: progress,
          color: OnboardingColors.primary,
          strokeWidth: 3,
        ),
        const SizedBox(height: 12),
        Text(
          '${(progress * 100).toInt()}%',
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: OnboardingColors.primary,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Uploading...',
          style: TextStyle(fontSize: 12, color: OnboardingColors.textSecondary),
        ),
      ],
    );
  }
}

class _PreviewState extends StatelessWidget {
  const _PreviewState({
    required this.cdnUrl,
    this.localPath,
    this.onRemove,
  });

  final String cdnUrl;
  final String? localPath;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: localPath != null
              ? Image.file(File(localPath!), fit: BoxFit.cover)
              : CachedNetworkImage(imageUrl: cdnUrl, fit: BoxFit.cover),
        ),
        if (onRemove != null)
          Positioned(
            top: 8,
            right: 8,
            child: GestureDetector(
              onTap: onRemove,
              child: Container(
                width: 28,
                height: 28,
                decoration: const BoxDecoration(
                  color: Colors.black54,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.close, color: Colors.white, size: 16),
              ),
            ),
          ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.allowedTypes,
    this.error,
    this.placeholder,
  });

  final List<String> allowedTypes;
  final String? error;
  final Widget? placeholder;

  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 32),
          const SizedBox(height: 8),
          Text(
            error!,
            style: const TextStyle(color: Colors.red, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ],
      );
    }
    if (placeholder != null) return Center(child: placeholder!);

    final icon = allowedTypes.first == 'image'
        ? Icons.image_outlined
        : allowedTypes.first == 'video'
            ? Icons.videocam_outlined
            : allowedTypes.first == 'document'
                ? Icons.description_outlined
                : Icons.upload_file_outlined;

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, color: const Color(0xFFBBBBBB), size: 36),
        const SizedBox(height: 8),
        Text(
          'Tap to upload ${allowedTypes.join(' or ')}',
          style: const TextStyle(fontSize: 13, color: OnboardingColors.textSecondary),
        ),
      ],
    );
  }
}