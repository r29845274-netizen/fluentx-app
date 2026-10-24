#!/usr/bin/env python3
"""Add native continuous Gemini Live audio, waveform and interruption support."""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "fluentx_admin_secure")
pub=root/"pubspec.yaml"
s=pub.read_text()
if "  record: " not in s:
    marker="dependencies:\n"
    assert marker in s
    s=s.replace(marker,marker+"  record: 6.2.1\n  flutter_sound: 9.30.0\n",1)
pub.write_text(s)

voice=root/"lib/features/ai_practice/presentation/screens/gemini_voice_screen.dart"
s=voice.read_text()
if "import 'gemini_live_audio_screen.dart';" not in s:
    s="import 'gemini_live_audio_screen.dart';\n"+s
marker="        const Text('Personalized English speaking coach'),"
if "GeminiLiveAudioScreen()" not in s:
    assert marker in s
    s=s.replace(marker,marker+"""
        const SizedBox(height:10),
        FilledButton.icon(
          onPressed:()=>Navigator.of(context).push(
            MaterialPageRoute<void>(builder:(_)=>const GeminiLiveAudioScreen()),
          ),
          icon:const Icon(Icons.waves),
          label:const Text('Gemini Live • Hands-free Voice'),
        ),
""",1)
voice.write_text(s)

