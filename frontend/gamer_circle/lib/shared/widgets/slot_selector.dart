import 'package:flutter/material.dart';

class SlotSelector extends StatelessWidget {
  const SlotSelector({
    super.key,
    required this.totalSlots,
    required this.bookedSlots,
    this.mySlotNumber,
  });

  final int totalSlots;
  final int bookedSlots;
  final int? mySlotNumber;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 5,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
      ),
      itemCount: totalSlots,
      itemBuilder: (context, index) {
        final slotNum = index + 1;
        Color color;
        if (mySlotNumber == slotNum) {
          color = Colors.blue;
        } else if (slotNum <= bookedSlots) {
          color = Colors.red.shade300;
        } else {
          color = Colors.green.shade300;
        }

        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
          ),
          alignment: Alignment.center,
          child: Text(
            '$slotNum',
            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
          ),
        );
      },
    );
  }
}