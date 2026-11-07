const $=id=>document.getElementById(id);let state={providers:[],agents:[],chats:[]},current=null,page='chat',busy=false,editing=null;
const uid=()=>crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random();
async function api(path,body){const r=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});let j=await r.json();if(!r.ok)throw Error(j.error||'Falha na requisição');return j}
function toast(t){let d=document.createElement('div');d.textContent=t;$('toast').append(d);setTimeout(()=>d.remove(),4500)}
function opt(sel,items,value){sel.replaceChildren();for(let item of items){let o=document.createElement('option');o.value=item.id;o.textContent=item.name;sel.append(o)}if(value&&items.some(x=>x.id===value))sel.value=value}
function activeChat(){return state.chats.find(x=>x.id===current)}
async function reload(){state=await api('state');if(!current||!activeChat())current=state.chats[0]?.id||null;render()}
function render(){renderSidebar();renderChat();renderCards();$('agentCount').textContent=state.agents.length;$('chatCount').textContent=state.chats.length}
function renderSidebar(){let list=$('chatList');list.replaceChildren();for(let c of [...state.chats].reverse()){let b=document.createElement('button');b.className='chat-item'+(c.id===current?' active':'');let s=document.createElement('span');s.textContent='▤  '+c.title;b.append(s);b.onclick=()=>{current=c.id;show('chat')};list.append(b)}}
function renderChat(){let c=activeChat();$('chatTitle').textContent=c?.title||'Central de inteligência';opt($('chatProvider'),state.providers.map(x=>({id:x.id,name:x.name})),c?.provider_id);opt($('chatAgent'),state.agents.map(x=>({id:x.id,name:x.name})),c?.agent_id);$('temperature').value=c?.temperature??.7;$('tempValue').textContent=Number($('temperature').value).toFixed(1);let p=state.providers.find(x=>x.id===(c?.provider_id||$('chatProvider').value));let models=[{id:c?.model||p?.model||'',name:c?.model||p?.model||'Selecione um modelo'}];opt($('chatModel'),models,c?.model);let area=$('messages');area.replaceChildren();if(!c?.messages?.length){let w=document.createElement('div');w.className='welcome';w.innerHTML='<div class="orbit">⌘</div><div class="eyebrow">// SYSTEM READY</div><h2>O que vamos construir hoje?</h2><p>Selecione seu agente, escolha o provedor e comece a conversa.</p><div class="suggestions"><button data-prompt="Explique como criar uma aplicação web modular e segura.">⌘ Arquitetura de software</button><button data-prompt="Crie ideias originais para um jogo 2D de estratégia.">✦ Ideias para jogos</button><button data-prompt="Como posso integrar Ollama, MCP e ComfyUI?">◈ Integração de IA</button></div>';area.append(w);w.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>{$('prompt').value=b.dataset.prompt;$('prompt').focus()})}else for(let m of c.messages)addMessage(m.role,m.content,m.image_job);area.scrollTop=area.scrollHeight;renderToolRequests(c)}
function addMessage(role,content,imageJob){let m=document.createElement('div');m.className='message '+role;let a=document.createElement('div');a.className='msg-avatar';a.textContent=role==='user'?'EU':'⌘';let b=document.createElement('div');b.className='msg-body';let meta=document.createElement('div');meta.className='msg-meta';meta.textContent=role==='user'?'VOCÊ':'AGENTE IA';let bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=content;b.append(meta,bubble);if(role==='assistant'&&window._wmkPendingRequests){const req=window._wmkPendingRequests.find(x=>x.message===content);if(req)attachTool(b,req.chatId,req.tool)}
 if(imageJob){let status=document.createElement('div');status.className='image-status';status.textContent='Consultando geração...';b.append(status);watchImage(imageJob,status)}m.append(a,b);$('messages').append(m);$('messages').scrollTop=$('messages').scrollHeight;return m}
