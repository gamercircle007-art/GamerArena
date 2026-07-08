import 'package:flutter/material.dart';
import 'package:gamer_circle/app/theme/app_colors.dart';

class DestinationCity {
  final String id;
  final String name;
  final IconData? icon;
  final Color? iconColor;
  final bool isNearMe;

  const DestinationCity({
    required this.id,
    required this.name,
    this.icon,
    this.iconColor,
    this.isNearMe = false,
  });
}

const kExploreCities = [
  DestinationCity(
    id: 'near_me',
    name: 'Near me',
    icon: Icons.near_me_rounded,
    iconColor: AppColors.secondary,
    isNearMe: true,
  ),
  DestinationCity(id: 'bangalore', name: 'Bangalore'),
  DestinationCity(id: 'chennai', name: 'Chennai'),
  DestinationCity(id: 'delhi', name: 'Delhi'),
  DestinationCity(id: 'gurgaon', name: 'Gurgaon'),
  DestinationCity(id: 'mumbai', name: 'Mumbai'),
  DestinationCity(id: 'hyderabad', name: 'Hyderabad'),
];