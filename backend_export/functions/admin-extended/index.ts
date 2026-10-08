import { createClient } from 'jsr:@supabase/supabase-js@2';

const URL=Deno.env.get('SUPABASE_URL');
const SERVICE=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
const jwt=(token:string)=>{try{const p=token.split('.')[1];if(!p)return null;const n=p.replace(/-/g,'+').replace(/_/g,'/');return JSON.parse(atob(n.padEnd(Math.ceil(n.length/4)*4,'=')));}catch{return null;}};
const txt=(v:unknown,max=1000)=>typeof v==='string'?v.trim().slice(0,max):'';

Deno.serve(async(req:Request)=>{
  if(req.method!=='POST')return json({error:'Method not allowed'},405);
  if(!URL||!SERVICE)return json({error:'Server configuration error'},500);
  const h=req.headers.get('Authorization');
  if(!h?.startsWith('Bearer '))return json({error:'Unauthorized'},401);
  const token=h.slice(7);
  const db=createClient(URL,SERVICE,{auth:{persistSession:false,autoRefreshToken:false}});
  const {data:u,error:ue}=await db.auth.getUser(token);
  if(ue||!u.user)return json({error:'Unauthorized'},401);
  const user=u.user;
  const {data:a,error:ae}=await db.from('admin_users').select('role,is_active').eq('user_id',user.id).eq('is_active',true).maybeSingle();
  if(ae||!a)return json({error:'Admin access denied'},403);
  if(jwt(token)?.aal!=='aal2')return json({error:'Admin MFA verification required'},403);
  const role=a.role as string;
  const elevated=role==='owner'||role==='admin';
  const owner=role==='owner';

  let b:Record<string,unknown>={};
  try{b=await req.json()}catch{return json({error:'Invalid JSON'},400)}
  const action=txt(b.action,80);

  const audit=async(name:string,target:string|null=null,reason:string|null=null,metadata:Record<string,unknown>={})=>{
    await db.from('admin_audit_log').insert({admin_user_id:user.id,action:name,target_user_id:target,reason,metadata});
  };

  if(action==='list_partners'){
    const {data,error}=await db.from('partners').select('*').order('created_at',{ascending:false}).limit(300);
    if(error)return json({error:'Could not load partners'},500);
    return json({partners:data??[]});
  }
  if(action==='save_partner'){
    if(!elevated)return json({error:'Insufficient admin role'},403);
    const name=txt(b.name,160), type=txt(b.partner_type,60)||'other', email=txt(b.contact_email,200), status=txt(b.status,40)||'active', notes=txt(b.notes,2000);
    if(name.length<2)return json({error:'Partner name is required'},400);
    const row:any={name,partner_type:type,contact_email:email||null,status,notes:notes||null,updated_at:new Date().toISOString()};
    if(typeof b.id==='string'&&b.id)row.id=b.id;
    const {data,error}=await db.from('partners').upsert(row).select().single();
    if(error)return json({error:'Could not save partner'},500);
    await audit('save_partner',null,null,{partner_id:data.id,status:data.status});
    return json({partner:data});
  }

  if(action==='list_moderation'){
    const status=txt(b.status,40);
    let q=db.from('content_moderation_reports').select('*').order('created_at',{ascending:false}).limit(300);
    if(status)q=q.eq('status',status);
    const {data,error}=await q;
    if(error)return json({error:'Could not load moderation reports'},500);
    return json({reports:data??[]});
  }
  if(action==='resolve_moderation'){
    if(!elevated)return json({error:'Insufficient admin role'},403);
    const id=txt(b.id,80), status=txt(b.status,40), resolution=txt(b.resolution,2000);
    if(!id||!['open','reviewing','resolved','dismissed'].includes(status))return json({error:'Invalid moderation update'},400);
    const {error}=await db.from('content_moderation_reports').update({status,resolution:resolution||null,reviewed_by:user.id,reviewed_at:new Date().toISOString()}).eq('id',id);
    if(error)return json({error:'Could not update moderation report'},500);
    await audit('resolve_moderation',null,resolution||null,{report_id:id,status});
    return json({ok:true});
  }

  if(action==='list_subscription_events'){
    const {data,error}=await db.from('subscription_events').select('id,event_id,app_user_id,user_id,event_type,product_id,entitlement_id,store,price,currency,purchased_at,expires_at,created_at').order('created_at',{ascending:false}).limit(500);
    if(error)return json({error:'Could not load subscription events'},500);
    const rows=data??[];
    const revenue=rows.reduce((sum:any,r:any)=>sum+(Number(r.price)||0),0);
    return json({events:rows,event_count:rows.length,revenue_total:revenue,provider:'RevenueCat',webhook_tracking:true});
  }

  if(action==='list_premium_overrides'){
    const {data,error}=await db.from('premium_overrides').select('*').order('updated_at',{ascending:false}).limit(300);
    if(error)return json({error:'Could not load premium overrides'},500);
    return json({overrides:data??[]});
  }
  if(action==='grant_premium_override'){
    if(!elevated)return json({error:'Insufficient admin role'},403);
    const userId=txt(b.user_id,80);
    const days=Math.max(1,Math.min(3650,Number(b.days)||30));
    if(!userId)return json({error:'user_id is required'},400);
    const until=new Date(Date.now()+days*86400000).toISOString();
    const {data,error}=await db.from('premium_overrides').upsert({user_id:userId,active_until:until,source:'admin',granted_by:user.id,updated_at:new Date().toISOString()},{onConflict:'user_id'}).select().single();
    if(error)return json({error:'Could not grant premium override'},500);
    await audit('grant_premium_override',userId,null,{days,active_until:until});
    return json({override:data});
  }
  if(action==='revoke_premium_override'){
    if(!elevated)return json({error:'Insufficient admin role'},403);
    const userId=txt(b.user_id,80);
    const {error}=await db.from('premium_overrides').delete().eq('user_id',userId);
    if(error)return json({error:'Could not revoke premium override'},500);
    await audit('revoke_premium_override',userId);
    return json({ok:true});
  }

  // Retired invitation-based privileged access. Use the owner-only role-admin function.
  if(['list_admin_invites','save_admin_invite','revoke_admin_invite'].includes(action)) return json({error:'Not found'},404);

  if(action==='send_in_app_notification'){
    if(!elevated)return json({error:'Insufficient admin role'},403);
    const id=txt(b.id,80);
    if(!id)return json({error:'Notification id is required'},400);
    const {data,error}=await db.from('admin_notifications').update({status:'sent',sent_at:new Date().toISOString(),updated_at:new Date().toISOString()}).eq('id',id).select().single();
    if(error)return json({error:'Could not send notification'},500);
    await audit('send_in_app_notification',null,null,{notification_id:id,target:data.target_segment});
    return json({notification:data});
  }

  return json({error:'Unknown action'},400);
});