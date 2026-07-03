import 'package:dio/dio.dart';
import 'package:gamer_circle/core/constants/messaging_api_paths.dart';
import 'package:gamer_circle/shared/models/story.dart';

class StoriesRepository {
  StoriesRepository(this._dio);

  final Dio _dio;

  Future<List<StoryGroup>> getFeed() async {
    final res = await _dio.get(StoriesApiPaths.feed);
    return (res.data as List<dynamic>)
        .map((e) => StoryGroup.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> createStory({
    required String mediaUrl,
    required String mediaType,
    String? assetId,
    String? caption,
    String privacy = 'friends',
    int durationSeconds = 5,
  }) async {
    await _dio.post(StoriesApiPaths.stories, data: {
      'media_url': mediaUrl,
      'media_type': mediaType,
      if (assetId != null) 'asset_id': assetId,
      if (caption != null) 'caption': caption,
      'privacy': privacy,
      'duration_seconds': durationSeconds,
    });
  }

  Future<void> markViewed(String storyId) async {
    await _dio.post(StoriesApiPaths.view(storyId));
  }

  Future<List<Story>> getUserStories(String userId) async {
    final res = await _dio.get(StoriesApiPaths.userStories(userId));
    return (res.data as List<dynamic>)
        .map((e) => Story.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<StoryViewEntry>> getStoryViewers(String storyId) async {
    final res = await _dio.get(StoriesApiPaths.viewers(storyId));
    return (res.data as List<dynamic>)
        .map((e) => StoryViewEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> deleteStory(String storyId) async {
    await _dio.delete(StoriesApiPaths.delete(storyId));
  }
}