target=voice.with_name("gemini_live_audio_screen.dart")
target.write_text(r"""import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:record/record.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Gemini Live: continuous 16-kHz mono PCM microphone to a signed-in Edge
/// relay; 24-kHz mono PCM AI output. API key stays on Supabase, not in the APK.
class GeminiLiveAudioScreen extends StatefulWidget {
  const GeminiLiveAudioScreen({super.key});
  @override
  State<GeminiLiveAudioScreen> createState()=>_GeminiLiveAudioScreenState();
}
class _GeminiLiveAudioScreenState extends State<GeminiLiveAudioScreen> {
  final AudioRecorder _recorder=AudioRecorder();
  final FlutterSoundPlayer _player=FlutterSoundPlayer();
  StreamSubscription<Uint8List>? _microphone;
  StreamSubscription<dynamic>? _socketMessages;
  WebSocket? _socket;
  bool _running=false, _playerReady=false, _playing=false, _micReady=false;
  bool _connected=false;
  String _state='Ready',_learnerText='',_aiText='';
  String? _error;
  DateTime? _startedAt;
  Duration _elapsed=Duration.zero;
  Timer? _clock;
  double _level=0;
  DateTime _levelAt=DateTime.fromMillisecondsSinceEpoch(0);
  Future<void> _pendingAudio=Future<void>.value();
  int _audioGeneration=0;
  int _sessionId=0;
  final List<String> _userTurns=[];

  void _update(String value){
    if(mounted)setState(()=>_state=value);
  }

  Future<void> _start() async{
    if(_running)return;
    final session=Supabase.instance.client.auth.currentSession;
    if(session==null){setState(()=>_error='Please log in before using Live Voice.');return;}
    _running=true;
    final run=++_sessionId;
    _startedAt=DateTime.now();
    _userTurns.clear();
    setState((){
      _state='Connecting';
      _error=null;_connected=false;_learnerText='';_aiText='';
      _elapsed=Duration.zero;_level=0;
    });
    _clock=Timer.periodic(const Duration(seconds:1),(_){
      if(mounted && _startedAt!=null)setState(()=>_elapsed=DateTime.now().difference(_startedAt!));
    });
    try{
      final url=Uri.parse(const String.fromEnvironment('SUPABASE_URL'))
          .replace(scheme:'wss',path:'/functions/v1/voice-assistant/live');
      _socket=await WebSocket.connect(
        url.toString(),
        headers:{'Authorization':'Bearer '+session.accessToken},
      ).timeout(const Duration(seconds:18));
      if(!_running || run!=_sessionId){await _socket?.close();return;}
      _socketMessages=_socket!.listen((message){
        if(!_running || run!=_sessionId)return;
        if(message is String)_onGemini(message);
      },onError:(Object error){if(mounted)setState((){_error='Live connection failed. Try again.';_state='Disconnected';});_stop();},
        onDone:(){if(_running){if(mounted)setState((){_error='Live conversation disconnected. Tap Start to reconnect.';_state='Disconnected';});_stop();}});
      if(!await _recorder.hasPermission())throw StateError('Microphone permission denied');
      await _player.openPlayer();
      _playerReady=true;
      // The Gemini setupComplete frame will start the microphone and player.
      _update('Authenticating Gemini');
    }catch(error){
      await _stop();
      if(mounted)setState(()=>_error='Unable to start Live Voice: '+error.toString());
    }
  }

  Future<void> _openAudio() async{
    if(!_running || _micReady)return;
    try{
      await _player.startPlayerFromStream(
        codec:Codec.pcm16,
        interleaved:true,
        numChannels:1,
        sampleRate:24000,
        bufferSize:8192,
      );
      _playing=true;
      final stream=await _recorder.startStream(const RecordConfig(
        encoder:AudioEncoder.pcm16bits,
        sampleRate:16000,
        numChannels:1,
        autoGain:true,
        echoCancel:true,
        noiseSuppress:true,
      ));
      _microphone=stream.listen((buffer){
        if(!_running || !_connected || _socket?.readyState!=WebSocket.open)return;
        _showAmplitude(buffer);
        _socket!.add(jsonEncode({'realtimeInput':{'audio':{
          'data':base64Encode(buffer),'mimeType':'audio/pcm;rate=16000'
        }}}));
      },onError:(Object error){if(mounted)setState(()=>_error='Microphone stream interrupted.');});
      _micReady=true;
      _update('Listening');
    }catch(error){
      if(mounted)setState(()=>_error='Audio device error: '+error.toString());
      await _stop();
    }
  }

  void _showAmplitude(Uint8List bytes){
    final now=DateTime.now();
    if(now.difference(_levelAt).inMilliseconds<125)return;
    _levelAt=now;
    double sum=0;
    for(var i=0;i+1<bytes.length;i+=8){
      final sample=(bytes[i] | (bytes[i+1]<<8));
      final signed=sample>=32768?sample-65536:sample;
      sum+=signed*signed;
    }
    final n=max(1,bytes.length~/8);
    final rms=sqrt(sum/n)/32768;
    if(mounted)setState(()=>_level=(rms*7).clamp(0.04,1.0));
  }

  void _onGemini(String data){
    try{
      final decoded=jsonDecode(data);
      if(decoded is! Map)return;
      if(decoded['error']!=null){
        if(mounted)setState(()=>_error=decoded['error'].toString());
        return;
      }
      if(decoded.containsKey('setupComplete')){
        _connected=true;
        _openAudio();
        return;
      }
      final content=decoded['serverContent'];
      if(content is! Map)return;
      final input=content['inputTranscription'];
      final output=content['outputTranscription'];
      if(input is Map && input['text'] is String){
        final text=input['text'].toString();
        if(text.isNotEmpty && text!=_learnerText){
          _userTurns.add(text);
          if(mounted)setState(()=>_learnerText=text);
        }
      }
      if(output is Map && output['text'] is String && mounted){
        setState(()=>_aiText=output['text'].toString());
      }
      if(content['interrupted']==true){
        _audioGeneration++;
        _pendingAudio=Future<void>.value();
        _restartPlayback();
        _update('Listening');
        return;
      }
      final modelTurn=content['modelTurn'];
      if(modelTurn is Map){
        final parts=modelTurn['parts'];
        if(parts is List){
          for(final part in parts){
            if(part is Map && part['inlineData'] is Map){
              final audio=part['inlineData'] as Map;
              if(audio['data'] is String)_enqueueAudio(audio['data'].toString());
            }
          }
        }
      }
      if(content['turnComplete']==true)_update('Listening');
    }catch(_){
      if(mounted)setState(()=>_error='Received an invalid Live audio frame.');
    }
  }

  void _enqueueAudio(String payload){
    if(!_playing || !_running)return;
    final generation=_audioGeneration;
    _update('Speaking');
    _pendingAudio=_pendingAudio.then((_) async{
      if(!_running || !_playing || generation!=_audioGeneration)return;
      try{
        await _player.feedUint8FromStream(base64Decode(payload));
      }catch(_){
        if(mounted)setState(()=>_error='Audio playback interrupted.');
      }
    });
  }

  Future<void> _restartPlayback() async{
    try{
      await _player.stopPlayer();
      if(!_running)return;
      await _player.startPlayerFromStream(codec:Codec.pcm16,interleaved:true,numChannels:1,sampleRate:24000,bufferSize:8192);
    }catch(_){if(mounted)setState(()=>_error='Speaker could not restart.');}
  }

  Future<void> _stop() async{
    _running=false;
    ++_sessionId;
    _clock?.cancel();_clock=null;
    _audioGeneration++;
    _connected=false;
    _micReady=false;
    _playing=false;
    final microphone=_microphone;_microphone=null;
    await microphone?.cancel();
    try{await _recorder.stop();}catch(_){}
    final socket=_socket;_socket=null;
    try{await _socketMessages?.cancel();}catch(_){}
    _socketMessages=null;
    try{await socket?.close();}catch(_){}
    if(_playerReady){
      try{await _player.stopPlayer();}catch(_){}
      try{await _player.closePlayer();}catch(_){}
      _playerReady=false;
    }
    if(mounted && _state!='Disconnected')setState(()=>_state='Stopped');
  }

  Future<void> _openScorecard() async{
    if(_userTurns.length<2){
      setState(()=>_error='Speak at least two answers before making a scorecard.');
      return;
    }
    await _stop();
    setState((){_state='Assessing';_error=null;});
    try{
      final r=await Supabase.instance.client.functions.invoke('voice-assistant/scorecard',
        body:{'turns':_userTurns.take(24).toList(),'duration_seconds':_elapsed.inSeconds});
      if(!mounted)return;
      if(r.status>=300 || r.data is! Map || (r.data as Map)['report'] is! Map)throw StateError('Scorecard not available.');
      final card=(r.data as Map)['report'] as Map;
      await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
        title:const Text('Live Speaking Scorecard'),
        content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Score: '+card['overall_score'].toString()+'/100'),
          Text('Level: '+card['level'].toString()),
          Text('Fluency: '+card['fluency_score'].toString()),
          Text('Grammar: '+card['grammar_score'].toString()),
          Text('Vocabulary: '+card['vocabulary_score'].toString()),
          const SizedBox(height:8),
          Text('Next practice: '+card['next_practice'].toString()),
        ])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Done'))]));
    }catch(error){if(mounted)setState(()=>_error='Scorecard failed: '+error.toString());}
    finally{if(mounted)setState(()=>_state='Ready');}
  }

  @override
  void dispose(){
    // Dispose closes streams and sockets without blocking widget teardown.
    _stop();
    _recorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context){
    final bars=List<double>.generate(17,(index)=>0.16+0.84*_level*(0.5+0.5*sin(index*0.9+_elapsed.inMilliseconds/500)));
    final duration=_elapsed.inMinutes.toString().padLeft(2,'0')+':'+(_elapsed.inSeconds%60).toString().padLeft(2,'0');
    return Scaffold(
      appBar:AppBar(title:const Text('FluentX • Gemini Live')),
      body:SafeArea(child:Padding(
        padding:const EdgeInsets.all(18),
        child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[
          Text(_state,style:Theme.of(context).textTheme.headlineMedium),
          Text(duration,style:Theme.of(context).textTheme.titleLarge),
          const SizedBox(height:20),
          SizedBox(height:90,child:Row(mainAxisAlignment:MainAxisAlignment.center,children:[
            for(final b in bars)Container(
              margin:const EdgeInsets.symmetric(horizontal:2),
              height:12+65*b,width:4,
              decoration:BoxDecoration(color:Theme.of(context).colorScheme.primary,borderRadius:BorderRadius.circular(4)),
            ),
          ])),
          const SizedBox(height:12),
          const Text('You',style:TextStyle(fontWeight:FontWeight.bold)),
          Text(_learnerText.isEmpty?'Speak naturally — interrupt any time.':_learnerText,textAlign:TextAlign.center),
          const SizedBox(height:15),
          const Text('Gemini',style:TextStyle(fontWeight:FontWeight.bold)),
          Flexible(child:SingleChildScrollView(child:Text(_aiText,textAlign:TextAlign.center))),
          if(_error!=null)Text(_error!,style:const TextStyle(color:Colors.red)),
          const SizedBox(height:18),
          FilledButton.icon(
            onPressed:_running?_stop:_start,
            icon:Icon(_running?Icons.stop:Icons.mic),
            label:Text(_running?'End Live Session':'Start Live Conversation'),
          ),
          const SizedBox(height:8),
          TextButton.icon(onPressed:_running?null:_openScorecard,icon:const Icon(Icons.assessment_outlined),label:const Text('End & Scorecard')),
          const SizedBox(height:8),
          const Text('Streaming 16 kHz microphone / 24 kHz AI audio • authenticated',textAlign:TextAlign.center),
        ]),
      )),
    );
  }
}
""")
print("GEMINI_LIVE_AUDIO_CLIENT_READY", target)
