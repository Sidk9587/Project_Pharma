import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../features/chat/bloc/chat_bloc.dart';
import '../features/chat/data/chat_websocket.dart';
import 'pharma_shell.dart';
import 'theme.dart';

class PharmaApp extends StatelessWidget {
  const PharmaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Pharma AI',
      theme: AppTheme.light,
      home: BlocProvider(
        create: (_) => ChatBloc(webSocket: ChatWebSocket()),
        child: const PharmaShell(),
      ),
    );
  }
}