async function newChat(){let c={id:uid(),title:'Nova conversa',provider_id:state.providers[0]?.id||'',agent_id:state.agents[0]?.id||'',model:state.providers[0]?.model||'',temperature:.7,messages:[],updated:new Date().toISOString()};await api('save',{section:'chats',item:c});state.chats.push(c);current=c.id;show('chat')}
async function updateChat(prop,value){let c=activeChat();if(!c)return;c[prop]=value;try{await api('save',{section:'chats',item:c});renderSidebar()}catch(e){toast(e.message)}}
async function models(){let id=$('chatProvider').value;if(!id)return;let p=state.providers.find(x=>x.id===id);$('refreshModels').disabled=true;try{let data=await api('models/'+encodeURIComponent(id));let values=data.models.map(x=>({id:x,name:x}));if(!values.length)throw Error('Nenhum modelo disponível');opt($('chatModel'),values,activeChat()?.model||p?.model);if(!values.some(x=>x.id===activeChat()?.model))await updateChat('model',$('chatModel').value);toast(values.length+' modelo(s) carregado(s)')}catch(e){toast('Modelos: '+e.message);opt($('chatModel'),[{id:p?.model||'',name:p?.model||'Sem modelo'}],p?.model)}finally{$('refreshModels').disabled=false}}
async function send(){if(busy)return;let txt=$('prompt').value.trim();if(!txt)return;if(!activeChat())await newChat();let c=activeChat();busy=true;$('send').disabled=true;$('prompt').value='';if($('messages').querySelector('.welcome'))$('messages').replaceChildren();addMessage('user',txt);let loading=addMessage('assistant','Processando resposta...');try{let res=await api('agent-chat',{chat_id:c.id,text:txt});let i=state.chats.findIndex(x=>x.id===c.id);if(i>=0)state.chats[i]=res.chat;render()}catch(e){loading.querySelector('.bubble').textContent='ERRO: '+e.message;toast('Falha no provedor: '+e.message)}finally{busy=false;$('send').disabled=false;$('prompt').focus()}}
function show(which){page=which;for(let x of ['Chat','Agents','Providers','About'])$('view'+x).classList.toggle('hidden',x.toLowerCase()!==which.toLowerCase());$('pageName').textContent={chat:'CONSOLE',agents:'AGENTES',providers:'PROVEDORES',about:'DOCUMENTAÇÃO'}[which];render()}
function renderCards(){let a=$('agentCards');a.replaceChildren();for(let x of state.agents){let d=document.createElement('div');d.className='tile';d.innerHTML='<div class="tile-icon">◈</div>';let h=document.createElement('h3');h.textContent=x.name;let p=document.createElement('p');p.textContent=x.role||x.prompt;let foot=document.createElement('div');foot.className='tile-bottom';let status=document.createElement('span');status.textContent='● CONFIGURADO';let btn=document.createElement('button');btn.className='outline';btn.textContent='Editar ↗';btn.onclick=()=>openEditor('agents',x);foot.append(status,btn);d.append(h,p,foot);a.append(d)}let b=$('providerCards');b.replaceChildren();for(let x of state.providers){let d=document.createElement('div');d.className='tile';d.innerHTML='<div class="tile-icon">◉</div>';let h=document.createElement('h3');h.textContent=x.name;let p=document.createElement('p');p.textContent=x.url+'\nModelo padrão: '+(x.model||'Não definido');p.style.whiteSpace='pre-wrap';p.style.overflowWrap='anywhere';let foot=document.createElement('div');foot.className='tile-bottom';let status=document.createElement('span');status.textContent=x.kind==='ollama'?'● LOCAL':x.has_key?'● CHAVE CONFIGURADA':'○ SEM CHAVE';let btn=document.createElement('button');btn.className='outline';btn.textContent='Configurar ↗';btn.onclick=()=>openEditor('providers',x);foot.append(status,btn);d.append(h,p,foot);b.append(d)}}
function field(label,name,value,type='text',options){let l=document.createElement('label');l.textContent=label;let el;if(type==='textarea'){el=document.createElement('textarea');el.value=value||''}else if(type==='select'){el=document.createElement('select');for(let o of options){let opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.append(opt)}el.value=value||options[0][0]}else{el=document.createElement('input');el.type=type;el.value=value||''}el.name=name;l.append(el);$('fields').append(l)}
function openEditor(section,item={}){editing={section,id:item.id};$('fields').replaceChildren();$('modalType').textContent=section==='agents'?'// AGENT CONFIG':'// PROVIDER CONFIG';$('modalTitle').textContent=item.id?'Editar '+(section==='agents'?'agente':'provedor'):'Novo '+(section==='agents'?'agente':'provedor');field('NOME','name',item.name);if(section==='agents'){field('ESPECIALIDADE','role',item.role);field('ÍCONE','icon',item.icon||'◈');field('PROMPT DE SISTEMA','prompt',item.prompt,'textarea')}else{field('TIPO DE API','kind',item.kind||'openai','select',[['ollama','Ollama'],['openai','OpenAI compatível (Groq / OpenAI / outros)']]);field('URL BASE','url',item.url||'https://');field('MODELO PADRÃO','model',item.model);field(item.has_key?'CHAVE API (deixe vazio para manter)':'CHAVE API (opcional no Ollama)','api_key','','password')}$('modal').showModal()}
async function submitEditor(e){e.preventDefault();let data=Object.fromEntries(new FormData($('editForm')));if(editing.id)data.id=editing.id;try{await api('save',{section:editing.section,item:data});$('modal').close();await reload();toast('Configuração salva com sucesso')}catch(e){toast(e.message)}}
function exportChat(){let c=activeChat();if(!c)return;let blob=new Blob([JSON.stringify(c,null,2)],{type:'application/json'});let url=URL.createObjectURL(blob);let a=document.createElement('a');a.href=url;a.download='wmk-chat-'+c.id.slice(0,8)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}
async function deleteChat(){let c=activeChat();if(!c||!confirm('Excluir esta conversa permanentemente?'))return;try{await api('delete',{section:'chats',id:c.id});await reload();toast('Conversa excluída')}catch(e){toast(e.message)}}
$('newChat').onclick=()=>newChat().catch(e=>toast(e.message));$('send').onclick=send;$('prompt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}};document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key.toLowerCase()==='n'){e.preventDefault();newChat().catch(x=>toast(x.message))}});$('chatProvider').onchange=async e=>{await updateChat('provider_id',e.target.value);await updateChat('model',state.providers.find(x=>x.id===e.target.value)?.model||'');await models()};$('chatAgent').onchange=e=>updateChat('agent_id',e.target.value);$('chatModel').onchange=e=>updateChat('model',e.target.value);$('temperature').oninput=e=>$('tempValue').textContent=Number(e.target.value).toFixed(1);$('temperature').onchange=e=>updateChat('temperature',Number(e.target.value));$('refreshModels').onclick=models;$('exportChat').onclick=exportChat;$('deleteChat').onclick=deleteChat;$('addAgent').onclick=()=>openEditor('agents');$('addProvider').onclick=()=>openEditor('providers');document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>show(b.dataset.page));$('closeModal').onclick=$('cancelModal').onclick=()=>$('modal').close();$('editForm').onsubmit=submitEditor;setInterval(()=>$('clock').textContent=new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}),1000);reload().then(()=>{if(!current)newChat();else models()}).catch(e=>toast(e.message));
const watched=new Map();
async function watchImage(id,el){
 if(watched.has(id)){watched.get(id).add(el);return}
 const elements=new Set([el]);watched.set(id,elements);
 for(let i=0;i<360;i++){
  try{
   const r=await api('image-status/'+id);
   if(r.status==='done'){for(const node of elements){node.textContent='Imagem gerada pelo ComfyUI:';let img=document.createElement('img');img.src=r.url;img.alt='Imagem gerada pelo ComfyUI';img.style.cssText='display:block;max-width:100%;width:320px;margin-top:12px;border:1px solid #3d6b4d;border-radius:4px';node.append(img);const a=document.createElement('a');a.href=r.url;a.download='WMK_Agent_Studio_'+id.slice(0,8)+'.png';a.textContent='Baixar imagem PNG';a.style.cssText='display:inline-block;margin-top:10px;color:#8ff2af;text-decoration:underline;font-weight:bold';node.append(a)}watched.delete(id);return}
   if(r.status==='error'){for(const node of elements)node.textContent='Falha no workflow: '+(r.error||'Erro desconhecido');watched.delete(id);return}
   for(const node of elements)node.textContent='ComfyUI gerando imagem na CPU... ('+(i*5)+' s)';
  }catch(e){for(const node of elements)node.textContent='Aguardando ComfyUI: '+e.message}
  await new Promise(resolve=>setTimeout(resolve,5000))
 }
 for(const node of elements)node.textContent='Tempo de espera excedido. Verifique o ComfyUI.';watched.delete(id)
}
$('imageAction').onclick=async()=>{if(!activeChat())await newChat();$('imagePrompt').value=$('prompt').value.trim();$('imageDialog').showModal()};
$('imageClose').onclick=$('imageCancel').onclick=()=>$('imageDialog').close();
const manualFields={};for(const [key,label,val,type,options] of [['negative','PROMPT NEGATIVO','blurry, low quality, watermark, text','textarea'],['cfg','CFG',7,'number'],['sampler','SAMPLER','euler','select',[['euler','Euler'],['dpmpp_2m','DPM++ 2M'],['euler_ancestral','Euler ancestral'],['uni_pc','UniPC']]],['scheduler','SCHEDULER','normal','select',[['normal','Normal'],['karras','Karras'],['simple','Simple']]],['seed','SEED (-1 = aleatoria)',-1,'number'],['lora','LORA PIXEL ART','pytorch_lora_weights.safetensors','select',[['pytorch_lora_weights.safetensors','Pixel Art (instalado)'],['','Desativado']]],['lora_strength','FORCA DO LORA (0-1.5)',0.7,'number']]){const f=imageControl(label,val,type,options||[]);$('imageSteps').parentElement.after(f.wrap);manualFields[key]=f.input;}
const getManualSettings=()=>({prompt:$('imagePrompt').value,negative:manualFields.negative.value,size:Number($('imageSize').value),steps:Number($('imageSteps').value),cfg:Number(manualFields.cfg.value),sampler:manualFields.sampler.value,scheduler:manualFields.scheduler.value,seed:Number(manualFields.seed.value),lora:manualFields.lora.value,lora_strength:Number(manualFields.lora_strength.value)});
const previewBtn=document.createElement('button');previewBtn.type='button';previewBtn.className='outline';previewBtn.textContent='Ver grafo antes de gerar';previewBtn.onclick=()=>showWorkflowGraph(getManualSettings());$('imageConfirm').parentElement.prepend(previewBtn);
$('imageConfirm').onclick=async()=>{
 const prompt=$('imagePrompt').value.trim();if(!prompt){toast('Descreva a imagem');return}
 if(!confirm('Enviar a geração ao ComfyUI em CPU? Pode demorar vários minutos.'))return;
 $('imageConfirm').disabled=true;
 try{
  const r=await api('generate-image',{chat_id:current,...getManualSettings()});
  $('imageDialog').close();$('prompt').value='';await reload();toast('Workflow enviado ao ComfyUI: '+r.prompt_id.slice(0,8))
 }catch(e){toast('Geração: '+e.message)}
 finally{$('imageConfirm').disabled=false}
};

function renderToolRequests(c){
 if(!c)return;
 for(const m of c.messages||[]){
  if(!m.tool_request_id)continue;
  const tool=(c.tool_requests||[]).find(t=>t.id===m.tool_request_id);
  if(!tool)continue;
  const nodes=[...$('messages').querySelectorAll('.message.assistant')];
  const target=nodes.find(n=>n.querySelector('.bubble')?.textContent===m.content);
  if(target)attachTool(target.querySelector('.msg-body'),c.id,tool)
 }
}
function attachTool(target,cid,tool){
 if(target.querySelector('[data-tool-id="'+tool.id+'"]'))return;
 const box=document.createElement('div');box.dataset.toolId=tool.id;box.style.cssText='margin-top:12px;border:1px solid #3f8659;background:#10291b;padding:14px;border-radius:5px;white-space:normal';
 const title=document.createElement('strong');title.textContent='◈ FERRAMENTA: GERAR IMAGEM';title.style.color='#80ffae';box.append(title);
 const desc=document.createElement('p');desc.textContent=tool.prompt;desc.style.cssText='margin:10px 0;color:#d8eadf;white-space:pre-wrap;overflow-wrap:anywhere';box.append(desc);
 const info=document.createElement('div');info.textContent=tool.size+' × '+tool.size+' px  ·  '+tool.steps+' steps  ·  CPU';info.style.cssText='font:11px Consolas;color:#8fba9d;margin-bottom:12px';box.append(info);
 const state=document.createElement('div');state.textContent='Status: '+tool.state;state.style.cssText='font:11px Consolas;color:#b7d7bf';box.append(state);
 const readToolSettings=imageSettingsEditor(box,tool);
 const graphBtn=document.createElement('button');graphBtn.type='button';graphBtn.className='outline';graphBtn.textContent='Ver grafo / plano';graphBtn.style.cssText='margin:10px 8px 8px 0';graphBtn.onclick=()=>showWorkflowGraph(readToolSettings());box.append(graphBtn);
 if(tool.state==='pending'){
  const yes=document.createElement('button');yes.textContent='✓ Autorizar geração';yes.className='primary';yes.style.margin='12px 8px 0 0';
  const no=document.createElement('button');no.textContent='✕ Rejeitar';no.className='outline';
  const decide=async(action)=>{yes.disabled=true;no.disabled=true;try{const res=await api('approve-tool',{chat_id:cid,request_id:tool.id,action,settings:readToolSettings()});toast(action==='approve'?'Imagem enviada ao ComfyUI':'Geração recusada');await reload()}catch(e){toast(e.message);yes.disabled=false;no.disabled=false}};
  yes.onclick=()=>decide('approve');no.onclick=()=>decide('reject');box.append(yes,no)
 }
 target.append(box)
}

const GRAPH_TYPES=['CheckpointLoaderSimple','CLIPTextEncode','CLIPTextEncode','EmptyLatentImage','KSampler','VAEDecode','SaveImage'];
function buildWorkflow(tool){
 const size=[256,320,384,512].includes(Number(tool.size))?Number(tool.size):384;
 const steps=Math.max(5,Math.min(30,Number(tool.steps)||20));
 const prompt=String(tool.prompt||'').slice(0,1200);
 const nodes={
  '1':{class_type:'CheckpointLoaderSimple',inputs:{ckpt_name:'v1-5-pruned-emaonly.safetensors'}},
  '2':{class_type:'CLIPTextEncode',inputs:{text:prompt,clip:['1',1]}},
  '3':{class_type:'CLIPTextEncode',inputs:{text:String(tool.negative||'blurry, low quality, watermark, text'),clip:['1',1]}},
  '4':{class_type:'EmptyLatentImage',inputs:{width:size,height:size,batch_size:1}},
  '5':{class_type:'KSampler',inputs:{seed:Number(tool.seed)>=0?Number(tool.seed):42,steps:steps,cfg:Number(tool.cfg)||7,sampler_name:tool.sampler||'euler',scheduler:tool.scheduler||'normal',denoise:1,model:['1',0],positive:['2',0],negative:['3',0],latent_image:['4',0]}},
  '6':{class_type:'VAEDecode',inputs:{samples:['5',0],vae:['1',2]}},
  '7':{class_type:'SaveImage',inputs:{filename_prefix:'WMK_Agent_Studio',images:['6',0]}}
 };
  if(tool.lora!==''){nodes['8']={class_type:'LoraLoader',inputs:{lora_name:tool.lora||'pytorch_lora_weights.safetensors',strength_model:Number(tool.lora_strength??0.7),strength_clip:Number(tool.lora_strength??0.7),model:['1',0],clip:['1',1]}};nodes['2'].inputs.clip=['8',1];nodes['3'].inputs.clip=['8',1];nodes['5'].inputs.model=['8',0];}
  return nodes;
}
function showWorkflowGraph(tool){
 const workflow=buildWorkflow(tool);const svgNS='http://www.w3.org/2000/svg';
 const positions={'1':[25,15],'2':[280,15],'3':[280,175],'4':[25,345],'5':[535,165],'6':[790,165],'7':[790,345],'8':[280,345]};
 const titles={'1':'Checkpoint','2':'Prompt positivo','3':'Prompt negativo','4':'Latente vazio','5':'KSampler','6':'VAE Decode','7':'Save Image','8':'LoRA Pixel Art'};
 const colors={'1':'#4d8bc2','2':'#42a979','3':'#b16a78','4':'#826bb8','5':'#d49c52','6':'#4d8bc2','7':'#42a979','8':'#a47ad6'};
 const width=220,height=115;const svg=document.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','0 0 1040 500');svg.style.cssText='width:100%;min-width:760px;height:auto;font-family:Consolas,monospace';
 const nodeEl=(tag,attrs,parent=svg)=>{const el=document.createElementNS(svgNS,tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);parent.append(el);return el};
 const edges=workflow['8']?[['1','8'],['8','2'],['8','3'],['8','5'],['1','6'],['2','5'],['3','5'],['4','5'],['5','6'],['6','7']]:[['1','2'],['1','3'],['1','5'],['1','6'],['2','5'],['3','5'],['4','5'],['5','6'],['6','7']];
 for(const [from,to] of edges){const [x1,y1]=positions[from],[x2,y2]=positions[to];const sx=x1+width,sy=y1+height/2,ex=x2,ey=y2+height/2;nodeEl('path',{d:'M'+sx+' '+sy+' C'+(sx+ex)/2+' '+sy+' '+(sx+ex)/2+' '+ey+' '+ex+' '+ey,fill:'none',stroke:'#7fa993','stroke-width':'2',opacity:'.65'})}
 for(const [id,node] of Object.entries(workflow)){const [x,y]=positions[id];nodeEl('rect',{x,y,width,height,rx:8,fill:'#17271f',stroke:colors[id],'stroke-width':'2'});nodeEl('rect',{x,y,width,height:30,rx:7,fill:colors[id],opacity:'.7'});const t=nodeEl('text',{x:x+10,y:y+20,fill:'#ffffff','font-size':'13','font-weight':'bold'});t.textContent=id+' · '+titles[id];let lines=[];if(id==='1')lines=['SD 1.5','v1-5-pruned-emaonly'];if(id==='2')lines=[String(tool.prompt||'').slice(0,26),String(tool.prompt||'').slice(26,52)];if(id==='3')lines=[String(tool.negative||'blurry, low quality').slice(0,26),String(tool.negative||'').slice(26,52)];if(id==='4')lines=[node.inputs.width+' × '+node.inputs.height,'batch: 1'];if(id==='5')lines=['steps: '+node.inputs.steps+'  cfg: '+node.inputs.cfg,'sampler: '+node.inputs.sampler_name];if(id==='6')lines=['Latente → imagem'];if(id==='7')lines=['PNG em output/'];if(id==='8')lines=['Pixel Art LoRA','forca: '+node.inputs.strength_model];lines.forEach((line,i)=>{const text=nodeEl('text',{x:x+10,y:y+55+i*19,fill:'#c9e6d4','font-size':'12'});text.textContent=line})}
 $('graphCanvas').replaceChildren(svg);$('graphSummary').textContent='Prévia do workflow API. A seed será aleatória durante a execução; o arquivo exportado usa seed fixa 42 para reprodução. O grafo não representa o editor nativo do ComfyUI.';
 $('graphExport').onclick=()=>{const blob=new Blob([JSON.stringify(workflow,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='WMK_workflow_api_'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 $('graphDialog').showModal()
}
$('graphClose').onclick=()=>$('graphDialog').close();

function imageControl(label,value,type='text',options=[]){
 const wrap=document.createElement('label');wrap.style.cssText='display:block;margin:10px 0;font:12px Consolas;color:#a7d9b5';wrap.append(document.createTextNode(label));
 const input=type==='textarea'?document.createElement('textarea'):type==='select'?document.createElement('select'):document.createElement('input');
 if(type==='select')for(const [v,t] of options){const o=document.createElement('option');o.value=v;o.textContent=t;input.append(o)}
 if(type==='number')input.type='number';
 input.value=value??'';input.style.cssText='display:block;width:100%;box-sizing:border-box;margin-top:5px;padding:8px;background:#102019;color:#ecfff0;border:1px solid #3b7e52;border-radius:5px';wrap.append(input);return {wrap,input};
}
function imageSettingsEditor(host,tool){
 const panel=document.createElement('div');panel.style.cssText='margin:12px 0;padding:12px;background:#0c2015;border:1px solid #386d4a;border-radius:7px';
 const fields={};
 for(const [key,label,val,type,options] of [
 ['prompt','PROMPT POSITIVO',tool.prompt||'','textarea'],
 ['negative','PROMPT NEGATIVO',tool.negative||'blurry, low quality, watermark, text','textarea'],
 ['size','RESOLUÇÃO',tool.size||384,'select',[['256','256 x 256 (teste)'],['320','320 x 320'],['384','384 x 384 (equilibrado)'],['512','512 x 512 (lento)']]],
 ['steps','STEPS',tool.steps||20,'number'],
 ['cfg','CFG',tool.cfg||7,'number'],
 ['sampler','SAMPLER',tool.sampler||'euler','select',[['euler','Euler'],['dpmpp_2m','DPM++ 2M'],['euler_ancestral','Euler ancestral'],['dpmpp_2s_ancestral','DPM++ 2S ancestral'],['uni_pc','UniPC'],['heun','Heun']]],
 ['scheduler','SCHEDULER',tool.scheduler||'normal','select',[['normal','Normal'],['karras','Karras'],['simple','Simple'],['sgm_uniform','SGM Uniform']]],
 ['seed','SEED (-1 = aleatoria)',tool.seed??-1,'number'],
 ['lora','LORA PIXEL ART',tool.lora??'pytorch_lora_weights.safetensors','select',[['pytorch_lora_weights.safetensors','Pixel Art (instalado)'],['','Desativado']]],
 ['lora_strength','FORCA DO LORA (0-1.5)',tool.lora_strength??0.7,'number']
 ]){const {wrap,input}=imageControl(label,val,type,options||[]);panel.append(wrap);fields[key]=input}
 host.append(panel);
 return ()=>({prompt:fields.prompt.value,negative:fields.negative.value,size:Number(fields.size.value),steps:Number(fields.steps.value),cfg:Number(fields.cfg.value),sampler:fields.sampler.value,scheduler:fields.scheduler.value,seed:Number(fields.seed.value),lora:fields.lora.value,lora_strength:Number(fields.lora_strength.value)});
}


