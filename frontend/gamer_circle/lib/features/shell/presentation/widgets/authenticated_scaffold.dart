import 'package:flutter/material.dart';
import 'package:gamer_circle/features/shell/presentation/widgets/app_drawer.dart';

class AuthenticatedScaffold extends StatelessWidget {
  final Widget body;
  final PreferredSizeWidget? appBar;

  const AuthenticatedScaffold({
    super.key,
    required this.body,
    this.appBar,
  });

  static void openDrawer(BuildContext context) {
    Scaffold.of(context).openDrawer();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      drawer: const AppDrawer(),
      backgroundColor: Colors.white,
      body: body,
    );
  }
}