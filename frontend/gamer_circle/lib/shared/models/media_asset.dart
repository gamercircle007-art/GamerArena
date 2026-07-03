class MediaAsset {
  const MediaAsset({
    required this.id,
    required this.cdnUrl,
    required this.assetType,
    this.thumbnailUrl,
    this.fileType,
    this.fileSizeBytes,
    this.fileSizeLabel,
    this.context,
    this.contextId,
    this.widthPx,
    this.heightPx,
    this.durationSeconds,
    this.status = 'active',
    this.uploaderName,
  });

  final String id;
  final String cdnUrl;
  final String assetType;
  final String? thumbnailUrl;
  final String? fileType;
  final int? fileSizeBytes;
  final String? fileSizeLabel;
  final String? context;
  final String? contextId;
  final int? widthPx;
  final int? heightPx;
  final double? durationSeconds;
  final String status;
  final String? uploaderName;

  bool get isImage => assetType == 'image';
  bool get isVideo => assetType == 'video';
  bool get isDocument => assetType == 'document';
  bool get isAudio => assetType == 'audio';

  factory MediaAsset.fromJson(Map<String, dynamic> json) => MediaAsset(
        id: json['id'] as String,
        cdnUrl: json['cdn_url'] as String,
        assetType: json['asset_type'] as String,
        thumbnailUrl: json['thumbnail_url'] as String?,
        fileType: json['file_type'] as String?,
        fileSizeBytes: json['file_size_bytes'] as int?,
        fileSizeLabel: json['file_size_label'] as String?,
        context: json['context'] as String?,
        contextId: json['context_id'] as String?,
        widthPx: json['width_px'] as int?,
        heightPx: json['height_px'] as int?,
        durationSeconds: (json['duration_seconds'] as num?)?.toDouble(),
        status: json['status'] as String? ?? 'active',
        uploaderName: json['uploader_name'] as String?,
      );
}

class DmsUploadResult {
  const DmsUploadResult({
    required this.assetId,
    required this.cdnUrl,
    this.thumbnailUrl,
  });

  final String assetId;
  final String cdnUrl;
  final String? thumbnailUrl;
}