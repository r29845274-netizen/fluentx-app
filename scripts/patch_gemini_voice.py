from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "fluentx_admin_secure")
hub=root/"lib/features/ai_practice/presentation/screens/ai_practice_hub_screen.dart"
text=hub.read_text()
if "import 'gemini_voice_screen.dart';" not in text:
    text="import 'gemini_voice_screen.dart';\n"+text
if "GeminiVoiceScreen()" not in text:
    old="return Scaffold("
    if old not in text: raise SystemExit("Missing practice hub scaffold")
    pos=text.rfind(old)
    text=text[:pos]+text[pos:].replace(old,"""return Scaffold(
        floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
        floatingActionButton: FloatingActionButton.extended(
          heroTag: 'gemini-voice-entry',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute<void>(builder: (_) => const GeminiVoiceScreen()),
          ),
          icon: const Icon(Icons.mic),
          label: const Text('Talk to AI'),
        ),""",1)
hub.write_text(text)
out=hub.with_name("gemini_voice_screen.dart")
out.write_text("""import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:supabase_flutter/supabase_flutter.dart';

class GeminiVoiceScreen extends StatefulWidget {
  const GeminiVoiceScreen({super.key});
  @override
  State<GeminiVoiceScreen> createState()=>_GeminiVoiceScreenState();
}

class _GeminiVoiceScreenState extends State<GeminiVoiceScreen> {
  final _speech=stt.SpeechToText();
  final _tts=FlutterTts();
  final List<Map<String,String>> _history=[];
  String _state='Idle',_heard='',_reply='';
  String? _error;
  bool _stopped=true,_sending=false,_sent=false;
  int _round=0;

  @override
  void initState(){
    super.initState();
    _tts.setSpeechRate(0.5);
    _tts.setCompletionHandler((){
      if(mounted && !_stopped && !_sending && _state=='Speaking'){
        Future<void>.delayed(const Duration(milliseconds:300),(){
          if(mounted && !_stopped && !_sending && _state=='Speaking')_listen();
        });
      }
    });
  }

  Future<void> _listen() async{
    if(_stopped || _sending)return;
    await _tts.stop();
    _sent=false;
    try{
      final ready=await _speech.initialize(
        onStatus:(status){
          if(!mounted || _stopped || _sending || _sent)return;
          if(status=='done' || status=='notListening'){
            final words=_heard.trim();
            if(words.isNotEmpty)_send(words);
            else setState(()=>_state='Idle');
          }
        },
        onError:(e){if(mounted)setState((){_state='Idle';_error=e.errorMsg;});},
      );
      if(!ready){if(mounted)setState((){_state='Idle';_error='Speech recognition or mic permission unavailable.';});return;}
      if(_stopped || !mounted)return;
      setState((){_state='Listening';_heard='';_error=null;});
      await _speech.listen(
        onResult:(r){
          if(!mounted || _stopped || _sending)return;
          setState(()=>_heard=r.recognizedWords);
          if(r.finalResult && !_sent && _heard.trim().isNotEmpty)_send(_heard.trim());
        },
        listenFor:const Duration(seconds:45),
        pauseFor:const Duration(seconds:2),
        partialResults:true,
      );
    }catch(e){if(mounted)setState((){_state='Idle';_error='Microphone failed: $e';});}
  }

  Future<void> _send(String words) async{
    if(_sent || _stopped || _sending)return;
    _sent=true;_sending=true;
    final round=++_round;
    await _speech.stop();
    if(_stopped || !mounted){_sending=false;return;}
    setState((){_state='Thinking';_heard=words;});
    try{
      final client=Supabase.instance.client;
      if(client.auth.currentSession==null)throw StateError('Sign in to use voice AI');
      final response=await client.functions.invoke(
        'voice-assistant/api/chat',
        body:{'text':words,'history':_history},
      );
      if(!mounted || _stopped || round!=_round)return;
      final data=response.data;
      if(response.status<200 || response.status>=300 || data is! Map || data['reply'] is! String){
        throw StateError(data is Map?data['error']?.toString()??'Gemini error':'Gemini unavailable');
      }
      final reply=(data['reply'] as String).trim();
      if(reply.isEmpty)throw StateError('Empty Gemini reply');
      _history.add({'role':'user','content':words});
      _history.add({'role':'assistant','content':reply});
      if(_history.length>12)_history.removeRange(0,_history.length-12);
      setState((){_reply=reply;_state='Speaking';});
      await _tts.setLanguage(RegExp(r'[\\u0900-\\u097F]').hasMatch(reply)?'hi-IN':'en-IN');
      await _tts.speak(reply);
    }catch(e){if(mounted && round==_round)setState((){_state='Idle';_error=e.toString();});}
    finally{_sending=false;}
  }

  Future<void> _stop() async{
    _stopped=true;_round++;_sending=false;
    await _speech.stop();await _tts.stop();
    if(mounted)setState(()=>_state='Idle');
  }

  @override
  void dispose(){
    _stopped=true;_round++;_speech.stop();_tts.stop();super.dispose();
  }

  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('FluentX · Gemini Voice')),
    body:SafeArea(child:Padding(
      padding:const EdgeInsets.all(20),
      child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[
        const Icon(Icons.graphic_eq,size:56),
        const SizedBox(height:20),
        Text(_state,style:Theme.of(context).textTheme.headlineMedium),
        if(_state=='Listening')const LinearProgressIndicator(),
        const SizedBox(height:20),
        const Text('You said',style:TextStyle(fontWeight:FontWeight.bold)),
        Text(_heard.isEmpty?'Speak Hindi, English or Hinglish':_heard,textAlign:TextAlign.center),
        const SizedBox(height:25),
        const Text('AI reply',style:TextStyle(fontWeight:FontWeight.bold)),
        Flexible(child:SingleChildScrollView(child:Text(_reply,textAlign:TextAlign.center))),
        if(_error!=null)Text(_error!,style:const TextStyle(color:Colors.red)),
        const SizedBox(height:24),
        FilledButton.icon(
          onPressed:_sending?null:() async{
            if(!_stopped)await _stop();
            _stopped=false;
            await _listen();
          },
          icon:const Icon(Icons.mic),label:Text(_state=='Speaking'?'Interrupt':'Start speaking'),
        ),
        OutlinedButton.icon(onPressed:_stop,icon:const Icon(Icons.stop),label:const Text('Stop')),
        const SizedBox(height:12),
        const Text('Gemini AI replies with device speech recognition and playback',textAlign:TextAlign.center),
      ]),
    )),
  );
}
""")
print("GEMINI_VOICE_INTEGRATION_APPLIED")
