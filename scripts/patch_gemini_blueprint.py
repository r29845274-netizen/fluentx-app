from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "fluentx_admin_secure")/"lib/features/ai_practice/presentation/screens/gemini_voice_screen.dart"
s=p.read_text()
def patch(old,new):
 global s
 if old not in s:raise SystemExit("Voice code marker missing: "+old[:60])
 s=s.replace(old,new,1)
patch("  int _round=0;", """  int _round=0;
  String _track='student';
  final List<String> _turns=[];
  bool _assessing=false;
  bool _profileLoaded=false;
  bool _diagnosticMode=false;
  Timer? _diagnosticTimer;
  DateTime _startedAt=DateTime.now();

  @override
  void didChangeDependencies(){
    super.didChangeDependencies();
    if(!_profileLoaded){_profileLoaded=true;_loadProfile();}
  }

  Future<void> _loadProfile() async{
    try{
      final res=await Supabase.instance.client.functions.invoke('voice-assistant/profile',body:{});
      if(!mounted)return;
      final value=res.data is Map?(res.data as Map)['track']:null;
      if(value is String && ['student','homemaker','professional'].contains(value))setState(()=>_track=value);
    }catch(_){}
  }

  Future<void> _changeTrack(String next) async{
    setState(()=>_track=next);
    try{
      final res=await Supabase.instance.client.functions.invoke('voice-assistant/save_profile',body:{'track':next,'goal':''});
      if(res.status>=300)throw StateError('Track save failed');
    }catch(e){if(mounted)setState(()=>_error='Cannot save track. Please retry.');}
  }

  Future<void> _startDiagnostic() async{
    if(_assessing)return;
    _diagnosticTimer?.cancel();
    _turns.clear();
    _history.clear();
    _startedAt=DateTime.now();
    setState((){
      _diagnosticMode=true;
      _error=null;
      _reply='Tell me about yourself, your daily activities and when you want to speak English.';
    });
    _stopped=false;
    await _listen();
    _diagnosticTimer=Timer(const Duration(minutes:2),(){
      if(mounted && _diagnosticMode && !_assessing){
        _diagnosticMode=false;
        _evaluate(true);
      }
    });
  }

  Future<void> _evaluate(bool diagnostic) async{
    _diagnosticTimer?.cancel();
    _diagnosticMode=false;
    if(_assessing)return;
    await _stop();
    if(_turns.length<2){
      if(mounted)setState(()=>_error='Please speak at least two answers before assessment.');
      return;
    }
    setState((){_assessing=true;_state='Assessing';_error=null;});
    try{
      final result=await Supabase.instance.client.functions.invoke(
        diagnostic?'voice-assistant/diagnostic':'voice-assistant/scorecard',
        body:{'turns':_turns,'duration_seconds':DateTime.now().difference(_startedAt).inSeconds},
      );
      if(!mounted)return;
      if(result.status>=300 || result.data is! Map || (result.data as Map)['report'] is! Map){
        throw StateError(result.data is Map?(result.data as Map)['error']?.toString()??'Assessment failed':'Assessment failed');
      }
      final card=Map<String,dynamic>.from((result.data as Map)['report'] as Map);
      await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
        title:Text(diagnostic?'Diagnostic Assessment':'Session Scorecard'),
        content:SingleChildScrollView(child:Column(crossAxisAlignment:CrossAxisAlignment.start,mainAxisSize:MainAxisSize.min,children:[
          Text('Overall: '+card['overall_score'].toString()+'/100 · Level: '+card['level'].toString()),
          Text('Fluency: '+card['fluency_score'].toString()+'/100'),
          Text('Grammar: '+card['grammar_score'].toString()+'/100'),
          Text('Vocabulary: '+card['vocabulary_score'].toString()+'/100'),
          const SizedBox(height:12),
          const Text('Strengths',style:TextStyle(fontWeight:FontWeight.bold)),
          for(final item in (card['strengths'] as List? ?? []))Text('• '+item.toString()),
          const SizedBox(height:12),
          const Text('Improvements',style:TextStyle(fontWeight:FontWeight.bold)),
          for(final item in (card['improvements'] as List? ?? []))Text('• '+item.toString()),
          const SizedBox(height:10),
          Text('Next: '+card['next_practice'].toString()),
          const SizedBox(height:10),
          const Text('Estimated from transcript; not a certified proficiency test.'),
        ])),
        actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Done'))],
      ));
      _turns.clear();_startedAt=DateTime.now();
    }catch(_){if(mounted)setState(()=>_error='Unable to generate scorecard. Try again.');}
    finally{if(mounted)setState((){_assessing=false;_state='Idle';});}
  }
""")
patch("      _history.add({'role':'user','content':words});", "      _turns.add(words);\n      _history.add({'role':'user','content':words});")
patch("        const Icon(Icons.graphic_eq,size:56),", """        const Icon(Icons.graphic_eq,size:56),
        DropdownButton<String>(value:_track,items:const [
          DropdownMenuItem(value:'student',child:Text('Student · Confidence')),
          DropdownMenuItem(value:'homemaker',child:Text('Everyday English')),
          DropdownMenuItem(value:'professional',child:Text('Working Professional')),
        ],onChanged:_assessing?null:(track){if(track!=null)_changeTrack(track);}),
        const Text('Personalized English speaking coach'),
        if(_diagnosticMode)const Text('Initial assessment · 2 minutes'),
        if(_diagnosticMode)const LinearProgressIndicator(),
        if(_error!=null)TextButton.icon(
          onPressed:_assessing?null:()async{_stopped=false;await _listen();},
          icon:const Icon(Icons.refresh),
          label:const Text('Retry microphone'),
        ),
""")
patch("        OutlinedButton.icon(onPressed:_stop,icon:const Icon(Icons.stop),label:const Text('Stop')),", """        OutlinedButton.icon(onPressed:_stop,icon:const Icon(Icons.stop),label:const Text('Stop')),
        Wrap(alignment:WrapAlignment.center,spacing:8,children:[
          TextButton.icon(onPressed:_assessing?null:_startDiagnostic,icon:const Icon(Icons.school_outlined),label:const Text('2-min Assessment')),
          TextButton.icon(onPressed:_assessing?null:()=>_evaluate(false),icon:const Icon(Icons.assessment_outlined),label:const Text('End & Scorecard')),
        ]),
""")
s=s.replace('  void dispose(){\n    _stopped=true;', '  void dispose(){\n    _diagnosticTimer?.cancel();\n    _stopped=true;')
p.write_text(s)
print("PERSONALIZED_GEMINI_UI_APPLIED")
