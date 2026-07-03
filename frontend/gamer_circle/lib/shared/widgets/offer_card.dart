import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:gamer_circle/core/constants/booking_colors.dart';
import 'package:gamer_circle/shared/models/home_data.dart';
import 'package:gamer_circle/shared/models/parlour_detail.dart';

class OfferCard extends StatelessWidget {
  const OfferCard({
    super.key,
    this.homeOffer,
    this.parlourOffer,
    this.onTap,
    this.width = 260,
  }) : assert(homeOffer != null || parlourOffer != null);

  final HomeOffer? homeOffer;
  final ParlourOffer? parlourOffer;
  final VoidCallback? onTap;
  final double width;

  String get _title => homeOffer?.title ?? parlourOffer!.title;
  String? get _description =>
      homeOffer?.description ?? parlourOffer?.description;
  String? get _imageUrl => homeOffer?.imageUrl;
  int? get _discount =>
      homeOffer?.discountPercent ?? parlourOffer?.discountPercent;
  String? get _code => homeOffer?.code ?? parlourOffer?.code;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: BookingColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_imageUrl != null && _imageUrl!.isNotEmpty)
                  ClipRRect(
                    borderRadius:
                        const BorderRadius.vertical(top: Radius.circular(11)),
                    child: CachedNetworkImage(
                      imageUrl: _imageUrl!,
                      height: 100,
                      width: double.infinity,
                      fit: BoxFit.cover,
                    ),
                  )
                else
                  Container(
                    height: 80,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(11),
                      ),
                      gradient: LinearGradient(
                        colors: [
                          BookingColors.oyoRed,
                          BookingColors.oyoRed.withOpacity(0.7),
                        ],
                      ),
                    ),
                    padding: const EdgeInsets.all(12),
                    alignment: Alignment.bottomLeft,
                    child: _discount != null
                        ? Text(
                            '$_discount% OFF',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                            ),
                          )
                        : null,
                  ),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: BookingColors.textPrimary,
                        ),
                      ),
                      if (_description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          _description!,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12,
                            color: BookingColors.textSecondary,
                          ),
                        ),
                      ],
                      if (_code != null) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: BookingColors.background,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: BookingColors.oyoRed,
                              style: BorderStyle.solid,
                            ),
                          ),
                          child: Text(
                            'Use: $_code',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: BookingColors.oyoRed,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}