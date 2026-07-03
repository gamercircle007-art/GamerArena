import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gamer_circle/core/constants/dms_api_paths.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:gamer_circle/shared/models/media_asset.dart';

final dmsServiceProvider = Provider<DmsService>(
  (ref) => DmsService(ref.watch(dioProvider)),
);

class DmsService {
  DmsService(this._dio);

  final Dio _dio;

  Future<DmsUploadResult> uploadFile({
    required File file,
    required String assetType,
    required String fileType,
    required String context,
    String? contextId,
    void Function(double progress)? onProgress,
  }) async {
    final fileSize = await file.length();
    final fileName = file.path.split(Platform.pathSeparator).last;

    final intentRes = await _dio.post<Map<String, dynamic>>(
      DmsApiPaths.uploadIntent,
      data: {
        'file_type': fileType,
        'file_name': fileName,
        'file_size': fileSize,
        'asset_type': assetType,
        'context': context,
        if (contextId != null) 'context_id': contextId,
      },
    );
    final data = intentRes.data ?? {};
    final assetId = data['asset_id'] as String;
    final uploadUrl = data['upload_url'] as String;
    final cdnUrl = data['cdn_url'] as String;

    final bytes = await file.readAsBytes();
    await _dio.put(
      uploadUrl,
      data: bytes,
      options: Options(
        headers: {'Content-Type': fileType},
        contentType: fileType,
        sendTimeout: const Duration(minutes: 10),
        receiveTimeout: const Duration(minutes: 10),
      ),
      onSendProgress: (sent, total) {
        if (total > 0) onProgress?.call(sent / total);
      },
    );
    onProgress?.call(1.0);

    final confirmRes = await _dio.post<Map<String, dynamic>>(
      DmsApiPaths.confirmUpload,
      data: {'asset_id': assetId},
    );
    final confirm = confirmRes.data ?? {};

    return DmsUploadResult(
      assetId: assetId,
      cdnUrl: cdnUrl,
      thumbnailUrl: confirm['thumbnail_url'] as String?,
    );
  }

  Future<MediaAsset> getAsset(String assetId) async {
    final res = await _dio.get<Map<String, dynamic>>(DmsApiPaths.asset(assetId));
    return MediaAsset.fromJson(res.data ?? {});
  }

  Future<void> deleteAsset(String assetId) async {
    await _dio.delete(DmsApiPaths.asset(assetId));
  }

  Future<void> updateContext(String assetId, String contextId) async {
    await _dio.patch(
      DmsApiPaths.assetContext(assetId),
      data: {'context_id': contextId},
    );
  }
}