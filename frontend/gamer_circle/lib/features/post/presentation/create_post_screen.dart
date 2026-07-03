import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/core/providers/dio_provider.dart';
import 'package:image_picker/image_picker.dart';

class CreatePostScreen extends ConsumerStatefulWidget {
  const CreatePostScreen({super.key});

  @override
  ConsumerState<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends ConsumerState<CreatePostScreen> {
  final _content = TextEditingController();
  final List<String> _mediaUrls = [];
  bool _submitting = false;

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    final api = ref.read(socialApiProvider);
    final presigned = await api.presignedUrl('image/jpeg', 'post_media');
    final bytes = await file.readAsBytes();
    await api.uploadToPresignedUrl(
      uploadUrl: presigned['upload_url'] as String,
      bytes: bytes,
      contentType: 'image/jpeg',
    );
    _mediaUrls.add(presigned['public_url'] as String);
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Post')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _content,
              maxLines: 5,
              decoration: const InputDecoration(labelText: 'What\'s happening?'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickImage,
              icon: const Icon(Icons.image),
              label: Text('Add image (${_mediaUrls.length})'),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _submitting
                  ? null
                  : () async {
                      setState(() => _submitting = true);
                      try {
                        await ref.read(socialApiProvider).createPost({
                          'content': _content.text,
                          'media_urls': _mediaUrls,
                        });
                        if (context.mounted) context.go('/feed');
                      } finally {
                        if (mounted) setState(() => _submitting = false);
                      }
                    },
              child: _submitting
                  ? const CircularProgressIndicator()
                  : const Text('Post'),
            ),
          ],
        ),
      ),
    );
  }
}