"""WMK Agent Studio — servidor local sem dependências externas."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib import request, error, parse
import json, os, uuid, datetime, threading

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
LOCK=threading.RLock()
DEFAULT={
 "providers":[
  {"id":"ollama","name":"Ollama Local","kind":"ollama","url":"http://127.0.0.1:11434","model":"qwen2.5-coder:3b","api_key":""},
  {"id":"groq","name":"Groq Cloud","kind":"openai","url":"https://api.groq.com/openai/v1","model":"llama-3.3-70b-versatile","api_key":""},
  {"id":"openai","name":"OpenAI","kind":"openai","url":"https://api.openai.com/v1","model":"","api_key":""}
 ],
 "agents":[{"id":"general","name":"WMK Assistente","role":"Assistente geral","icon":"◈","prompt":"Você é um assistente profissional, preciso, prestativo e responde em português do Brasil."},
 {"id":"dev","name":"Arquiteto de Software","role":"Programação e arquitetura","icon":"⌘","prompt":"Você é um engenheiro de software sênior. Explique arquitetura, segurança, testes, desempenho e forneça código correto. Responda em português do Brasil."},
 {"id":"creative","name":"Diretor Criativo","role":"Ideias, jogos e conteúdo","icon":"✦","prompt":"Você é um diretor criativo de jogos e produtos digitais. Proponha ideias concretas e originais em português do Brasil."}],
 "chats":[]
}
def load():
 p=DATA/'studio.json'
 if not p.exists(): save(DEFAULT); return json.loads(json.dumps(DEFAULT))
 return json.loads(p.read_text(encoding='utf-8'))
def save(data):
 p=DATA/'studio.json'; tmp=DATA/'studio.tmp'
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(p)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def call(url,method='GET',body=None,key=None,timeout=90):
 headers={'Accept':'application/json','User-Agent':'WMK-Agent-Studio/1.0'}
 if body is not None: headers['Content-Type']='application/json'
 if key: headers['Authorization']='Bearer '+key
 req=request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
 try:
  with request.urlopen(req,timeout=timeout) as r: return json.loads(r.read(12_000_000).decode())
 except error.HTTPError as e:
  detail=e.read(1000).decode(errors='replace')
  raise ValueError(f'Provedor HTTP {e.code}: {detail}') from e
 except Exception as e: raise ValueError('Falha de conexão com o provedor: '+str(e)) from e
def safe_provider(p):
 return {k:v for k,v in p.items() if k!='api_key'} | {'has_key':bool(p.get('api_key'))}
def model_list(p):
 url=p['url'].rstrip('/')
 if p['kind']=='ollama':
  return [x.get('name') for x in call(url+'/api/tags').get('models',[]) if x.get('name')]
 return [x.get('id') for x in call(url+'/models',key=p.get('api_key')).get('data',[]) if x.get('id')]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args): print('[WMK]',fmt%args,flush=True)
 def reply(self,data,status=200):
  raw=json.dumps(data,ensure_ascii=False).encode()
  self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
 def fail(self,msg,status=400): self.reply({'error':str(msg)},status)
 def do_GET(self):
  path=parse.urlparse(self.path).path
  if path=='/api/state':
   with LOCK:
    s=load(); s['providers']=[safe_provider(p) for p in s['providers']]
   return self.reply(s)
  if path.startswith('/api/models/'):
   with LOCK: p=next((x for x in load()['providers'] if x['id']==path.split('/')[-1]),None)
   if not p: return self.fail('Provedor inexistente',404)
   try: return self.reply({'models':model_list(p)})
   except Exception as e: return self.fail(e,502)
  if path.startswith('/api/image-status/'):
   pid=path.rsplit('/',1)[-1]
   if not __import__('re').fullmatch(r'[0-9a-f-]{36}',pid): return self.fail('ID inválido')
   try:
    h=call('http://127.0.0.1:8188/history/'+pid,timeout=5).get(pid)
    if not h: return self.reply({'status':'processing'})
    images=[img for out in h.get('outputs',{}).values() for img in out.get('images',[])]
    if images:
     img=images[0]
     if img.get('type')!='output': return self.fail('Tipo de imagem inválido')
     qs=parse.urlencode({'filename':img['filename'],'subfolder':img.get('subfolder',''),'type':'output'})
     return self.reply({'status':'done','url':'/api/comfy-image?'+qs})
    return self.reply({'status':'error','error':str(h.get('status',{}).get('messages',[]))[:500]})
   except Exception as e: return self.fail(e,502)
  if path=='/api/comfy-image':
   qs=parse.parse_qs(parse.urlparse(self.path).query)
   name=qs.get('filename',[''])[0]; sub=qs.get('subfolder',[''])[0]
   if not name or Path(name).name!=name or '..' in sub or '\\' in sub or sub.startswith('/'): return self.fail('Nome inválido')
   folder=(Path(r'D:\IA-Local\ComfyUI\output')/sub).resolve()
   root=Path(r'D:\IA-Local\ComfyUI\output').resolve()
   img=(folder/name).resolve()
   if not img.is_relative_to(root) or not img.is_file() or img.suffix.lower()!='.png': return self.fail('Imagem não encontrada',404)
   b=img.read_bytes(); self.send_response(200); self.send_header('Content-Type','image/png'); self.send_header('Content-Disposition','attachment; filename=WMK_'+Path(name).name); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b); return
  if path=='/api/health': return self.reply({'ok':True,'service':'WMK Agent Studio','time':now()})
  if path=='/manuais' or path=='/manuais/': path='/manuais/index.html'
  if path in ('/','/index.html'): path='/index.html'
  if path.startswith('/api/'): return self.fail('Rota não encontrada',404)
  asset=(ROOT/path.lstrip('/')).resolve() if path.startswith('/manuais/') else (ROOT/'web'/path.lstrip('/')).resolve()
  if not (asset.is_relative_to((ROOT/'web').resolve()) or asset.is_relative_to((ROOT/'manuais').resolve())) or not asset.is_file(): return self.fail('Arquivo não encontrado',404)
  mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}.get(asset.suffix,'application/octet-stream')
  b=asset.read_bytes(); self.send_response(200); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(b))); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(b)
 def do_POST(self):
  if not self.path.startswith('/api/'): return self.fail('Rota inválida',404)
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<1 or n>1000000: return self.fail('Tamanho de requisição inválido',413)
   payload=json.loads(self.rfile.read(n))
   if self.path=='/api/save': return self.save_config(payload)
   if self.path=='/api/delete': return self.delete_item(payload)
   if self.path=='/api/chat': return self.chat(payload)
   if self.path=='/api/generate-image': return self.generate_image(payload)
   if self.path=='/api/agent-chat': return self.agent_chat(payload)
   if self.path=='/api/approve-tool': return self.approve_tool(payload)
   return self.fail('Rota inválida',404)
  except (ValueError,KeyError,TypeError) as e: return self.fail(e)
  except Exception as e: return self.fail('Erro interno: '+str(e),500)
 def agent_chat(self,payload):
  cid=str(payload.get('chat_id','')); message=str(payload.get('text','')).strip()
  if not message or len(message)>4000: return self.fail('Mensagem inválida')
  with LOCK:
   state=load(); c=next((x for x in state['chats'] if x['id']==cid),None)
   if not c: return self.fail('Conversa inexistente',404)
   p=next((x for x in state['providers'] if x['id']==c.get('provider_id')),None)
   a=next((x for x in state['agents'] if x['id']==c.get('agent_id')),None)
   if not p or not a: return self.fail('Agente ou provedor inexistente')
   model=c.get('model') or p.get('model')
   if not model: return self.fail('Selecione um modelo')
   history=[{'role':m['role'],'content':m['content']} for m in c.get('messages',[])[-16:] if m.get('role') in ('user','assistant') and not m.get('image_job')]
  schema={'type':'function','function':{'name':'gerar_imagem','description':'Propor geração de imagem no ComfyUI local. Requer confirmação humana antes de executar. Use somente quando o usuário solicitar uma imagem ou arte visual.','parameters':{'type':'object','properties':{'prompt':{'type':'string','description':'Descrição visual detalhada em inglês para Stable Diffusion 1.5'},'size':{'type':'integer','enum':[256,320,384,512]},'steps':{'type':'integer','minimum':5,'maximum':30}},'required':['prompt']}}}
  sys=a.get('prompt','')+'\nVocê pode propor gerar imagens usando a ferramenta gerar_imagem. Nunca diga que gerou uma imagem antes da confirmação e conclusão. Para pedidos de imagem use a ferramenta. Responda em português do Brasil.'
  messages=[{'role':'system','content':sys}]+history+[{'role':'user','content':message}]
  temp=max(0,min(1,float(c.get('temperature',0.7))))
  if p['kind']=='ollama':
   result=call(p['url'].rstrip('/')+'/api/chat','POST',{'model':model,'messages':messages,'tools':[schema],'stream':False,'options':{'temperature':temp}},timeout=300)
   reply=result.get('message',{})
  else:
   result=call(p['url'].rstrip('/')+'/chat/completions','POST',{'model':model,'messages':messages,'tools':[schema],'tool_choice':'auto','temperature':temp},key=p.get('api_key'),timeout=120)
   reply=result.get('choices',[{}])[0].get('message',{})
  calls=reply.get('tool_calls') or []
  proposed=None
  for tool in calls:
   fn=tool.get('function',{})
   if fn.get('name')!='gerar_imagem': continue
   args=fn.get('arguments',{})
   if isinstance(args,str):
    try: args=json.loads(args)
    except json.JSONDecodeError: return self.fail('O modelo enviou argumentos de ferramenta inválidos',502)
   if not isinstance(args,dict): return self.fail('Argumentos inválidos')
   prompt=str(args.get('prompt','')).strip()[:1200]
   if not prompt: return self.fail('O modelo não enviou prompt')
   try: size=int(args.get('size',256)); steps=int(args.get('steps',10))
   except (TypeError,ValueError): return self.fail('Parâmetros inválidos')
   if size not in (256,320,384,512): size=384
   steps=max(5,min(30,steps))
   proposed={'id':uuid.uuid4().hex,'tool':'gerar_imagem','prompt':prompt,'size':size,'steps':steps,'state':'pending','created':now()}
   break
  answer=str(reply.get('content') or '').strip()
  import re
  wants_image=bool(re.search(r'\b(crie|criar|gere|gerar|desenhe|desenhar|produza|faca|faça)\b',message,re.I) and re.search(r'\b(imagem|arte|ilustracao|ilustração|desenho|pixel art|sprite|foto)\b',message,re.I))
  # Alguns modelos retornam a DEFINICAO do schema como texto.
  # Reconhecer esse erro e transformar o pedido visual em proposta,
  # nunca executando automaticamente.
  schema_echo=('"name"' in answer and '"gerar_imagem"' in answer and '"arguments"' in answer and ('"type"' in answer or '"enum"' in answer))
  visual_description=bool(re.search(r'\b(pixel art|dark knight|warrior|medieval|flaming sword|armadura|guerreiro|castelo|portrait|landscape)\b',message,re.I))
  if schema_echo and visual_description: wants_image=True
  if not proposed and wants_image:
   prompt=message[:1200]
   try:
    raw=answer.strip()
    if raw.startswith(chr(96)*3):
     raw=re.sub(r'^'+chr(96)*3+r'(?:json)?\s*|\s*'+chr(96)*3+'$', '',raw)
    obj=json.loads(raw)
    if isinstance(obj,dict) and obj.get('name')=='gerar_imagem':
     args=obj.get('arguments',{})
     if isinstance(args,dict) and isinstance(args.get('prompt'),str) and args['prompt'].strip():
      prompt=args['prompt'].strip()[:1200]
   except (ValueError,TypeError): pass
   proposed={'id':uuid.uuid4().hex,'tool':'gerar_imagem','prompt':prompt,'size':384,'steps':20,'state':'pending','created':now(),'source':'fallback_explicit_intent'}
  if proposed: answer='Preparei uma proposta de imagem. Revise os parâmetros e confirme a execução no ComfyUI.'
  if not answer: answer='O modelo não retornou uma resposta utilizável.'
  with LOCK:
   state=load(); c=next((x for x in state['chats'] if x['id']==cid),None)
   if not c: return self.fail('Conversa excluída',404)
   c.setdefault('messages',[]).append({'role':'user','content':message,'time':now()})
   entry={'role':'assistant','content':answer,'time':now()}
   if proposed:
    c.setdefault('tool_requests',[]).append(proposed)
    entry['tool_request_id']=proposed['id']
   c['messages'].append(entry)
   if c.get('title')=='Nova conversa': c['title']=message[:48]
   c['updated']=now(); save(state)
  return self.reply({'answer':answer,'tool_request':proposed,'chat':c})
 def image_settings(self,raw):
   import re
   raw=raw if isinstance(raw,dict) else {}
   prompt=str(raw.get('prompt','')).strip()[:1200]
   if not prompt: raise ValueError('Prompt positivo obrigatorio')
   negative=str(raw.get('negative','blurry, low quality, watermark, text')).strip()[:1000]
   size=int(raw.get('size',384)); steps=int(raw.get('steps',20))
   cfg=float(raw.get('cfg',7))
   sampler=str(raw.get('sampler','euler'))
   scheduler=str(raw.get('scheduler','normal'))
   seed=int(raw.get('seed',-1))
   lora=str(raw.get('lora','pytorch_lora_weights.safetensors')).strip()
   lora_strength=float(raw.get('lora_strength',0.7))
   if size not in (256,320,384,512): raise ValueError('Resolucao permitida: 256, 320, 384, 512')
   if not 5<=steps<=30: raise ValueError('Steps permitidos: 5-30')
   if not 1<=cfg<=15: raise ValueError('CFG permitido: 1-15')
   if scheduler not in ('normal','karras','simple','sgm_uniform'): raise ValueError('Scheduler nao permitido')
   if lora not in ('','pytorch_lora_weights.safetensors'): raise ValueError('LoRA nao permitido')
   if not 0<=lora_strength<=1.5: raise ValueError('Forca LoRA permitida: 0-1.5')
   if seed < -1 or seed > 4294967295: raise ValueError('Seed fora do intervalo')
   if sampler not in ('euler','dpmpp_2m','euler_ancestral','dpmpp_2s_ancestral','uni_pc','heun'): raise ValueError('Sampler nao permitido')
   return dict(prompt=prompt,negative=negative,size=size,steps=steps,cfg=cfg,sampler=sampler,scheduler=scheduler,seed=seed,lora=lora,lora_strength=lora_strength)
 def workflow_nodes(self,settings):
   a=self.image_settings(settings)
   nodes={
    '1':{'class_type':'CheckpointLoaderSimple','inputs':{'ckpt_name':'v1-5-pruned-emaonly.safetensors'}},
    '2':{'class_type':'CLIPTextEncode','inputs':{'text':a['prompt'],'clip':['1',1]}},
    '3':{'class_type':'CLIPTextEncode','inputs':{'text':a['negative'],'clip':['1',1]}},
    '4':{'class_type':'EmptyLatentImage','inputs':{'width':a['size'],'height':a['size'],'batch_size':1}},
    '5':{'class_type':'KSampler','inputs':{'seed':a['seed'] if a['seed']>=0 else int.from_bytes(os.urandom(4),'big'),'steps':a['steps'],'cfg':a['cfg'],'sampler_name':a['sampler'],'scheduler':a['scheduler'],'denoise':1,'model':['1',0],'positive':['2',0],'negative':['3',0],'latent_image':['4',0]}},
    '6':{'class_type':'VAEDecode','inputs':{'samples':['5',0],'vae':['1',2]}},
    '7':{'class_type':'SaveImage','inputs':{'filename_prefix':'WMK_Agent_Studio','images':['6',0]}}
   }
   if a['lora']:
    nodes['8']={'class_type':'LoraLoader','inputs':{'lora_name':a['lora'],'strength_model':a['lora_strength'],'strength_clip':a['lora_strength'],'model':['1',0],'clip':['1',1]}}
    nodes['2']['inputs']['clip']=['8',1]
    nodes['3']['inputs']['clip']=['8',1]
    nodes['5']['inputs']['model']=['8',0]
   return nodes
 def approve_tool(self,payload):
  cid=str(payload.get('chat_id','')); rid=str(payload.get('request_id',''))
  action=str(payload.get('action',''))
  if action not in ('approve','reject'): return self.fail('Ação inválida')
  with LOCK:
   state=load(); c=next((x for x in state['chats'] if x['id']==cid),None)
   if not c: return self.fail('Conversa inexistente',404)
   item=next((x for x in c.get('tool_requests',[]) if x['id']==rid),None)
   if not item or item.get('state')!='pending': return self.fail('Solicitação já processada ou inexistente',409)
   if action=='approve':
    item.update(self.image_settings(payload.get('settings',item)))
   if action=='reject':
    item['state']='rejected';save(state);return self.reply({'ok':True,'state':'rejected'})
   item['state']='submitting';save(state)
  try:
   res=self.generate_image_job(cid,item)
  except Exception:
   with LOCK:
    state=load();c=next((x for x in state['chats'] if x['id']==cid),None)
    if c:
     item=next((x for x in c.get('tool_requests',[]) if x['id']==rid),None)
     if item and item['state']=='submitting': item['state']='pending';save(state)
   raise
  with LOCK:
   state=load();c=next((x for x in state['chats'] if x['id']==cid),None)
   if c:
    item=next((x for x in c.get('tool_requests',[]) if x['id']==rid),None)
    if item: item['state']='queued';item['image_job']=res['prompt_id']
    c['messages'].append({'role':'assistant','content':'Workflow enviado ao ComfyUI. Acompanhe a geração abaixo.','image_job':res['prompt_id'],'time':now()})
    save(state)
  return self.reply({'ok':True,'state':'queued','prompt_id':res['prompt_id']})
 def generate_image_job(self,cid,settings):
   q=call('http://127.0.0.1:8188/queue',timeout=5)
   if q.get('queue_running') or q.get('queue_pending'): raise ValueError('ComfyUI ocupado: aguarde a fila')
   nodes=self.workflow_nodes(settings)
   res=call('http://127.0.0.1:8188/prompt','POST',{'prompt':nodes,'client_id':'wmk-agent-studio'},timeout=30)
   if res.get('node_errors') or not res.get('prompt_id'): raise ValueError('ComfyUI rejeitou o workflow: '+str(res.get('node_errors')))
   return {'prompt_id':res['prompt_id']}
 def generate_image(self,payload):
   settings=self.image_settings(payload)
   with LOCK:
    c=next((x for x in load()['chats'] if x['id']==payload.get('chat_id')),None)
    if not c: return self.fail('Conversa inexistente',404)
   res=self.generate_image_job(payload['chat_id'],settings)
   pid=res['prompt_id']
   with LOCK:
    st=load(); c=next((x for x in st['chats'] if x['id']==payload['chat_id']),None)
    if c:
     c.setdefault('messages',[]).append({'role':'user','content':'[Imagem solicitada] '+settings['prompt'],'time':now()})
     c['messages'].append({'role':'assistant','content':'Imagem enviada ao ComfyUI. Aguarde a conclusao.','image_job':pid,'time':now()})
     c['updated']=now();save(st)
   return self.reply({'prompt_id':pid,'status':'queued'})
 def delete_item(self,payload):
  section=payload.get('section'); iid=payload.get('id')
  if section not in ('chats','agents','providers') or not iid: return self.fail('Dados invalidos')
  with LOCK:
   s=load(); s[section]=[x for x in s[section] if x['id']!=iid]; save(s)
  return self.reply({'ok':True})
 def save_config(self,payload):
  section=payload.get('section'); item=payload.get('item')
  if section not in ('agents','providers','chats') or not isinstance(item,dict): return self.fail('Dados inválidos')
  with LOCK:
   s=load(); iid=str(item.get('id') or uuid.uuid4().hex)
   if section=='providers':
    old=next((x for x in s[section] if x['id']==iid),{})
    if item.get('api_key')=='': item['api_key']=old.get('api_key','')
    item={k:item.get(k,old.get(k,'')) for k in ('id','name','kind','url','model','api_key')}
    item['id']=iid
    if item['kind'] not in ('ollama','openai'): return self.fail('Tipo inválido')
    u=parse.urlparse(item['url'])
    if u.scheme not in ('http','https') or not u.netloc: return self.fail('URL inválida')
    if u.scheme=='http' and u.hostname not in ('localhost','127.0.0.1','::1'): return self.fail('HTTP permitido apenas para localhost')
   else: item['id']=iid
   s[section]=[x for x in s[section] if x['id']!=iid]+[item]
   save(s)
  return self.reply({'ok':True,'id':iid})
 def chat(self,payload):
  cid=str(payload.get('chat_id','')); text=str(payload.get('text','')).strip()
  if not text or len(text)>16000: return self.fail('Mensagem vazia ou muito longa')
  with LOCK:
   s=load(); c=next((x for x in s['chats'] if x['id']==cid),None)
   if not c: return self.fail('Conversa inexistente',404)
   p=next((x for x in s['providers'] if x['id']==c.get('provider_id')),None)
   a=next((x for x in s['agents'] if x['id']==c.get('agent_id')),None)
   if not p or not a: return self.fail('Provedor ou agente não encontrado')
   model=str(c.get('model') or p.get('model') or '').strip()
   if not model: return self.fail('Selecione um modelo')
   messages=[{'role':'system','content':a.get('prompt','')}] + [{'role':m['role'],'content':m['content']} for m in c.get('messages',[])[-24:] if m.get('role') in ('user','assistant')]
   messages.append({'role':'user','content':text})
  opts={'temperature':max(0,min(2,float(c.get('temperature',0.7))))}
  if p['kind']=='ollama':
   response=call(p['url'].rstrip('/')+'/api/chat','POST',{'model':model,'messages':messages,'stream':False,'options':opts},timeout=300)
   answer=response.get('message',{}).get('content','')
  else:
   response=call(p['url'].rstrip('/')+'/chat/completions','POST',{'model':model,'messages':messages,'temperature':opts['temperature']},key=p.get('api_key'),timeout=120)
   answer=response.get('choices',[{}])[0].get('message',{}).get('content','')
  if not isinstance(answer,str) or not answer.strip(): return self.fail('O provedor não retornou texto',502)
  with LOCK:
   s=load(); c=next((x for x in s['chats'] if x['id']==cid),None)
   if c is None: return self.fail('Conversa excluída',404)
   c.setdefault('messages',[]).extend([{'role':'user','content':text,'time':now()},{'role':'assistant','content':answer,'time':now()}])
   c['updated']=now()
   if c.get('title')=='Nova conversa': c['title']=text[:48]
   save(s)
  return self.reply({'answer':answer,'chat':c})
if __name__=='__main__':
 print('WMK Agent Studio: http://127.0.0.1:8765',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()




