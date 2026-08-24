import { createClient } from 'jsr:@supabase/supabase-js@2';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
const MODEL = 'gemini-3.6-flash';

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {status, headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
}
function extractText(payload:any){const parts=payload?.candidates?.[0]?.content?.parts;return Array.isArray(parts)?parts.map((p:any)=>typeof p?.text==='string'?p.text:'').join('').trim():'';}
async function gemini(system:string,user:any,schema:any){
  if(!GEMINI_API_KEY) throw new Error('AI_NOT_CONFIGURED');
  const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`,{method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':GEMINI_API_KEY},body:JSON.stringify({systemInstruction:{parts:[{text:system}]},contents:[{role:'user',parts:[{text:JSON.stringify(user)}]}],generationConfig:{temperature:.2,maxOutputTokens:2200,responseMimeType:'application/json',responseSchema:schema}})});
  if(!r.ok){console.error('weekly mastery Gemini',r.status,await r.text());throw new Error('AI_FAILED')}
  const text=extractText(await r.json());if(!text)throw new Error('AI_EMPTY');return JSON.parse(text);
}
function scoreGroup(questions:any[],answers:any[],skill:string){const rows=questions.map((q,i)=>({q,i})).filter(x=>x.q?.skill===skill);if(!rows.length)return 0;let correct=0;for(const {q,i} of rows){if(Number(answers[i])===Number(q.correct_index))correct++;}return Math.round(correct*100/rows.length);}

Deno.serve(async(req:Request)=>{try{
  if(req.method!=='POST')return json({error:'Method not allowed'},405);
  if(!SUPABASE_URL||!SUPABASE_SERVICE_ROLE_KEY)return json({error:'Server configuration error'},500);
  const auth=req.headers.get('Authorization');if(!auth?.startsWith('Bearer '))return json({error:'Unauthorized'},401);
  const admin=createClient(SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
  const {data:authData,error:authError}=await admin.auth.getUser(auth.slice(7));const user=authData.user;if(authError||!user)return json({error:'Unauthorized'},401);
  let body:any;try{body=await req.json()}catch{return json({error:'Invalid JSON'},400)}
  const action=typeof body?.action==='string'?body.action:'';

  const {data:home}=await admin.from('user_home_stats').select('audience_type,learning_goal,current_week,current_cefr_level').eq('user_id',user.id).single();
  if(!home)return json({error:'Learning profile not found'},404);
  const {data:week}=await admin.from('learning_weeks').select('id,week_number,cefr_level,title,focus,pass_score,speaking_min_score').eq('audience_type',home.audience_type).eq('goal',home.learning_goal).eq('week_number',home.current_week).eq('is_active',true).single();
  if(!week)return json({error:'Current week not found'},404);

  if(action==='start'){
    const {data:components}=await admin.from('learning_week_components').select('id,component_type,title,required_count,config,sort_order').eq('week_id',week.id).order('sort_order');
    const regular=(components??[]).filter((c:any)=>c.component_type!=='checkpoint');
    const ids=regular.map((c:any)=>c.id);
    const {data:progress}=ids.length?await admin.from('user_week_component_progress').select('component_id,status').eq('user_id',user.id).in('component_id',ids):{data:[]};
    const done=new Set((progress??[]).filter((p:any)=>p.status==='completed').map((p:any)=>p.component_id));
    if(regular.length===0||regular.some((c:any)=>!done.has(c.id)))return json({error:'Complete all current-week activities before the mastery test',code:'WEEK_ACTIVITIES_INCOMPLETE'},409);

    const schema={type:'object',properties:{questions:{type:'array',minItems:8,maxItems:8,items:{type:'object',properties:{skill:{type:'string',enum:['grammar','vocabulary','listening','practical']},prompt:{type:'string'},options:{type:'array',minItems:4,maxItems:4,items:{type:'string'}},correct_index:{type:'integer',minimum:0,maximum:3}},required:['skill','prompt','options','correct_index']}},speaking_prompt:{type:'string'}},required:['questions','speaking_prompt']};
    const generated=await gemini("Create a fair FluentX weekly mastery assessment for an English learner. Produce exactly 8 multiple-choice questions: exactly 2 grammar, 2 vocabulary, 2 listening/comprehension (the prompt may contain a short transcript), and 2 practical real-world usage questions. Four options each, one correct index. Also provide one short speaking prompt that can be answered in 3-6 sentences. Match the CEFR level and week focus. Never include the correct answer in the prompt or option wording.",{week_number:week.week_number,cefr_level:week.cefr_level,title:week.title,focus:week.focus,audience_type:home.audience_type,goal:home.learning_goal},schema);
    const questions=Array.isArray(generated?.questions)?generated.questions.slice(0,8):[];
    if(questions.length!==8)return json({error:'Could not generate mastery assessment'},502);
    const speakingPrompt=String(generated?.speaking_prompt??'').trim();if(!speakingPrompt)return json({error:'Could not generate speaking assessment'},502);
    const {data:session,error:saveError}=await admin.from('weekly_mastery_sessions').insert({user_id:user.id,week_id:week.id,questions:{questions,speaking_prompt:speakingPrompt}}).select('id').single();
    if(saveError||!session)return json({error:'Could not start mastery test'},500);
    return json({session_id:session.id,week_number:week.week_number,cefr_level:week.cefr_level,title:week.title,questions:questions.map((q:any,i:number)=>({number:i+1,skill:q.skill,prompt:q.prompt,options:q.options})),speaking_prompt:speakingPrompt});
  }

  if(action==='submit'){
    const sessionId=typeof body?.session_id==='string'?body.session_id:'';const answers=Array.isArray(body?.answers)?body.answers:[];const speakingAnswer=typeof body?.speaking_answer==='string'?body.speaking_answer.trim():'';
    if(!sessionId||answers.length!==8||speakingAnswer.length<20)return json({error:'Complete all answers and provide a meaningful speaking response'},400);
    if(speakingAnswer.length>5000)return json({error:'Speaking response is too long'},400);
    const {data:session}=await admin.from('weekly_mastery_sessions').select('id,week_id,questions,status,created_at').eq('id',sessionId).eq('user_id',user.id).single();
    if(!session||session.week_id!==week.id)return json({error:'Mastery session not found'},404);
    if(session.status!=='started')return json({error:'This mastery session has already been submitted'},409);
    if(Date.parse(session.created_at)<Date.now()-2*60*60*1000){await admin.from('weekly_mastery_sessions').update({status:'expired'}).eq('id',session.id);return json({error:'Mastery session expired. Start a new test.'},410);}
    const questions=Array.isArray(session.questions?.questions)?session.questions.questions:[];if(questions.length!==8)return json({error:'Invalid mastery session'},500);
    const grammar=scoreGroup(questions,answers,'grammar');const vocabulary=scoreGroup(questions,answers,'vocabulary');const listening=scoreGroup(questions,answers,'listening');const practical=scoreGroup(questions,answers,'practical');
    const speakingSchema={type:'object',properties:{score:{type:'integer',minimum:0,maximum:100},feedback:{type:'string'}},required:['score','feedback']};
    const speaking=await gemini("Score an English learner's response from 0-100 for CEFR-appropriate clarity, grammar, vocabulary, relevance, fluency of wording and completeness. Do not infer accent or pronunciation from text. Return concise learning feedback.",{cefr_level:week.cefr_level,prompt:session.questions?.speaking_prompt,answer:speakingAnswer},speakingSchema);
    const speakingScore=Math.max(0,Math.min(100,Math.round(Number(speaking?.score??0))));
    const overall=Math.round((grammar+vocabulary+listening+practical+speakingScore)/5);
    const passed=overall>=Number(week.pass_score)&&speakingScore>=Number(week.speaking_min_score);
    const weakAreas:any[]=[];for(const [name,value] of Object.entries({grammar,vocabulary,listening,practical,speaking:speakingScore})){if(Number(value)<70)weakAreas.push({skill:name,score:value});}
    const {error:testError}=await admin.from('weekly_test_attempts').insert({user_id:user.id,week_id:week.id,grammar_score:grammar,vocabulary_score:vocabulary,listening_score:listening,speaking_score:speakingScore,practical_score:practical,overall_score:overall,passed,weak_areas:weakAreas});
    if(testError)return json({error:'Could not save mastery result'},500);
    await admin.from('weekly_mastery_sessions').update({status:'submitted',submitted_at:new Date().toISOString()}).eq('id',session.id).eq('user_id',user.id);
    const {data:prior}=await admin.from('user_week_progress').select('attempts,best_overall_score,best_speaking_score,started_at').eq('user_id',user.id).eq('week_id',week.id).maybeSingle();
    await admin.from('user_week_progress').upsert({user_id:user.id,week_id:week.id,status:passed?'mastered':'remediation',best_overall_score:Math.max(Number(prior?.best_overall_score??0),overall),best_speaking_score:Math.max(Number(prior?.best_speaking_score??0),speakingScore),attempts:Number(prior?.attempts??0)+1,started_at:prior?.started_at??new Date().toISOString(),completed_at:passed?new Date().toISOString():null,updated_at:new Date().toISOString()},{onConflict:'user_id,week_id'});
    if(passed){
      const {data:checkpoint}=await admin.from('learning_week_components').select('id,required_count').eq('week_id',week.id).eq('component_type','checkpoint').maybeSingle();
      if(checkpoint)await admin.from('user_week_component_progress').upsert({user_id:user.id,week_id:week.id,component_id:checkpoint.id,completed_count:checkpoint.required_count,status:'completed',first_started_at:new Date().toISOString(),last_completed_at:new Date().toISOString(),updated_at:new Date().toISOString()},{onConflict:'user_id,component_id'});
      if(Number(week.week_number)<60){
        const nextWeek=Number(week.week_number)+1;const {data:next}=await admin.from('learning_weeks').select('cefr_level').eq('audience_type',home.audience_type).eq('goal',home.learning_goal).eq('week_number',nextWeek).eq('is_active',true).single();
        await admin.from('user_home_stats').update({current_week:nextWeek,current_cefr_level:next?.cefr_level??week.cefr_level,updated_at:new Date().toISOString()}).eq('user_id',user.id).eq('current_week',week.week_number);
      }
    }
    return json({passed,week_number:week.week_number,overall_score:overall,speaking_score:speakingScore,grammar_score:grammar,vocabulary_score:vocabulary,listening_score:listening,practical_score:practical,pass_score:week.pass_score,speaking_min_score:week.speaking_min_score,weak_areas:weakAreas,speaking_feedback:String(speaking?.feedback??'').trim(),next_week:passed&&Number(week.week_number)<60?Number(week.week_number)+1:Number(week.week_number)});
  }
  return json({error:'Unknown action'},400);
}catch(error){console.error('weekly-mastery-test',error instanceof Error?error.message:String(error));return json({error:'Weekly mastery test failed. Please try again.'},502)}});