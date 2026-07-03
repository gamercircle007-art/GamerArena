import 'package:flutter/material.dart';

class LandingSearchCard extends StatelessWidget {
  final String destination;
  final String dateTimeLabel;
  final VoidCallback onDestinationTap;
  final VoidCallback onDateTimeTap;
  final VoidCallback onSearch;

  const LandingSearchCard({
    super.key,
    required this.destination,
    required this.dateTimeLabel,
    required this.onDestinationTap,
    required this.onDateTimeTap,
    required this.onSearch,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE8E8E8)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          _SearchField(
            label: 'Destination',
            value: destination.isEmpty ? 'Search for city, location or venue' : destination,
            isPlaceholder: destination.isEmpty,
            onTap: onDestinationTap,
            showDivider: true,
          ),
          IntrinsicHeight(
            child: Row(
              children: [
                Expanded(
                  child: _SearchField(
                    label: 'Date & time',
                    value: dateTimeLabel,
                    isPlaceholder: false,
                    onTap: onDateTimeTap,
                    showDivider: false,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SearchField extends StatelessWidget {
  final String label;
  final String value;
  final bool isPlaceholder;
  final VoidCallback onTap;
  final bool showDivider;

  const _SearchField({
    required this.label,
    required this.value,
    required this.isPlaceholder,
    required this.onTap,
    required this.showDivider,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: showDivider
            ? const BorderRadius.vertical(top: Radius.circular(16))
            : const BorderRadius.vertical(bottom: Radius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF888888),
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: isPlaceholder
                      ? const Color(0xFFAAAAAA)
                      : const Color(0xFF1A1A2E),
                ),
              ),
              if (showDivider) ...[
                const SizedBox(height: 14),
                const Divider(height: 1, color: Color(0xFFEEEEEE)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class LandingSearchButton extends StatelessWidget {
  final VoidCallback onPressed;

  const LandingSearchButton({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        gradient: const LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [Color(0xFF7B2FF7), Color(0xFF3B82F6)],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF7B2FF7).withOpacity(0.35),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(14),
          child: const SizedBox(
            width: double.infinity,
            height: 52,
            child: Center(
              child: Text(
                'Search',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}