import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';
import 'package:image_picker/image_picker.dart';

class CreatePostScreen extends ConsumerStatefulWidget {
  const CreatePostScreen({super.key});

  @override
  ConsumerState<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends ConsumerState<CreatePostScreen> {
  final _content = TextEditingController();
  final List<String> _mediaUrls = [];
  String _currentTab = 'Post';
  bool _submitting = false;

  final List<String> _tabs = ['Video', 'Short', 'Live', 'Post'];

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    // For demo, just add local path or placeholder; in real use DMS
    _mediaUrls.add(file.path); // TODO: replace with real DMS upload
    setState(() {});
  }

  void _switchTab(String tab) {
    if (tab == _currentTab) return;
    setState(() => _currentTab = tab);
    if (tab == 'Short') {
      context.push('/create/camera', extra: 'short');
    } else if (tab == 'Video') {
      context.push('/create/camera', extra: 'video');
    } else if (tab == 'Live') {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Live coming soon')));
    }
    // Post stays here
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: isDark ? Colors.black : AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: isDark ? Colors.black : AppColors.surfaceLight,
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.pop(),
        ),
        title: const Text('Create post', style: TextStyle(fontWeight: FontWeight.w600)),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: FilledButton(
              onPressed: _submitting || (_content.text.trim().isEmpty && _mediaUrls.isEmpty)
                  ? null
                  : () {
                      context.push('/create/add-details', extra: {
                        'postType': _currentTab.toLowerCase(),
                        'caption': _content.text,
                        'media': _mediaUrls,
                      });
                    },
              style: FilledButton.styleFrom(
                backgroundColor: (_content.text.trim().isNotEmpty || _mediaUrls.isNotEmpty)
                    ? AppColors.primary
                    : Colors.grey.shade700,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              ),
              child: const Text('Next'),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Author row
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const CircleAvatar(
                  radius: 18,
                  backgroundImage: NetworkImage('https://picsum.photos/id/1011/200/200'), // Sheera placeholder
                ),
                const SizedBox(width: 12),
                const Text('Sheera', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade800,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.public, size: 14, color: Colors.white70),
                      SizedBox(width: 4),
                      Text('Public', style: TextStyle(fontSize: 12, color: Colors.white70)),
                    ],
                  ),
                ),
                const Spacer(),
                const Icon(Icons.more_horiz, color: Colors.white70),
              ],
            ),
          ),

          // Main input area
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: TextField(
                controller: _content,
                maxLines: null,
                expands: true,
                style: const TextStyle(fontSize: 16, color: Colors.white),
                decoration: InputDecoration(
                  hintText: _currentTab == 'Post' ? "What's on your gaming mind? Type @ to mention" : 'Share a sneak peek of your next video',
                  hintStyle: const TextStyle(color: Colors.white38, fontSize: 16),
                  border: InputBorder.none,
                ),
              ),
            ),
          ),

          // Media previews if any
          if (_mediaUrls.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(
                spacing: 8,
                children: _mediaUrls
                    .map((url) => ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(url, width: 80, height: 80, fit: BoxFit.cover, errorBuilder: (_, __, ___) => Container(width: 80, height: 80, color: Colors.grey)),
                        ))
                    .toList(),
              ),
            ),

          const Spacer(),

          // Bottom media strip (simplified)
          Container(
            height: 70,
            color: Colors.grey.shade900,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              children: [
                _buildMediaStripItem(Icons.camera_alt, 'Camera', () => _pickImage()),
                _buildMediaStripItem(Icons.image, 'Gallery', () => _pickImage()),
                ..._mediaUrls.map((u) => _buildMediaThumb(u)),
              ],
            ),
          ),

          // Bottom action icons
          Container(
            color: Colors.black,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                IconButton(icon: const Icon(Icons.text_fields), onPressed: () {}),
                IconButton(icon: const Icon(Icons.image), onPressed: _pickImage),
                IconButton(icon: const Icon(Icons.poll), onPressed: () {}),
              ],
            ),
          ),

          // Bottom tabs like YouTube
          Container(
            color: Colors.black,
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: _tabs.map((tab) {
                final isSelected = tab == _currentTab;
                return GestureDetector(
                  onTap: () => _switchTab(tab),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    decoration: isSelected
                        ? BoxDecoration(color: Colors.grey.shade800, borderRadius: BorderRadius.circular(20))
                        : null,
                    child: Text(
                      tab,
                      style: TextStyle(
                        color: isSelected ? Colors.white : Colors.white70,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMediaStripItem(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 60,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        decoration: BoxDecoration(color: Colors.grey.shade800, borderRadius: BorderRadius.circular(8)),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white70),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 10, color: Colors.white70)),
          ],
        ),
      ),
    );
  }

  Widget _buildMediaThumb(String url) {
    return Container(
      width: 60,
      height: 60,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        image: DecorationImage(image: NetworkImage(url), fit: BoxFit.cover, onError: (_, __) {}),
      ),
    );
  }
}