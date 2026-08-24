import { createClient } from 'jsr:@supabase/supabase-js@2';

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const REVENUECAT_SECRET_API_KEY = Deno.env.get('REVENUECAT_SECRET_API_KEY');
const MODEL = 'gemini-3.6-flash';

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'},
  });
}
function extractText(payload: any): string {const parts=payload?.candidates?.[0]?.content?.parts;return Array.isArray(parts)?parts.map((p:any)=>typeof p?.text==='string'?p.text:'').join('').trim():'';}
function tierFromProduct(product:string|null):'free'|'monthly'|'annual'{const p=(product??'').toLowerCase();if(p.includes('annual')||p.includes('yearly'))return'annual';if(p.includes('month'))return'monthly';return p?'monthly':'free'}
async function ensureAnnual(admin:any,userId:string){
  const {data:cached}=await admin.from('user_subscription_access').select('tier,entitlement_active,expires_at,verified_at').eq('user_id',userId).maybeSingle();
  const verifiedMs=cached?.verified_at?Date.parse(cached.verified_at):0;const expiresMs=cached?.expires_at?Date.parse(cached.expires_at):Number.POSITIVE_INFINITY;
  if(cached?.entitlement_active&&cached?.tier==='annual'&&verifiedMs>Date.now()-24*60*60*1000&&expiresMs>Date.now()) return;
  if(!REVENUECAT_SECRET_API_KEY) throw new Error('SUBSCRIPTION_VERIFIER_NOT_CONFIGURED');
  const r=await fetch(`https://api.revenuecat.com/v1/subscribers/${encodeURIComponent(userId)}`,{headers:{Authorization:`Bearer ${REVENUECAT_SECRET_API_KEY}`,Accept:'application/json'}});
  if(!r.ok) throw new Error('SUBSCRIPTION_VERIFY_FAILED');
  const p=await r.json();const e=p?.subscriber?.entitlements?.premium??null;const product=typeof e?.product_identifier==='string'?e.product_identifier:null;const exp=typeof e?.expires_date==='string'?new Date(e.expires_date):null;const active=Boolean(e)&&(!exp||exp.getTime()>Date.now());const tier=active?tierFromProduct(product):'free';
  await admin.from('user_subscription_access').upsert({user_id:userId,tier,entitlement_active:active,product_identifier:product,expires_at:exp?.toISOString()??null,verified_at:new Date().toISOString(),source:'revenuecat_v1',updated_at:new Date().toISOString()},{onConflict:'user_id'});
  if(!active||tier!=='annual') throw new Error('ANNUAL_REQUIRED');
}

Deno.serve(async (req: Request) => {
  try {
    if (req.method !== 'POST') return json({error:'Method not allowed'},405);
    if (!GEMINI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) return json({error:'Server misconfigured'},500);
    const authHeader = req.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) return json({error:'Unauthorized'},401);

    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {auth:{persistSession:false,autoRefreshToken:false}});
    const {data:authData,error:authError} = await admin.auth.getUser(authHeader.slice(7));
    const user = authData.user;
    if (authError || !user) return json({error:'Unauthorized'},401);
    try{await ensureAnnual(admin,user.id)}catch(e){const c=e instanceof Error?e.message:'';if(c==='ANNUAL_REQUIRED')return json({error:'FluentX Annual Elite subscription required',code:'ANNUAL_REQUIRED'},403);if(c==='SUBSCRIPTION_VERIFIER_NOT_CONFIGURED')return json({error:'Subscription verification is not configured',code:'BILLING_CONFIG_REQUIRED'},503);return json({error:'Could not verify subscription'},502)}

    let body:any; try{body=await req.json()}catch{return json({error:'Invalid JSON'},400)}
    const attemptId = typeof body?.attempt_id === 'string' ? body.attempt_id : '';
    const questionId = typeof body?.question_id === 'string' ? body.question_id : '';
    const answerText = typeof body?.answer_text === 'string' ? body.answer_text.trim() : '';
    if (!attemptId || !questionId || !answerText) return json({error:'attempt_id, question_id and answer_text are required'},400);
    if (answerText.length > 8000) return json({error:'answer_text is too long'},400);

    const {data:attempt} = await admin.from('interview_attempts').select('id,user_id,category').eq('id',attemptId).eq('user_id',user.id).single();
    if (!attempt) return json({error:'Attempt not found'},404);
    const {data:question} = await admin.from('interview_questions').select('id,category,question,coaching_tip').eq('id',questionId).eq('is_active',true).single();
    if (!question) return json({error:'Question not found'},404);

    const systemInstruction = `You are FluentX's professional English interview coach for Indian students and working professionals. Evaluate the learner's answer to the interview question. Score 0-100 based on clarity, relevance, structure, confidence of wording, grammar, and evidence/examples. Be practical and encouraging. Do not reward verbosity. Return JSON only with score (integer 0-100), feedback (2-4 concise sentences), strengths (array up to 3), improvements (array up to 3).`;
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':GEMINI_API_KEY},body:JSON.stringify({systemInstruction:{parts:[{text:systemInstruction}]},contents:[{role:'user',parts:[{text:JSON.stringify({category:question.category,question:question.question,coaching_tip:question.coaching_tip,answer:answerText})}]}],generationConfig:{maxOutputTokens:700,responseMimeType:'application/json',responseSchema:{type:'object',properties:{score:{type:'integer',minimum:0,maximum:100},feedback:{type:'string'},strengths:{type:'array',maxItems:3,items:{type:'string'}},improvements:{type:'array',maxItems:3,items:{type:'string'}}},required:['score','feedback','strengths','improvements']}}})});
    if (!response.ok) {console.error('Gemini interview error',response.status,await response.text());return json({error:'AI interview scoring failed'},502);}
    const payload = await response.json();
    let parsed:any; try { parsed = JSON.parse(extractText(payload)); } catch { return json({error:'AI returned invalid scoring data'},502); }
    const score = Math.max(0,Math.min(100,Math.round(Number(parsed?.score ?? 0))));
    const feedback = typeof parsed?.feedback === 'string' ? parsed.feedback.trim() : '';
    const strengths = Array.isArray(parsed?.strengths) ? parsed.strengths.slice(0,3).map(String) : [];
    const improvements = Array.isArray(parsed?.improvements) ? parsed.improvements.slice(0,3).map(String) : [];
    const {error:saveError} = await admin.from('interview_answers').upsert({attempt_id:attemptId,user_id:user.id,question_id:questionId,answer_text:answerText,score,feedback,strengths,improvements},{onConflict:'attempt_id,question_id'});
    if (saveError) return json({error:'Failed to save interview score'},500);
    const {data:rows} = await admin.from('interview_answers').select('score').eq('attempt_id',attemptId).eq('user_id',user.id).not('score','is',null);
    const scores = (rows ?? []).map((r:any)=>Number(r.score)).filter(Number.isFinite);
    const overall = scores.length ? Math.round(scores.reduce((a:number,b:number)=>a+b,0)/scores.length) : score;
    await admin.from('interview_attempts').update({overall_score:overall}).eq('id',attemptId).eq('user_id',user.id);
    return json({score,feedback,strengths,improvements,overall_score:overall});
  } catch (error) {
    console.error('score-interview-answer error',error instanceof Error ? error.message : String(error));
    return json({error:'Interview scoring failed'},502);
  }
});